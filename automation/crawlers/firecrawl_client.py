"""
Firecrawl Client & Tech Source Harvester for BitBytes.
Handles live web crawling and scraping via the Firecrawl API (SDK + REST)
with direct HTTP BeautifulSoup fallback for zero-dependency operation.
"""

import os
import sys
import re
import json
import logging
import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("firecrawl_client")

FIRECRAWL_API_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"
MIN_ARTICLE_CHAR_LENGTH = 800
MAX_ARTICLE_CHARS_TO_MODEL = 12000


class FirecrawlClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "").strip()
        self._app = None
        if self.api_key:
            try:
                from firecrawl import FirecrawlApp
                self._app = FirecrawlApp(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize FirecrawlApp SDK: {e}")
                self._app = None

    def search_trending(self, query: str = "trending artificial intelligence machine learning systems breakthrough", limit: int = 5) -> list:
        """
        Uses Firecrawl search to discover latest tech/AI articles on the live web.
        """
        if not self.api_key or not self._app:
            return []

        try:
            search_res = self._app.search(query=query, limit=limit)
            results = []
            items = getattr(search_res, "data", None) or getattr(search_res, "results", None) or search_res
            if isinstance(items, list):
                for item in items:
                    title = getattr(item, "title", None) or (item.get("title") if isinstance(item, dict) else "")
                    url = getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else "")
                    markdown = getattr(item, "markdown", None) or (item.get("markdown") if isinstance(item, dict) else "")
                    if url and title:
                        results.append({
                            "title": title,
                            "url": url,
                            "markdown": markdown or ""
                        })
            return results
        except Exception as exc:
            logger.warning(f"Firecrawl search error: {exc}")
            return []

    def scrape_url(self, target_url: str) -> dict:
        """
        Scrapes a target web URL using Firecrawl API (SDK / REST).
        Falls back to direct HTTP extraction.
        Rejects candidates with cleaned text < 800 characters without placeholders.
        """
        if self.api_key:
            # 1. Try SDK first
            if self._app:
                try:
                    if hasattr(self._app, "scrape"):
                        scrape_data = self._app.scrape(url=target_url, formats=["markdown"], only_main_content=True)
                        markdown = getattr(scrape_data, "markdown", "") or ""
                        metadata = getattr(scrape_data, "metadata", {}) or {}
                    elif hasattr(self._app, "scrape_url"):
                        scrape_data = self._app.scrape_url(target_url, params={"formats": ["markdown"]})
                        markdown = getattr(scrape_data, "markdown", None)
                        metadata = getattr(scrape_data, "metadata", {})
                        if markdown is None and isinstance(scrape_data, dict):
                            markdown = scrape_data.get("markdown") or scrape_data.get("data", {}).get("markdown", "")
                            metadata = scrape_data.get("metadata") or scrape_data.get("data", {}).get("metadata", {})
                    else:
                        markdown = None
                        metadata = {}

                    if markdown is not None:
                        clean_text = str(markdown).strip()
                        if len(clean_text) < MIN_ARTICLE_CHAR_LENGTH:
                            return {
                                "success": False,
                                "engine": "firecrawl-sdk",
                                "url": target_url,
                                "error": f"Article text under {MIN_ARTICLE_CHAR_LENGTH} characters ({len(clean_text)} chars)",
                                "markdown": ""
                            }
                        title = getattr(metadata, "title", "") if not isinstance(metadata, dict) else metadata.get("title", "")
                        return {
                            "success": True,
                            "engine": "firecrawl-sdk",
                            "url": target_url,
                            "title": title or "",
                            "markdown": clean_text[:MAX_ARTICLE_CHARS_TO_MODEL],
                            "metadata": metadata if isinstance(metadata, dict) else {}
                        }
                except Exception as sdk_err:
                    logger.warning(f"Firecrawl SDK scrape failed ({sdk_err}), trying REST endpoint...")

            # 2. Try REST endpoint
            rest_result = self._scrape_with_firecrawl_rest(target_url)
            if rest_result.get("success"):
                return rest_result
            logger.warning("Firecrawl REST failed, falling back to direct HTTP...")

        return self._scrape_with_direct_http(target_url)

    def _scrape_with_firecrawl_rest(self, target_url: str) -> dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "url": target_url,
                "formats": ["markdown"],
                "onlyMainContent": True
            }
            res = requests.post(FIRECRAWL_API_ENDPOINT, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                doc = data.get("data", {})
                markdown = doc.get("markdown", "").strip()
                if len(markdown) < MIN_ARTICLE_CHAR_LENGTH:
                    return {
                        "success": False,
                        "engine": "firecrawl-rest",
                        "url": target_url,
                        "error": f"Article text under {MIN_ARTICLE_CHAR_LENGTH} characters ({len(markdown)} chars)",
                        "markdown": ""
                    }
                metadata = doc.get("metadata", {})
                title = metadata.get("title") or metadata.get("ogTitle") or ""
                return {
                    "success": True,
                    "engine": "firecrawl-rest",
                    "url": target_url,
                    "title": title,
                    "markdown": markdown[:MAX_ARTICLE_CHARS_TO_MODEL],
                    "metadata": metadata
                }
            return {
                "success": False,
                "engine": "firecrawl-rest",
                "url": target_url,
                "error": f"HTTP {res.status_code}: {res.text[:200]}"
            }
        except Exception as exc:
            return {
                "success": False,
                "engine": "firecrawl-rest",
                "url": target_url,
                "error": str(exc)
            }

    def _scrape_with_direct_http(self, target_url: str) -> dict:
        """Lightweight direct HTTP reader using BeautifulSoup with boilerplate removal."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            res = requests.get(target_url, headers=headers, timeout=15)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg", "button", "iframe"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            paragraphs = []
            boilerplate_patterns = [
                re.compile(r'\b(cookie|privacy policy|terms of (use|service)|all rights reserved|sign in|subscribe|newsletter)\b', re.I)
            ]
            for el in soup.find_all(["p", "article", "section", "h1", "h2", "h3", "li"]):
                txt = el.get_text().strip()
                if not txt:
                    continue
                if any(p.search(txt) and len(txt) < 120 for p in boilerplate_patterns):
                    continue
                paragraphs.append(txt)

            cleaned_text = "\n\n".join(paragraphs)
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()

            if len(cleaned_text) < MIN_ARTICLE_CHAR_LENGTH:
                return {
                    "success": False,
                    "engine": "direct_http",
                    "url": target_url,
                    "error": f"Article text under {MIN_ARTICLE_CHAR_LENGTH} characters ({len(cleaned_text)} chars)",
                    "markdown": ""
                }

            return {
                "success": True,
                "engine": "direct_http",
                "url": target_url,
                "title": title,
                "markdown": cleaned_text[:MAX_ARTICLE_CHARS_TO_MODEL],
                "metadata": {"title": title}
            }
        except Exception as exc:
            return {
                "success": False,
                "engine": "direct_http",
                "url": target_url,
                "error": str(exc),
                "markdown": ""
            }


def fetch_trending_tech_leads(limit: int = 30) -> list:
    """
    Fetches real-time trending stories from Hacker News front page via Algolia in one request.
    Zero API key required. Keeps points for ranking.
    """
    url = f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={limit}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        hits = data.get("hits", [])
        leads = []
        for h in hits:
            u = (h.get("url") or "").strip()
            t = (h.get("title") or "").strip()
            if u and t:
                leads.append({
                    "id": str(h.get("objectID") or h.get("story_id") or ""),
                    "title": t,
                    "url": u,
                    "score": h.get("points") or 0,
                    "by": h.get("author") or ""
                })
        return leads
    except Exception as exc:
        logger.warning(f"Error fetching HN leads via Algolia: {exc}")
        return []
