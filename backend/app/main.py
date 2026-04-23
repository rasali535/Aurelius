import logging
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.db import init_db, db
from app.routes import orchestrator, dashboard, commerce, market, router
from app.config import settings

app = FastAPI(title="Aurelius Backend")

# Build CORS origins dynamically
_dev_origins = ["http://localhost:5173", "http://localhost:3000"]
_static_origins = ["https://lightseagreen-bear-113896.hostingersite.com", "https://aurelius-production-2ec3.up.railway.app"]
_frontend_origin_env = os.environ.get("FRONTEND_ORIGIN", "")

if _frontend_origin_env:
    _configured_origins = []
    for _raw in _frontend_origin_env.split(","):
        _origin = _raw.strip()
        if not _origin:
            continue
        if _origin.startswith("http://") or _origin.startswith("https://"):
            _configured_origins.append(_origin)
        else:
            _configured_origins.append(f"https://{_origin}")
            _configured_origins.append(f"http://{_origin}")
else:
    _configured_origins = []

_allow_origins = list(set(_configured_origins + _dev_origins + _static_origins))
logger.info("CORS allow_origins: %s", _allow_origins)

# Permissive CORS for production stability
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "alive", "database": "postgresql", "initialized": db._db is not None}

@app.on_event("startup")
async def startup_event():
    # Immediate start to satisfy Railway health check
    # Defer database initialization and seeding to a background task
    asyncio.create_task(deferred_startup())

async def deferred_startup():
    try:
        print("Starting Aurelius Backend deferred initialization...")
        db_instance = await init_db()
        db.set_db(db_instance)
        
        # Seed validators
        from app.services.validator_service import seed_validators
        await seed_validators(db)
        
        print("Aurelius Backend initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Backend initialization failed: {e}")
        logger.error(f"Backend initialization failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
