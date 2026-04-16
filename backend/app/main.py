from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import db
from app.routes.health import router as health_router
from app.routes.orchestrator import router as orchestrator_router
from app.routes.dashboard import router as dashboard_router
from app.routes.validators import router as validators_router
from app.services.validator_service import seed_validators

app = FastAPI(title="Aurelius API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_seed():
    seed_validators(db)

app.include_router(health_router)
app.include_router(orchestrator_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(validators_router, prefix="/api")
