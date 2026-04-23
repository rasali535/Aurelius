import logging
import asyncio
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Immediate stdout logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("aurelius")
logger.info(">>> AURELIUS BACKEND STARTING <<<")

# --- Initialize FastAPI ---
app = FastAPI(title="Aurelius Backend")

# --- Explicit CORS for Production ---
# We use both the middleware and a manual header just to be safe
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://lightseagreen-bear-113896.hostingersite.com")
ALLOWED_ORIGINS = [
    FRONTEND_ORIGIN,
    "https://lightseagreen-bear-113896.hostingersite.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily keep wildcard to rule out matching issues
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED ERROR: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# --- Deferred Imports to prevent startup crashes ---
from app.db import init_db, db
from app.routes import orchestrator, dashboard, commerce, market, router

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
        return {"status": "initializing", "initialized": False}
    return {"status": "alive", "initialized": True}

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI startup event triggered")
    asyncio.create_task(deferred_startup())

async def deferred_startup():
    try:
        logger.info("Initializing database connection...")
        db_instance = await init_db()
        db.set_db(db_instance)
        
        from app.db import seed_initial_data
        await seed_initial_data(db_instance)
        
        logger.info(">>> AURELIUS READY <<<")
    except Exception as e:
        logger.error(f"CRITICAL INITIALIZATION FAILURE: {e}", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
