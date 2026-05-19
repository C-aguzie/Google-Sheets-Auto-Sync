"""Run the CoinGecko to Google Sheets sync on a fixed interval."""

from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timezone
from types import FrameType

from config import MAX_CONSECUTIVE_FAILURES, RETRY_DELAY_SECONDS, SYNC_INTERVAL_SECONDS
from fetcher import fetch_crypto_prices
from logger import log
from sheets import write_to_sheet


_running = True
_consecutive_failures = 0


def _handle_signal(signum: int, frame: FrameType | None) -> None:  # noqa: ARG001
    global _running
    sig_name = signal.Signals(signum).name
    log.info("Received %s; stopping after the current sync", sig_name)
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def run_sync() -> bool:
    start = time.perf_counter()
    log.info("Sync started")

    rows = fetch_crypto_prices()
    if not rows:
        log.error("Fetch returned no data")
        return False

    success = write_to_sheet(rows)
    elapsed = time.perf_counter() - start

    if success:
        log.info("Sync complete in %.2fs", elapsed)
    else:
        log.error("Sync failed after %.2fs", elapsed)

    return success


def main() -> None:
    global _consecutive_failures

    log.info("Sync scheduler started; interval=%ds", SYNC_INTERVAL_SECONDS)
    next_run = time.monotonic()

    while _running:
        now = time.monotonic()

        if now >= next_run:
            next_run = now + SYNC_INTERVAL_SECONDS
            success = run_sync()

            if success:
                _consecutive_failures = 0
                _log_next_run(next_run)
            else:
                _consecutive_failures += 1
                log.warning(
                    "Consecutive failures: %d/%d",
                    _consecutive_failures,
                    MAX_CONSECUTIVE_FAILURES,
                )

                if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.critical("Stopping after too many failed sync attempts")
                    sys.exit(1)

                next_run = time.monotonic() + RETRY_DELAY_SECONDS
                log.info("Retrying in %ds", RETRY_DELAY_SECONDS)

        time.sleep(1)

    log.info("Sync scheduler stopped")


def _log_next_run(next_run_monotonic: float) -> None:
    delta_seconds = max(0, next_run_monotonic - time.monotonic())
    next_wall = datetime.fromtimestamp(time.time() + delta_seconds, tz=timezone.utc)
    log.info("Next sync at %s UTC", next_wall.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
