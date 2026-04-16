from pydantic import BaseModel
from typing import List, Dict, Any

class DashboardSummary(BaseModel):
    total_prompt_runs: int
    total_validations: int
    total_payments: int
    total_spend_usdc: float
    latest_transactions: List[Dict[str, Any]]
