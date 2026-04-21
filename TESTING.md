# Local testing

## Proven smoke test
Start the API:

```bash
./run.sh
```

or

```bash
make run
```

Run health check:

```bash
make health
```

Run the first real Octoclick query:

```bash
make test-query
```

Equivalent raw curl:

```bash
curl -X POST http://127.0.0.1:8000/octoclick/query \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-octo-001",
    "requested_by": "alex",
    "payload": {
      "webmaster_id": 77551,
      "date_from": "2026-04-21 00:00:00",
      "date_to": "2026-04-21 23:59:59",
      "datetime_range": "hour",
      "group_by": ["AdTypeId", "Country", "AdvertiserId"],
      "metrics": ["Impression", "Click", "Ctr", "cpmWM", "cpmN"],
      "filters": [
        {"field": "WebmasterId", "operator": "=", "value": [77551]},
        {"field": "AdTypeId", "operator": "=", "value": [2]}
      ]
    }
  }'
```

Export CSV:

```bash
make export-csv
```

Equivalent raw curl:

```bash
curl -X POST "http://127.0.0.1:8000/exports/csv?task_id=test-octo-001"
```

Check produced files:

```bash
make show-files
```
