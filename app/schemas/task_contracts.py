from typing import Literal
from pydantic import BaseModel, Field, model_validator


ALLOWED_GROUP_BY = [
    'AdTypeId', 'Country', 'AdvertiserId', 'WebmasterId', 'SiteId', 'SiteRealDomain',
    'CampaignId', 'CampaignCategory', 'CampaignName', 'CreativeId', 'CreativePage',
    'CreativeName', 'GoalId', 'DspProvider', 'SspProvider', 'WebmasterAffiliateId',
    'SiteCategory', 'RefUrl', 'Url', 'ZoneId', 'ZoneName', 'EventDate', 'EventHour',
    'Os', 'OsVersion', 'DeviceType', 'Browser', 'BrowserVersion'
]
ALLOWED_METRICS = ['Impression', 'Click', 'Ctr', 'cpmWM', 'cpmN', 'WebmasterProfit', 'NetworkProfit']
ALLOWED_FILTER_FIELDS = ['AdTypeId', 'Country', 'WebmasterId', 'SiteId', 'AdvertiserId']


class FilterRule(BaseModel):
    field: str
    operator: Literal['=', '!=', 'in'] = '='
    value: list[int | str] | int | str


class OctoclickReportPayload(BaseModel):
    webmaster_id: int
    date_from: str
    date_to: str
    group_by: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    filters: list[FilterRule] = Field(default_factory=list)
    ad_format: str | None = None
    timezone: int = 78
    datetime_range: str = 'day'
    page_number: int = 1
    sample: int = 100
    order_field: str = 'Impression'
    order_sort: Literal['ASC', 'DESC'] = 'DESC'

    @model_validator(mode='after')
    def ensure_webmaster_filter(self):
        if not any(f.field == 'WebmasterId' for f in self.filters):
            self.filters.append(FilterRule(field='WebmasterId', operator='=', value=[self.webmaster_id]))
        return self


class OctoclickReportTask(BaseModel):
    task_id: str
    task_type: Literal['octoclick_report'] = 'octoclick_report'
    source: Literal['octoclick'] = 'octoclick'
    payload: OctoclickReportPayload
    output_format: Literal['json', 'csv'] = 'json'
    priority: Literal['low', 'normal', 'high'] = 'normal'
    requested_by: str
    approval_required: bool = True
    contract_version: str = 'v1'
