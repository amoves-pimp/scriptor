# Scriptor v1

Scriptor v1 is a report-first FastAPI backend for Octoclick reports.

## Roles
- Joe: orchestrator, creates tasks and reads results
- Scriptor: controlled gateway to Octoclick, snapshots, normalization, review, export
- Crack: optional analyst over prepared datasets only, no direct API access

## Main flow
report query -> Octoclick table -> normalize -> CSV -> review

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
- `POST /octoclick/query`
- `POST /octoclick/table-total`
- `POST /exports/csv?task_id=...`

## Confirmed group_by fields
- `AdTypeId`
- `Country`
- `AdvertiserId`
- `SiteRealDomain`
