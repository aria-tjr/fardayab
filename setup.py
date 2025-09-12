#!/usr/bin/env python3
"""
Setup script for Telegram Bot deployment
"""

from setuptools import setup, find_packages

setup(
    name="telegram-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.8.0",
        "httpx>=0.27.0",
        "python-dotenv>=1.0.1",
        "APScheduler>=3.10.4",
        "aiosqlite>=0.20.0",
        "openai>=1.40.0",
        "pytrends>=4.9.2",
        "tenacity>=8.5.0",
        "orjson>=3.10.7",
    ],
    entry_points={
        "console_scripts": [
            "telegram-bot=telegram_bot.main:main",
        ],
    },
    python_requires=">=3.12",
)
