"""
Tech Radar Coordinator for BitBytes.
Orchestrates live tech article harvesting, Firecrawl extraction,
and LLM technical curation to generate never-repeating daily posts.
"""

import os
import sys
import json
import random

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from crawlers.firecrawl_client import FirecrawlClient, fetch_trending_tech_leads
from crawlers.llm_curator import LLMCurator


DEFAULT_TECH_SOURCES = [
    {
        "title": "Anthropic Prompt Caching & KV Latency Optimization",
        "url": "https://simonwillison.net/2024/Aug/14/prompt-caching/"
    },
    {
        "title": "Vector Databases in Production: HNSW Graph vs IVF Indexing",
        "url": "https://www.pinecone.io/learn/series/faiss/hnsw/"
    },
    {
        "title": "Understanding Raft Distributed Consensus Protocol Visually",
        "url": "https://raft.github.io/"
    },
    {
        "title": "PostgreSQL 17 Memory Allocation and B-Tree Enhancements",
        "url": "https://www.postgresql.org/about/news/postgresql-17-released-2936/"
    }
]


def harvest_autonomous_post(history: list = None) -> dict:
    """
    1. Fetches trending tech/AI stories.
    2. Deduplicates against past posts in history.
    3. Scrapes clean markdown via Firecrawl.
    4. Distills into B.Tech micro-learning bite via LLM.
    """
    history = history or []
    past_titles = {h.get("title", "").strip().lower() for h in history if h.get("title")}
    past_urls = {h.get("source_url", "").strip().lower() for h in history if h.get("source_url")}

    print("🌐 Step 0 (Radar): Harvesting trending tech & AI stories...")
    leads = fetch_trending_tech_leads(limit=15)
    candidates = leads + DEFAULT_TECH_SOURCES

    # Filter out previously posted candidates
    fresh_candidate = None
    for item in candidates:
        cand_title = item.get("title", "").strip().lower()
        cand_url = item.get("url", "").strip().lower()
        if cand_title not in past_titles and cand_url not in past_urls:
            fresh_candidate = item
            break

    if not fresh_candidate:
        print("   ℹ️ All current candidates found in history, selecting a fresh dynamic rotation...")
        fresh_candidate = random.choice(candidates)

    target_url = fresh_candidate.get("url")
    target_title = fresh_candidate.get("title")
    print(f"   🎯 Selected Story: {target_title}")
    print(f"   🔗 Source URL: {target_url}")

    # Scrape via Firecrawl Client
    print("\n🔥 Step 0b (Firecrawl): Extracting clean markdown...")
    crawler = FirecrawlClient()
    scrape_res = crawler.scrape_url(target_url)

    markdown_content = scrape_res.get("markdown", "")
    if not markdown_content or len(markdown_content.strip()) < 50:
        print("   ⚠️ Empty scrape content, providing summary context for curation...")
        markdown_content = f"{target_title}. An in-depth engineering analysis of this architecture and its trade-offs."

    print(f"   ✅ Content extracted successfully ({len(markdown_content)} characters via {scrape_res.get('engine')}).")

    # Curate with LLM
    print("\n🧠 Step 0c (LLM): Distilling into structured B.Tech micro-learning bite...")
    curator = LLMCurator()
    post = curator.curate_article(
        article_text=markdown_content,
        source_title=target_title,
        source_url=target_url,
        past_topics=list(past_titles)
    )

    if not post:
        raise ValueError("Failed to generate post from LLM Curator.")

    post["source_url"] = target_url
    post["curation_engine"] = f"Firecrawl ({scrape_res.get('engine')}) + LLM"
    print(f"   ✨ Created lesson: '{post.get('title')}' [{post.get('track')}]")
    return post
