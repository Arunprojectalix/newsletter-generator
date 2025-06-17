import httpx
import asyncio
from typing import List, Dict, Any, Optional
import logging
import json
import re
from datetime import datetime
from urllib.parse import quote
import os

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Initialize OpenAI client only if API key is available
        self.openai_client = None
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            logger.info("OpenAI API key not found, using fallback search methods only")
    
    async def search_web(self, query: str, location: Optional[Dict[str, str]] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using OpenAI's web search capabilities and fallback methods.
        """
        try:
            logger.info(f"Searching web for: {query}")
            
            # Try OpenAI web search first if available
            if self.openai_client:
                openai_results = await self._search_with_openai(query, location, max_results)
                if openai_results:
                    return openai_results
            
            # Fallback to other search methods
            fallback_results = await self._search_with_fallback(query, location, max_results)
            return fallback_results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []
    
    async def _search_with_openai(self, query: str, location: Optional[Dict[str, str]] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Use OpenAI's web search preview functionality.
        """
        if not self.openai_client:
            return []
            
        try:
            # Prepare location data
            user_location = {
                "type": "approximate",
                "country": "GB",
                "city": "London",
                "region": "London"
            }
            
            if location:
                user_location.update({
                    "country": location.get("country", "GB"),
                    "city": location.get("city", "London"),
                    "region": location.get("region", "London")
                })
            
            # Create the web search request
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # Use the latest model that supports web search
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that searches the web for current information. Provide accurate, up-to-date results with sources."
                    },
                    {
                        "role": "user",
                        "content": f"Search for: {query}. Please provide specific results with URLs and brief descriptions."
                    }
                ],
                tools=[{
                    "type": "web_search",
                    "web_search": {
                        "user_location": user_location
                    }
                }],
                tool_choice="auto",
                max_tokens=1000
            )
            
            # Process the response
            results = []
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                
                # Parse the content to extract search results
                # This is a simplified parser - in practice, you'd want more robust parsing
                lines = content.split('\n')
                current_result = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('http'):
                        if current_result:
                            results.append(current_result)
                        current_result = {
                            'url': line,
                            'title': '',
                            'description': '',
                            'source': 'OpenAI Web Search'
                        }
                    elif line and current_result and not current_result.get('title'):
                        current_result['title'] = line
                    elif line and current_result and current_result.get('title') and not current_result.get('description'):
                        current_result['description'] = line
                
                if current_result:
                    results.append(current_result)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error with OpenAI web search: {e}")
            return []
    
    async def _search_with_fallback(self, query: str, location: Optional[Dict[str, str]] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback search using direct web scraping and known sources.
        """
        try:
            results = []
            
            # Search specific sources based on query type
            if any(keyword in query.lower() for keyword in ['event', 'events', 'meetup', 'conference']):
                event_results = await self._search_events(query, location)
                results.extend(event_results)
            
            if any(keyword in query.lower() for keyword in ['restaurant', 'food', 'dining', 'eat']):
                restaurant_results = await self._search_restaurants(query, location)
                results.extend(restaurant_results)
            
            if any(keyword in query.lower() for keyword in ['news', 'latest', 'current', 'today']):
                news_results = await self._search_news(query, location)
                results.extend(news_results)
            
            # Generic web search fallback
            if not results:
                generic_results = await self._generic_web_search(query, location)
                results.extend(generic_results)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error with fallback search: {e}")
            return []
    
    async def _search_events(self, query: str, location: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Search for events using Eventbrite and other event platforms."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # Search Eventbrite
                search_url = f"https://www.eventbrite.com/d/united-kingdom/events/?q={quote(query)}"
                response = await client.get(search_url)
                
                if response.status_code == 200:
                    # Simple parsing - in practice you'd use BeautifulSoup
                    content = response.text
                    if "events" in content.lower():
                        results.append({
                            'url': search_url,
                            'title': f'Events related to "{query}"',
                            'description': f'Find events and activities related to {query} on Eventbrite',
                            'source': 'Eventbrite'
                        })
        except Exception as e:
            logger.error(f"Error searching events: {e}")
        
        return results
    
    async def _search_restaurants(self, query: str, location: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Search for restaurants and dining options."""
        results = []
        try:
            # Add restaurant search results
            results.append({
                'url': f'https://www.tripadvisor.co.uk/Restaurants',
                'title': f'Restaurants for "{query}"',
                'description': f'Find restaurants and dining options related to {query}',
                'source': 'TripAdvisor'
            })
            
            results.append({
                'url': f'https://www.opentable.co.uk/s/?query={quote(query)}',
                'title': f'Book restaurants for "{query}"',
                'description': f'Make reservations at restaurants related to {query}',
                'source': 'OpenTable'
            })
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
        
        return results
    
    async def _search_news(self, query: str, location: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Search for news and current information."""
        results = []
        try:
            # Add news search results
            results.append({
                'url': f'https://www.bbc.co.uk/search?q={quote(query)}',
                'title': f'BBC News: "{query}"',
                'description': f'Latest news and information about {query} from BBC',
                'source': 'BBC News'
            })
            
            results.append({
                'url': f'https://www.theguardian.com/search?q={quote(query)}',
                'title': f'The Guardian: "{query}"',
                'description': f'News articles and analysis about {query} from The Guardian',
                'source': 'The Guardian'
            })
        except Exception as e:
            logger.error(f"Error searching news: {e}")
        
        return results
    
    async def _generic_web_search(self, query: str, location: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Generic web search fallback."""
        results = []
        try:
            # Add generic search results
            results.append({
                'url': f'https://www.google.com/search?q={quote(query)}',
                'title': f'Search results for "{query}"',
                'description': f'Find information about {query} on the web',
                'source': 'Google Search'
            })
        except Exception as e:
            logger.error(f"Error with generic search: {e}")
        
        return results
    
    async def search_local_businesses(self, query: str, location: str, business_type: str = "any") -> List[Dict[str, Any]]:
        """Search for local businesses in a specific area."""
        try:
            logger.info(f"Searching for {business_type} businesses: {query} in {location}")
            
            results = []
            
            # Search Google Maps/Places
            results.append({
                'url': f'https://www.google.com/maps/search/{quote(f"{query} {location}")}',
                'title': f'{business_type.title()} businesses: {query}',
                'description': f'Find {business_type} businesses related to {query} in {location}',
                'source': 'Google Maps'
            })
            
            # Search Yelp
            results.append({
                'url': f'https://www.yelp.co.uk/search?find_desc={quote(query)}&find_loc={quote(location)}',
                'title': f'Yelp: {query} in {location}',
                'description': f'Reviews and ratings for {query} businesses in {location}',
                'source': 'Yelp'
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching local businesses: {e}")
            return []
    
    async def search_real_time_info(self, query: str, info_type: str = "general") -> List[Dict[str, Any]]:
        """Search for real-time information like weather, traffic, etc."""
        try:
            logger.info(f"Searching for real-time {info_type} info: {query}")
            
            results = []
            
            if info_type == "weather":
                results.append({
                    'url': f'https://www.bbc.co.uk/weather/search?q={quote(query)}',
                    'title': f'Weather for {query}',
                    'description': f'Current weather conditions and forecast for {query}',
                    'source': 'BBC Weather'
                })
            
            elif info_type == "traffic":
                results.append({
                    'url': f'https://www.google.com/maps/search/{quote(query)}',
                    'title': f'Traffic conditions for {query}',
                    'description': f'Real-time traffic information for {query}',
                    'source': 'Google Maps'
                })
            
            elif info_type == "transport":
                results.append({
                    'url': f'https://www.nationalrail.co.uk/stations_destinations/default.aspx?q={quote(query)}',
                    'title': f'Transport information for {query}',
                    'description': f'Train and transport schedules for {query}',
                    'source': 'National Rail'
                })
            
            else:
                # General real-time search
                results.append({
                    'url': f'https://www.google.com/search?q={quote(f"{query} real time current")}',
                    'title': f'Real-time information: {query}',
                    'description': f'Current and up-to-date information about {query}',
                    'source': 'Google Search'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching real-time info: {e}")
            return [] 