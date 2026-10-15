"""
Firecrawl Client & Tech Source Harvester for BitBytes.
Handles web scraping via the Firecrawl API (https://api.firecrawl.dev/v1/scrape)
with intelligent fallbacks for zero-dependency live news scraping.
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


class FirecrawlClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "").strip()

    def scrape_url(self, target_url: str) -> dict:
        """
        Scrapes a target web URL using Firecrawl API.
        If no API key is provided, falls back to direct HTTP extraction.
        """
        if self.api_key:
            return self._scrape_with_firecrawl_api(target_url)
        else:
            print("   ℹ️ FIRECRAWL_API_KEY not detected, using direct web scraper fallback...")
            return self._scrape_with_direct_http(target_url)

    def _scrape_with_firecrawl_api(self, target_url: str) -> dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "url": target_url,
                "formats": ["markdown"]
            }
            res = requests.post(FIRECRAWL_API_ENDPOINT, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                doc = data.get("data", {})
                markdown = doc.get("markdown", "")
                metadata = doc.get("metadata", {})
                title = metadata.get("title") or metadata.get("ogTitle") or ""
                return {
                    "success": True,
                    "engine": "firecrawl",
                    "url": target_url,
                    "title": title,
                    "markdown": markdown,
                    "metadata": metadata
                }
            else:
                print(f"   ⚠️ Firecrawl API returned {res.status_code}: {res.text[:200]}")
                print("   Falling back to direct HTTP scraper...")
                return self._scrape_with_direct_http(target_url)
        except Exception as exc:
            print(f"   ⚠️ Firecrawl API error: {exc}. Falling back to direct HTTP...")
            return self._scrape_with_direct_http(target_url)

    def _scrape_with_direct_http(self, target_url: str) -> dict:
        """Lightweight zero-cost direct HTTP reader using BeautifulSoup."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            res = requests.get(target_url, headers=headers, timeout=15)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "li"]) if p.get_text().strip()]
            cleaned_text = "\n\n".join(paragraphs[:30])

            return {
                "success": True,
                "engine": "direct_http",
                "url": target_url,
                "title": title,
                "markdown": cleaned_text[:5000],
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


def fetch_trending_tech_leads(limit: int = 15) -> list:
    """
    Fetches real-time trending tech and AI articles from Hacker News public API.
    Zero API key required for discovery.
    """
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        res = requests.get(top_url, timeout=10)
        story_ids = res.json()[:limit]

        leads = []
        for sid in story_ids:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                item_res = requests.get(item_url, timeout=5)
                item = item_res.json()
                if item and "url" in item and item.get("type") == "story":
                    leads.append({
                        "id": str(item.get("id")),
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "score": item.get("score", 0),
                        "by": item.get("by", "")
                    })
            except Exception:
                continue

        return leads
    except Exception as exc:
        print(f"⚠️ Error fetching trending tech leads: {exc}")
        return []
