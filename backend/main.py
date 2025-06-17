from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.api.v1.endpoints import neighborhoods, newsletters, conversations, preview, test_events, chat, context_chat

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from app.database.mongodb import connect_to_mongo, close_mongo_connection
        await connect_to_mongo()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Some features may not work.")
    yield
    # Shutdown
    try:
        from app.database.mongodb import close_mongo_connection
        await close_mongo_connection()
    except Exception as e:
        logger.warning(f"MongoDB disconnect failed: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    redirect_slashes=False
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_origin_regex="https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Order matters! More specific routes first
app.include_router(context_chat.router, prefix="/api/v1", tags=["context-chat"])
app.include_router(neighborhoods.router, prefix="/api/v1/neighborhoods", tags=["neighborhoods"])
app.include_router(newsletters.router, prefix="/api/v1/newsletters", tags=["newsletters"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(preview.router, prefix="/api/v1/preview", tags=["preview"])
app.include_router(test_events.router, prefix="/api/v1", tags=["test"])
# Chat router MUST be last because it has a generic /{newsletter_id} route
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Newsletter Generator API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "AI Chat API is running",
        "version": settings.VERSION,
        "ai_chat_available": True
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
