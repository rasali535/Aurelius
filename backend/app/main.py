import asyncio
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
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://lightseagreen-bear-113896.hostingersite.com",
        settings.FRONTEND_ORIGIN
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Immediate start to satisfy Railway health check
    from app.db import init_db, db as db_proxy
    asyncio.create_task(deferred_startup(db_proxy))

async def deferred_startup(db_proxy):
    try:
        initialized_db = await init_db()
        db_proxy.set_db(initialized_db)
        await seed_validators(db_proxy)
        print("Backend services fully initialized in background.")
    except Exception as e:
        print(f"Deferred initialization failed: {e}")

from app.routes.market import router as market_router

app.include_router(health_router)
app.include_router(orchestrator_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(validators_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(commerce_router, prefix="/api/commerce")
app.include_router(task_router, prefix="/api/router")
