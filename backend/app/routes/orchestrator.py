from fastapi import APIRouter
from app.db import db
from app.schemas.prompt import PromptRequest
from app.services.orchestrator_service import process_prompt_run, run_batch_demo

router = APIRouter()

@router.post("/run-prompt")
async def run_prompt(payload: PromptRequest):
    return await process_prompt_run(db, payload.prompt)

@router.post("/run-demo-batch")
async def run_demo_batch():
    # Calling the updated run_batch_demo which handles its own prompt list internally
    return await run_batch_demo(db, count=10) # Run 10 prompts for a healthy batch demo
