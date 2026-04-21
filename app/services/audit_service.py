from datetime import datetime, UTC
from app.storage.audit_store import audit_store


class AuditService:
    def log(self, task_id: str, source: str, status: str, error_code: str | None = None):
        audit_store.append({
            'task_id': task_id,
            'source': source,
            'timestamp': datetime.now(UTC).isoformat(),
            'status': status,
            'error_code': error_code,
        })


audit_service = AuditService()
