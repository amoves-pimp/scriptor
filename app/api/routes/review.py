from fastapi import APIRouter

from app.services.review_queue_service import review_queue_service

router = APIRouter(prefix='/review', tags=['review'])


@router.get('/pending')
def pending() -> dict:
    return {'items': review_queue_service.list_pending()}


@router.post('/{task_id}/approve')
def approve(task_id: str) -> dict:
    return review_queue_service.set_status(task_id, 'approved')


@router.post('/{task_id}/reject')
def reject(task_id: str) -> dict:
    return review_queue_service.set_status(task_id, 'rejected')
