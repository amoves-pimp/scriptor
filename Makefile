.PHONY: run test-query export-csv show-files health

TASK_ID ?= test-octo-001
BASE_URL ?= http://127.0.0.1:8000

run:
	uvicorn app.main:app --reload

health:
	curl $(BASE_URL)/health

test-query:
	curl -X POST $(BASE_URL)/octoclick/query 	  -H "Content-Type: application/json" 	  -d '{
	    "task_id": "$(TASK_ID)",
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

export-csv:
	curl -X POST "$(BASE_URL)/exports/csv?task_id=$(TASK_ID)"

show-files:
	find data -maxdepth 3 -type f | sort
