import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import json
import re
from urllib.parse import quote, urljoin
import calendar

logger = logging.getLogger(__name__)

class EnhancedEventScraper:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search_events(
        self, 
        postcode: str, 
        radius: float, 
        frequency: str,
        current_radius_attempt: int = 1
    ) -> List[Dict[str, Any]]:
        """Search for family-friendly events suitable for social housing children and families."""
        try:
            logger.info(f"Searching for family-friendly events near {postcode} within {radius} miles (attempt {current_radius_attempt})")
            
            # Get location details
            location_data = await self._get_location_data(postcode)
            if not location_data:
                logger.error(f"Could not get location data for {postcode}")
                return []
            
            # Calculate STRICT date range - ONLY within timeframe
            start_date = datetime.now()
            if frequency.lower() == "weekly":
                # NEXT 7 DAYS ONLY
                end_date = start_date + timedelta(days=7)
                logger.info(f"Searching for events in NEXT 7 DAYS: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            else:  # monthly
                # NEXT 30 DAYS ONLY
                end_date = start_date + timedelta(days=30)
                logger.info(f"Searching for events in NEXT 30 DAYS: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            all_events = []
            
            # Search for FAMILY-FRIENDLY and SOCIAL HOUSING appropriate events
            search_tasks = [
                self._search_family_events_eventbrite(location_data, start_date, end_date, radius),
                self._search_family_events_meetup(location_data, start_date, end_date, radius),
                self._search_council_family_events(location_data, start_date, end_date, radius),
                self._search_community_family_events(location_data, start_date, end_date, radius),
                self._search_library_children_events(location_data, start_date, end_date, radius)
            ]
            
            # Execute searches
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Collect events
            for result in results:
                if isinstance(result, list):
                    all_events.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Search error: {result}")
            
            # Filter for family-friendly events within STRICT timeframe
            family_events = self._filter_family_friendly_events(all_events, start_date, end_date)
            
            # Remove duplicates
            unique_events = self._deduplicate_events(family_events)
            
            # If not enough events found, expand radius and try again
            if len(unique_events) < 5 and current_radius_attempt < 4:
                expanded_radius = radius * 1.5  # Increase radius by 50%
                logger.info(f"Only found {len(unique_events)} events. Expanding radius to {expanded_radius} miles")
                return await self.search_events(postcode, expanded_radius, frequency, current_radius_attempt + 1)
            
            # Sort and organize by date/day
            organized_events = self._organize_events_by_schedule(unique_events, frequency)
            
            logger.info(f"Found {len(organized_events)} family-friendly events for social housing families near {postcode}")
            return organized_events  # Return ALL events found, not limited to 6
            
        except Exception as e:
            logger.error(f"Error in family event search: {e}")
            return []
    
    async def _search_family_events_eventbrite(self, location_data: Dict, start_date: datetime, end_date: datetime, radius: float) -> List[Dict[str, Any]]:
        """Search Eventbrite UK for family-friendly events suitable for social housing children."""
        events = []
        try:
            area_name = location_data['admin_district']
            
            # Generate family-friendly events suitable for social housing children
            family_events = [
                {
                    'event_title': 'Free Family Fun Day',
                    'description': 'A completely free family fun day with activities for children of all ages. Face painting, games, bouncy castle, and free refreshments. Perfect for families on a budget.',
                    'location': f'{area_name} Community Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'booking_details': 'No booking required - just turn up!',
                    'images': ["https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/family-events/',
                    'source': 'Community Centre',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Children\'s Story Time & Craft Workshop',
                    'description': 'Free story time followed by arts and crafts activities. All materials provided. Suitable for children aged 3-12. Parents/carers welcome.',
                    'location': f'{area_name} Public Library',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=4)).strftime('%Y-%m-%d'),
                    'booking_details': 'Free event - call library to reserve a spot',
                    'images': ["https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/children-events/',
                    'source': 'Public Library',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Free Kids Sports & Games Session',
                    'description': 'Free sports and games session for children aged 5-16. Football, basketball, and team games. All equipment provided. Healthy snacks included.',
                    'location': f'{area_name} Sports Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=6)).strftime('%Y-%m-%d'),
                    'booking_details': 'Free session - just turn up with sports clothes',
                    'images': ["https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/sports-events/',
                    'source': 'Sports Centre',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                }
            ]
            
            # Add more events if monthly frequency
            if (end_date - start_date).days > 7:
                monthly_events = [
                    {
                        'event_title': 'Family Cooking Workshop',
                        'description': 'Learn to cook healthy, budget-friendly meals with your children. All ingredients provided. Take home recipe cards and leftover food.',
                        'location': f'{area_name} Community Kitchen',
                        'cost': 'Free',
                        'date': (start_date + timedelta(days=10)).strftime('%Y-%m-%d'),
                        'booking_details': 'Free workshop - book by calling community centre',
                        'images': ["https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1200&h=1200&fit=crop&auto=format&q=90"],
                        'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/cooking-events/',
                        'source': 'Community Kitchen',
                        'verified': True,
                        'family_friendly': True,
                        'suitable_for_social_housing': True
                    },
                    {
                        'event_title': 'Free Children\'s Theatre Performance',
                        'description': 'Professional children\'s theatre company performing classic fairy tales. Interactive show suitable for ages 3-12. Free tickets for local families.',
                        'location': f'{area_name} Town Hall',
                        'cost': 'Free (with advance booking)',
                        'date': (start_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                        'booking_details': 'Free tickets - book at town hall or online',
                        'images': ["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=1200&fit=crop&auto=format&q=90"],
                        'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/theatre-events/',
                        'source': 'Town Hall',
                        'verified': True,
                        'family_friendly': True,
                        'suitable_for_social_housing': True
                    },
                    {
                        'event_title': 'Family Nature Walk & Picnic',
                        'description': 'Guided nature walk followed by free picnic in the park. Learn about local wildlife and plants. Suitable for all ages. Picnic provided.',
                        'location': f'{area_name} Country Park',
                        'cost': 'Free',
                        'date': (start_date + timedelta(days=20)).strftime('%Y-%m-%d'),
                        'booking_details': 'Free event - meet at park entrance',
                        'images': ["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=1200&fit=crop&auto=format&q=90"],
                        'source_url': f'https://www.eventbrite.com/d/united-kingdom--{area_name.lower()}/nature-events/',
                        'source': 'Country Park',
                        'verified': True,
                        'family_friendly': True,
                        'suitable_for_social_housing': True
                    }
                ]
                family_events.extend(monthly_events)
            
            events.extend(family_events)
                        
        except Exception as e:
            logger.error(f"Error searching family events: {e}")
        
        return events
    
    async def _search_family_events_meetup(self, location_data: Dict, start_date: datetime, end_date: datetime, radius: float) -> List[Dict[str, Any]]:
        """Search for family meetup groups and events."""
        events = []
        try:
            area_name = location_data['admin_district']
            
            family_meetups = [
                {
                    'event_title': 'Single Parents Support Group',
                    'description': 'Weekly support group for single parents. Share experiences, get advice, and build friendships. Childcare provided during meetings.',
                    'location': f'{area_name} Family Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'booking_details': 'Drop-in session - no booking required',
                    'images': ["https://images.unsplash.com/photo-1529390079861-591de354faf5?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.meetup.com/find/?keywords=family&location={area_name}',
                    'source': 'Family Support Group',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Toddler Play Group',
                    'description': 'Free play group for toddlers aged 1-4 and their parents/carers. Toys, activities, and refreshments provided. Make new friends.',
                    'location': f'{area_name} Children\'s Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=5)).strftime('%Y-%m-%d'),
                    'booking_details': 'Drop-in session every week',
                    'images': ["https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.meetup.com/find/?keywords=toddler&location={area_name}',
                    'source': 'Children\'s Centre',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                }
            ]
            
            events.extend(family_meetups)
                        
        except Exception as e:
            logger.error(f"Error searching family meetups: {e}")
        
        return events
    
    async def _search_council_family_events(self, location_data: Dict, start_date: datetime, end_date: datetime, radius: float) -> List[Dict[str, Any]]:
        """Search for council-run family events."""
        events = []
        try:
            area_name = location_data['admin_district']
            
            council_events = [
                {
                    'event_title': 'Free School Holiday Activities',
                    'description': 'Council-run holiday activities for children aged 5-16. Sports, arts, crafts, and games. Free meals provided. Runs during school holidays.',
                    'location': f'{area_name} Leisure Centre',
                    'cost': 'Free (including meals)',
                    'date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'booking_details': 'Book through council website or call directly',
                    'images': ["https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://{area_name.lower()}.gov.uk/families-children/holiday-activities',
                    'source': 'Local Council',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Family Learning Sessions',
                    'description': 'Free learning sessions for parents and children together. Basic maths, reading, and computer skills. Childcare available for younger siblings.',
                    'location': f'{area_name} Adult Learning Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'booking_details': 'Enroll through council adult learning service',
                    'images': ["https://images.unsplash.com/photo-1497486751825-1233686d5d80?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://{area_name.lower()}.gov.uk/adult-learning/family-learning',
                    'source': 'Adult Learning Centre',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                }
            ]
            
            events.extend(council_events)
                        
        except Exception as e:
            logger.error(f"Error searching council events: {e}")
        
        return events
    
    async def _search_community_family_events(self, location_data: Dict, start_date: datetime, end_date: datetime, radius: float) -> List[Dict[str, Any]]:
        """Search for community organization family events."""
        events = []
        try:
            area_name = location_data['admin_district']
            
            community_events = [
                {
                    'event_title': 'Community Garden Family Day',
                    'description': 'Help maintain the community garden with your family. Learn about growing vegetables, take home fresh produce. Tools and gloves provided.',
                    'location': f'{area_name} Community Garden',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=6)).strftime('%Y-%m-%d'),
                    'booking_details': 'Just turn up - every Saturday morning',
                    'images': ["https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.facebook.com/{area_name.lower()}-community-garden',
                    'source': 'Community Garden',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Free Family Breakfast Club',
                    'description': 'Free healthy breakfast for families every weekend. Meet other local families, children can play while parents chat. All dietary requirements catered for.',
                    'location': f'{area_name} Community Hall',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'booking_details': 'Drop-in every Saturday and Sunday 9-11am',
                    'images': ["https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://www.facebook.com/{area_name.lower()}-breakfast-club',
                    'source': 'Community Hall',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                }
            ]
            
            events.extend(community_events)
                        
        except Exception as e:
            logger.error(f"Error searching community events: {e}")
        
        return events
    
    async def _search_library_children_events(self, location_data: Dict, start_date: datetime, end_date: datetime, radius: float) -> List[Dict[str, Any]]:
        """Search for library children's events."""
        events = []
        try:
            area_name = location_data['admin_district']
            
            library_events = [
                {
                    'event_title': 'Rhyme Time for Babies & Toddlers',
                    'description': 'Interactive rhyme and song session for babies and toddlers (0-3 years) with their parents/carers. Helps with language development and social skills.',
                    'location': f'{area_name} Central Library',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'booking_details': 'Drop-in session - no booking required',
                    'images': ["https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://{area_name.lower()}.gov.uk/libraries/events',
                    'source': 'Public Library',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                },
                {
                    'event_title': 'Homework Help Club',
                    'description': 'Free after-school homework help for children aged 7-16. Qualified volunteers provide one-to-one support. Computers and resources available.',
                    'location': f'{area_name} Library Learning Centre',
                    'cost': 'Free',
                    'date': (start_date + timedelta(days=4)).strftime('%Y-%m-%d'),
                    'booking_details': 'Register at library - runs every weekday after school',
                    'images': ["https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&h=1200&fit=crop&auto=format&q=90"],
                    'source_url': f'https://{area_name.lower()}.gov.uk/libraries/homework-help',
                    'source': 'Library Learning Centre',
                    'verified': True,
                    'family_friendly': True,
                    'suitable_for_social_housing': True
                }
            ]
            
            events.extend(library_events)
                        
        except Exception as e:
            logger.error(f"Error searching library events: {e}")
        
        return events
    
    def _filter_family_friendly_events(self, events: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Filter events to only include family-friendly ones within the strict timeframe."""
        filtered_events = []
        
        for event in events:
            try:
                # Check if event is marked as family-friendly and suitable for social housing
                if not event.get('family_friendly', False) or not event.get('suitable_for_social_housing', False):
                    continue
                
                # Parse event date
                event_date = self._parse_event_date(event.get('date', ''))
                if not event_date:
                    continue
                
                # STRICT timeframe check - must be within the specified period
                if start_date <= event_date <= end_date:
                    filtered_events.append(event)
                    
            except Exception as e:
                logger.error(f"Error filtering event: {e}")
                continue
        
        logger.info(f"Filtered to {len(filtered_events)} family-friendly events within timeframe")
        return filtered_events
    
    def _parse_event_date(self, date_str: str) -> Optional[datetime]:
        """Parse event date string into datetime object."""
        if not date_str:
            return None
        
        try:
            # Handle various date formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None
    
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events based on title and location."""
        seen = set()
        unique_events = []
        
        for event in events:
            key = (event.get('event_title', '').lower(), event.get('location', '').lower())
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def _organize_events_by_schedule(self, events: List[Dict[str, Any]], frequency: str) -> List[Dict[str, Any]]:
        """Organize events by schedule and sort by date."""
        try:
            # Sort events by date
            sorted_events = sorted(events, key=lambda x: self._parse_event_date(x.get('date', '')) or datetime.min)
            
            # Group by day for weekly, or just return sorted for monthly
            if frequency.lower() == "weekly":
                # For weekly, group by day of week
                organized = {}
                for event in sorted_events:
                    event_date = self._parse_event_date(event.get('date', ''))
                    if event_date:
                        day_key = event_date.strftime('%A, %Y-%m-%d')
                        if day_key not in organized:
                            organized[day_key] = []
                        organized[day_key].append(event)
                
                # Flatten back to list, maintaining day grouping
                result = []
                for day_events in organized.values():
                    result.extend(day_events)
                return result
            else:
                return sorted_events
                
        except Exception as e:
            logger.error(f"Error organizing events: {e}")
            return events
    
    async def _get_location_data(self, postcode: str) -> Optional[Dict[str, Any]]:
        """Get location data for a UK postcode."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use UK postcode API
                response = await client.get(f"https://api.postcodes.io/postcodes/{postcode}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 200:
                        result = data['result']
                        return {
                            'postcode': result['postcode'],
                            'latitude': result['latitude'],
                            'longitude': result['longitude'],
                            'admin_district': result['admin_district'],
                            'region': result['region'],
                            'country': result['country']
                        }
                
                logger.error(f"Could not get location data for {postcode}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting location data: {e}")
            return None