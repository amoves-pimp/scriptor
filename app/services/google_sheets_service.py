from time import perf_counter

from httpx import HTTPError, TimeoutException

from app.clients.google_sheets_client import google_sheets_client
from app.config import settings
from app.core.errors import INTERNAL_ERROR, SOURCE_UNAVAILABLE, UPSTREAM_TIMEOUT
from app.services.audit_service import audit_service
from app.storage.task_store import task_store


class GoogleSheetsService:
    def _get_task(self, task_id: str) -> dict | None:
        return task_store.get(task_id)

    def _tab_name(self, task: dict) -> str:
        return task.get('source_task_id') or task['task_id']

    def _headers_and_rows(self, task: dict) -> tuple[list[str], list[list[str]]]:
        export_rows = task.get('export_rows') or []
        if not export_rows:
            raise ValueError('task has no export_rows for Google Sheets export')
        if len(export_rows) > settings.google_sheets_max_rows_per_request:
            export_rows = export_rows[:settings.google_sheets_max_rows_per_request]
        headers = list(export_rows[0].keys())
        rows = [[str(row.get(header, '')) for header in headers] for row in export_rows]
        return headers, rows

    def _find_sheet(self, spreadsheet_meta: dict, tab_name: str) -> dict | None:
        for sheet in spreadsheet_meta.get('sheets', []):
            properties = sheet.get('properties', {})
            if properties.get('title') == tab_name:
                return properties
        return None

    def _ensure_registered_tab(self, task: dict) -> dict:
        spreadsheet_id = settings.google_sheets_spreadsheet_id
        tab_name = self._tab_name(task)
        spreadsheet_meta = google_sheets_client.get_spreadsheet(spreadsheet_id)
        properties = self._find_sheet(spreadsheet_meta, tab_name)
        if properties is None:
            google_sheets_client.add_sheet(spreadsheet_id, tab_name)
            spreadsheet_meta = google_sheets_client.get_spreadsheet(spreadsheet_id)
            properties = self._find_sheet(spreadsheet_meta, tab_name)
        if properties is None:
            raise ValueError('failed to create or locate Google Sheets tab')
        sheet_gid = properties.get('sheetId')
        sheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_gid}'
        return {
            'spreadsheet_id': spreadsheet_id,
            'sheet_id': sheet_gid,
            'tab_name': tab_name,
            'sheet_url': sheet_url,
        }

    def _persist_mapping(self, task: dict, mapping: dict):
        task['google_sheets'] = mapping
        task_store.save(task)

    def export_task(self, task_id: str) -> dict:
        started = perf_counter()
        task = self._get_task(task_id)
        if not task:
            return {'error_code': 'TASK_NOT_FOUND'}

        try:
            headers, rows = self._headers_and_rows(task)
            mapping = self._ensure_registered_tab(task)
            values = [headers, *rows]
            google_sheets_client.clear_values(mapping['spreadsheet_id'], mapping['tab_name'])
            google_sheets_client.update_values(mapping['spreadsheet_id'], mapping['tab_name'], values)
            self._persist_mapping(task, mapping)
        except TimeoutException:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', UPSTREAM_TIMEOUT, route='/google-sheets/export', duration_ms=duration_ms)
            return {'error_code': UPSTREAM_TIMEOUT}
        except HTTPError as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', SOURCE_UNAVAILABLE, route='/google-sheets/export', duration_ms=duration_ms)
            return {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
        except Exception as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', INTERNAL_ERROR, route='/google-sheets/export', duration_ms=duration_ms)
            return {'error_code': INTERNAL_ERROR, 'detail': str(exc)}

        duration_ms = round((perf_counter() - started) * 1000, 2)
        audit_service.log(task_id, 'google_sheets', 'done', route='/google-sheets/export', duration_ms=duration_ms, extra={'tab_name': mapping['tab_name'], 'spreadsheet_id': mapping['spreadsheet_id']})
        return {
            'task_id': task_id,
            'status': 'done',
            **mapping,
            'rows_exported': len(rows),
        }

    def write_task(self, task_id: str) -> dict:
        started = perf_counter()
        task = self._get_task(task_id)
        if not task:
            return {'error_code': 'TASK_NOT_FOUND'}
        mapping = task.get('google_sheets')
        if not mapping:
            return {'error_code': 'REGISTERED_TAB_NOT_FOUND'}

        try:
            headers, rows = self._headers_and_rows(task)
            values = [headers, *rows]
            google_sheets_client.clear_values(mapping['spreadsheet_id'], mapping['tab_name'])
            google_sheets_client.update_values(mapping['spreadsheet_id'], mapping['tab_name'], values)
        except TimeoutException:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', UPSTREAM_TIMEOUT, route='/google-sheets/write', duration_ms=duration_ms)
            return {'error_code': UPSTREAM_TIMEOUT}
        except HTTPError as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', SOURCE_UNAVAILABLE, route='/google-sheets/write', duration_ms=duration_ms)
            return {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
        except Exception as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', INTERNAL_ERROR, route='/google-sheets/write', duration_ms=duration_ms)
            return {'error_code': INTERNAL_ERROR, 'detail': str(exc)}

        duration_ms = round((perf_counter() - started) * 1000, 2)
        audit_service.log(task_id, 'google_sheets', 'done', route='/google-sheets/write', duration_ms=duration_ms, extra={'tab_name': mapping['tab_name'], 'spreadsheet_id': mapping['spreadsheet_id']})
        return {
            'task_id': task_id,
            'status': 'done',
            **mapping,
            'rows_written': len(rows),
        }

    def read_task(self, task_id: str, limit: int) -> dict:
        started = perf_counter()
        task = self._get_task(task_id)
        if not task:
            return {'error_code': 'TASK_NOT_FOUND'}
        mapping = task.get('google_sheets')
        if not mapping:
            return {'error_code': 'REGISTERED_TAB_NOT_FOUND'}
        capped_limit = min(limit, settings.google_sheets_max_rows_per_request)

        try:
            response = google_sheets_client.read_values(mapping['spreadsheet_id'], mapping['tab_name'], capped_limit)
            values = response.get('values', [])
        except TimeoutException:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', UPSTREAM_TIMEOUT, route='/google-sheets/read', duration_ms=duration_ms)
            return {'error_code': UPSTREAM_TIMEOUT}
        except HTTPError as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', SOURCE_UNAVAILABLE, route='/google-sheets/read', duration_ms=duration_ms)
            return {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
        except Exception as exc:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            audit_service.log(task_id, 'google_sheets', 'failed', INTERNAL_ERROR, route='/google-sheets/read', duration_ms=duration_ms)
            return {'error_code': INTERNAL_ERROR, 'detail': str(exc)}

        headers = values[0] if values else []
        rows = values[1:] if len(values) > 1 else []
        duration_ms = round((perf_counter() - started) * 1000, 2)
        audit_service.log(task_id, 'google_sheets', 'done', route='/google-sheets/read', duration_ms=duration_ms, extra={'tab_name': mapping['tab_name'], 'spreadsheet_id': mapping['spreadsheet_id']})
        return {
            'task_id': task_id,
            'status': 'done',
            **mapping,
            'headers': headers,
            'rows': rows,
        }

    def meta(self) -> dict:
        configured = all([
            settings.google_client_id != 'change-me',
            settings.google_client_secret != 'change-me',
            settings.google_refresh_token != 'change-me',
            settings.google_sheets_spreadsheet_id != 'change-me',
        ])
        return {
            'configured': configured,
            'spreadsheet_id': settings.google_sheets_spreadsheet_id,
            'max_rows_per_request': settings.google_sheets_max_rows_per_request,
            'write_policy': 'controlled_overwrite_registered_tab',
            'read_policy': 'registered_tab_only',
            'export_policy': 'one_managed_spreadsheet_one_task_one_tab',
        }


google_sheets_service = GoogleSheetsService()
