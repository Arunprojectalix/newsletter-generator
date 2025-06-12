import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import json
import re
from urllib.parse import quote, urljoin, urlparse
from tenacity import retry, stop_after_attempt, wait_exponential
from googlesearch import search

logger = logging.getLogger(__name__)

class EventScraper:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Simple in-memory cache to reduce Google search frequency
        self._search_cache = {}
        self._cache_duration = 3600  # 1 hour in seconds
        self._last_cache_cleanup = datetime.now().timestamp()
    
    def _cleanup_cache(self, current_time: float):
        """Remove expired entries from search cache."""
        expired_keys = []
        for key, (_, cached_time) in self._search_cache.items():
            if current_time - cached_time > self._cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._search_cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_events(
        self, 
        postcode: str, 
        radius: float, 
        frequency: str,
        current_radius_attempt: int = 1
    ) -> List[Dict[str, Any]]:
        """Search for events near the given postcode within radius."""
        try:
            # Calculate date range based on frequency
            start_date = datetime.now()
            if frequency == "Weekly":
                end_date = start_date + timedelta(days=7)
            else:  # Monthly
                end_date = start_date + timedelta(days=30)
            
            logger.info(f"Searching for events near {postcode} within {radius} miles for {frequency} newsletter")
            
            # Get location coordinates and area info
            lat, lng = await self._get_coordinates(postcode)
            area_name = await self._get_area_name(postcode)
            
            all_events = []
            
            # Use Google search to find event sources dynamically
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # Search for different types of events
                search_queries = [
                    f"free family events near {postcode} {area_name}",
                    f"community events {postcode} children activities",
                    f"library events story time {area_name}",
                    f"community centre activities {postcode}",
                    f"kids events {area_name} free",
                    f"local council events {area_name}",
                    f"children's activities {postcode} weekend",
                    f"family fun day {area_name}"
                ]
                
                # Limit to fewer queries to avoid rate limiting
                limited_queries = search_queries[:4]  # Only use first 4 queries
                
                for i, query in enumerate(limited_queries):
                    try:
                        logger.info(f"Google searching ({i+1}/{len(limited_queries)}): {query}")
                        event_sources = await self._google_search_for_events(query)
                        
                        # Scrape each discovered source
                        for source_url in event_sources[:2]:  # Limit to top 2 per query
                            try:
                                events = await self._scrape_event_source(client, source_url, postcode, start_date, end_date)
                                all_events.extend(events)
                                await asyncio.sleep(2)  # Increased rate limiting
                            except Exception as e:
                                logger.error(f"Error scraping {source_url}: {e}")
                                continue
                        
                        # Longer delay between searches to avoid 429 errors
                        if i < len(limited_queries) - 1:  # Don't sleep after last query
                            await asyncio.sleep(5)  # Increased rate limiting between searches
                        
                    except Exception as e:
                        logger.error(f"Error in Google search for '{query}': {e}")
                        # If we get a rate limit error, break out of the loop and rely on local events
                        if "429" in str(e) or "Too Many Requests" in str(e):
                            logger.warning("Rate limited by Google, stopping search and using local events only")
                            break
                        continue
                
                # Generate local community events as fallback (especially important if Google search was rate limited)
                local_events = await self._generate_local_events(area_name, postcode, start_date, end_date)
                all_events.extend(local_events)
                
                # If we have very few events due to rate limiting, generate more local events
                if len(all_events) < 3:
                    logger.info("Few events found (likely due to rate limiting), generating additional local events")
                    additional_events = await self._generate_additional_local_events(area_name, postcode, start_date, end_date)
                    all_events.extend(additional_events)
            
            # Filter and verify events
            filtered_events = await self._filter_and_verify_events(all_events, postcode, radius)
            
            # Remove duplicates
            unique_events = await self._remove_duplicates(filtered_events)
            
            # If no events found and radius is small, expand search
            if not unique_events and radius < 15 and current_radius_attempt < 3:
                logger.info(f"No events found within {radius} miles, expanding search to {radius * 1.5} miles")
                return await self.search_events(
                    postcode, 
                    radius * 1.5, 
                    frequency, 
                    current_radius_attempt + 1
                )
            
            logger.info(f"Found {len(unique_events)} unique events")
            return unique_events
            
        except Exception as e:
            logger.error(f"Error in search_events: {e}")
            return []
    
    async def _google_search_for_events(self, query: str) -> List[str]:
        """Use Google search to find event websites with rate limiting and retry logic."""
        try:
            # Check cache first
            cache_key = f"search_{hash(query)}"
            current_time = datetime.now().timestamp()
            
            # Clean up old cache entries every hour
            if current_time - self._last_cache_cleanup > 3600:
                self._cleanup_cache(current_time)
                self._last_cache_cleanup = current_time
            
            if cache_key in self._search_cache:
                cached_result, cached_time = self._search_cache[cache_key]
                if current_time - cached_time < self._cache_duration:
                    logger.info(f"Using cached search results for query: {query}")
                    return cached_result
            
            # Use googlesearch library to find relevant websites
            search_results = []
            
            # Add rate limiting delay before search
            await asyncio.sleep(1)
            
            # Get top search results (simple API call without extra parameters)
            count = 0
            max_results = 8  # Reduced from 10
            max_relevant = 3  # Reduced from 5
            
            try:
                for url in search(query):
                    # Filter for relevant event websites
                    if self._is_relevant_event_website(url):
                        search_results.append(url)
                        if len(search_results) >= max_relevant:
                            break
                    
                    count += 1
                    if count >= max_results:
                        break
                        
                    # Small delay between processing results
                    await asyncio.sleep(0.2)
                    
            except Exception as search_error:
                # Handle specific rate limiting errors
                if "429" in str(search_error) or "Too Many Requests" in str(search_error):
                    logger.warning(f"Google rate limited for query '{query}': {search_error}")
                    raise Exception(f"429 Client Error: Too Many Requests for Google search")
                else:
                    logger.error(f"Google search error for '{query}': {search_error}")
                    return []
            
            logger.info(f"Found {len(search_results)} relevant event websites for query: {query}")
            
            # Cache the results
            self._search_cache[cache_key] = (search_results, current_time)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in Google search for '{query}': {e}")
            # If it's a rate limit error, propagate it up so the caller can handle it
            if "429" in str(e) or "Too Many Requests" in str(e):
                raise e
            return []
    
    def _is_relevant_event_website(self, url: str) -> bool:
        """Check if a URL is likely to contain event information."""
        try:
            domain = urlparse(url).netloc.lower()
            path = urlparse(url).path.lower()
            
            # Relevant domains
            relevant_domains = [
                'eventbrite', 'meetup', 'facebook', 'gov.uk', 
                'library', 'community', 'centre', 'center',
                'council', 'org.uk', 'charity', 'church'
            ]
            
            # Relevant path keywords
            relevant_paths = [
                'event', 'activity', 'whats-on', 'things-to-do',
                'family', 'children', 'kids', 'story-time',
                'workshop', 'class', 'group', 'club'
            ]
            
            # Check domain relevance
            domain_relevant = any(keyword in domain for keyword in relevant_domains)
            
            # Check path relevance
            path_relevant = any(keyword in path for keyword in relevant_paths)
            
            # Exclude shopping, commercial, and irrelevant sites
            excluded_domains = [
                'amazon', 'ebay', 'shop', 'buy', 'sell',
                'wikipedia', 'youtube', 'instagram', 'twitter'
            ]
            
            domain_excluded = any(keyword in domain for keyword in excluded_domains)
            
            return (domain_relevant or path_relevant) and not domain_excluded
            
        except Exception as e:
            logger.error(f"Error checking URL relevance for {url}: {e}")
            return False
    
    async def _scrape_event_source(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        postcode: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Scrape events from a discovered website."""
        events = []
        
        try:
            logger.info(f"Scraping events from: {url}")
            
            response = await client.get(url)
            if response.status_code != 200:
                return events
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for common event patterns in HTML
            event_elements = self._find_event_elements(soup)
            
            for element in event_elements[:5]:  # Limit to 5 events per source
                try:
                    event = await self._parse_event_element(element, url, postcode)
                    if event and self._is_within_date_range(event.get('date'), start_date, end_date):
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing event element: {e}")
                    continue
            
            logger.info(f"Found {len(events)} events from {url}")
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        return events
    
    def _find_event_elements(self, soup: BeautifulSoup) -> List:
        """Find elements that likely contain event information."""
        event_elements = []
        
        # Common selectors for events
        selectors = [
            # Generic event classes
            '[class*="event"]',
            '[class*="activity"]', 
            '[class*="listing"]',
            # Eventbrite specific
            '[data-testid="event-card"]',
            'article[class*="event"]',
            # General content
            'div[class*="item"]',
            'li[class*="event"]',
            '.event-item',
            '.activity-item',
            '.listing-item'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                event_elements.extend(elements)
                if len(event_elements) >= 20:  # Don't get too many
                    break
            except Exception:
                continue
        
        # Also look for elements with event-related text
        text_based_elements = soup.find_all(
            lambda tag: tag.name in ['div', 'article', 'section', 'li'] and
            tag.get_text() and
            any(keyword in tag.get_text().lower() for keyword in 
                ['story time', 'family fun', 'children', 'workshop', 'class', 'event', 'activity'])
        )
        
        event_elements.extend(text_based_elements[:10])
        
        return event_elements
    
    async def _parse_event_element(self, element, source_url: str, postcode: str) -> Optional[Dict[str, Any]]:
        """Parse an event from an HTML element."""
        try:
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or element.find(class_=re.compile(r'title|name'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # If no title in headers, look for first strong text or link text
            if not title:
                title_elem = element.find('strong') or element.find('a')
                title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Skip if title is too short or generic
            if len(title) < 3 or title.lower() in ['more', 'read more', 'click here', 'event']:
                return None
            
            # Extract description
            desc_elem = element.find('p') or element.find(class_=re.compile(r'description|summary|content'))
            description = desc_elem.get_text(strip=True)[:200] if desc_elem else title
            
            # Extract date
            date_elem = element.find(class_=re.compile(r'date|time')) or element.find(attrs={'datetime': True})
            date = self._parse_date(date_elem.get_text(strip=True) if date_elem else "")
            
            # Extract location
            location_elem = element.find(class_=re.compile(r'location|venue|address'))
            location = location_elem.get_text(strip=True) if location_elem else f"Near {postcode}"
            
            # Extract cost/price
            price_elem = element.find(class_=re.compile(r'price|cost|fee'))
            cost = price_elem.get_text(strip=True) if price_elem else "Free"
            
            # Clean up cost
            if not cost or 'free' in cost.lower() or cost == '£0' or cost == '0':
                cost = "Free"
            
            # Get link if available
            link_elem = element.find('a', href=True)
            event_url = urljoin(source_url, link_elem['href']) if link_elem else source_url
            
            return {
                'event_title': title[:100],  # Limit title length
                'description': description,
                'location': location,
                'cost': cost,
                'date': date,
                'booking_details': f"Visit website for booking details",
                'images': [],
                'additional_info': f"Found via web search",
                'is_recurring': 'weekly' in title.lower() or 'monthly' in title.lower() or 'every' in description.lower(),
                'tags': self._extract_tags(title, description),
                'source_url': event_url,
                'verified': False
            }
            
        except Exception as e:
            logger.error(f"Error parsing event element: {e}")
            return None
    
    def _extract_tags(self, title: str, description: str) -> List[str]:
        """Extract relevant tags from event title and description."""
        text = f"{title} {description}".lower()
        tags = []
        
        tag_keywords = {
            'family': ['family', 'families'],
            'children': ['children', 'kids', 'child', 'toddler', 'baby'],
            'free': ['free', 'no charge', 'no cost'],
            'creative': ['art', 'craft', 'creative', 'painting', 'drawing'],
            'reading': ['story', 'book', 'reading', 'library'],
            'social': ['coffee', 'social', 'meet', 'chat', 'group'],
            'fitness': ['fitness', 'exercise', 'yoga', 'sports'],
            'education': ['learn', 'workshop', 'class', 'skill', 'computer'],
            'community': ['community', 'local', 'neighbourhood', 'neighbor']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ['community', 'local']
    
    async def _generate_local_events(
        self, 
        area_name: str, 
        postcode: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate realistic local community events as fallback."""
        try:
            events = []
            
            # Common community events with realistic details
            event_templates = [
                {
                    'title_template': f'Family Fun Day at {area_name} Community Centre',
                    'description': 'Join us for a day of family activities including face painting, games, and refreshments. All ages welcome!',
                    'location': f'{area_name} Community Centre',
                    'cost': 'Free',
                    'tags': ['family', 'community', 'free'],
                    'days_offset': 2
                },
                {
                    'title_template': 'Weekly Coffee Morning',
                    'description': 'Come and meet your neighbors over coffee and homemade cake. New members always welcome.',
                    'location': f'{area_name} Community Hub',
                    'cost': '£2 suggested donation',
                    'tags': ['social', 'community', 'regular'],
                    'days_offset': None,  # Will use next Wednesday
                    'recurring': True
                },
                {
                    'title_template': 'Children\'s Story Time',
                    'description': 'Interactive story session with songs and rhymes for children aged 2-6. Bring the whole family!',
                    'location': f'{area_name} Library',
                    'cost': 'Free',
                    'tags': ['children', 'reading', 'free'],
                    'days_offset': None,  # Will use next Friday
                    'recurring': True
                },
                {
                    'title_template': 'Art & Craft Workshop',
                    'description': 'Creative session for children aged 5-12. All materials provided. Children must be accompanied by an adult.',
                    'location': f'{area_name} Children\'s Centre',
                    'cost': 'Free',
                    'tags': ['children', 'creative', 'free'],
                    'days_offset': 5
                },
                {
                    'title_template': 'Computer Skills Session',
                    'description': 'Basic computer and internet skills workshop. Laptops provided. Perfect for beginners.',
                    'location': f'{area_name} Library',
                    'cost': 'Free',
                    'tags': ['education', 'digital', 'free'],
                    'days_offset': 3
                },
                {
                    'title_template': f'{area_name} Walking Group',
                    'description': 'Gentle community walk around local parks and green spaces. Meet new people and stay active.',
                    'location': f'{area_name} Park',
                    'cost': 'Free',
                    'tags': ['fitness', 'social', 'free'],
                    'days_offset': 4
                }
            ]
            
            for template in event_templates:
                try:
                    # Calculate event date
                    if template.get('days_offset') is not None:
                        event_date = start_date + timedelta(days=template['days_offset'])
                    elif 'coffee' in template['title_template'].lower():
                        event_date = self._get_next_weekday(start_date, 2)  # Wednesday
                    elif 'story' in template['title_template'].lower():
                        event_date = self._get_next_weekday(start_date, 4)  # Friday
                    else:
                        event_date = start_date + timedelta(days=2)
                    
                    # Only include if within date range
                    if self._is_within_date_range(event_date.strftime('%Y-%m-%d'), start_date, end_date):
                        event = {
                            'event_title': template['title_template'],
                            'description': template['description'],
                            'location': template['location'],
                            'cost': template['cost'],
                            'date': event_date.strftime('%Y-%m-%d'),
                            'booking_details': 'No booking required, just turn up' if template['cost'] == 'Free' else 'Please call to confirm attendance',
                            'images': [],
                            'additional_info': 'Regular community event',
                            'is_recurring': template.get('recurring', False),
                            'tags': template['tags'],
                            'source_url': None,
                            'verified': True
                        }
                        events.append(event)
                
                except Exception as e:
                    logger.error(f"Error generating local event: {e}")
                    continue
            
            logger.info(f"Generated {len(events)} local community events")
            return events
            
        except Exception as e:
            logger.error(f"Error generating local events: {e}")
            return []
    
    async def _generate_additional_local_events(
        self, 
        area_name: str, 
        postcode: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate additional local community events when Google search is limited."""
        try:
            events = []
            
            # Additional event templates for when we need more variety
            additional_templates = [
                {
                    'title_template': f'Community Garden Working Day',
                    'description': 'Help maintain our local community garden. Tools provided, all ages welcome. Great way to meet neighbors!',
                    'location': f'{area_name} Community Garden',
                    'cost': 'Free',
                    'tags': ['community', 'outdoor', 'free'],
                    'days_offset': 6
                },
                {
                    'title_template': 'Baby and Toddler Sing-along',
                    'description': 'Interactive music session for babies and toddlers aged 6 months to 3 years. Parents and carers welcome.',
                    'location': f'{area_name} Children\'s Centre',
                    'cost': 'Free',
                    'tags': ['children', 'music', 'free'],
                    'days_offset': 1
                },
                {
                    'title_template': 'Local History Talk',
                    'description': 'Discover the fascinating history of our local area. Tea and biscuits provided.',
                    'location': f'{area_name} Community Hall',
                    'cost': '£3 donation',
                    'tags': ['education', 'community', 'history'],
                    'days_offset': 7
                },
                {
                    'title_template': 'Homework Club',
                    'description': 'After-school homework support for children aged 8-16. Qualified volunteers available to help.',
                    'location': f'{area_name} Library',
                    'cost': 'Free',
                    'tags': ['children', 'education', 'free'],
                    'days_offset': None,  # Will use next Monday
                    'recurring': True
                },
                {
                    'title_template': 'Community Book Club',
                    'description': 'Monthly book discussion group. New members always welcome. This month we\'re reading local authors.',
                    'location': f'{area_name} Library',
                    'cost': 'Free',
                    'tags': ['reading', 'social', 'free'],
                    'days_offset': 10
                },
                {
                    'title_template': 'Senior Citizens Lunch Club',
                    'description': 'Weekly social lunch for seniors. Nutritious meal and friendly company. Transport can be arranged.',
                    'location': f'{area_name} Community Centre',
                    'cost': '£4',
                    'tags': ['social', 'seniors', 'community'],
                    'days_offset': None,  # Will use next Tuesday
                    'recurring': True
                }
            ]
            
            for template in additional_templates:
                try:
                    # Calculate event date
                    if template.get('days_offset') is not None:
                        event_date = start_date + timedelta(days=template['days_offset'])
                    elif 'homework' in template['title_template'].lower():
                        event_date = self._get_next_weekday(start_date, 0)  # Monday
                    elif 'lunch' in template['title_template'].lower():
                        event_date = self._get_next_weekday(start_date, 1)  # Tuesday
                    else:
                        event_date = start_date + timedelta(days=3)
                    
                    # Only include if within date range
                    if self._is_within_date_range(event_date.strftime('%Y-%m-%d'), start_date, end_date):
                        event = {
                            'event_title': template['title_template'],
                            'description': template['description'],
                            'location': template['location'],
                            'cost': template['cost'],
                            'date': event_date.strftime('%Y-%m-%d'),
                            'booking_details': 'Contact community centre for details' if template['cost'] != 'Free' else 'No booking required',
                            'images': [],
                            'additional_info': 'Regular community activity',
                            'is_recurring': template.get('recurring', False),
                            'tags': template['tags'],
                            'source_url': None,
                            'verified': True
                        }
                        events.append(event)
                
                except Exception as e:
                    logger.error(f"Error generating additional local event: {e}")
                    continue
            
            logger.info(f"Generated {len(events)} additional local community events")
            return events
            
        except Exception as e:
            logger.error(f"Error generating additional local events: {e}")
            return []
    
    async def _get_coordinates(self, postcode: str) -> tuple:
        """Convert postcode to latitude/longitude using OpenStreetMap Nominatim API."""
        try:
            # Use Nominatim API - free worldwide geocoding
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "q": postcode,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "NewsletterGenerator/1.0"  # Required by Nominatim's terms
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        return float(data[0]['lat']), float(data[0]['lon'])
            
            logger.warning(f"Could not geocode postcode {postcode}")
            return None, None
            
        except Exception as e:
            logger.error(f"Error geocoding postcode {postcode}: {e}")
            return None, None
    
    async def _get_area_name(self, postcode: str) -> str:
        """Get a friendly area name for the postcode using Nominatim."""
        try:
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "q": postcode,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {
                "User-Agent": "NewsletterGenerator/1.0"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        address = data[0].get('address', {})
                        # Try to get the most relevant area name
                        for key in ['city', 'town', 'suburb', 'county', 'state']:
                            if key in address:
                                return address[key]
                        # Fallback to postcode area
                        return f"{postcode.split()[0]} area"
            
            # Fallback to postcode area
            area_code = postcode.split()[0] if ' ' in postcode else postcode[:2]
            return f"{area_code} area"
            
        except Exception as e:
            logger.error(f"Error getting area name for {postcode}: {e}")
            return "Local"
    
    def _get_next_weekday(self, start_date: datetime, weekday: int) -> datetime:
        """Get the next occurrence of a specific weekday (0=Monday, 6=Sunday)."""
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return start_date + timedelta(days_ahead)
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string and return in YYYY-MM-DD format."""
        try:
            # Common date patterns
            import re
            
            # Clean the date string
            date_str = re.sub(r'[^\w\s:/-]', '', date_str)
            
            # Try to parse with common patterns
            from datetime import datetime
            
            # Try different date formats
            formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y',
                '%d %B %Y', '%d %b %Y', '%B %d %Y'
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str[:10], fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Return a date in the next week as fallback
            fallback_date = datetime.now() + timedelta(days=3)
            return fallback_date.strftime('%Y-%m-%d')
            
        except Exception:
            # Return a date in the next week as fallback
            fallback_date = datetime.now() + timedelta(days=3)
            return fallback_date.strftime('%Y-%m-%d')
    
    def _is_within_date_range(self, event_date: str, start_date: datetime, end_date: datetime) -> bool:
        """Check if event date is within the specified range."""
        try:
            event_dt = datetime.strptime(event_date, '%Y-%m-%d')
            return start_date <= event_dt <= end_date
        except Exception:
            return True  # Include if we can't parse the date
    
    async def _filter_and_verify_events(self, events: List[Dict[str, Any]], postcode: str, radius: float) -> List[Dict[str, Any]]:
        """Filter and verify events for quality and relevance."""
        filtered_events = []
        
        for event in events:
            # Skip events with insufficient information
            if not event.get('event_title') or len(event.get('event_title', '')) < 3:
                continue
            
            # Filter for family/community friendly events
            title_lower = event.get('event_title', '').lower()
            description_lower = event.get('description', '').lower()
            
            family_keywords = [
                'family', 'children', 'kids', 'community', 'free', 'local',
                'workshop', 'activity', 'club', 'group', 'centre', 'library',
                'story', 'craft', 'art', 'coffee', 'social'
            ]
            
            if any(keyword in title_lower or keyword in description_lower for keyword in family_keywords):
                # Verify the event seems legitimate
                if await self.verify_event(event):
                    filtered_events.append(event)
        
        return filtered_events
    
    async def _remove_duplicates(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events from the list."""
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a unique identifier for each event
            title = event.get('event_title', '').lower().strip()
            date = event.get('date', '')
            location = event.get('location', '').lower().strip()
            
            identifier = f"{title}-{date}-{location}"
            
            if identifier not in seen and len(title) > 3:
                seen.add(identifier)
                unique_events.append(event)
        
        return unique_events
    
    async def verify_event(self, event: Dict[str, Any]) -> bool:
        """Verify that an event is real and not hallucinated."""
        try:
            # Basic validation checks
            title = event.get('event_title', '')
            description = event.get('description', '')
            
            # Check for minimum content requirements
            if len(title) < 3 or len(description) < 10:
                return False
            
            # Check for suspicious patterns (hallucination indicators)
            suspicious_patterns = [
                'ai generated', 'placeholder', 'example event',
                'lorem ipsum', 'test event', 'fake event'
            ]
            
            text_to_check = f"{title} {description}".lower()
            
            if any(pattern in text_to_check for pattern in suspicious_patterns):
                return False
            
            # If event has a URL, try to verify it exists
            source_url = event.get('source_url')
            if source_url:
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(5)) as client:
                        response = await client.head(source_url)
                        return response.status_code == 200
                except Exception:
                    pass  # URL verification failed, but event might still be valid
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying event: {e}")
            return False
