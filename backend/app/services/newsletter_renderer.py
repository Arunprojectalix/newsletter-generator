from jinja2 import Environment, FileSystemLoader
import mjml
from typing import Dict, Any
import logging
from pathlib import Path
import html

logger = logging.getLogger(__name__)

class NewsletterRenderer:
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Add custom filters for XML escaping
        self.env.filters['xml_escape'] = self._xml_escape
    
    def _xml_escape(self, text):
        """Escape special XML characters in text."""
        if not text:
            return text
        
        # Convert to string if not already
        text = str(text)
        
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
        
        return text
    
    def _clean_newsletter_data(self, newsletter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean newsletter data to ensure XML compatibility."""
        import copy
        
        # Deep copy to avoid modifying original data
        cleaned_data = copy.deepcopy(newsletter_data)
        
        # Recursively clean all text content
        def clean_text_content(obj):
            if isinstance(obj, str):
                return self._xml_escape(obj)
            elif isinstance(obj, dict):
                return {key: clean_text_content(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [clean_text_content(item) for item in obj]
            else:
                return obj
        
        # Clean specific fields that commonly contain text
        if 'content' in cleaned_data:
            cleaned_data['content'] = clean_text_content(cleaned_data['content'])
        
        return cleaned_data
        
    def render_newsletter(self, newsletter_data: Dict[str, Any], branding: Dict[str, Any]) -> str:
        """Render newsletter data to HTML using MJML."""
        try:
            # Load MJML template
            template = self.env.get_template("newsletter.mjml")
            
            # Prepare template data with cleaned content
            cleaned_newsletter_data = self._clean_newsletter_data(newsletter_data)
            
            template_data = {
                "newsletter": cleaned_newsletter_data,
                "branding": branding,
                "current_date": newsletter_data["newsletter_metadata"]["generation_date"]
            }
            
            # Render MJML
            mjml_content = template.render(**template_data)
            
            # Log MJML content for debugging (first 500 chars)
            logger.debug(f"Generated MJML content preview: {mjml_content[:500]}...")
            
            # Convert MJML to HTML
            result = mjml.mjml_to_html(mjml_content)
            
            if result.errors:
                logger.warning(f"MJML rendering warnings: {result.errors}")
            
            return result.html
            
        except Exception as e:
            logger.error(f"Error rendering newsletter: {e}")
            # Try to identify the problematic line if it's an XML error
            if "line" in str(e) and "column" in str(e):
                try:
                    # Try to extract line number and show context
                    import re
                    match = re.search(r'line (\d+)', str(e))
                    if match:
                        line_num = int(match.group(1))
                        mjml_lines = mjml_content.split('\n')
                        if line_num <= len(mjml_lines):
                            problematic_line = mjml_lines[line_num - 1]
                            logger.error(f"Problematic MJML line {line_num}: {problematic_line}")
                except:
                    pass
            raise
