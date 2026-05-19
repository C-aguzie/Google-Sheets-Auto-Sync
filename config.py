"""Project settings for the CoinGecko to Google Sheets sync."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR: Path = Path(__file__).parent.resolve()
load_dotenv(ROOT_DIR / ".env")

CREDENTIALS_FILE: Path = ROOT_DIR / os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
LOG_FILE: Path = ROOT_DIR / "sync.log"

SHEET_NAME: str = os.getenv("SHEET_NAME", "Crypto Dashboard")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "").strip()

SCOPES: list[str] = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER_RANGE: str = "A1"
DATA_START_ROW: int = 2
WORKSHEET_INDEX: int = 0

COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT_SECONDS: int = 15

TRACKED_COINS: list[str] = [
    "bitcoin",
    "ethereum",
    "solana",
    "binancecoin",
    "cardano",
    "ripple",
    "dogecoin",
    "polkadot",
]

VS_CURRENCY: str = "usd"

COINGECKO_FIELDS: list[str] = [
    "current_price",
    "price_change_percentage_24h",
    "market_cap",
    "total_volume",
    "high_24h",
    "low_24h",
]

SYNC_INTERVAL_SECONDS: int = int(os.getenv("SYNC_INTERVAL_SECONDS", 3600))
RETRY_DELAY_SECONDS: int = 60
MAX_CONSECUTIVE_FAILURES: int = 5


@dataclass(frozen=True)
class Column:
    label: str
    key: str


COLUMNS: list[Column] = [
    Column("Coin", "name"),
    Column("Symbol", "symbol"),
    Column("Price (USD)", "current_price"),
    Column("24h Change (%)", "price_change_percentage_24h"),
    Column("Market Cap (USD)", "market_cap"),
    Column("24h Volume (USD)", "total_volume"),
    Column("24h High (USD)", "high_24h"),
    Column("24h Low (USD)", "low_24h"),
    Column("Last Updated", "last_updated"),
]
