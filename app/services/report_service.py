from app.clients.octoclick_client import octoclick_client
from app.core.errors import INVALID_FIELD
from app.schemas.task_contracts import ALLOWED_FILTER_FIELDS, ALLOWED_GROUP_BY, ALLOWED_METRICS
from app.services.audit_service import audit_service
from app.services.normalization_service import normalization_service
from app.storage.review_store import review_store
from app.storage.snapshot_store import snapshot_store
from app.storage.task_store import task_store


class ReportService:
    def run_report(self, task):
        payload = task.payload
        invalid_group = [x for x in payload.group_by if x not in ALLOWED_GROUP_BY]
        invalid_metrics = [x for x in payload.metrics if x not in ALLOWED_METRICS]
        invalid_filters = [x.field for x in payload.filters if x.field not in ALLOWED_FILTER_FIELDS]
        if invalid_group or invalid_metrics or invalid_filters:
            error = {'error_code': INVALID_FIELD, 'invalid_group_by': invalid_group, 'invalid_metrics': invalid_metrics, 'invalid_filters': invalid_filters}
            audit_service.log(task.task_id, 'octoclick', 'failed', INVALID_FIELD)
            return error

        response = octoclick_client.fetch_table(task)
        snapshot_store.save(task.task_id, {'request': task.model_dump(), 'response': response})
        rows = normalization_service.normalize_table_rows(response, payload.webmaster_id)
        task_data = task.model_dump()
        task_data['normalized_rows'] = rows
        task_data['status'] = 'waiting_review'
        task_store.save(task_data)
        review_store.enqueue(task.task_id, rows[:50])
        audit_service.log(task.task_id, 'octoclick', 'waiting_review')
        return {'task_id': task.task_id, 'status': 'waiting_review', 'normalized_rows': rows}


report_service = ReportService()
