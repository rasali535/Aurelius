import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("aurelius")

from app.config import settings
from app.db import db
from app.db import init_db
from app.routes.dashboard import router as dashboard_router
from app.routes.health import router as health_router
from app.routes.orchestrator import router as orchestrator_router
from app.routes.validators import router as validators_router
from app.routes.market import router as market_router
from app.routes.commerce import router as commerce_router
from app.routes.router import router as task_router
from app.services.validator_service import seed_validators

logger.info("Starting Aurelius Backend initialization...")

app = FastAPI(title="Aurelius API")

# Build CORS origins dynamically from FRONTEND_ORIGIN env var
_dev_origins = ["http://localhost:5173", "http://localhost:3000"]
_frontend_origin_env = os.environ.get("FRONTEND_ORIGIN", "")

if _frontend_origin_env:
    _configured_origins = []
    for _raw in _frontend_origin_env.split(","):
        _origin = _raw.strip()
        if not _origin:
            continue
        # If the value already includes a scheme, use it as-is;
        # otherwise add both https:// and http:// variants.
        if _origin.startswith("http://") or _origin.startswith("https://"):
            _configured_origins.append(_origin)
        else:
            _configured_origins.append(f"https://{_origin}")
            _configured_origins.append(f"http://{_origin}")
else:
    _configured_origins = []

_allow_origins = _configured_origins + _dev_origins

logger.info("CORS allow_origins: %s", _allow_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "alive", "database": "initialized" if db._db else "pending"}

@app.on_event("startup")
async def startup_event():
    # Immediate start to satisfy Railway health check
    from app.db import db as db_proxy
    asyncio.create_task(deferred_startup(db_proxy))

async def deferred_startup(db_proxy):
    try:
        initialized_db = await init_db()
        db_proxy.set_db(initialized_db)
        await seed_validators(db_proxy)
        print("Backend services fully initialized in background.")
    except Exception as e:
        print(f"Deferred initialization failed: {e}")
        import traceback
        traceback.print_exc()

app.include_router(health_router)
app.include_router(orchestrator_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(validators_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(commerce_router, prefix="/api/commerce")
app.include_router(task_router, prefix="/api/router")
