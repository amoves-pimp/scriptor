from app.core.idempotency import task_fingerprint
from app.storage.task_store import task_store


class TaskService:
    def create_task(self, task):
        payload = task.model_dump()
        payload['fingerprint'] = task_fingerprint(payload['payload'])
        task_store.save(payload)
        return payload

    def get_task(self, task_id: str):
        return task_store.get(task_id)


task_service = TaskService()
