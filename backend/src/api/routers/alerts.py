from fastapi import APIRouter

from src.api.dependencies import AlertServiceDep
from src.schemas import AlertItem


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertItem])
async def list_alerts(service: AlertServiceDep):
    return await service.list_alerts()
