from fastapi import APIRouter

from app.core.ad_formats import list_ad_formats
from app.schemas.task_contracts import OctoclickReportTask
from app.services.report_service import report_service

router = APIRouter(prefix='/octoclick', tags=['octoclick'])


@router.get('/meta/ad-formats')
def octoclick_ad_formats() -> dict:
    return {'items': list_ad_formats()}


@router.post('/query')
def octoclick_query(task: OctoclickReportTask) -> dict:
    return report_service.run_report(task)


@router.post('/table-total')
def octoclick_table_total(task: OctoclickReportTask) -> dict:
    return report_service.run_table_total(task)
