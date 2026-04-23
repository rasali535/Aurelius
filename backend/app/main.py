import logging
import asyncio
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging to be extremely visible in Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("aurelius")
logger.info("Aurelius process starting up...")

from app.db import init_db, db
from app.routes import orchestrator, dashboard, commerce, market, router
from app.config import settings

app = FastAPI(title="Aurelius Backend")

# --- Extremely Permissive CORS for Production Stability ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Must be False for wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handler to ensure CORS headers even on errors ---
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global handler caught error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
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
    logger.info("Scheduling deferred startup task...")
    asyncio.create_task(deferred_startup())

async def deferred_startup():
    try:
        logger.info("Running deferred initialization...")
        db_instance = await init_db()
        db.set_db(db_instance)
        
        # Seed initial agents if needed
        from app.db import seed_initial_data
        await seed_initial_data(db_instance)
        
        logger.info("Aurelius Backend initialization complete.")
    except Exception as e:
        logger.error(f"CRITICAL: Backend initialization failed: {e}", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
