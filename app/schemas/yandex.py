from typing import Literal

from pydantic import BaseModel, Field


class YandexSearchPayload(BaseModel):
    query: str = Field(min_length=1, max_length=400)
    region: str | None = None
    page: int = Field(default=0, ge=0, le=15)
    max_results: int = Field(default=10, ge=10, le=200)
    family_mode: Literal['FAMILY_MODE_MODERATE', 'FAMILY_MODE_NONE'] = 'FAMILY_MODE_MODERATE'
    search_type: Literal['SEARCH_TYPE_RU', 'SEARCH_TYPE_COM', 'SEARCH_TYPE_TURKISH'] = 'SEARCH_TYPE_RU'
    response_format: Literal['FORMAT_XML'] = 'FORMAT_XML'


class YandexSearchTask(BaseModel):
    task_id: str
    task_type: Literal['yandex_search_domains'] = 'yandex_search_domains'
    source: Literal['yandex_search'] = 'yandex_search'
    payload: YandexSearchPayload
    output_format: Literal['json', 'csv'] = 'json'
    priority: Literal['low', 'normal', 'high'] = 'normal'
    requested_by: str
    approval_required: bool = False
    contract_version: str = 'v1'


class YandexSearchNormalizedRow(BaseModel):
    query: str
    page: int
    domain: str
    position: int
    title: str | None = None
    snippet: str | None = None
    url: str
    source: Literal['yandex_search'] = 'yandex_search'
    checked_at: str


class YandexSearchExportRow(BaseModel):
    query: str
    page: int
    position: int
    domain: str
    title: str | None = None
    snippet: str | None = None
    url: str
    source: Literal['yandex_search'] = 'yandex_search'
    checked_at: str
