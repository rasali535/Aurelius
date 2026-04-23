import logging
import asyncio
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

from app.db import init_db, db
from app.routes import orchestrator, dashboard, commerce, market, router
from app.config import settings

app = FastAPI(title="Aurelius Backend")

# --- CORS Configuration ---
_dev_origins = ["http://localhost:5173", "http://localhost:3000"]
_static_origins = [
    "https://lightseagreen-bear-113896.hostingersite.com",
    "https://aurelius-production-2ec3.up.railway.app",
]
_configured_origins = [settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else []

_allow_origins = list(set(_configured_origins + _dev_origins + _static_origins))
logger.info("CORS allow_origins: %s", _allow_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(orchestrator.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(commerce.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(router.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Aurelius AI Lead Agent API", "status": "active"}

@app.get("/health")
async def health():
    if db._db is None:
        return {
            "status": "initializing",
            "database": "postgresql",
            "initialized": False,
            "message": "Aurelius is connecting to the neural network..."
        }
    return {"status": "alive", "database": "postgresql", "initialized": True}

@app.on_event("startup")
async def startup_event():
    # Immediate start to satisfy Railway health check
    # Defer database initialization and seeding to a background task
    asyncio.create_task(deferred_startup())

async def deferred_startup():
    try:
        logger.info("Starting Aurelius Backend deferred initialization...")
        db_instance = await init_db()
        db.set_db(db_instance)
        
        # Seed initial agents if needed
        from app.db import seed_initial_data
        await seed_initial_data(db_instance)
        
        logger.info("Aurelius Backend initialization complete.")
    except Exception as e:
        logger.error(f"CRITICAL: Backend initialization failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
