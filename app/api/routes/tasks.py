from fastapi import APIRouter, HTTPException

from app.schemas.task_contracts import OctoclickReportTask
from app.services.task_service import task_service

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('/create')
def create_task(task: OctoclickReportTask) -> dict:
    return task_service.create_task(task)


@router.get('/{task_id}')
def get_task(task_id: str) -> dict:
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='task_not_found')
    return task
