import os
import json
import urllib.parse
import urllib.request
import logging

logger = logging.getLogger(__name__)

class SearXNGRetriever:
    """Enterprise Web Search Integration for Market & Pricing Research (Phase 3)."""
    
    def __init__(self, base_url: str | None = None):
        # Default to the Docker service name if not provided
        self.base_url = (base_url or os.getenv("SEARXNG_BASE_URL", "http://searxng:8080")).rstrip("/")
        
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Runs a search query on the local SearXNG instance and returns top results."""
        url = f"{self.base_url}/search?q={urllib.parse.quote(query)}&format=json"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Clarere-Research-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
                
                results = []
                for res in data.get("results", [])[:limit]:
                    results.append({
                        "title": res.get("title", ""),
                        "url": res.get("url", ""),
                        "content": res.get("content", "")
                    })
                return results
                
        except Exception as e:
            logger.error(f"SearXNG request failed for query '{query}': {e}")
            return []


class Crawl4AIExtractor:
    """Crawl4AI Integration for Deep Web Scraping (Phase 3)."""
    
    def __init__(self):
        try:
            from crawl4ai import AsyncWebCrawler
            self._crawler_class = AsyncWebCrawler
        except ImportError:
            self._crawler_class = None
            logger.warning("Crawl4AI package not found. Web scraping will be mocked.")

    async def extract_content(self, url: str) -> str:
        """Extracts text content from a given URL using Crawl4AI."""
        if not self._crawler_class:
            # Production'da mock içerik ASLA kanıt olarak kullanılmaz.
            if os.getenv("APP_ENV", "development") == "production":
                logger.warning(
                    "Crawl4AI kurulu değil; production'da derin web çıkarımı atlanıyor (url=%s).",
                    url,
                )
                return ""
            logger.debug(
                "Crawl4AI yok; test/geliştirme bağlamında açıkça etiketli mock içerik döndürülüyor (url=%s).",
                url,
            )
            return f"[TEST FIXTURE — Mock Content for {url}] (Crawl4AI not installed)"
            
        try:
            async with self._crawler_class() as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    extraction_strategy="Basic",
                    chunking_strategy="RegexChunking"
                )
                return result.extracted_content or result.markdown or ""
        except Exception as e:
            logger.error(f"Crawl4AI extraction failed for url '{url}': {e}")
            return ""


# Singleton Instances
search_retriever = SearXNGRetriever()
web_extractor = Crawl4AIExtractor()
