from datetime import datetime, UTC


class NormalizationService:
    def normalize_table_rows(self, response: dict, webmaster_id: int) -> list[dict]:
        rows = []
        for item in response.get('data', []):
            metric = item.get('metric', {})
            group = item.get('group', {})
            country = group.get('Country', {})
            ad_type = group.get('AdTypeId', {})
            advertiser = group.get('AdvertiserId', {})
            rows.append({
                'webmaster_id': webmaster_id,
                'ad_type_id': ad_type.get('id'),
                'ad_type_name': ad_type.get('name'),
                'country_id': country.get('id'),
                'country_name': country.get('name'),
                'advertiser_id': advertiser.get('id'),
                'clicks': metric.get('Click'),
                'ctr': metric.get('Ctr'),
                'impression': metric.get('Impression'),
                'cpm_wm': metric.get('cpmWM'),
                'cpm_n': metric.get('cpmN'),
                'source': 'octoclick',
                'checked_at': datetime.now(UTC).isoformat(),
            })
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
