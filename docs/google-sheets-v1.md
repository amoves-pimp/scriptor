# Google Sheets connector v1

## Scope

Controlled Google Sheets connector for Scriptor only.

Primary flow:

`task_id -> export_rows -> managed spreadsheet tab -> sheet_url`

## Routes

- `POST /google-sheets/read`
- `POST /google-sheets/write`
- `POST /google-sheets/export?task_id=...`
- `GET /google-sheets/meta`

## Auth

- OAuth 2.0 under one Google account
- refresh token stored only in Scriptor env/secrets
- tokens and auth headers are never logged

## Required env

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token`
- `GOOGLE_SHEETS_BASE_URL=https://sheets.googleapis.com/v4/spreadsheets`
- `GOOGLE_SHEETS_MAX_ROWS_PER_REQUEST=1000`

## Hard rules

1. Google Sheets is a controlled connector, not a universal engine.
2. Read/write/export only through Scriptor.
3. Sheets receives only stable `export_rows`.
4. CSV remains the source of truth.
5. One managed spreadsheet only.
6. One task = one tab.
7. Re-export same task = overwrite existing tab.
8. Read only registered tabs from storage.
9. Write only registered tabs from storage.
10. No Drive search and no arbitrary access to all spreadsheets.

## Storage mapping

Stored in task state:

- `spreadsheet_id`
- `sheet_id`
- `tab_name`
- `sheet_url`

## Read / write policy

### Export

- creates the tab if missing
- otherwise overwrites the existing task tab

### Write

- accepts only `task_id`
- loads registered tab metadata from storage
- overwrites the registered tab with current `export_rows`

### Read

- accepts only `task_id`
- reads only the registered tab from storage
- max rows per read: `1000`
