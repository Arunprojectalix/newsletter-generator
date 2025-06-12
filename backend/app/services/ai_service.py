from openai import AsyncOpenAI
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.newsletter import EventDetails, NewsletterContent
from app.services.event_scraper import EventScraper

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.event_scraper = EventScraper()
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_newsletter(
        self, 
        neighborhood_data: Dict[str, Any],
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> NewsletterContent:
        """Generate newsletter content using AI."""
        try:
            # First, search for real events
            events = await self.event_scraper.search_events(
                postcode=neighborhood_data["postcode"],
                radius=neighborhood_data["radius"],
                frequency=neighborhood_data["frequency"]
            )
            
            # Check if OpenAI API key is properly configured
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
                raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            
            # Create system prompt with anti-hallucination guidelines
            system_prompt = self._create_system_prompt(neighborhood_data, events)
            
            # Create messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_context:
                messages.extend(conversation_context)
            
            # User prompt
            user_prompt = self._create_user_prompt(neighborhood_data, events)
            messages.append({"role": "user", "content": user_prompt})
            
            # Generate newsletter content
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.3,  # Lower temperature for more factual output
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = json.loads(response.choices[0].message.content)
            
            # Validate and enhance content
            newsletter_content = self._validate_content(content, events)
            
            return NewsletterContent(**newsletter_content)
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            raise
    
    def _create_system_prompt(
        self, 
        neighborhood_data: Dict[str, Any], 
        verified_events: List[Dict[str, Any]]
    ) -> str:
        return f"""You are a community newsletter generator for social housing communities in the UK.

CRITICAL INSTRUCTIONS:
1. ONLY use events from the provided verified events list. DO NOT create or imagine any events.
2. If no events are provided, clearly state that no events were found and suggest checking back later.
3. Focus on free or low-cost activities suitable for families in social housing.
4. Maintain a warm, inclusive, and community-focused tone.
5. Format all content according to the required JSON structure.
6. NEVER generate fake image filenames or URLs. Leave images array empty [] unless you have real image URLs.

NEIGHBORHOOD CONTEXT:
- Location: {neighborhood_data['postcode']}
- Radius: {neighborhood_data['radius']} miles
- Frequency: {neighborhood_data['frequency']}
- Community Info: {neighborhood_data.get('info', 'General community newsletter')}
- Branding: {neighborhood_data['branding']['company_name']}

VERIFIED EVENTS:
{json.dumps(verified_events, indent=2)}

You must return a JSON object with this EXACT structure:
{{
  "header": {{
    "title": "Community Newsletter Title",
    "date": "Current Date",
    "issue_number": "Issue #X",
    "location": "Postcode Area"
  }},
  "main_channel": {{
    "welcome_message": "Welcome text",
    "community_updates": ["Update 1", "Update 2"],
    "featured_message": "Feature message"
  }},
  "weekly_schedule": {{
    "Monday": ["Activity 1"],
    "Tuesday": ["Activity 2"]
  }} OR null,
  "monthly_schedule": {{
    "Week 1": ["Activity"],
    "Week 2": ["Activity"]  
  }} OR null,
  "featured_venue": {{
    "name": "Venue Name",
    "description": "Description",
    "services": ["Service 1", "Service 2"]
  }} OR null,
  "partner_spotlight": {{
    "organization": "Org Name",
    "description": "Description",
    "contact": "Contact info"
  }} OR null,
  "newsletter_highlights": [
    {{
      "title": "Highlight Title",
      "description": "Description",
      "priority": "high|medium|low"
    }}
  ],
  "events": [
    {{
      "event_title": "Event Name",
      "description": "Event Description",
      "location": "Event Location",
      "cost": "Free|£X",
      "date": "YYYY-MM-DD",
      "booking_details": "How to book",
      "images": [],
      "additional_info": "Extra info",
      "is_recurring": true/false,
      "tags": ["tag1", "tag2"],
      "source_url": null,
      "verified": true
    }}
  ]
}}

CRITICAL: 
- newsletter_highlights MUST be a direct array, NOT wrapped in any other object.
- images MUST always be an empty array [] - DO NOT generate fake filenames like 'event.jpg'."""

    def _create_user_prompt(
        self, 
        neighborhood_data: Dict[str, Any], 
        events: List[Dict[str, Any]]
    ) -> str:
        if not events:
            return f"""Generate a newsletter for {neighborhood_data['postcode']} area. 
No events were found within {neighborhood_data['radius']} miles. 
Create a newsletter that acknowledges this and provides general community information and resources."""
        
        return f"""Generate a {neighborhood_data['frequency'].lower()} newsletter for the {neighborhood_data['postcode']} area.
Use ONLY the verified events provided. Organize them appropriately and create engaging content that serves the community."""

    def _validate_content(
        self, 
        content: Dict[str, Any], 
        verified_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate AI-generated content against verified events."""
        # Fix newsletter_highlights structure if AI returned it wrapped in a dictionary
        if 'newsletter_highlights' in content:
            highlights = content['newsletter_highlights']
            if isinstance(highlights, dict):
                # If AI returned {"key_highlights": [...]} instead of [...]
                if 'key_highlights' in highlights:
                    content['newsletter_highlights'] = highlights['key_highlights']
                # If AI returned {"highlights": [...]} instead of [...]
                elif 'highlights' in highlights:
                    content['newsletter_highlights'] = highlights['highlights']
                # If it's a dict with other keys, try to extract the list
                else:
                    for key, value in highlights.items():
                        if isinstance(value, list):
                            content['newsletter_highlights'] = value
                            break
            elif not isinstance(highlights, list):
                # If it's neither dict nor list, initialize as empty list
                content['newsletter_highlights'] = []
        else:
            # Ensure newsletter_highlights exists
            content['newsletter_highlights'] = []
        
        # Ensure all events in the content are from verified list
        verified_titles = {e['event_title'] for e in verified_events}
        
        if 'events' in content:
            content['events'] = [
                event for event in content['events']
                if event.get('event_title') in verified_titles
            ]
        
        # Add verification flag
        for event in content.get('events', []):
            event['verified'] = True
            
            # Clean up images - remove fake filenames
            if 'images' in event:
                valid_images = []
                for img in event['images']:
                    if isinstance(img, str):
                        # Only keep real URLs, skip placeholder filenames
                        if img.startswith('http://') or img.startswith('https://'):
                            valid_images.append(img)
                        # Skip fake filenames like 'event.jpg', 'family_fun_day.jpg', etc.
                event['images'] = valid_images
            
        return content
    
    async def update_newsletter(
        self,
        current_content: Dict[str, Any],
        user_message: str,
        neighborhood_data: Dict[str, Any]
    ) -> NewsletterContent:
        """Update newsletter based on user feedback."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are updating a community newsletter based on user feedback.
                    Maintain all verified events and factual information.
                    Only make the requested changes while keeping the structure intact.
                    Return the complete updated newsletter in JSON format."""
                },
                {
                    "role": "assistant",
                    "content": f"Current newsletter: {json.dumps(current_content)}"
                },
                {
                    "role": "user",
                    "content": f"Please make this change: {user_message}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            updated_content = json.loads(response.choices[0].message.content)
            return NewsletterContent(**updated_content)
            
        except Exception as e:
            logger.error(f"Error updating newsletter: {e}")
            raise
    

