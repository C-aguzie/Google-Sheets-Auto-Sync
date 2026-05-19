"""Tests for the CoinGecko fetcher."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

_cfg = types.ModuleType("config")
_cfg.COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
_cfg.REQUEST_TIMEOUT_SECONDS = 5
_cfg.TRACKED_COINS = ["bitcoin", "ethereum"]
_cfg.VS_CURRENCY = "usd"
sys.modules["config"] = _cfg

_log_mod = types.ModuleType("logger")
_log_mod.log = MagicMock()
sys.modules["logger"] = _log_mod

from fetcher import _fmt_large, _fmt_pct, _fmt_price, _parse_coin  # noqa: E402


class TestFmtPrice:
    def test_large_price(self):
        assert _fmt_price(67432.11) == "$67,432.11"

    def test_small_price(self):
        assert _fmt_price(0.00042) == "$0.0004"

    def test_sub_dollar(self):
        assert _fmt_price(0.25) == "$0.2500"

    def test_none(self):
        assert _fmt_price(None) == "N/A"


class TestFmtPct:
    def test_positive(self):
        assert _fmt_pct(3.45) == "+3.45%"

    def test_negative(self):
        assert _fmt_pct(-1.2) == "-1.20%"

    def test_zero(self):
        assert _fmt_pct(0.0) == "+0.00%"

    def test_none(self):
        assert _fmt_pct(None) == "N/A"


class TestFmtLarge:
    def test_billions(self):
        assert _fmt_large(1_300_000_000) == "$1.30B"

    def test_millions(self):
        assert _fmt_large(5_500_000) == "$5.50M"

    def test_thousands(self):
        assert _fmt_large(850_000) == "$850,000"

    def test_none(self):
        assert _fmt_large(None) == "N/A"


SAMPLE_RAW = {
    "name": "Bitcoin",
    "symbol": "btc",
    "current_price": 67000.0,
    "price_change_percentage_24h": 2.31,
    "market_cap": 1_300_000_000_000,
    "total_volume": 28_000_000_000,
    "high_24h": 68500.0,
    "low_24h": 65000.0,
}


class TestParseCoin:
    def test_name_preserved(self):
        row = _parse_coin(SAMPLE_RAW)
        assert row["name"] == "Bitcoin"

    def test_symbol_uppercased(self):
        row = _parse_coin(SAMPLE_RAW)
        assert row["symbol"] == "BTC"

    def test_price_formatted(self):
        row = _parse_coin(SAMPLE_RAW)
        assert row["current_price"].startswith("$")

    def test_pct_change_has_sign(self):
        row = _parse_coin(SAMPLE_RAW)
        assert "+" in row["price_change_percentage_24h"] or "-" in row["price_change_percentage_24h"]

    def test_market_cap_in_billions(self):
        row = _parse_coin(SAMPLE_RAW)
        assert "B" in row["market_cap"]

    def test_last_updated_utc(self):
        row = _parse_coin(SAMPLE_RAW)
        assert "UTC" in row["last_updated"]

    def test_missing_fields_fallback(self):
        row = _parse_coin({})
        assert row["name"] == "-"
        assert row["current_price"] == "N/A"


class TestFetchCryptoPrices:
    @patch("fetcher.requests.get")
    def test_returns_parsed_rows(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [SAMPLE_RAW]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        from fetcher import fetch_crypto_prices

        result = fetch_crypto_prices()
        assert len(result) == 1
        assert result[0]["name"] == "Bitcoin"

    @patch("fetcher.requests.get")
    def test_timeout_returns_empty(self, mock_get):
        import requests as req

        mock_get.side_effect = req.exceptions.Timeout

        from fetcher import fetch_crypto_prices

        assert fetch_crypto_prices() == []

    @patch("fetcher.requests.get")
    def test_http_error_returns_empty(self, mock_get):
        import requests as req

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError("429")
        mock_get.return_value = mock_response

        from fetcher import fetch_crypto_prices

        assert fetch_crypto_prices() == []
