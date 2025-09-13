from __future__ import annotations

import json
from typing import Sequence
from urllib.parse import quote
from telegram_bot.utils.json_encoder import safe_json_dumps


def build_line_chart_url(title: str, labels: Sequence[str], datasets: list[dict]) -> str:
    cfg = {
        "type": "line",
        "data": {
            "labels": list(labels),
            "datasets": datasets,
        },
        "options": {
            "plugins": {
                "legend": {"display": True},
                "title": {"display": True, "text": title},
            },
            "scales": {
                "y": {"beginAtZero": False}
            }
        },
    }
    return f"https://quickchart.io/chart?c={quote(safe_json_dumps(cfg))}"


def btc_chart_url(prices: list[tuple[int, float]]) -> str | None:
    if not prices:
        return None
    from datetime import datetime
    labels = [datetime.utcfromtimestamp(ts/1000).strftime('%m-%d') for ts, _ in prices]
    values = [round(v, 2) for _, v in prices]
    url = build_line_chart_url(
        "BTC/USD - Last 7d",
        labels,
        [
            {"label": "BTC", "data": values, "borderColor": "#f2a900", "fill": False}
        ],
    )
    return url

