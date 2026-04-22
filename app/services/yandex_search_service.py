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
        for index, group in enumerate(groups, start=1):
            doc = group.find('./doc')
            if doc is None:
                continue
            yield index, doc

    def _normalize_rows(self, task, xml_text: str) -> tuple[list[dict], list[dict], int]:
        checked_at = self._checked_at()
        normalized_rows: list[dict] = []
        export_rows: list[dict] = []
        parse_errors = 0

        for position, doc in self._iter_docs(xml_text):
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
            row = {
                'query': task.payload.query,
                'domain': domain,
                'position': position,
                'title': title,
                'snippet': snippet,
                'url': url,
                'source': 'yandex_search',
                'checked_at': checked_at,
            }
            normalized_rows.append(row)
            export_rows.append(dict(row))

        return normalized_rows, export_rows, parse_errors

    def run_search(self, task) -> dict:
        started = perf_counter()
        request_body = yandex_search_client.build_body(task)
        fingerprint = task_fingerprint(task.payload.model_dump())
        try:
            response = yandex_search_client.search(task)
            raw_xml = self._extract_raw_xml(response)
            normalized_rows, export_rows, parse_errors = self._normalize_rows(task, raw_xml)
        except TimeoutException:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': UPSTREAM_TIMEOUT}
            snapshot_store.save(task.task_id, {
                'task_id': task.task_id,
                'status': 'failed',
                'timestamp': self._checked_at(),
                'request': request_body,
                'response': error,
            })
            audit_service.log(task.task_id, 'yandex_search', 'failed', UPSTREAM_TIMEOUT, route='/yandex/search', duration_ms=duration_ms)
            return error
        except HTTPError as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
            snapshot_store.save(task.task_id, {
                'task_id': task.task_id,
                'status': 'failed',
                'timestamp': self._checked_at(),
                'request': request_body,
                'response': error,
            })
            audit_service.log(task.task_id, 'yandex_search', 'failed', SOURCE_UNAVAILABLE, route='/yandex/search', duration_ms=duration_ms)
            return error
        except ValueError as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': PARTIAL_DATA, 'detail': str(exc)}
            snapshot_store.save(task.task_id, {
                'task_id': task.task_id,
                'status': 'failed',
                'timestamp': self._checked_at(),
                'request': request_body,
                'response': error,
            })
            audit_service.log(task.task_id, 'yandex_search', 'failed', PARTIAL_DATA, route='/yandex/search', duration_ms=duration_ms)
            return error
        except Exception as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': INTERNAL_ERROR, 'detail': str(exc)}
            snapshot_store.save(task.task_id, {
                'task_id': task.task_id,
                'status': 'failed',
                'timestamp': self._checked_at(),
                'request': request_body,
                'response': error,
            })
            audit_service.log(task.task_id, 'yandex_search', 'failed', INTERNAL_ERROR, route='/yandex/search', duration_ms=duration_ms)
            return error

        total_groups = len(list(self._iter_docs(raw_xml)))
        if total_groups > 0 and not normalized_rows:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            error = {'error_code': PARTIAL_DATA, 'detail': 'upstream returned groups but no usable rows were parsed'}
            snapshot_store.save(task.task_id, {
                'task_id': task.task_id,
                'status': 'failed',
                'timestamp': self._checked_at(),
                'request': request_body,
                'response': response,
                'warning': error,
            })
            audit_service.log(task.task_id, 'yandex_search', 'failed', PARTIAL_DATA, route='/yandex/search', duration_ms=duration_ms)
            return error

        warning_code = PARTIAL_DATA if parse_errors > 0 else None
        status = 'waiting_review'
        snapshot_store.save(task.task_id, {
            'task_id': task.task_id,
            'status': status,
            'timestamp': self._checked_at(),
            'request': request_body,
            'response': response,
            'warning_code': warning_code,
        })

        task_data = task.model_dump()
        task_data['fingerprint'] = fingerprint
        task_data['normalized_rows'] = normalized_rows
        task_data['export_rows'] = export_rows
        task_data['status'] = status
        task_data['warning_code'] = warning_code
        task_store.save(task_data)

        review_rows = export_rows if len(export_rows) <= 50 else sorted(export_rows, key=lambda row: int(row.get('position') or 0))[:50]
        review_store.enqueue(task.task_id, review_rows)

        csv_export = export_service.export_csv(task_data)
        json_export = export_service.export_json(task_data) if task.output_format == 'json' else None

        duration_ms = round((perf_counter() - started) * 1000, 2)
        audit_service.log(task.task_id, 'yandex_search', status, warning_code, route='/yandex/search', duration_ms=duration_ms)
        return {
            'task_id': task.task_id,
            'status': status,
            'warning_code': warning_code,
            'normalized_rows': normalized_rows,
            'export_rows': export_rows,
            'csv_export': csv_export,
            'json_export': json_export,
        }


yandex_search_service = YandexSearchService()
