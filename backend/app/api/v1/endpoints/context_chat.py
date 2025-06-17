from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel

from app.services.context_aware_ai_service import ContextAwareAIService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instance of the context-aware service (lazy-loaded)
context_ai_service = None

def get_context_ai_service():
    """Get context AI service, initializing only when needed"""
    global context_ai_service
    if context_ai_service is None:
        context_ai_service = ContextAwareAIService()
    return context_ai_service

class ContextChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ContextChatResponse(BaseModel):
    success: bool
    action_taken: str
    target: str
    reasoning: str
    result: Dict[str, Any]
    confidence: float
    conversation_history: List[Dict[str, Any]]
    newsletter_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/context-chat", response_model=ContextChatResponse)
async def context_aware_chat(request: ContextChatRequest):
    """
    Context-aware chat endpoint that can:
    1. Generate newsletters
    2. Add/modify/delete events
    3. Change tone and content
    4. Search web for information
    5. Make intelligent decisions about where to apply changes
    """
    try:
        logger.info(f"Processing context-aware chat request: {request.message[:100]}...")
        
        # Process the user request with full context awareness
        service = get_context_ai_service()
        result = await service.process_user_request(
            user_message=request.message,
            context=request.context or {}
        )
        
        if result.get("success", False):
            return ContextChatResponse(
                success=True,
                action_taken=result["action_taken"],
                target=result["target"],
                reasoning=result["reasoning"],
                result=result["result"],
                confidence=result["confidence"],
                conversation_history=service.get_conversation_history(),
                newsletter_state=service.get_current_newsletter_state()
            )
        else:
            return ContextChatResponse(
                success=False,
                action_taken="error",
                target="chat",
                reasoning="Error occurred during processing",
                result={},
                confidence=0.0,
                conversation_history=service.get_conversation_history(),
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Error in context-aware chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/newsletter-state")
async def get_newsletter_state():
    """Get the current newsletter state"""
    try:
        service = get_context_ai_service()
        state = service.get_current_newsletter_state()
        return {
            "success": True,
            "newsletter_state": state,
            "has_newsletter": state is not None
        }
    except Exception as e:
        logger.error(f"Error getting newsletter state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation-history")
async def get_conversation_history():
    """Get the conversation history"""
    try:
        service = get_context_ai_service()
        history = service.get_conversation_history()
        return {
            "success": True,
            "conversation_history": history,
            "total_interactions": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-preferences")
async def set_user_preferences(preferences: Dict[str, Any]):
    """Set user preferences for context"""
    try:
        service = get_context_ai_service()
        service.set_user_preferences(preferences)
        return {
            "success": True,
            "message": "User preferences updated",
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error setting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-context")
async def reset_context():
    """Reset the context and conversation history"""
    try:
        global context_ai_service
        context_ai_service = None  # Reset to None, will be lazy-loaded on next use
        return {
            "success": True,
            "message": "Context and conversation history reset"
        }
    except Exception as e:
        logger.error(f"Error resetting context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Tool-specific endpoints for direct access
@router.post("/generate-newsletter")
async def generate_newsletter_direct(
    postcode: str,
    radius: float = 5.0,
    frequency: str = "weekly",
    target_audience: str = "families with children in social housing",
    tone: str = "friendly and informative"
):
    """Direct newsletter generation endpoint"""
    try:
        service = get_context_ai_service()
        result = await service.process_user_request(
            user_message=f"Generate a {frequency} newsletter for {target_audience} in {postcode} within {radius} miles with a {tone} tone",
            context={
                "postcode": postcode,
                "radius": radius,
                "frequency": frequency,
                "target_audience": target_audience,
                "tone": tone
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in direct newsletter generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-events")
async def add_events_to_newsletter(
    postcode: str = "TS1 3BA",
    radius: float = 10.0,
    frequency: str = "weekly"
):
    """Add more events to existing newsletter"""
    try:
        service = get_context_ai_service()
        result = await service.process_user_request(
            user_message=f"Add more events to the newsletter from {postcode} within {radius} miles",
            context={
                "postcode": postcode,
                "radius": radius,
                "frequency": frequency
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-tone")
async def change_newsletter_tone(tone: str):
    """Change the tone of the existing newsletter"""
    try:
        service = get_context_ai_service()
        result = await service.process_user_request(
            user_message=f"Change the newsletter tone to {tone}",
            context={"new_tone": tone}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error changing tone: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-events")
async def delete_events_from_newsletter(event_titles: List[str]):
    """Delete specific events from newsletter"""
    try:
        service = get_context_ai_service()
        result = await service.process_user_request(
            user_message=f"Delete these events from the newsletter: {', '.join(event_titles)}",
            context={"events_to_delete": event_titles}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 