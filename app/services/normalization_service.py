from datetime import datetime, UTC


class NormalizationService:
    def normalize_table_rows(self, response: dict, webmaster_id: int) -> list[dict]:
        rows = []
        for item in response.get('data', []):
            metric = item.get('metric', {})
            group = item.get('group', {})
            country = group.get('Country', {})
            rows.append({
                'webmaster_id': webmaster_id,
                'country_id': country.get('id'),
                'country_name': country.get('name'),
                'clicks': metric.get('Click'),
                'ctr': metric.get('Ctr'),
                'cpm_wm': metric.get('cpmWM'),
                'cpm_n': metric.get('cpmN'),
                'source': 'octoclick',
                'checked_at': datetime.now(UTC).isoformat(),
            })
        return rows


normalization_service = NormalizationService()
