# Fardayab — AI-Powered Crypto Signal Telegram Bot

Fardayab (فردایاب) is an automated cryptocurrency signal bot that combines **Freqtrade** algorithmic trading with **GPT-4 analysis** to deliver actionable trading signals via Telegram.

## Overview

An end-to-end crypto trading intelligence system that backtests strategies, runs live signal generation, and delivers formatted alerts to a Telegram channel — all deployed on Railway with Docker.

## Features

- **AI-Enhanced Signals** — GPT-4 analyzes market context and enhances raw Freqtrade signals with sentiment and reasoning
- **Freqtrade Integration** — Battle-tested algorithmic trading framework with custom strategies and backtesting
- **Telegram Bot** — Formatted signal delivery with entry, stop-loss, and take-profit levels
- **Multi-Exchange Support** — Binance, Bybit, and other major exchanges via CCXT
- **Backtesting Engine** — Historical strategy validation before live deployment
- **Docker + Railway Deployment** — Containerized microservices deployed on Railway cloud
- **Strategy Optimization** — Multiple strategy variants with win-rate tuning (Optimal, Ultra-Winrate modes)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Trading Engine | Freqtrade |
| AI Analysis | OpenAI GPT-4 API |
| Bot Framework | python-telegram-bot |
| Exchange APIs | Binance API, CCXT |
| Deployment | Docker, Railway |
| Language | Python 3.10+ |

## Architecture

```
Market Data → Freqtrade Strategy → Signal Generator
                                        ↓
                              GPT-4 Context Analysis
                                        ↓
                              Telegram Bot → Channel
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials:
   - Telegram Bot Token & Channel ID
   - OpenAI API Key
   - Binance/Exchange API Key & Secret
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `python main.py`
5. Or deploy via Docker: `docker-compose up -d`

## Configuration

See `.env.example` for all required environment variables. Never commit your actual `.env` file.

## Disclaimer

This bot is for educational and research purposes. Cryptocurrency trading involves significant financial risk. Past performance does not guarantee future results.

## License

MIT License
