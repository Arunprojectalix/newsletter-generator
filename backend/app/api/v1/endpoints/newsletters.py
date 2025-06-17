from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.database.mongodb import get_database
from app.schemas.newsletter import (
    NewsletterGenerateRequest, 
    NewsletterResponse, 
    NewsletterUpdateRequest,
    NewsletterActionRequest
)
from app.models.newsletter import NewsletterModel, NewsletterMetadata
from app.models.conversation import ConversationModel, Message
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

async def generate_newsletter_task(
    neighborhood_id: str, 
    newsletter_id: str,
    conversation_id: Optional[str] = None
):
    """Background task to generate newsletter."""
    db = get_database()
    
    try:
        # Get neighborhood data
        neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(neighborhood_id)})
        if not neighborhood:
            raise Exception("Neighborhood not found")
        
        # Get conversation context if exists
        conversation_context = None
        if conversation_id:
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if conversation:
                conversation_context = [
                    {"role": msg["role"], "content": msg["content"]} 
                    for msg in conversation.get("messages", [])
                ]
        
        # Generate newsletter content
        newsletter_content = await ai_service.generate_newsletter(
            neighborhood, 
            conversation_context
        )
        
        # Create metadata
        metadata = NewsletterMetadata(
            location=neighborhood["title"],
            postcode=neighborhood["postcode"],
            radius=neighborhood["radius"],
            generation_date=datetime.utcnow(),
            template_version="v1",
            verification_status="verified"
        )
        
        # Update newsletter
        await db.newsletters.update_one(
            {"_id": ObjectId(newsletter_id)},
            {
                "$set": {
                    "content": newsletter_content.dict(),
                    "newsletter_metadata": metadata.dict(),
                    "status": "generated",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update conversation if exists
        if conversation_id:
            ai_message = Message(
                role="assistant",
                content="Newsletter has been generated successfully! You can preview it on the right panel."
            )
            
            await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": ai_message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
    except Exception as e:
        # Update newsletter with error
        await db.newsletters.update_one(
            {"_id": ObjectId(newsletter_id)},
            {
                "$set": {
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }
            }
        )

@router.post("/generate", response_model=NewsletterResponse)
async def generate_newsletter(
    request: NewsletterGenerateRequest,
    background_tasks: BackgroundTasks
):
    """Generate a new newsletter."""
    db = get_database()
    
    # Validate neighborhood exists
    if not ObjectId.is_valid(request.neighborhood_id):
        raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
    
    neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(request.neighborhood_id)})
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    # Create initial newsletter
    newsletter = NewsletterModel(
        neighborhood_id=ObjectId(request.neighborhood_id),
        conversation_id=ObjectId(request.conversation_id) if request.conversation_id else None,
        newsletter_metadata={
            "location": neighborhood["title"],
            "postcode": neighborhood["postcode"],
            "radius": neighborhood["radius"],
            "generation_date": datetime.utcnow(),
            "template_version": "v1",
            "source_count": 0,
            "verification_status": "pending"
        },
        content={
            "header": {},
            "main_channel": {},
            "events": []
        },
        status="generating"
    )
    
    # Insert newsletter
    result = await db.newsletters.insert_one(
        newsletter.dict(by_alias=True, exclude={"id"})
    )
    
    # Start background generation
    background_tasks.add_task(
        generate_newsletter_task,
        request.neighborhood_id,
        str(result.inserted_id),
        request.conversation_id
    )
    
    # Return newsletter
    created = await db.newsletters.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])  # Convert ObjectId to string
    created["neighborhood_id"] = str(created["neighborhood_id"])  # Convert ObjectId to string
    if created.get("conversation_id"):
        created["conversation_id"] = str(created["conversation_id"])  # Convert ObjectId to string
    return NewsletterResponse(**created)

@router.get("/{newsletter_id}", response_model=NewsletterResponse)
@router.get("/{newsletter_id}/", response_model=NewsletterResponse)
async def get_newsletter(newsletter_id: str):
    """Get a specific newsletter."""
    db = get_database()
    
    if not ObjectId.is_valid(newsletter_id):
        raise HTTPException(status_code=400, detail="Invalid newsletter ID")
    
    newsletter = await db.newsletters.find_one({"_id": ObjectId(newsletter_id)})
    
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    newsletter["_id"] = str(newsletter["_id"])  # Convert ObjectId to string
    newsletter["neighborhood_id"] = str(newsletter["neighborhood_id"])  # Convert ObjectId to string
    if newsletter.get("conversation_id"):
        newsletter["conversation_id"] = str(newsletter["conversation_id"])  # Convert ObjectId to string
    return NewsletterResponse(**newsletter)

@router.put("/{newsletter_id}/update", response_model=NewsletterResponse)
async def update_newsletter(
    newsletter_id: str,
    request: NewsletterUpdateRequest,
    background_tasks: BackgroundTasks
):
    """Update newsletter based on user feedback."""
    db = get_database()
    
    if not ObjectId.is_valid(newsletter_id):
        raise HTTPException(status_code=400, detail="Invalid newsletter ID")
    
    # Get current newsletter
    newsletter = await db.newsletters.find_one({"_id": ObjectId(newsletter_id)})
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    # Get neighborhood data
    neighborhood = await db.neighborhoods.find_one({"_id": newsletter["neighborhood_id"]})
    
    try:
        # Update newsletter content
        updated_content = await ai_service.update_newsletter(
            newsletter["content"],
            request.user_message,
            neighborhood
        )
        
        # Update in database
        await db.newsletters.update_one(
            {"_id": ObjectId(newsletter_id)},
            {
                "$set": {
                    "content": updated_content.dict(),
                    "updated_at": datetime.utcnow(),
                    "version": newsletter.get("version", 1) + 1
                }
            }
        )
        
        # Get updated newsletter
        updated = await db.newsletters.find_one({"_id": ObjectId(newsletter_id)})
        updated["_id"] = str(updated["_id"])  # Convert ObjectId to string
        updated["neighborhood_id"] = str(updated["neighborhood_id"])  # Convert ObjectId to string
        if updated.get("conversation_id"):
            updated["conversation_id"] = str(updated["conversation_id"])  # Convert ObjectId to string
        return NewsletterResponse(**updated)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{newsletter_id}/action")
async def newsletter_action(
    newsletter_id: str,
    request: NewsletterActionRequest
):
    """Accept or reject a newsletter."""
    db = get_database()
    
    if not ObjectId.is_valid(newsletter_id):
        raise HTTPException(status_code=400, detail="Invalid newsletter ID")
    
    # Update newsletter status
    result = await db.newsletters.update_one(
        {"_id": ObjectId(newsletter_id)},
        {
            "$set": {
                "status": request.action + "ed",  # accepted or rejected
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    # Close associated conversation
    newsletter = await db.newsletters.find_one({"_id": ObjectId(newsletter_id)})
    if newsletter and newsletter.get("conversation_id"):
        await db.conversations.update_one(
            {"_id": newsletter["conversation_id"]},
            {
                "$set": {
                    "status": "closed",
                    "closed_at": datetime.utcnow()
                }
            }
        )
    
    return {"message": f"Newsletter {request.action}ed successfully"}

@router.get("/", response_model=List[NewsletterResponse])
@router.get("", response_model=List[NewsletterResponse])
async def list_newsletters(skip: int = 0, limit: int = 50):
    """Get all newsletters."""
    db = get_database()
    
    newsletters = []
    cursor = db.newsletters.find().sort("created_at", -1).skip(skip).limit(limit)
    
    async for newsletter in cursor:
        newsletter["_id"] = str(newsletter["_id"])  # Convert ObjectId to string
        newsletter["neighborhood_id"] = str(newsletter["neighborhood_id"])  # Convert ObjectId to string
        if newsletter.get("conversation_id"):
            newsletter["conversation_id"] = str(newsletter["conversation_id"])  # Convert ObjectId to string
        newsletters.append(NewsletterResponse(**newsletter))
    
    return newsletters

@router.delete("/{newsletter_id}")
@router.delete("/{newsletter_id}/")
async def delete_newsletter(newsletter_id: str):
    """Delete a newsletter."""
    db = get_database()
    
    if not ObjectId.is_valid(newsletter_id):
        raise HTTPException(status_code=400, detail="Invalid newsletter ID")
    
    result = await db.newsletters.delete_one({"_id": ObjectId(newsletter_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    return {"message": "Newsletter deleted successfully"}
