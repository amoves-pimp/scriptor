from fastapi import APIRouter

from app.schemas.task_contracts import OctoclickReportTask
from app.services.report_service import report_service

router = APIRouter(prefix='/octoclick', tags=['octoclick'])


@router.post('/query')
def octoclick_query(task: OctoclickReportTask) -> dict:
    return report_service.run_report(task)


@router.post('/table-total')
def octoclick_table_total(task: OctoclickReportTask) -> dict:
    return report_service.run_table_total(task)
