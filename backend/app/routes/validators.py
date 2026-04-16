from fastapi import APIRouter
from app.services.validator_service import VALIDATORS

router = APIRouter()

@router.get("/validators")
async def get_validators():
    return VALIDATORS
