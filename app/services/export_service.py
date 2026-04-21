import json
from app.config import settings


class ExportService:
    def export_csv(self, task: dict) -> dict:
        rows = task.get('normalized_rows', [])
        export_dir = settings.data_path / 'exports'
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{task['task_id']}.csv"
        preferred = [
            'webmaster_id', 'ad_type_id', 'ad_type', 'country_id', 'country',
            'advertiser_id', 'advertiser', 'site_id', 'site', 'site_real_domain_id', 'site_real_domain',
            'campaign_id', 'campaign', 'campaign_category', 'creative_id', 'creative_name',
            'goal_id', 'zone_id', 'zone_name', 'event_date', 'event_hour', 'os', 'os_version',
            'device_type', 'browser', 'browser_version', 'impression', 'clicks', 'ctr',
            'cpm_wm', 'cpm_n', 'webmaster_profit', 'network_profit', 'source', 'checked_at'
        ]
        extra = []
        seen = set(preferred)
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    extra.append(key)
                    seen.add(key)
        headers = [h for h in preferred if any(h in row for row in rows)] + extra
        if not headers:
            headers = preferred
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
