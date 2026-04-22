from datetime import datetime, UTC
from app.storage.audit_store import audit_store


class AuditService:
    def log(
        self,
        task_id: str,
        source: str,
        status: str,
        error_code: str | None = None,
        route: str | None = None,
        duration_ms: float | None = None,
        extra: dict | None = None,
    ):
        row = {
            'task_id': task_id,
            'source': source,
            'timestamp': datetime.now(UTC).isoformat(),
            'status': status,
            'error_code': error_code,
        }
        if route is not None:
            row['route'] = route
        if duration_ms is not None:
            row['duration_ms'] = duration_ms
        if extra:
            row.update(extra)
        audit_store.append(row)


audit_service = AuditService()
