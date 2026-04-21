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

## v1 scope
- 1 working Octoclick report endpoint
- snapshots
- normalized JSON
- CSV export
- review queue

## Run
```bash
uvicorn app.main:app --reload
```
