from fastapi import APIRouter, Depends

from services.bff.clients.automation_client import AutomationClient
from services.bff.deps import get_automation_client

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", summary="Список правил автоматизации")
async def list_rules(client: AutomationClient = Depends(get_automation_client)):
    return await client.list_rules()
