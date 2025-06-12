from fastapi import APIRouter, HTTPException, Response
from bson import ObjectId

from app.database.mongodb import get_database
from app.services.newsletter_renderer import NewsletterRenderer

router = APIRouter()
renderer = NewsletterRenderer()

@router.get("/{newsletter_id}")
@router.get("/{newsletter_id}/")
async def preview_newsletter(newsletter_id: str):
    """Generate HTML preview of newsletter."""
    db = get_database()
    
    if not ObjectId.is_valid(newsletter_id):
        raise HTTPException(status_code=400, detail="Invalid newsletter ID")
    
    # Get newsletter
    newsletter = await db.newsletters.find_one({"_id": ObjectId(newsletter_id)})
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    # Get neighborhood for branding
    neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(newsletter["neighborhood_id"])})
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    # Render newsletter
    html_content = renderer.render_newsletter(
        newsletter,
        neighborhood["branding"]
    )
    
    return Response(content=html_content, media_type="text/html")
