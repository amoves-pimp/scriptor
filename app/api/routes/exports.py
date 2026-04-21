from fastapi import APIRouter, HTTPException

from app.services.export_service import export_service
from app.services.task_service import task_service

router = APIRouter(prefix='/exports', tags=['exports'])


@router.post('/csv')
def export_csv(task_id: str) -> dict:
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='task_not_found')
    return export_service.export_csv(task)


@router.post('/json')
def export_json(task_id: str) -> dict:
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='task_not_found')
    return export_service.export_json(task)
