from typing import Literal
from pydantic import BaseModel, Field


ALLOWED_GROUP_BY = ['AdTypeId', 'Country', 'AdvertiserId', 'WebmasterId', 'SiteId', 'CampaignId', 'CreativeId', 'EventDate']
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
    timezone: int = 78
    datetime_range: str = 'day'


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
