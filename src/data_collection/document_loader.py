"""
Document loader for fetching and parsing web content from HDFC mutual fund pages.
"""
import asyncio
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import hashlib

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError, NetworkError, ParsingError


class DocumentLoader:
    """Handles fetching and parsing of web documents."""
    
    def __init__(self):
        """Initialize the document loader."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = settings.user_agent
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=settings.ssl_verify
        )
        timeout = aiohttp.ClientTimeout(total=settings.timeout_seconds)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch a single page and extract its content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary containing page content and metadata
            
        Raises:
            NetworkError: If network request fails
            ParsingError: If content parsing fails
        """
        try:
            logger.info(f"Fetching page: {url}")
            
            # Add delay to be respectful
            await asyncio.sleep(settings.data_collection_delay)
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise NetworkError(f"HTTP {response.status}: {url}")
                
                content = await response.text()
                
                # Parse HTML content
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract page title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title"
                
                # Extract main content
                main_content = self._extract_main_content(soup)
                
                # Generate content hash for deduplication
                content_hash = hashlib.md5(main_content.encode()).hexdigest()
                
                # Extract metadata
                metadata = self._extract_metadata(soup, url)
                
                result = {
                    'url': url,
                    'title': title_text,
                    'content': main_content,
                    'content_hash': content_hash,
                    'metadata': metadata,
                    'fetched_at': time.time(),
                    'status_code': response.status
                }
                
                logger.info(f"Successfully fetched page: {url}")
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching {url}: {e}")
            raise NetworkError(f"Failed to fetch {url}: {e}")
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            raise ParsingError(f"Failed to parse {url}: {e}")
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted text content
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main',
            '.main-content',
            '.content',
            '.fund-details',
            '.scheme-details',
            '#main-content',
            '.page-content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return ""
        
        # Extract text and clean it
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = ' '.join(lines)
        
        return cleaned_text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract metadata from the page.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'fund_name': None,
            'fund_type': None,
            'nav': None,
            'expense_ratio': None,
            'exit_load': None,
            'min_sip': None,
            'risk_level': None,
            'benchmark': None
        }
        
        # Try to extract fund-specific information
        # This is a basic implementation - can be enhanced based on actual page structure
        
        # Extract fund name from title or URL
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            if "HDFC" in title_text:
                metadata['fund_name'] = title_text
        
        # Extract from URL
        url_parts = url.split('/')
        if len(url_parts) > 4:
            fund_part = url_parts[-1]
            metadata['fund_name'] = fund_part.replace('-', ' ').title()
        
        # Look for key information in the content
        content_text = soup.get_text().lower()
        
        # Basic pattern matching for financial data
        # This is simplified - would need enhancement for production
        if 'expense ratio' in content_text:
            # Look for percentage values near "expense ratio"
            metadata['expense_ratio'] = self._extract_percentage(content_text, 'expense ratio')
        
        if 'exit load' in content_text:
            metadata['exit_load'] = self._extract_percentage(content_text, 'exit load')
        
        if 'sip' in content_text and 'minimum' in content_text:
            metadata['min_sip'] = self._extract_amount(content_text, 'sip')
        
        return metadata
    
    def _extract_percentage(self, text: str, keyword: str) -> Optional[str]:
        """
        Extract percentage values near a keyword.
        
        Args:
            text: Text to search in
            keyword: Keyword to search for
            
        Returns:
            Percentage string if found, None otherwise
        """
        # This is a simplified implementation
        # Would need more sophisticated pattern matching for production
        import re
        
        # Look for percentage patterns near the keyword
        pattern = rf'{keyword}.*?(\d+\.?\d*%)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    def _extract_amount(self, text: str, keyword: str) -> Optional[str]:
        """
        Extract amount values near a keyword.
        
        Args:
            text: Text to search in
            keyword: Keyword to search for
            
        Returns:
            Amount string if found, None otherwise
        """
        # This is a simplified implementation
        import re
        
        # Look for amount patterns near the keyword
        pattern = rf'{keyword}.*?(₹\s*\d+,?\d*|\d+,?\d*\s*rs)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None


async def fetch_multiple_pages(urls: list[str]) -> list[Dict[str, Any]]:
    """
    Fetch multiple pages concurrently.
    
    Args:
        urls: List of URLs to fetch
        
    Returns:
        List of page content dictionaries
        
    Raises:
        DataCollectionError: If fetching fails for multiple URLs
    """
    logger.info(f"Starting to fetch {len(urls)} pages")
    
    results = []
    errors = []
    
    async with DocumentLoader() as loader:
        tasks = []
        for url in urls:
            task = asyncio.create_task(loader.fetch_page(url))
            tasks.append(task)
        
        # Wait for all tasks to complete
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {urls[i]}: {result}")
                errors.append({"url": urls[i], "error": str(result)})
            else:
                results.append(result)
    
    if errors:
        logger.warning(f"Failed to fetch {len(errors)} pages out of {len(urls)}")
        for error in errors:
            logger.error(f"Error: {error}")
    
    logger.info(f"Successfully fetched {len(results)} pages")
    return results
