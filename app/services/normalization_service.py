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

    def normalize_table_rows(self, response: dict, webmaster_id: int) -> list[dict]:
        rows = []
        for item in response.get('data', []):
            metric = item.get('metric', {})
            group = item.get('group', {})
            row = {
                'webmaster_id': webmaster_id,
                'clicks': metric.get('Click'),
                'ctr': metric.get('Ctr'),
                'impression': metric.get('Impression'),
                'cpm_wm': metric.get('cpmWM'),
                'cpm_n': metric.get('cpmN'),
                'webmaster_profit': metric.get('WebmasterProfit'),
                'network_profit': metric.get('NetworkProfit'),
                'source': 'octoclick',
                'checked_at': datetime.now(UTC).isoformat(),
            }
            row.update(self._flatten_group(group))
            rows.append(row)
        return rows

    def normalize_table_total(self, response: dict, webmaster_id: int) -> dict:
        data = response.get('data', {})
        return {
            'webmaster_id': webmaster_id,
            'impression': data.get('Impression'),
            'clicks': data.get('Click'),
            'ctr': data.get('Ctr'),
            'cpm_w': data.get('cpmW'),
            'cpm_m': data.get('cpmM'),
            'source': 'octoclick',
            'checked_at': datetime.now(UTC).isoformat(),
        }


normalization_service = NormalizationService()
