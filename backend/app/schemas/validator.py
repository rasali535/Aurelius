from pydantic import BaseModel

class ValidatorResult(BaseModel):
    validator_id: str
    check_type: str
    status: str
    risk_score: float
    reason: str
    response_time_ms: int
    unit_price: float
