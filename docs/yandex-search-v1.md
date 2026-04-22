# Yandex Search API v1.1

## Scope

Single pipeline only:

`query -> Yandex Search API -> multi-page normalized rows -> CSV -> review`

No Wordstat. No Google Sheets. No shared universal Yandex engine.

## Confirmed v1 route

- `POST /yandex/search`

## Official API contour

Based on official Yandex Search API docs / API reference:

- service URL: `https://searchapi.api.cloud.yandex.net`
- synchronous web search endpoint: `POST /v2/web/search`
- auth header: `Authorization: Api-Key <YANDEX_SEARCH_API_KEY>`
- required folder context: `folderId` in request body
- result format: XML or HTML returned in `rawData` as Base64-encoded payload

## Required env

- `YANDEX_SEARCH_API_KEY`
- `YANDEX_SEARCH_FOLDER_ID`
- `YANDEX_SEARCH_BASE_URL=https://searchapi.api.cloud.yandex.net`
- `YANDEX_SEARCH_TIMEOUT_SECONDS=30`

## Request shape used in v1

```json
{
  "query": {
    "queryText": "купить сосиски спб",
    "searchType": "SEARCH_TYPE_RU",
    "familyMode": "FAMILY_MODE_MODERATE",
    "page": 0
  },
  "folderId": "<YANDEX_SEARCH_FOLDER_ID>",
  "responseFormat": "FORMAT_XML"
}
```

Public task payload used by Scriptor:

```json
{
  "query": "купить сосиски спб",
  "page": 0,
  "max_results": 100,
  "search_type": "SEARCH_TYPE_RU",
  "family_mode": "FAMILY_MODE_MODERATE",
  "response_format": "FORMAT_XML"
}
```

`max_results` is the user-facing control; the service computes how many result pages to fetch.

## Raw response shape used in v1

The service response is expected to contain:

```json
{
  "rawData": "<base64-encoded XML>"
}
```

The XML is decoded and parsed locally.

## Normalized row shape (fixed for v1)

- `query`
- `page`
- `domain`
- `position`
- `title`
- `snippet`
- `url`
- `source`
- `checked_at`

## Export row shape

CSV/export rows are logically separate from normalized rows, even if they currently mirror the same fields.

## Multi-page collection rules

- supported `max_results`: `10..200`
- pagination is orchestrated in `yandex_search_service.py`
- the HTTP client still performs one request per page
- global `position` is calculated across pages (`page * 10 + local_position`)
- duplicate URLs are skipped during aggregation
- stop conditions:
  - enough rows collected to satisfy `max_results`
  - upstream page returns zero docs
  - a page contributes no new URLs
  - upstream degradation after partial success

## Partial data rule

Return / log `PARTIAL_DATA` when upstream responded successfully but:

- some result groups could not be parsed into usable rows, or
- required fields such as `url` / `domain` are missing for part of the response, or
- the upstream response is structurally usable but incomplete, or
- some pages in a multi-page run succeeded while later pages failed / degraded.

If upstream returns result groups but zero usable rows are parsed, treat the task as failed with `PARTIAL_DATA`.

If at least some pages succeeded and usable rows were collected, return success with `warning_code=PARTIAL_DATA` instead of silently pretending the full target was reached.

## Review rule

- if rows `<= 50`: review all rows
- if rows `> 50`: review top 50 by `position ASC`

## Errors in scope

- `INVALID_TASK_SCHEMA`
- `UPSTREAM_TIMEOUT`
- `SOURCE_UNAVAILABLE`
- `PARTIAL_DATA`
- `INTERNAL_ERROR`
