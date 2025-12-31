from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import hashlib
import time
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WebsiteFetcherService:
    """Service for fetching and parsing website pages"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChatbotCrawler/1.0 (Domain-Restricted Bot)'
        })
        self.session.timeout = settings.CRAWL_TIMEOUT_SECONDS
    
    def fetch_page(self, url: str, request_id: str = None) -> Optional[Tuple[str, str, str]]:
        """Fetch a single page and return (title, content_text, content_hash)"""
        try:
            logger.debug(
                "Fetching page",
                extra={
                    "request_id": request_id,
                    "url": url,
                    "timeout_seconds": settings.CRAWL_TIMEOUT_SECONDS,
                }
            )
            
            response = self.session.get(url, timeout=settings.CRAWL_TIMEOUT_SECONDS)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(
                    "Skipping non-HTML content",
                    extra={
                        "request_id": request_id,
                        "url": url,
                        "content_type": content_type,
                    }
                )
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements: scripts, styles, navigation, headers, footers, ads, etc.
            unwanted_tags = [
                'script', 'style', 'nav', 'footer', 'header', 
                'aside', 'iframe', 'noscript', 'meta', 'link',
                'form', 'button', 'input', 'select', 'textarea'
            ]
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove elements with common ad/analytics classes
            for element in soup.find_all(class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['ad', 'advertisement', 'ads', 'analytics', 'tracking', 'cookie']
            )):
                element.decompose()
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"
            
            # Extract main content - prioritize semantic HTML5 elements
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_=lambda x: x and 'content' in x.lower()) or
                soup.find('div', id=lambda x: x and 'content' in x.lower()) or
                soup.find('body')
            )
            
            if main_content:
                # Get text from main content only
                content_text = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback: get all text but still clean
                content_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace and normalize
            content_text = ' '.join(content_text.split())
            
            # Remove very short content (likely garbage)
            if len(content_text) < 50:
                logger.warning(
                    "Content too short, skipping",
                    extra={
                        "request_id": request_id,
                        "url": url,
                        "content_length": len(content_text),
                    }
                )
                return None
            
            # Generate content hash
            content_hash = hashlib.md5(content_text.encode()).hexdigest()
            
            logger.debug(
                "Page fetched successfully",
                extra={
                    "request_id": request_id,
                    "url": url,
                    "title": title[:100],
                    "content_length": len(content_text),
                    "content_hash": content_hash,
                }
            )
            
            return title, content_text, content_hash
            
        except requests.Timeout as e:
            logger.error(
                "Timeout fetching page",
                extra={
                    "request_id": request_id,
                    "error_type": "Timeout",
                    "url": url,
                    "timeout_seconds": settings.CRAWL_TIMEOUT_SECONDS,
                    "error_message": str(e),
                }
            )
            return None
        except requests.RequestException as e:
            logger.error(
                "Error fetching page",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "url": url,
                    "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                    "error_message": str(e),
                }
            )
            return None
        except Exception as e:
            logger.error(
                "Error parsing page",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "url": url,
                    "error_message": str(e),
                },
                exc_info=True
            )
            return None
    
    def get_sitemap_urls(self, base_url: str) -> List[str]:
        """Try to get URLs from sitemap.xml - only from same domain"""
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc
        
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml')
        ]
        
        all_urls = []
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=settings.CRAWL_TIMEOUT_SECONDS)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'xml')
                    urls = []
                    
                    # Handle sitemap index
                    sitemapindex = soup.find('sitemapindex')
                    if sitemapindex:
                        for sitemap in sitemapindex.find_all('sitemap'):
                            loc = sitemap.find('loc')
                            if loc:
                                nested_sitemap_url = loc.text
                                # Only fetch nested sitemaps from same domain
                                nested_parsed = urlparse(nested_sitemap_url)
                                if nested_parsed.netloc == base_domain:
                                    nested_urls = self._parse_sitemap(nested_sitemap_url)
                                    # Filter nested URLs to same domain
                                    nested_urls = [
                                        url for url in nested_urls 
                                        if urlparse(url).netloc == base_domain
                                    ]
                                    urls.extend(nested_urls)
                    else:
                        urls = self._parse_sitemap(response.text)
                        # Filter URLs to same domain only
                        urls = [
                            url for url in urls 
                            if urlparse(url).netloc == base_domain
                        ]
                    
                    all_urls.extend(urls)
                    
                    # Stop if we have enough URLs
                    if len(all_urls) >= settings.MAX_CRAWL_PAGES:
                        break
                        
            except Exception as e:
                logger.debug(f"Could not fetch sitemap from {sitemap_url}: {e}")
                continue
        
        # Remove duplicates and limit
        unique_urls = list(dict.fromkeys(all_urls))  # Preserves order
        return unique_urls[:settings.MAX_CRAWL_PAGES]
    
    def _parse_sitemap(self, sitemap_url_or_content: str) -> List[str]:
        """Parse sitemap XML content - can accept URL or content string"""
        # If it looks like a URL, fetch it first
        if sitemap_url_or_content.startswith('http'):
            try:
                response = self.session.get(sitemap_url_or_content, timeout=settings.CRAWL_TIMEOUT_SECONDS)
                if response.status_code != 200:
                    return []
                sitemap_content = response.text
            except Exception as e:
                logger.debug(f"Error fetching sitemap {sitemap_url_or_content}: {e}")
                return []
        else:
            sitemap_content = sitemap_url_or_content
        
        soup = BeautifulSoup(sitemap_content, 'xml')
        urls = []
        
        for url_tag in soup.find_all('url'):
            loc = url_tag.find('loc')
            if loc:
                urls.append(loc.text.strip())
        
        return urls
    
    def crawl_from_base(self, base_url: str, max_pages: int = None) -> List[str]:
        """Crawl website starting from base URL"""
        if max_pages is None:
            max_pages = settings.MAX_CRAWL_PAGES
        
        # Try sitemap first
        sitemap_urls = self.get_sitemap_urls(base_url)
        if sitemap_urls:
            return sitemap_urls[:max_pages]
        
        # Otherwise, crawl by following links
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        visited = set()
        to_visit = [base_url]
        urls = []
        
        while to_visit and len(urls) < max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            try:
                response = self.session.get(current_url, timeout=settings.CRAWL_TIMEOUT_SECONDS)
                if response.status_code == 200:
                    urls.append(current_url)
                    
                    # Extract links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(current_url, href)
                        parsed = urlparse(absolute_url)
                        
                        # Only same domain
                        if parsed.netloc == parsed_base.netloc:
                            if absolute_url not in visited and absolute_url not in to_visit:
                                to_visit.append(absolute_url)
                
                # Rate limiting
                time.sleep(settings.CRAWL_RATE_LIMIT_DELAY)
                
            except requests.Timeout as e:
                logger.error(
                    "Timeout crawling URL",
                    extra={
                        "url": current_url,
                        "error_type": "Timeout",
                        "timeout_seconds": settings.CRAWL_TIMEOUT_SECONDS,
                        "error_message": str(e),
                    }
                )
                continue
            except requests.RequestException as e:
                logger.error(
                    "Error crawling URL",
                    extra={
                        "url": current_url,
                        "error_type": type(e).__name__,
                        "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                        "error_message": str(e),
                    }
                )
                continue
            except Exception as e:
                logger.error(
                    "Unexpected error crawling URL",
                    extra={
                        "url": current_url,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                    exc_info=True
                )
                continue
        
        return urls

