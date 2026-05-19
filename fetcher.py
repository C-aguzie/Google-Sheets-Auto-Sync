"""CoinGecko API client."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from config import COINGECKO_BASE_URL, REQUEST_TIMEOUT_SECONDS, TRACKED_COINS, VS_CURRENCY
from logger import log


def fetch_crypto_prices() -> list[dict[str, Any]]:
    """Return current market data for the configured coins."""
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    params = {
        "vs_currency": VS_CURRENCY,
        "ids": ",".join(TRACKED_COINS),
        "order": "market_cap_desc",
        "per_page": len(TRACKED_COINS),
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        log.error("CoinGecko request timed out after %ss", REQUEST_TIMEOUT_SECONDS)
        return []
    except requests.exceptions.HTTPError as exc:
        log.error("CoinGecko HTTP error: %s", exc)
        return []
    except requests.exceptions.RequestException as exc:
        log.error("CoinGecko network error: %s", exc)
        return []

    raw: list[dict[str, Any]] = response.json()
    log.info("Fetched data for %d coin(s)", len(raw))
    return [_parse_coin(coin) for coin in raw]


def _parse_coin(raw: dict[str, Any]) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "name": raw.get("name", "-"),
        "symbol": raw.get("symbol", "-").upper(),
        "current_price": _fmt_price(raw.get("current_price")),
        "price_change_percentage_24h": _fmt_pct(raw.get("price_change_percentage_24h")),
        "market_cap": _fmt_large(raw.get("market_cap")),
        "total_volume": _fmt_large(raw.get("total_volume")),
        "high_24h": _fmt_price(raw.get("high_24h")),
        "low_24h": _fmt_price(raw.get("low_24h")),
        "last_updated": timestamp,
    }


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.4f}" if value < 1 else f"${value:,.2f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _fmt_large(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"
