# Fardayab — AI-Powered Crypto Signal Telegram Bot

Fardayab (فردایاب) is an automated cryptocurrency signal bot that generates rule-based technical-analysis trading signals and publishes them, together with GPT-written market content, to a Telegram channel.

## Overview

An end-to-end crypto trading intelligence system that backtests strategies, runs live signal generation, and delivers formatted alerts to a Telegram channel — all deployed on Railway with Docker.

## Features

- **Rule-based signal engine** — trend-following, mean-reversion and momentum strategies on technical indicators (`src/strategies/`)
- **GPT-written content** — OpenAI generates market summaries, altcoin spotlights and education posts (`src/content/content_generator.py`); it does not generate the trade signals
- **Telegram Bot** — Formatted signal delivery with entry, stop-loss, and take-profit levels
- **Multi-Exchange Support** — Binance, Bybit, and other major exchanges via CCXT
- **Backtesting Engine** — Historical strategy validation before live deployment
- **Docker + Railway Deployment** — Containerized microservices deployed on Railway cloud
- **Strategy Optimization** — Multiple strategy variants with win-rate tuning (Optimal, Ultra-Winrate modes)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Signal Engine | Custom Python strategies (`src/strategies/`) |
| AI Content | OpenAI API (written posts only) |
| Bot Framework | python-telegram-bot |
| Exchange APIs | Binance API, CCXT |
| Deployment | Docker, Railway |
| Language | Python 3.10+ |

## Architecture

```
Market Data (CCXT) → Indicator strategies → Signal Generator → Telegram Bot → Channel
                                                   ↑
                         OpenAI → market summaries / education posts
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials:
   - Telegram Bot Token & Channel ID
   - OpenAI API Key
   - Binance/Exchange API Key & Secret
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `python -m src.main`
5. Or deploy via Docker: `docker-compose up -d`

## Configuration

See `.env.example` for all required environment variables (credentials are intentionally empty). Never commit your actual `.env` file.

## Backtest note

The backtest reports in this repository are historical experiments and have not been independently verified. An independent walk-forward test of the default `SignalGenerator` on Binance BTCUSDT/ETHUSDT 5m data (Apr–Sep 2026, 1x, 0.04% fee per side) was strongly negative. Do not treat the win-rate figures in the `*_RESULTS.md` files as expected live performance.

## Disclaimer

This bot is for educational and research purposes. Cryptocurrency trading involves significant financial risk. Past performance does not guarantee future results.

## License

MIT — see [LICENSE](LICENSE).
