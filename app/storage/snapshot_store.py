from pathlib import Path
import json
from app.config import settings


class SnapshotStore:
    def save(self, task_id: str, payload: dict):
        path = settings.data_path / 'snapshots' / f'{task_id}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return path


snapshot_store = SnapshotStore()
