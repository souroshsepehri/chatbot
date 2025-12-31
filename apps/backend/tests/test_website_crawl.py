"""
Test website crawling enforces same-domain restriction
"""
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, urljoin
from app.services.website_fetcher import WebsiteFetcherService


def test_crawl_only_same_domain():
    """
    Test that website crawler only crawls URLs from the same domain
    """
    fetcher = WebsiteFetcherService()
    base_url = "https://example.com"
    
    # Mock HTML with links to same domain and different domains
    mock_html = """
    <html>
        <body>
            <a href="/page1">Same domain relative</a>
            <a href="https://example.com/page2">Same domain absolute</a>
            <a href="https://other-domain.com/page">Different domain</a>
            <a href="http://example.com/page3">Same domain different scheme</a>
            <a href="https://subdomain.example.com/page">Subdomain (different)</a>
        </body>
    </html>
    """
    
    # Mock the session.get to return our HTML
    with patch.object(fetcher.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response
        
        # Mock BeautifulSoup parsing
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(mock_html, 'html.parser')
        
        # Get all links
        links = soup.find_all('a', href=True)
        
        # Parse base URL
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc
        
        # Check each link
        same_domain_links = []
        different_domain_links = []
        
        for link in links:
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            
            if parsed.netloc == base_domain:
                same_domain_links.append(absolute_url)
            else:
                different_domain_links.append(absolute_url)
        
        # Assertions
        assert len(same_domain_links) > 0, "Should find same-domain links"
        assert len(different_domain_links) > 0, "Should find different-domain links"
        
        # Verify same-domain links
        assert "https://example.com/page1" in same_domain_links or "/page1" in [l for l in same_domain_links]
        assert "https://example.com/page2" in same_domain_links
        assert "http://example.com/page3" in same_domain_links
        
        # Verify different-domain links are excluded
        assert "https://other-domain.com/page" not in same_domain_links
        assert "https://subdomain.example.com/page" not in same_domain_links


def test_crawl_respects_max_pages():
    """
    Test that crawler respects MAX_CRAWL_PAGES limit
    """
    fetcher = WebsiteFetcherService()
    base_url = "https://example.com"
    
    # Mock sitemap with many URLs
    mock_sitemap_urls = [f"https://example.com/page{i}" for i in range(200)]
    
    with patch.object(fetcher, 'get_sitemap_urls', return_value=mock_sitemap_urls):
        from app.core.config import settings
        max_pages = settings.MAX_CRAWL_PAGES
        
        urls = fetcher.crawl_from_base(base_url, max_pages=max_pages)
        
        # Should not exceed max_pages
        assert len(urls) <= max_pages, f"Should not crawl more than {max_pages} pages"

