import time
import httpx

from app.config import settings


class OctoclickClient:
    def _headers(self) -> dict:
        return {
            'Authorization': f'ApiToken {settings.octoclick_api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _build_body(self, task) -> dict:
        payload = task.payload
        where = []
        for rule in payload.filters:
            value = rule.value
            if not isinstance(value, list):
                value = [value]
            where.append({'field': rule.field, 'operator': rule.operator, 'value': value})
        return {
            'date_from': payload.date_from,
            'date_to': payload.date_to,
            'datetime_range': payload.datetime_range,
            'group_by': payload.group_by,
            'metrics': payload.metrics,
            'order': {'field': payload.order_field, 'sort': payload.order_sort},
            'page': {'number': payload.page_number},
            'sample': payload.sample,
            'timezone': payload.timezone,
            'user_role': settings.octoclick_role,
            'where': where,
        }

    def _post(self, endpoint: str, task):
        time.sleep(settings.request_delay_ms / 1000)
        url = f"{settings.octoclick_base_url}{endpoint}"
        params = {'lang': settings.octoclick_lang, 'role': settings.octoclick_role}
        body = self._build_body(task)
        with httpx.Client(timeout=settings.octoclick_timeout_seconds) as client:
            response = client.post(url, params=params, headers=self._headers(), json=body)
            response.raise_for_status()
            return response.json()

    def fetch_table(self, task):
        return self._post('/statistic/table', task)

    def fetch_table_total(self, task):
        return self._post('/statistic/table-total', task)


octoclick_client = OctoclickClient()
