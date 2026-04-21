AD_FORMATS = {
    'teasers': {'label': 'Teasers', 'ad_type_id': 1, 'confirmed': True},
    'popunder': {'label': 'Popunder', 'ad_type_id': 2, 'confirmed': True},
    'inpage_push': {'label': 'In-page Push', 'ad_type_id': None, 'confirmed': False},
    'in_stream': {'label': 'In-Stream', 'ad_type_id': None, 'confirmed': False},
    'out_stream': {'label': 'Out-Stream', 'ad_type_id': None, 'confirmed': False},
    'video_pop_up': {'label': 'Video Pop-Up', 'ad_type_id': None, 'confirmed': False},
}


def list_ad_formats() -> list[dict]:
    return [{'key': key, **value} for key, value in AD_FORMATS.items()]


def resolve_ad_format(ad_format: str | None) -> int | None:
    if not ad_format:
        return None
    key = ad_format.strip().lower().replace('-', '_').replace(' ', '_')
    item = AD_FORMATS.get(key)
    if not item:
        raise ValueError(f'unknown ad_format: {ad_format}')
    if item['ad_type_id'] is None:
        raise ValueError(f'ad_format_not_confirmed: {ad_format}')
    return item['ad_type_id']
