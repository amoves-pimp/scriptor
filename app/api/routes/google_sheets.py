from fastapi import APIRouter

from app.schemas.google_sheets import GoogleSheetsReadRequest, GoogleSheetsTaskRequest
from app.services.google_sheets_service import google_sheets_service

router = APIRouter(prefix='/google-sheets', tags=['google-sheets'])


@router.post('/read')
def google_sheets_read(request: GoogleSheetsReadRequest) -> dict:
    return google_sheets_service.read_task(request.task_id, request.limit)


@router.post('/write')
def google_sheets_write(request: GoogleSheetsTaskRequest) -> dict:
    return google_sheets_service.write_task(request.task_id)


@router.post('/export')
def google_sheets_export(task_id: str) -> dict:
    return google_sheets_service.export_task(task_id)


@router.get('/meta')
def google_sheets_meta() -> dict:
    return google_sheets_service.meta()
