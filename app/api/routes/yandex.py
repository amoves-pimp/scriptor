from fastapi import APIRouter

from app.schemas.yandex import YandexSearchTask
from app.services.yandex_search_service import yandex_search_service

router = APIRouter(prefix='/yandex', tags=['yandex'])


@router.post('/search')
def yandex_search(task: YandexSearchTask) -> dict:
    return yandex_search_service.run_search(task)
