from pathlib import Path
import json
from app.config import settings


class TaskStore:
    def __init__(self):
        self.path = settings.data_path / 'tasks.json'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('{}', encoding='utf-8')

    def _read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, task: dict):
        data = self._read()
        data[task['task_id']] = task
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def get(self, task_id: str):
        return self._read().get(task_id)


task_store = TaskStore()
