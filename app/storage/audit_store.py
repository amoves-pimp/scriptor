from pathlib import Path
import json
from app.config import settings


class AuditStore:
    def __init__(self):
        self.path = settings.data_path / 'audit.jsonl'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, row: dict):
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


audit_store = AuditStore()
