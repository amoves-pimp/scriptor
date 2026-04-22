import time
import httpx

from app.config import settings
from app.core.retry import MAX_RETRY


class YandexSearchClient:
    def _headers(self) -> dict:
        return {
            'Authorization': f'Api-Key {settings.yandex_search_api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def build_body(self, task) -> dict:
        payload = task.payload
        query = {
            'queryText': payload.query,
            'searchType': payload.search_type,
            'familyMode': payload.family_mode,
            'page': payload.page,
        }
        if payload.region:
            query['region'] = payload.region
        return {
            'query': query,
            'folderId': settings.yandex_search_folder_id,
            'responseFormat': payload.response_format,
        }

    def search(self, task):
        url = f"{settings.yandex_search_base_url}/v2/web/search"
        body = self.build_body(task)
        last_exc = None
        for attempt in range(MAX_RETRY + 1):
            if attempt:
                time.sleep((settings.request_delay_ms / 1000) * attempt)
            else:
                time.sleep(settings.request_delay_ms / 1000)
            try:
                with httpx.Client(timeout=settings.yandex_search_timeout_seconds) as client:
                    response = client.post(url, headers=self._headers(), json=body)
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_RETRY:
                        continue
                    response.raise_for_status()
                    return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt >= MAX_RETRY:
                    raise
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in {429, 500, 502, 503, 504} or attempt >= MAX_RETRY:
                    raise
        if last_exc:
            raise last_exc
        raise RuntimeError('unexpected_yandex_search_retry_exit')


yandex_search_client = YandexSearchClient()
