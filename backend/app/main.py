from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import db
from app.routes.health import router as health_router
from app.routes.orchestrator import router as orchestrator_router
from app.routes.dashboard import router as dashboard_router
from app.routes.validators import router as validators_router
from app.routes.commerce import router as commerce_router
from app.routes.router import router as task_router
from app.services.validator_service import seed_validators

app = FastAPI(title="Aurelius API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_seed():
    # Initialize the database proxy with either motor or mongomock
    from app.db import init_db, db as db_proxy
    initialized_db = await init_db()
    db_proxy.set_db(initialized_db)
    
    await seed_validators(db)

app.include_router(health_router)
app.include_router(orchestrator_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(validators_router, prefix="/api")
app.include_router(commerce_router, prefix="/api/commerce")
app.include_router(task_router, prefix="/api/router")
