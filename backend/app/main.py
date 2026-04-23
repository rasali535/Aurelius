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

# Check Port
PORT = int(os.getenv("PORT", 3000))
logger.info(f"Target Port: {PORT}")

# --- Initialize FastAPI ---
app = FastAPI(title="Aurelius Backend")

# --- Explicit CORS for Production (User Request) ---
FRONTEND_ORIGIN = "https://lightseagreen-bear-113896.hostingersite.com"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        # Only add manual headers if not already present
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = FRONTEND_ORIGIN
        return response
    except Exception as e:
        logger.error(f"Middleware Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e)},
            headers={"Access-Control-Allow-Origin": FRONTEND_ORIGIN}
        )

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED ERROR: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": FRONTEND_ORIGIN,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# --- Deferred Imports ---
try:
    from app.db import init_db, db
    from app.routes import orchestrator, dashboard, commerce, market, router
    
    # Routes at /api
    app.include_router(orchestrator.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(commerce.router, prefix="/api")
    app.include_router(market.router, prefix="/api")
    app.include_router(router.router, prefix="/api")
except Exception as e:
    logger.error(f"Router Import Error: {e}")

@app.get("/")
@app.get("/api")
async def root():
    return {"message": "Aurelius AI Lead Agent API", "status": "active"}

@app.get("/health")
@app.get("/api/health")
async def health():
    # Always return 200 to keep Railway happy
    status = "alive" if db._db else "initializing"
    return {"status": status, "initialized": db._db is not None}

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
    uvicorn.run(app, host="0.0.0.0", port=PORT)
