"""Google Sheets writer."""

from __future__ import annotations

from typing import Any

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException

from config import (
    COLUMNS,
    CREDENTIALS_FILE,
    DATA_START_ROW,
    HEADER_RANGE,
    GOOGLE_SHEET_ID,
    SCOPES,
    SHEET_NAME,
    WORKSHEET_INDEX,
)
from logger import log


def write_to_sheet(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        log.warning("No rows to write")
        return False

    try:
        client = _authenticate()
        worksheet = _open_worksheet(client)
        _clear_old_data(worksheet, len(rows))
        _write_headers(worksheet)
        _write_data(worksheet, rows)
        _apply_formatting(worksheet)
    except FileNotFoundError as exc:
        log.critical(str(exc))
        return False
    except GSpreadException as exc:
        log.exception("Google Sheets write failed: %s", exc)
        return False
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected sheet write error: %s", exc)
        return False

    log.info("Updated '%s' with %d row(s)", SHEET_NAME, len(rows))
    return True


def _authenticate() -> gspread.Client:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Missing Google credentials file: {CREDENTIALS_FILE}\n"
            "Download your service account key and save it there."
        )

    creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=SCOPES)
    return gspread.authorize(creds)


def _open_worksheet(client: gspread.Client) -> gspread.Worksheet:
    if GOOGLE_SHEET_ID:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    else:
        spreadsheet = client.open(SHEET_NAME)

    return spreadsheet.get_worksheet(WORKSHEET_INDEX)


def _clear_old_data(sheet: gspread.Worksheet, new_row_count: int) -> None:
    last_row = DATA_START_ROW + new_row_count - 1
    sheet.batch_clear([f"A1:Z{last_row}"])


def _write_headers(sheet: gspread.Worksheet) -> None:
    headers = [[col.label for col in COLUMNS]]
    sheet.update(
        values=headers,
        range_name=HEADER_RANGE,
        value_input_option="USER_ENTERED",
    )


def _write_data(sheet: gspread.Worksheet, rows: list[dict[str, Any]]) -> None:
    matrix = [[row.get(col.key, "N/A") for col in COLUMNS] for row in rows]
    sheet.update(
        values=matrix,
        range_name=f"A{DATA_START_ROW}",
        value_input_option="USER_ENTERED",
    )


def _apply_formatting(sheet: gspread.Worksheet) -> None:
    try:
        sheet.spreadsheet.batch_update(
            {
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet.id,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "textFormat": {"bold": True, "fontSize": 11},
                                    "backgroundColor": {
                                        "red": 0.122,
                                        "green": 0.141,
                                        "blue": 0.196,
                                    },
                                    "horizontalAlignment": "CENTER",
                                }
                            },
                            "fields": "userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)",
                        }
                    },
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet.id,
                                "gridProperties": {"frozenRowCount": 1},
                            },
                            "fields": "gridProperties.frozenRowCount",
                        }
                    },
                    {
                        "autoResizeDimensions": {
                            "dimensions": {
                                "sheetId": sheet.id,
                                "dimension": "COLUMNS",
                                "startIndex": 0,
                                "endIndex": len(COLUMNS),
                            }
                        }
                    },
                ]
            }
        )
    except GSpreadException as exc:
        log.warning("Could not apply sheet formatting: %s", exc)
