# crypto-sheets-sync

Pulls live market data from CoinGecko and writes it into a Google Sheet on a configurable schedule. The sheet becomes a lightweight live dashboard that refreshes without manual updates.

## What it does

| Step | Module | Detail |
|------|--------|--------|
| 1 | `fetcher.py` | Calls CoinGecko `/coins/markets` for the tracked coins |
| 2 | `sheets.py` | Authenticates with a Google service account and writes headers plus data rows |
| 3 | `scheduler.py` | Runs the sync immediately, then repeats every `SYNC_INTERVAL_SECONDS` |

## Setup

### 1. Google Cloud credentials

1. Go to <https://console.cloud.google.com> and create a project.
2. Enable the Google Sheets API and Google Drive API.
3. Go to IAM & Admin > Service Accounts and create a service account.
4. Under Keys, create a JSON key and download it.
5. Rename the downloaded JSON file to `credentials.json` and place it in this project directory.
6. Open your Google Sheet, click Share, and add the service account email with Editor access.

Important: `credentials.json` is gitignored. Do not commit it.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure

Copy the example env file:

```bash
copy .env.example .env
```

Then edit `.env`:

```env
SHEET_NAME=Crypto Dashboard
GOOGLE_SHEET_ID=
SYNC_INTERVAL_SECONDS=3600
GOOGLE_CREDENTIALS_FILE=credentials.json
```

`GOOGLE_SHEET_ID` is optional, but it is the most reliable way to open the sheet. Copy it from the Google Sheet URL:

```text
https://docs.google.com/spreadsheets/d/SHEET_ID_IS_HERE/edit
```

Most remaining settings live in `config.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `SHEET_NAME` | `Crypto Dashboard` | Exact name of your Google Sheet |
| `TRACKED_COINS` | 8 coins | CoinGecko coin IDs to track |
| `SYNC_INTERVAL_SECONDS` | `3600` | Update interval in seconds |

### 4. Run

Run one sync:

```bash
python -c "from fetcher import fetch_crypto_prices; from sheets import write_to_sheet; write_to_sheet(fetch_crypto_prices())"
```

Start the hourly scheduler:

```bash
python scheduler.py
```

## Tests

```bash
python -m pytest -q
```

## Project structure

```text
crypto-sheets-sync/
|-- config.py
|-- fetcher.py
|-- sheets.py
|-- scheduler.py
|-- logger.py
|-- requirements.txt
|-- README.md
|-- .env.example
|-- .gitignore
|-- screenshots/
|   |-- live-sheet.png
|   `-- scheduler-success.png
`-- tests/
    `-- test_fetcher.py
```

The local-only files below should exist on your machine, but should not be committed:

```text
.env
credentials.json
sync.log
__pycache__/
.pytest_cache/
```

## Screenshot proof

The screenshots below show the sync working end to end.

### Live Google Sheet

![Live Google Sheet updated by the sync](screenshots/live-sheet.png)

### Scheduler Run

![Terminal showing successful scheduler run](screenshots/scheduler-success.png)

When taking the sheet screenshot, make sure the `Last Updated` column is visible. That timestamp is the easiest proof that the sheet is being refreshed by the script.

Suggested portfolio caption:

> Built a zero-maintenance live data pipeline. The Google Sheet refreshes every hour through a scheduled Python service using the CoinGecko and Google Sheets APIs.
