from pathlib import Path
import json
from app.config import settings


class ReviewStore:
    def __init__(self):
        self.path = settings.data_path / 'reviews' / 'queue.json'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('{}', encoding='utf-8')

    def _read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def enqueue(self, task_id: str, rows: list[dict]):
        data = self._read()
        data[task_id] = {'status': 'pending', 'rows': rows}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def list_pending(self):
        data = self._read()
        return [{**{'task_id': k}, **v} for k, v in data.items() if v.get('status') == 'pending']

    def set_status(self, task_id: str, status: str):
        data = self._read()
        if task_id in data:
            data[task_id]['status'] = status
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


review_store = ReviewStore()
