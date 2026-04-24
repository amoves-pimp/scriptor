from httpx import HTTPError, TimeoutException

from app.clients.octoclick_client import octoclick_client
from app.core.errors import INVALID_FIELD, SOURCE_UNAVAILABLE, UPSTREAM_TIMEOUT
from app.schemas.task_contracts import ALLOWED_FILTER_FIELDS, ALLOWED_GROUP_BY, ALLOWED_METRICS
from app.services.audit_service import audit_service
from app.services.export_service import export_service
from app.services.normalization_service import normalization_service
from app.storage.review_store import review_store
from app.storage.snapshot_store import snapshot_store
from app.storage.task_store import task_store


class ReportService:
    def _validate(self, task):
        payload = task.payload
        invalid_group = [x for x in payload.group_by if x not in ALLOWED_GROUP_BY]
        invalid_metrics = [x for x in payload.metrics if x not in ALLOWED_METRICS]
        invalid_filters = [x.field for x in payload.filters if x.field not in ALLOWED_FILTER_FIELDS]
        if invalid_group or invalid_metrics or invalid_filters:
            error = {'error_code': INVALID_FIELD, 'invalid_group_by': invalid_group, 'invalid_metrics': invalid_metrics, 'invalid_filters': invalid_filters}
            audit_service.log(task.task_id, 'octoclick', 'failed', INVALID_FIELD)
            return error
        return None

    def run_report(self, task):
        error = self._validate(task)
        if error:
            return error
        payload = task.payload
        try:
            response = octoclick_client.fetch_table(task)
        except ValueError as exc:
            error = {'error_code': INVALID_FIELD, 'detail': str(exc)}
            audit_service.log(task.task_id, 'octoclick', 'failed', INVALID_FIELD)
            return error
        except TimeoutException:
            error = {'error_code': UPSTREAM_TIMEOUT}
            snapshot_store.save(task.task_id, {'request': task.model_dump(), 'response': error})
            audit_service.log(task.task_id, 'octoclick', 'failed', UPSTREAM_TIMEOUT)
            return error
        except HTTPError as exc:
            error = {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
            snapshot_store.save(task.task_id, {'request': task.model_dump(), 'response': error})
            audit_service.log(task.task_id, 'octoclick', 'failed', SOURCE_UNAVAILABLE)
            return error

        snapshot_store.save(task.task_id, {'request': octoclick_client._build_body(task), 'response': response})
        default_webmaster_id = payload.webmaster_id if len(payload.webmaster_ids) == 1 else None
        rows = normalization_service.normalize_table_rows(response, default_webmaster_id)
        task_data = task.model_dump()
        task_data['normalized_rows'] = rows
        task_data['export_rows'] = [dict(row) for row in rows]
        task_data['status'] = 'waiting_review'
        task_store.save(task_data)
        review_rows = rows if len(rows) <= 50 else sorted(rows, key=lambda x: float(x.get('clicks') or 0), reverse=True)[:50]
        review_store.enqueue(task.task_id, review_rows)
        csv_export = export_service.export_csv(task_data)
        json_export = export_service.export_json(task_data) if task.output_format == 'json' else None
        audit_service.log(task.task_id, 'octoclick', 'waiting_review')
        return {
            'task_id': task.task_id,
            'status': 'waiting_review',
            'normalized_rows': rows,
            'export_rows': task_data['export_rows'],
            'csv_export': csv_export,
            'json_export': json_export,
        }

    def run_table_total(self, task):
        error = self._validate(task)
        if error:
            return error
        try:
            response = octoclick_client.fetch_table_total(task)
        except ValueError as exc:
            error = {'error_code': INVALID_FIELD, 'detail': str(exc)}
            audit_service.log(task.task_id, 'octoclick', 'failed', INVALID_FIELD)
            return error
        except TimeoutException:
            error = {'error_code': UPSTREAM_TIMEOUT}
            snapshot_store.save(task.task_id + '-table-total', {'request': task.model_dump(), 'response': error})
            audit_service.log(task.task_id, 'octoclick', 'failed', UPSTREAM_TIMEOUT)
            return error
        except HTTPError as exc:
            error = {'error_code': SOURCE_UNAVAILABLE, 'detail': str(exc)}
            snapshot_store.save(task.task_id + '-table-total', {'request': task.model_dump(), 'response': error})
            audit_service.log(task.task_id, 'octoclick', 'failed', SOURCE_UNAVAILABLE)
            return error

        snapshot_store.save(task.task_id + '-table-total', {'request': octoclick_client._build_body(task), 'response': response})
        default_webmaster_id = task.payload.webmaster_id if len(task.payload.webmaster_ids) == 1 else None
        totals = normalization_service.normalize_table_total(response, default_webmaster_id)
        task_data = task.model_dump()
        task_data['summary'] = totals
        task_data['status'] = 'done'
        task_store.save(task_data)
        audit_service.log(task.task_id, 'octoclick', 'done')
        return {'task_id': task.task_id, 'status': 'done', 'summary': totals}


report_service = ReportService()
