import json
from app.config import settings


class ExportService:
    def export_csv(self, task: dict) -> dict:
        rows = task.get('normalized_rows', [])
        export_dir = settings.data_path / 'exports'
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{task['task_id']}.csv"
        headers = ['webmaster_id', 'ad_type_id', 'ad_type_name', 'country_id', 'country_name', 'advertiser_id', 'impression', 'clicks', 'ctr', 'cpm_wm', 'cpm_n', 'source', 'checked_at']
        with path.open('w', encoding='utf-8') as f:
            f.write(','.join(headers) + '\n')
            for row in rows:
                f.write(','.join(str(row.get(h, '')) for h in headers) + '\n')
        return {'task_id': task['task_id'], 'path': str(path)}

    def export_json(self, task: dict) -> dict:
        export_dir = settings.data_path / 'exports'
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{task['task_id']}.json"
        path.write_text(json.dumps(task.get('normalized_rows', []), ensure_ascii=False, indent=2), encoding='utf-8')
        return {'task_id': task['task_id'], 'path': str(path)}


export_service = ExportService()
