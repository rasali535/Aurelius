from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.router_service import router_service
from app.db import db

router = APIRouter()

class RouterRequest(BaseModel):
    task: str

@router.post("/execute")
async def execute_task(payload: RouterRequest):
    """
    Routes a task to the best Featherless model and settles in USDC.
    """
    try:
        result = await router_service.route_and_execute(db, payload.task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
