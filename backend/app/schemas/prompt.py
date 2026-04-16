from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    run_id: str
    draft_response: str
    final_status: str
    total_cost_usdc: float
    validator_count: int
