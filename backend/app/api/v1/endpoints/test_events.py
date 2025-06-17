from fastapi import APIRouter, HTTPException
from app.services.enhanced_event_scraper import EnhancedEventScraper
from openai import AsyncOpenAI
from app.core.config import settings
from datetime import datetime
from app.database.mongodb import get_database
from bson import ObjectId
from app.models.newsletter import NewsletterModel, NewsletterContent, NewsletterMetadata, EventDetails

router = APIRouter()

@router.get("/test-events/{postcode}")
async def test_events(postcode: str, radius: float = 5.0):
    """Test the enhanced event scraper directly."""
    scraper = EnhancedEventScraper()
    events = await scraper.search_events(postcode, radius, "Weekly")
    return {
        "postcode": postcode,
        "radius": radius,
        "events_found": len(events),
        "events": events
    }

@router.get("/test-openai")
async def test_openai():
    """Test OpenAI API connection."""
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in JSON format with a message field."}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return {
            "status": "success",
            "response": response.choices[0].message.content,
            "model": response.model
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/test-newsletter/{postcode}")
async def test_newsletter_generation(postcode: str):
    """Test newsletter generation with enhanced events."""
    try:
        # Get enhanced events
        scraper = EnhancedEventScraper()
        events = await scraper.search_events(postcode, 5.0, "Weekly")
        
        # Create a simple newsletter structure
        newsletter = {
            "header": {
                "title": f"{postcode} Community Newsletter",
                "date": datetime.now().strftime('%B %d, %Y'),
                "issue_number": "Issue #1",
                "location": postcode
            },
            "main_channel": {
                "welcome_message": f"Welcome to this week's {postcode} community newsletter! We're excited to share the latest events and opportunities in your neighborhood.",
                "community_updates": [
                    "Community center renovations are progressing well",
                    "New recycling bins have been installed throughout the area"
                ],
                "featured_message": "Stay connected with your community and discover new opportunities to get involved!"
            },
            "newsletter_highlights": [
                {
                    "title": "Enhanced Event Listings",
                    "description": "We now provide detailed event information with images, booking details, and direct links",
                    "priority": "high"
                },
                {
                    "title": "Community Engagement",
                    "description": "Join us for various activities designed to bring neighbors together",
                    "priority": "medium"
                }
            ],
            "events": events
        }
        
        return {
            "status": "success",
            "newsletter": newsletter,
            "events_count": len(events),
            "message": "Newsletter generated successfully with enhanced events!"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/create-enhanced-newsletter/{neighborhood_id}")
async def create_enhanced_newsletter(neighborhood_id: str):
    """Create a working newsletter with enhanced events and save to database."""
    try:
        db = get_database()
        
        # Validate neighborhood exists
        if not ObjectId.is_valid(neighborhood_id):
            raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
        
        neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(neighborhood_id)})
        if not neighborhood:
            raise HTTPException(status_code=404, detail="Neighborhood not found")
        
        # Get enhanced events
        scraper = EnhancedEventScraper()
        events_data = await scraper.search_events(
            postcode=neighborhood["postcode"],
            radius=neighborhood["radius"],
            frequency=neighborhood["frequency"]
        )
        
        # Convert events to EventDetails objects
        events = [EventDetails(**event) for event in events_data]
        
        # Create newsletter content
        content = NewsletterContent(
            header={
                "title": f"{neighborhood['title']} Community Newsletter",
                "date": datetime.now().strftime('%B %d, %Y'),
                "issue_number": "Issue #1",
                "location": neighborhood["postcode"]
            },
            main_channel={
                "welcome_message": f"Welcome to this week's {neighborhood['title']} community newsletter! We're excited to share the latest events and opportunities in your neighborhood.",
                "community_updates": [
                    "Enhanced event listings now include images and direct booking links",
                    "Community engagement opportunities are highlighted with detailed information"
                ],
                "featured_message": "Discover amazing local events with professional images, detailed descriptions, and easy booking!"
            },
            newsletter_highlights=[
                {
                    "title": "Enhanced Event Experience",
                    "description": "All events now feature high-quality images, detailed descriptions, and direct booking links",
                    "priority": "high"
                },
                {
                    "title": "Real Community Events",
                    "description": "Events sourced from local councils, libraries, community centers, and verified platforms",
                    "priority": "high"
                },
                {
                    "title": "Easy Booking",
                    "description": "Click through to book events directly or get more information from official sources",
                    "priority": "medium"
                }
            ],
            events=events
        )
        
        # Create metadata
        metadata = NewsletterMetadata(
            location=neighborhood["title"],
            postcode=neighborhood["postcode"],
            radius=neighborhood["radius"],
            generation_date=datetime.utcnow(),
            template_version="v1",
            source_count=len(events),
            verification_status="verified"
        )
        
        # Create newsletter
        newsletter = NewsletterModel(
            neighborhood_id=ObjectId(neighborhood_id),
            newsletter_metadata=metadata,
            content=content,
            status="generated"
        )
        
        # Insert newsletter
        result = await db.newsletters.insert_one(
            newsletter.dict(by_alias=True, exclude={"id"})
        )
        
        # Get created newsletter
        created = await db.newsletters.find_one({"_id": result.inserted_id})
        created["_id"] = str(created["_id"])
        created["neighborhood_id"] = str(created["neighborhood_id"])
        
        return {
            "status": "success",
            "newsletter_id": str(result.inserted_id),
            "events_count": len(events),
            "message": "Enhanced newsletter created successfully!",
            "newsletter": created
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        } 