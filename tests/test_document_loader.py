"""
Tests for document loader functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.data_collection.document_loader import DocumentLoader, fetch_multiple_pages
from src.utils.exceptions import NetworkError, ParsingError


class TestDocumentLoader:
    """Test cases for DocumentLoader class."""
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
        <head>
            <title>HDFC Mid Cap Fund - Direct Growth</title>
        </head>
        <body>
            <main>
                <h1>HDFC Mid Cap Fund</h1>
                <div class="fund-details">
                    <p>Expense Ratio: 0.85%</p>
                    <p>Exit Load: 1% if redeemed within 365 days</p>
                    <p>Minimum SIP: ₹500</p>
                    <p>NAV: ₹145.67</p>
                    <p>Risk Level: Moderately High</p>
                </div>
            </main>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_url(self):
        """Sample URL for testing."""
        return "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, sample_html, sample_url):
        """Test successful page fetching."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: sample_html)()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            async with DocumentLoader() as loader:
                result = await loader.fetch_page(sample_url)
                
                assert result['url'] == sample_url
                assert result['status_code'] == 200
                assert 'HDFC Mid Cap Fund' in result['title']
                assert result['content'] is not None
                assert len(result['content']) > 0
                assert result['content_hash'] is not None
                assert result['metadata'] is not None
    
    @pytest.mark.asyncio
    async def test_fetch_page_network_error(self, sample_url):
        """Test handling of network errors."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.side_effect = Exception("Network error")
            
            async with DocumentLoader() as loader:
                with pytest.raises(NetworkError):
                    await loader.fetch_page(sample_url)
    
    @pytest.mark.asyncio
    async def test_fetch_page_http_error(self, sample_url):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.status = 404
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            async with DocumentLoader() as loader:
                with pytest.raises(NetworkError):
                    await loader.fetch_page(sample_url)
    
    def test_extract_main_content(self, sample_html):
        """Test main content extraction."""
        loader = DocumentLoader()
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(sample_html, 'html.parser')
        content = loader._extract_main_content(soup)
        
        assert 'HDFC Mid Cap Fund' in content
        assert 'Expense Ratio: 0.85%' in content
        assert len(content) > 0
    
    def test_extract_metadata(self, sample_html, sample_url):
        """Test metadata extraction."""
        loader = DocumentLoader()
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(sample_html, 'html.parser')
        metadata = loader._extract_metadata(soup, sample_url)
        
        assert metadata['url'] == sample_url
        assert 'groww.in' in metadata['domain']
        assert metadata['fund_name'] is not None
    
    def test_extract_percentage(self):
        """Test percentage extraction."""
        loader = DocumentLoader()
        
        text = "The expense ratio is 0.85% and exit load is 1%"
        
        expense_ratio = loader._extract_percentage(text, 'expense ratio')
        exit_load = loader._extract_percentage(text, 'exit load')
        
        assert expense_ratio == "0.85%"
        assert exit_load == "1%"
    
    def test_extract_amount(self):
        """Test amount extraction."""
        loader = DocumentLoader()
        
        text = "Minimum SIP is ₹500 and investment amount is ₹1000"
        
        sip_amount = loader._extract_amount(text, 'sip')
        
        assert sip_amount == "₹500"
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_pages(self, sample_html):
        """Test fetching multiple pages."""
        urls = [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
        ]
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: sample_html)()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            results = await fetch_multiple_pages(urls)
            
            assert len(results) == 2
            assert all(result['status_code'] == 200 for result in results)
            assert all(result['url'] in urls for result in results)


@pytest.mark.asyncio
async def test_fetch_multiple_pages_with_errors():
    """Test fetching multiple pages with some errors."""
    urls = [
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://invalid-url.com/fund"
    ]
    
    sample_html = "<html><body>Test content</body></html>"
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = asyncio.coroutine(lambda: sample_html)()
    
    with patch('aiohttp.ClientSession') as mock_session:
        # First URL succeeds, second fails
        mock_session.return_value.__aenter__.return_value.get.side_effect = [
            mock_response,  # Success
            Exception("Network error")  # Failure
        ]
        
        results = await fetch_multiple_pages(urls)
        
        assert len(results) == 1  # Only successful fetch
        assert results[0]['url'] == urls[0]
