from openai import AsyncOpenAI
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
# from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.newsletter import EventDetails, NewsletterContent
from app.services.enhanced_event_scraper import EnhancedEventScraper

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.event_scraper = EnhancedEventScraper()
        
    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_newsletter(
        self, 
        neighborhood_data: Dict[str, Any],
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> NewsletterContent:
        """Generate newsletter content using AI with enhanced events."""
        try:
            # Search for real, detailed events
            events = await self.event_scraper.search_events(
                postcode=neighborhood_data["postcode"],
                radius=neighborhood_data["radius"],
                frequency=neighborhood_data["frequency"]
            )
            
            # Check if OpenAI API key is properly configured
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
                raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            
            # Create enhanced system prompt
            system_prompt = self._create_enhanced_system_prompt(neighborhood_data, events)
            
            # Create messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_context:
                messages.extend(conversation_context)
            
            # User prompt with enhanced event data
            user_prompt = self._create_enhanced_user_prompt(neighborhood_data, events)
            # Add JSON requirement for OpenAI response_format
            user_prompt += "\n\nPlease return the newsletter content as a valid JSON object following the structure specified above."
            messages.append({"role": "user", "content": user_prompt})
            
            # Generate newsletter content with very low temperature to prevent hallucination
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1,  # Very low temperature to prevent fake events
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = json.loads(response.choices[0].message.content)
            
            # Validate and enhance content with real event data
            newsletter_content = self._validate_and_enhance_content(content, events)
            
            return NewsletterContent(**newsletter_content)
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            raise
    
    def _create_enhanced_system_prompt(
        self, 
        neighborhood_data: Dict[str, Any], 
        verified_events: List[Dict[str, Any]]
    ) -> str:
        return f"""You are an expert community newsletter generator for social housing communities in the UK.

CRITICAL INSTRUCTIONS - NEVER BREAK THESE:
1. NEVER CREATE, INVENT, OR MAKE UP ANY EVENTS
2. Use ONLY the provided verified UPCOMING events with their exact details
3. If no events are provided, create a newsletter with NO EVENTS SECTION
4. NEVER add fictional venues like "Avalon Library" or "Community Kitchen"
5. NEVER create fake dates, times, or booking details
6. Copy event details EXACTLY as provided - do not modify them
7. If you create any fictional events, the newsletter will be rejected
8. Events must have real source URLs and real booking information
9. ONLY use the events from the VERIFIED UPCOMING EVENTS list below
10. Do NOT supplement with additional events not in the list

NEIGHBORHOOD CONTEXT:
- Location: {neighborhood_data['postcode']}
- Area: {neighborhood_data.get('title', 'Community')}
- Radius: {neighborhood_data['radius']} miles
- Frequency: {neighborhood_data['frequency']}
- Community Info: {neighborhood_data.get('info', 'General community newsletter')}
- Branding: {neighborhood_data['branding']['company_name']}

VERIFIED UPCOMING EVENTS (ORGANIZED BY SCHEDULE):
{json.dumps(verified_events, indent=2)}

EVENT ORGANIZATION:
- For WEEKLY newsletters: Events are organized Monday through Sunday
- For MONTHLY newsletters: Events are organized by date (earliest first)
- PRESERVE the event order as provided - they are already properly scheduled
- Only include events that are UPCOMING (not expired or past)

NEWSLETTER STRUCTURE REQUIREMENTS:
{{
  "header": {{
    "title": "Community Newsletter Title",
    "date": "Current Date",
    "issue_number": "Issue #X",
    "location": "Postcode Area"
  }},
  "main_channel": {{
    "welcome_message": "Engaging welcome text highlighting community spirit",
    "community_updates": ["Update 1", "Update 2"],
    "featured_message": "Feature message about community"
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
      "event_title": "Exact event title from verified events",
      "description": "Full description from verified events",
      "location": "Exact location from verified events",
      "cost": "Exact cost from verified events",
      "date": "YYYY-MM-DD from verified events",
      "booking_details": "Exact booking details from verified events",
      "images": ["Exact image URLs from verified events"],
      "additional_info": "Additional info from verified events",
      "is_recurring": true/false from verified events,
      "tags": ["tags from verified events"],
      "source_url": "Exact source URL from verified events",
      "verified": true
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- newsletter_highlights MUST be a direct array
- events MUST use exact details from verified_events (titles, descriptions, images, URLs, etc.)
- images MUST be the actual URLs provided in verified_events
- source_url MUST be the actual URLs from verified_events
- Do NOT modify event details - use them exactly as provided
- PRESERVE the event order as they are already organized by schedule
- Only include UPCOMING events (no expired or past events)
- Create engaging newsletter content around these real upcoming events"""

    def _create_enhanced_user_prompt(
        self, 
        neighborhood_data: Dict[str, Any], 
        events: List[Dict[str, Any]]
    ) -> str:
        if not events:
            return f"""Generate a newsletter for {neighborhood_data['postcode']} area. 
No events were found within {neighborhood_data['radius']} miles. 
Create a newsletter that acknowledges this and provides general community information and resources."""
        
        return f"""Generate a {neighborhood_data['frequency'].lower()} newsletter for the {neighborhood_data['postcode']} area.

Use ALL the verified events provided with their complete details including:
- Exact event titles and descriptions
- Real image URLs
- Actual booking details and costs
- Source URLs for more information
- All additional information provided

Create an engaging newsletter that showcases these real community opportunities and encourages participation.
Make the content warm, welcoming, and community-focused while maintaining professionalism.

Ensure all event details are preserved exactly as provided in the verified events list."""

    def _validate_and_enhance_content(
        self, 
        content: Dict[str, Any], 
        verified_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate AI-generated content and ensure it uses real event data."""
        
        # Fix newsletter_highlights structure if needed
        if 'newsletter_highlights' in content:
            highlights = content['newsletter_highlights']
            if isinstance(highlights, dict):
                if 'key_highlights' in highlights:
                    content['newsletter_highlights'] = highlights['key_highlights']
                elif 'highlights' in highlights:
                    content['newsletter_highlights'] = highlights['highlights']
                else:
                    for key, value in highlights.items():
                        if isinstance(value, list):
                            content['newsletter_highlights'] = value
                            break
            elif not isinstance(highlights, list):
                content['newsletter_highlights'] = []
        else:
            content['newsletter_highlights'] = []
        
        # STRICT EVENT VALIDATION - Reject any fake events
        if 'events' in content:
            ai_generated_events = content['events']
            
            # Check for fake event indicators
            for event in ai_generated_events:
                event_title = event.get('event_title', '').lower()
                location = event.get('location', '').lower()
                
                # Detect fake venues and events
                fake_indicators = [
                    'avalon', 'retronics', 'community kitchen', 'town square',
                    'kids science workshop', 'holiday baking class', 'winter wonderland festival'
                ]
                
                for indicator in fake_indicators:
                    if indicator in event_title or indicator in location:
                        logger.warning(f"FAKE EVENT DETECTED: {event_title} at {location}")
                        # Completely remove fake events
                        content['events'] = []
                        break
                else:
                    continue
                break
        
        # Use ONLY verified events - never AI generated ones
        if verified_events:
            content['events'] = verified_events
        else:
            content['events'] = []
        
        # Enhance header with current date
        if 'header' not in content:
            content['header'] = {}
        
        content['header']['date'] = datetime.now().strftime('%B %d, %Y')
        
        # Ensure all required sections exist
        required_sections = ['header', 'main_channel', 'newsletter_highlights', 'events']
        for section in required_sections:
            if section not in content:
                content[section] = {} if section != 'events' and section != 'newsletter_highlights' else []
        
        # Validate event structure
        validated_events = []
        for event in content.get('events', []):
            if self._validate_event_structure(event):
                validated_events.append(event)
        
        content['events'] = validated_events
        
        logger.info(f"Newsletter generated with {len(validated_events)} verified events")
        return content
    
    def _validate_event_structure(self, event: Dict[str, Any]) -> bool:
        """Validate that an event has the required structure."""
        required_fields = ['event_title', 'description', 'location', 'date']
        return all(field in event and event[field] for field in required_fields)
    
    async def update_newsletter(
        self,
        current_content: Dict[str, Any],
        user_message: str,
        neighborhood_data: Dict[str, Any]
    ) -> NewsletterContent:
        """Update newsletter content based on user feedback."""
        try:
            # Check if OpenAI API key is properly configured
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
                raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            
            # Create system prompt for newsletter updates
            system_prompt = f"""You are updating a newsletter for {neighborhood_data['title']} community.
            
Current newsletter content:
{json.dumps(current_content, indent=2)}

User's request: {user_message}

IMPORTANT: When updating events, preserve all real event data including:
- Exact image URLs
- Source URLs
- Booking details
- Verified status
- All additional information

Only modify the content as specifically requested by the user.
Return the complete updated newsletter as a valid JSON object in the same format."""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse and validate response
            updated_content = json.loads(response.choices[0].message.content)
            
            # Ensure event data integrity is maintained
            if 'events' in current_content and 'events' in updated_content:
                # Preserve verified event data
                for i, updated_event in enumerate(updated_content['events']):
                    if i < len(current_content['events']):
                        original_event = current_content['events'][i]
                        # Preserve critical verified data
                        for field in ['images', 'source_url', 'verified', 'additional_info']:
                            if field in original_event:
                                updated_event[field] = original_event[field]
            
            validated_content = self._validate_and_enhance_content(updated_content, updated_content.get('events', []))
            
            return NewsletterContent(**validated_content)
            
        except Exception as e:
            logger.error(f"Error updating newsletter: {e}")
            raise

    async def chat_response(
        self,
        messages: List[Dict[str, str]],
        neighborhood_data: Dict[str, Any]
    ) -> str:
        """Generate conversational AI response with full context - like Claude/GPT/Cursor."""
        try:
            # Check if OpenAI API key is properly configured
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
                raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            
            # Enhanced system prompt for conversational AI
            system_prompt = f"""You are a helpful AI assistant for {neighborhood_data['title']} community newsletter management.

CONTEXT:
- Community: {neighborhood_data['title']}
- Location: {neighborhood_data['postcode']}
- Type: {neighborhood_data.get('info', 'Community newsletter')}
- Company: {neighborhood_data['branding']['company_name']}

CAPABILITIES:
1. Answer questions about newsletters and community events
2. Help modify newsletter content based on user requests
3. Provide suggestions for community engagement
4. Explain newsletter features and sections
5. Help with community-related queries
6. Discuss real events with images, links, and detailed information

PERSONALITY:
- Friendly and helpful
- Community-focused
- Professional but approachable
- Knowledgeable about local community needs
- Supportive of social housing communities

IMPORTANT:
- Always maintain conversation context
- Remember what was discussed earlier
- Be specific and actionable in responses
- When discussing events, mention that they include images, links, and detailed booking information
- Ask clarifying questions when requests are unclear
- Emphasize the quality and detail of the events provided"""

            # Prepare messages for OpenAI (ensure system message is first)
            ai_messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (skip system messages from history to avoid duplicates)
            for msg in messages:
                if msg["role"] != "system":
                    ai_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Generate response
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=ai_messages,
                temperature=0.7,  # Slightly higher for more conversational responses
                max_tokens=1000   # Reasonable limit for chat responses
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            # Return a helpful error message instead of raising
            return f"I apologize, but I'm having trouble responding right now. The error is: {str(e)}. Please try again or contact support if the issue persists."
    

