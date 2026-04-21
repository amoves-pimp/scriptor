import re
from datetime import datetime, UTC


class NormalizationService:
    def _snake(self, value: str) -> str:
        value = re.sub(r'(.)([A-Z][a-z]+)', r'_', value)
        value = re.sub(r'([a-z0-9])([A-Z])', r'_', value)
        return value.replace('-', '_').replace(' ', '_').lower()

    def _flatten_group(self, group: dict) -> dict:
        row = {}
        for field_name, value in group.items():
            key = self._snake(field_name)
            if isinstance(value, dict):
                if 'id' in value:
                    row[f'{key}_id'] = value.get('id')
                if 'name' in value:
                    row[key] = value.get('name')
                if 'field_name' in value:
                    row[f'{key}_field_name'] = value.get('field_name')
            else:
                row[key] = value
        return row

    def _flatten_metric(self, metric: dict) -> dict:
        row = {}
        for metric_name, value in metric.items():
            key = self._snake(metric_name)
            row[key] = value
        if 'click' in row and 'clicks' not in row:
            row['clicks'] = row['click']
        if 'impression' in row and 'impressions' not in row:
            row['impressions'] = row['impression']
        return row

    def normalize_table_rows(self, response: dict, webmaster_id: int) -> list[dict]:
        rows = []
        for item in response.get('data', []):
            metric = item.get('metric', {})
            group = item.get('group', {})
            row = {
                'webmaster_id': webmaster_id,
                'source': 'octoclick',
                'checked_at': datetime.now(UTC).isoformat(),
            }
            row.update(self._flatten_metric(metric))
            row.update(self._flatten_group(group))
            rows.append(row)
        return rows

    def normalize_table_total(self, response: dict, webmaster_id: int) -> dict:
        data = response.get('data', {})
        row = {
            'webmaster_id': webmaster_id,
            'source': 'octoclick',
            'checked_at': datetime.now(UTC).isoformat(),
        }
        row.update(self._flatten_metric(data))
        return row


normalization_service = NormalizationService()
