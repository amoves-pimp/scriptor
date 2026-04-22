# Scriptor v1

Scriptor v1 is a report-first FastAPI backend for Octoclick reports and Yandex Search API extraction.

## Roles
- Joe: orchestrator, creates tasks and reads results
- Scriptor: controlled gateway to Octoclick, snapshots, normalization, review, export
- Crack: optional analyst over prepared datasets only, no direct API access

## Main flows
- Octoclick: `report query -> Octoclick table -> normalize -> CSV -> review`
- Yandex Search API: `query -> Yandex Search API -> normalize -> CSV -> review`

## Security
- API keys live only inside Scriptor env/secrets
- Joe and Crack never read Scriptor secrets
- No arbitrary URL fetches
- No shell execution
- No token/header logging

## Confirmed Octoclick request shape
- `POST /api/v4/statistic/table?lang=en&role=hunter`
- body fields confirmed from DevTools: `date_from`, `date_to`, `datetime_range`, `group_by`, `metrics`, `order`, `page`, `sample`, `timezone`, `user_role`, `where`

## Validated local milestone
A live local run already proved the first end-to-end contour:
- local FastAPI startup
- `POST /octoclick/query`
- real Octoclick `table` request
- snapshot file saved
- normalized JSON returned
- CSV exported successfully

Reference test task:
- `task_id`: `test-octo-001`
- `webmaster_id`: `77551`
- `AdTypeId`: `2`
- `group_by`: `AdTypeId`, `Country`, `AdvertiserId`
- `metrics`: `Impression`, `Click`, `Ctr`, `cpmWM`, `cpmN`

Expected artifacts after a successful run:
- `data/snapshots/test-octo-001.json`
- `data/reviews/queue.json`
- `data/tasks.json`
- `data/audit.jsonl`
- `data/exports/test-octo-001.csv`

## v1 scope
- working Octoclick report endpoint
- working Octoclick table-total summary endpoint
- working Yandex Search API domains endpoint
- snapshots
- normalized JSON
- CSV export
- review queue

## Run
```bash
./run.sh
```

or

```bash
make run
```

## Useful commands
```bash
make health
make test-query
make export-csv
make show-files
```

## Current API
- `GET /health`
- `GET /octoclick/meta/ad-formats`
- `POST /octoclick/query`
- `POST /octoclick/table-total`
- `POST /yandex/search`
- `POST /exports/csv?task_id=...`

## Yandex Search API v1
- route: `POST /yandex/search`
- auth: `Authorization: Api-Key <YANDEX_SEARCH_API_KEY>`
- required env:
  - `YANDEX_SEARCH_API_KEY`
  - `YANDEX_SEARCH_FOLDER_ID`
- design note: `docs/yandex-search-v1.md`

## Confirmed group_by fields
- `AdTypeId`
- `Country`
- `AdvertiserId`
- `SiteRealDomain`

## Ad format mapping
Currently confirmed:
- `teasers` -> `AdTypeId = 1`
- `popunder` -> `AdTypeId = 2`
- `inpage_push` -> `AdTypeId = 3`
- `in_stream` -> `AdTypeId = 4`

Known labels from admin, but not yet confirmed by ID:
- `teasers`
- `inpage_push`
- `in_stream`
- `out_stream`
- `video_pop_up`

## Extended confirmed work group_by set
- `EventDate`, `EventHour`
- `CampaignId`, `CampaignCategory`, `CampaignName`
- `CreativeId`, `CreativePage`, `CreativeName`, `GoalId`
- `WebmasterId`, `AdvertiserId`, `DspProvider`, `SspProvider`, `WebmasterAffiliateId`
- `SiteId`, `SiteRealDomain`, `SiteCategory`, `RefUrl`, `Url`, `ZoneId`, `ZoneName`
- `AdTypeId`
- `Os`, `OsVersion`, `DeviceType`
- `Browser`, `BrowserVersion`

## Extended metrics allowlist
Publisher metrics:
- `cpmWM`, `cpcW`, `WebmasterProfit`, `WebmasterPartnerProfit`, `uniqCpmWM`

Advertiser metrics:
- `cpcN`, `Cpa`, `EPC`, `EPM`, `LeadsCount`, `LeadsEarned`, `LeadsProfit`, `ROI`

Network metrics:
- `NetworkProfit`, `cpmN`, `uniqCpmN`

Common metrics:
- `Impression`, `Click`, `Ctr`, `BotPercent`, `uniqImpression`, `uniqClick`, `uniqCtr`, `uniqSspRequests`
