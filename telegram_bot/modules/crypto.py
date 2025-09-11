from __future__ import annotations

import asyncio
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> Any:
    r = await client.get(url, params=params, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_crypto_and_fx(timeout: float = 15.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        # CoinGecko simple price for BTC/USD
        coingecko = asyncio.create_task(
            _get_json(
                client,
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
            )
        )
        # ExchangeRate.host (USD to IRR, EUR)
        fx = asyncio.create_task(
            _get_json(
                client,
                "https://api.exchangerate.host/latest",
                {"base": "USD", "symbols": "IRR,EUR"},
            )
        )

        data: dict = {"btc": None, "fx": None}
        try:
            cg = await coingecko
            data["btc"] = cg.get("bitcoin")
        except Exception:
            data["btc"] = None
        try:
            fxj = await fx
            data["fx"] = fxj.get("rates", {})
        except Exception:
            data["fx"] = None

        # Derived lines for fallback formatter
        btc = data.get("btc") or {}
        usd = (data.get("fx") or {}).get("IRR")
        btc_price = btc.get("usd")
        btc_chg = btc.get("usd_24h_change")
        usd_line = None
        if usd:
            usd_line = f"دلار: حدود {round(usd, 2)} تومان"
        btc_line = None
        if btc_price is not None:
            pct = f" ({round(btc_chg, 2)}%)" if btc_chg is not None else ""
            btc_line = f"بیت‌کوین: {btc_price}$ {pct}"

        data["usd_line"] = usd_line
        data["btc_line"] = btc_line
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
