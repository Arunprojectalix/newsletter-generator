from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import api_router
from app.database.mongodb import init_db, close_mongo_connection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection on startup."""
    try:
        await init_db()
        logger.info("Database connection initialized on startup")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
        # Don't raise the exception - allow the app to start even if DB is down
        # The connection will be retried on first use

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown."""
    try:
        await close_mongo_connection()
        logger.info("Database connection closed on shutdown")
    except Exception as e:
        logger.error(f"Error closing database connection on shutdown: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get database connection
        from app.database.mongodb import get_database
        db = await get_database()
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
