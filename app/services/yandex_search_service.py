import base64
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from httpx import HTTPError, TimeoutException

from app.clients.yandex_search_client import yandex_search_client
from app.core.errors import INTERNAL_ERROR, PARTIAL_DATA, SOURCE_UNAVAILABLE, UPSTREAM_TIMEOUT
from app.core.idempotency import task_fingerprint
from app.services.audit_service import audit_service
from app.services.export_service import export_service
from app.storage.review_store import review_store
from app.storage.snapshot_store import snapshot_store
from app.storage.task_store import task_store


class YandexSearchService:
    PAGE_SIZE = 10

    def _checked_at(self) -> str:
        return datetime.now(UTC).isoformat()

    def _extract_raw_xml(self, response: dict) -> str:
        raw_data = response.get('rawData')
        if not raw_data:
            raise ValueError('missing rawData in Yandex Search API response')
        decoded = base64.b64decode(raw_data)
        return decoded.decode('utf-8', errors='replace')

    def _iter_docs(self, xml_text: str):
        root = ET.fromstring(xml_text)
        groups = root.findall('.//group')
        for local_position, group in enumerate(groups, start=1):
            doc = group.find('./doc')
            if doc is None:
                continue
            yield local_position, doc

    def _normalize_page_rows(self, task, xml_text: str, page: int) -> tuple[list[dict], list[dict], int, int]:
        checked_at = self._checked_at()
        normalized_rows: list[dict] = []
        export_rows: list[dict] = []
        parse_errors = 0
        raw_docs = 0

        for local_position, doc in self._iter_docs(xml_text):
            raw_docs += 1
            url = (doc.findtext('url') or '').strip()
            if not url:
                parse_errors += 1
                continue
            domain = (urlparse(url).hostname or '').lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            if not domain:
                parse_errors += 1
                continue

            title = (doc.findtext('title') or '').strip() or None
            passages = [
                (passage.text or '').strip()
                for passage in doc.findall('./passages/passage')
                if (passage.text or '').strip()
            ]
            snippet = ' '.join(passages) or None
            global_position = page * self.PAGE_SIZE + local_position
            row = {
                'query': task.payload.query,
                'page': page,
                'domain': domain,
                'position': global_position,
                'title': title,
                'snippet': snippet,
                'url': url,
                'source': 'yandex_search',
                'checked_at': checked_at,
            }
            normalized_rows.append(row)
            export_rows.append(dict(row))

        return normalized_rows, export_rows, parse_errors, raw_docs

    def _snapshot_payload(self, task_id: str, request: dict, responses: list[dict], status: str, warning_code: str | None = None) -> dict:
        payload = {
            'task_id': task_id,
            'status': status,
            'timestamp': self._checked_at(),
            'request': request,
            'pages_fetched': [item['page'] for item in responses],
            'responses': responses,
        }
        if warning_code:
            payload['warning_code'] = warning_code
        return payload

    def run_search(self, task) -> dict:
        started = perf_counter()
        base_request_body = yandex_search_client.build_body(task, page=task.payload.page)
        target_results = task.payload.max_results
        fingerprint = task_fingerprint(task.payload.model_dump())

        normalized_rows: list[dict] = []
        export_rows: list[dict] = []
        page_responses: list[dict] = []
        seen_urls: set[str] = set()
        pages_fetched = 0
        parse_errors = 0
        warning_code = None
        degraded = False
        exhausted = False
        page = task.payload.page
        last_page = task.payload.page + ((target_results - 1) // self.PAGE_SIZE)

        while len(export_rows) < target_results and page <= last_page:
            request_body = yandex_search_client.build_body(task, page=page)
            try:
                response = yandex_search_client.search_page(task, page)
                raw_xml = self._extract_raw_xml(response)
                page_normalized_rows, page_export_rows, page_parse_errors, raw_docs = self._normalize_page_rows(task, raw_xml, page)
            except TimeoutException:
                duration_ms = round((perf_counter() - started) * 1000, 2)
                if export_rows:
                    warning_code = PARTIAL_DATA
                    degraded = True
                    break
                error = {'error_code': UPSTREAM_TIMEOUT}
                snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, 'failed'))
                audit_service.log(task.task_id, 'yandex_search', 'failed', UPSTREAM_TIMEOUT, route='/yandex/search', duration_ms=duration_ms, extra={'pages_requested': last_page - task.payload.page + 1, 'pages_fetched': pages_fetched, 'rows_collected': len(export_rows)})
                return error
            except HTTPError as exc:
                duration_ms = round((perf_counter() - started) * 1000, 2)
                if export_rows:
                    warning_code = PARTIAL_DATA
                    degraded = True
                    break
                error = {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
                snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, 'failed'))
                audit_service.log(task.task_id, 'yandex_search', 'failed', SOURCE_UNAVAILABLE, route='/yandex/search', duration_ms=duration_ms, extra={'pages_requested': last_page - task.payload.page + 1, 'pages_fetched': pages_fetched, 'rows_collected': len(export_rows)})
                return error
            except ValueError as exc:
                duration_ms = round((perf_counter() - started) * 1000, 2)
                if export_rows:
                    warning_code = PARTIAL_DATA
                    degraded = True
                    break
                error = {'error_code': PARTIAL_DATA, 'detail': str(exc)}
                snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, 'failed', warning_code=PARTIAL_DATA))
                audit_service.log(task.task_id, 'yandex_search', 'failed', PARTIAL_DATA, route='/yandex/search', duration_ms=duration_ms, extra={'pages_requested': last_page - task.payload.page + 1, 'pages_fetched': pages_fetched, 'rows_collected': len(export_rows)})
                return error
            except Exception as exc:
                duration_ms = round((perf_counter() - started) * 1000, 2)
                if export_rows:
                    warning_code = PARTIAL_DATA
                    degraded = True
                    break
                error = {'error_code': INTERNAL_ERROR, 'detail': str(exc)}
                snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, 'failed'))
                audit_service.log(task.task_id, 'yandex_search', 'failed', INTERNAL_ERROR, route='/yandex/search', duration_ms=duration_ms, extra={'pages_requested': last_page - task.payload.page + 1, 'pages_fetched': pages_fetched, 'rows_collected': len(export_rows)})
                return error

            page_responses.append({'page': page, 'request': request_body, 'response': response})
            pages_fetched += 1
            parse_errors += page_parse_errors

            if raw_docs == 0:
                exhausted = True
                break

            new_rows = 0
            for normalized_row, export_row in zip(page_normalized_rows, page_export_rows):
                url = export_row['url']
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                normalized_rows.append(normalized_row)
                export_rows.append(export_row)
                new_rows += 1
                if len(export_rows) >= target_results:
                    break

            if new_rows == 0:
                warning_code = PARTIAL_DATA
                degraded = True
                break

            if page_parse_errors > 0:
                warning_code = PARTIAL_DATA

            page += 1

        if page_responses and not export_rows and not exhausted:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': PARTIAL_DATA, 'detail': 'upstream returned pages but no usable rows were parsed'}
            snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, 'failed', warning_code=PARTIAL_DATA))
            audit_service.log(task.task_id, 'yandex_search', 'failed', PARTIAL_DATA, route='/yandex/search', duration_ms=duration_ms, extra={'pages_requested': last_page - task.payload.page + 1, 'pages_fetched': pages_fetched, 'rows_collected': 0})
            return error

        if parse_errors > 0 or degraded:
            warning_code = PARTIAL_DATA

        status = 'waiting_review'
        meta = {
            'requested_max_results': target_results,
            'rows_collected': len(export_rows),
            'pages_requested': last_page - task.payload.page + 1,
            'pages_fetched': pages_fetched,
            'start_page': task.payload.page,
        }
        snapshot_store.save(task.task_id, self._snapshot_payload(task.task_id, base_request_body, page_responses, status, warning_code=warning_code))

        task_data = task.model_dump()
        task_data['fingerprint'] = fingerprint
        task_data['normalized_rows'] = normalized_rows
        task_data['export_rows'] = export_rows
        task_data['status'] = status
        task_data['warning_code'] = warning_code
        task_data['meta'] = meta
        task_store.save(task_data)

        review_rows = export_rows if len(export_rows) <= 50 else sorted(export_rows, key=lambda row: int(row.get('position') or 0))[:50]
        review_store.enqueue(task.task_id, review_rows)

        csv_export = export_service.export_csv(task_data)
        json_export = export_service.export_json(task_data) if task.output_format == 'json' else None

        duration_ms = round((perf_counter() - started) * 1000, 2)
        audit_service.log(task.task_id, 'yandex_search', status, warning_code, route='/yandex/search', duration_ms=duration_ms, extra=meta)
        return {
            'task_id': task.task_id,
            'status': status,
            'warning_code': warning_code,
            'meta': meta,
            'normalized_rows': normalized_rows,
            'export_rows': export_rows,
            'csv_export': csv_export,
            'json_export': json_export,
        }


yandex_search_service = YandexSearchService()
