from uuid import uuid4
from datetime import datetime, timezone

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"

def utc_now():
    return datetime.now(timezone.utc).isoformat()
