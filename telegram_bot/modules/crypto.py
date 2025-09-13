from __future__ import annotations

import asyncio
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from telegram_bot.modules.binance_api import BinanceAPI


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> Any:
    r = await client.get(url, params=params, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_crypto_and_fx(settings, timeout: float = 15.0) -> dict:
    # Initialize Binance API
    binance_api = BinanceAPI(settings)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Binance real-time crypto data (primary source)
        binance_crypto = asyncio.create_task(binance_api.get_crypto_prices())
        
        # CoinGecko comprehensive crypto data (backup)
        crypto_data = asyncio.create_task(
            _get_json(
                client,
                "https://api.coingecko.com/api/v3/coins/markets",
                {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": "10",
                    "page": "1",
                    "sparkline": "true",
                    "price_change_percentage": "24h,7d,30d"
                },
            )
        )
        
        # Binance forex rates (primary source)
        binance_forex = asyncio.create_task(binance_api.get_forex_rates())
        
        # ExchangeRate.host (USD to IRR, EUR, GBP, JPY) - backup
        fx = asyncio.create_task(
            _get_json(
                client,
                "https://api.exchangerate.host/latest",
                {"base": "USD", "symbols": "IRR,EUR,GBP,JPY,CHF,CAD,AUD"},
            )
        )
        
        # Fear & Greed Index
        fear_greed = asyncio.create_task(
            _get_json(
                client,
                "https://api.alternative.me/fng/",
            )
        )

        data: dict = {"crypto": None, "fx": None, "fear_greed": None, "binance_crypto": None, "binance_forex": None}
        
        # Get Binance data (primary source)
        try:
            binance_crypto_data = await binance_crypto
            data["binance_crypto"] = binance_crypto_data
        except Exception as e:
            data["binance_crypto"] = {}
        
        try:
            binance_forex_data = await binance_forex
            data["binance_forex"] = binance_forex_data
        except Exception as e:
            data["binance_forex"] = {}
        
        # Get backup data
        try:
            crypto = await crypto_data
            data["crypto"] = crypto
        except Exception:
            data["crypto"] = []
        try:
            fxj = await fx
            data["fx"] = fxj.get("rates", {})
        except Exception:
            data["fx"] = {}
        try:
            fg = await fear_greed
            data["fear_greed"] = fg.get("data", [{}])[0]
        except Exception:
            data["fear_greed"] = {"value": "50", "value_classification": "Neutral"}

        # Enhanced derived lines for fallback formatter
        # Prioritize Binance data over CoinGecko
        binance_crypto_data = data.get("binance_crypto", {}).get("crypto_prices", {})
        binance_forex_data = data.get("binance_forex", {}).get("forex_rates", {})
        
        crypto_list = data.get("crypto") or []
        fx_rates = data.get("fx") or {}
        fg_data = data.get("fear_greed") or {}
        
        # Bitcoin data (Binance first, then CoinGecko)
        btc_data = binance_crypto_data.get("BTC", {})
        if not btc_data:
            btc_data = next((coin for coin in crypto_list if coin.get("id") == "bitcoin"), {})
        
        btc_price = btc_data.get("price", 0)
        btc_chg = btc_data.get("price_change_24h", 0)
        btc_market_cap = btc_data.get("market_cap", 0)
        
        # Ethereum data (Binance first, then CoinGecko)
        eth_data = binance_crypto_data.get("ETH", {})
        if not eth_data:
            eth_data = next((coin for coin in crypto_list if coin.get("id") == "ethereum"), {})
        
        eth_price = eth_data.get("price", 0)
        eth_chg = eth_data.get("price_change_24h", 0)
        
        # Forex data (Binance first, then ExchangeRate.host)
        eur_usd = binance_forex_data.get("EUR/USD", {}).get("rate", 0)
        gbp_usd = binance_forex_data.get("GBP/USD", {}).get("rate", 0)
        
        if not eur_usd:
            eur_usd = 1 / fx_rates.get("EUR", 1) if fx_rates.get("EUR") else 0
        if not gbp_usd:
            gbp_usd = 1 / fx_rates.get("GBP", 1) if fx_rates.get("GBP") else 0
        
        # USD/IRR (only from ExchangeRate.host)
        usd_irr = fx_rates.get("IRR", 0)
        
        # Fear & Greed Index
        fg_value = fg_data.get("value", "50")
        fg_classification = fg_data.get("value_classification", "Neutral")
        
        # Format lines
        btc_line = f"بیت‌کوین: ${btc_price:,.0f} ({btc_chg:+.2f}%)" if btc_price else "بیت‌کوین: داده در دسترس نیست"
        eth_line = f"اتریوم: ${eth_price:,.0f} ({eth_chg:+.2f}%)" if eth_price else "اتریوم: داده در دسترس نیست"
        usd_line = f"دلار: {usd_irr:,.0f} تومان" if usd_irr else "دلار: داده در دسترس نیست"
        eur_line = f"یورو: ${eur_usd:.4f}" if eur_usd else "یورو: داده در دسترس نیست"
        gbp_line = f"پوند: ${gbp_usd:.4f}" if gbp_usd else "پوند: داده در دسترس نیست"
        fg_line = f"شاخص ترس و طمع: {fg_value} ({fg_classification})"

        data["btc_line"] = btc_line
        data["eth_line"] = eth_line
        data["usd_line"] = usd_line
        data["eur_line"] = eur_line
        data["gbp_line"] = gbp_line
        data["fear_greed_line"] = fg_line
        data["btc_market_cap"] = btc_market_cap
        data["total_crypto_count"] = len(crypto_list)
        
        return data


async def fetch_btc_market_chart(days: int = 7, timeout: float = 15.0) -> list[tuple[int, float]]:
    import httpx
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(
                "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
                params={"vs_currency": "usd", "days": days},
            )
            r.raise_for_status()
            data = r.json()
            prices = data.get("prices") or []
            out: list[tuple[int, float]] = []
            for ts, price in prices:
                out.append((int(ts), float(price)))
            return out
        except Exception:
            return []
