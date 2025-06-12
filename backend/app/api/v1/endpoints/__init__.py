from fastapi import APIRouter
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.newsletters import router as newsletters_router
from app.api.v1.endpoints.neighborhoods import router as neighborhoods_router
from app.api.v1.endpoints.preview import router as preview_router

api_router = APIRouter()
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(newsletters_router, prefix="/newsletters", tags=["newsletters"])
api_router.include_router(neighborhoods_router, prefix="/neighborhoods", tags=["neighborhoods"])
api_router.include_router(preview_router, prefix="/preview", tags=["preview"])