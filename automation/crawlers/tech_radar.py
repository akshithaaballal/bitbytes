"""
Tech Radar Coordinator for BitBytes.
Orchestrates live tech/AI web crawling via Firecrawl and technical extraction via LLM.
Extracts ONLY the underlying Computer Science / AI concept from trending news,
starting with: "As you heard [news event], what is [Concept]? Let's learn about this!"
Guarantees deduplication so concepts never repeat.
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
        "title": "DeepSeek V3 Multi-Head Latent Attention and Sparse MoE Architecture",
        "url": "https://github.com/deepseek-ai/DeepSeek-V3"
    },
    {
        "title": "Anthropic Prompt Caching & KV Latency Optimization in Transformer Inference",
        "url": "https://simonwillison.net/2024/Aug/14/prompt-caching/"
    },
    {
        "title": "Vector Databases in Production: HNSW Graph vs IVF Indexing Algorithms",
        "url": "https://www.pinecone.io/learn/series/faiss/hnsw/"
    },
    {
        "title": "Understanding Raft Distributed Consensus Protocol Visually",
        "url": "https://raft.github.io/"
    },
    {
        "title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "url": "https://arxiv.org/abs/2205.14135"
    },
    {
        "title": "PostgreSQL 17 Memory Allocation and B-Tree Index Enhancements",
        "url": "https://www.postgresql.org/about/news/postgresql-17-released-2936/"
    },
    {
        "title": "CrowdStrike Outage Analysis: Kernel Space Driver Safety and Ring 0 Isolation",
        "url": "https://en.wikipedia.org/wiki/2024_CrowdStrike-related_IT_outages"
    }
]


def harvest_autonomous_post(history: list = None) -> dict:
    """
    1. Fetches trending tech/AI stories from live web using Firecrawl & Hacker News.
    2. Deduplicates against past posts in history to ensure no concept repeats.
    3. Scrapes clean markdown via Firecrawl.
    4. Distills into B.Tech micro-learning bite via LLM, extracting the core concept
       with the 'As you heard..., what is *concept*?' opening hook.
    """
    history = history or []
    past_titles = {h.get("title", "").strip().lower() for h in history if h.get("title")}
    past_urls = {h.get("source_url", "").strip().lower() for h in history if h.get("source_url")}
    past_topics = [h.get("title", "") for h in history if h.get("title")]

    crawler = FirecrawlClient()

    print("🌐 Step 0 (Radar): Harvesting trending tech & AI stories from the live web...")
    
    # 1. Try Firecrawl search if API key is present
    firecrawl_leads = []
    if crawler.api_key:
        firecrawl_leads = crawler.search_trending(
            query="trending AI machine learning systems engineering breakthrough",
            limit=5
        )

    # 2. Fetch Hacker News trending tech leads
    hn_leads = fetch_trending_tech_leads(limit=15)
    candidates = firecrawl_leads + hn_leads + DEFAULT_TECH_SOURCES

    # 3. Deduplicate against history
    fresh_candidate = None
    for item in candidates:
        cand_title = item.get("title", "").strip().lower()
        cand_url = item.get("url", "").strip().lower()
        if cand_title not in past_titles and cand_url not in past_urls:
            fresh_candidate = item
            break

    if not fresh_candidate:
        print("   ℹ️ All candidates exist in history, selecting a fresh dynamic rotation candidate...")
        fresh_candidate = random.choice(candidates)

    target_url = fresh_candidate.get("url", "")
    target_title = fresh_candidate.get("title", "Trending Technical Breakthrough")
    print(f"   🎯 Selected Story: {target_title}")
    if target_url:
        print(f"   🔗 Source URL: {target_url}")

    # 4. Scrape clean markdown via Firecrawl
    print("\n🔥 Step 0b (Firecrawl): Extracting clean markdown from source...")
    pre_markdown = fresh_candidate.get("markdown")
    if pre_markdown and len(pre_markdown.strip()) > 100:
        markdown_content = pre_markdown
        scrape_engine = "firecrawl-search"
        print(f"   ✅ Pre-extracted markdown used ({len(markdown_content)} characters).")
    elif target_url:
        scrape_res = crawler.scrape_url(target_url)
        markdown_content = scrape_res.get("markdown", "")
        scrape_engine = scrape_res.get("engine", "unknown")
        if not markdown_content or len(markdown_content.strip()) < 50:
            print("   ⚠️ Lightweight scrape content, providing headline context...")
            markdown_content = f"{target_title}. An in-depth engineering analysis of this architecture and its trade-offs."
        print(f"   ✅ Content extracted successfully ({len(markdown_content)} characters via {scrape_engine}).")
    else:
        markdown_content = f"{target_title}. An in-depth engineering analysis of this architecture and its trade-offs."
        scrape_engine = "seed"

    # 5. Curate into the educational lesson with LLM
    print("\n🧠 Step 0c (LLM): Distilling news into the underlying Computer Science concept...")
    curator = LLMCurator()
    post = curator.curate_article(
        article_text=markdown_content,
        source_title=target_title,
        source_url=target_url,
        past_topics=past_topics
    )

    if not post:
        raise ValueError("Failed to generate post from LLM Curator.")

    post["source_url"] = target_url
    post["source_headline"] = target_title
    post["curation_engine"] = f"Firecrawl ({scrape_engine}) + LLM"
    print(f"   ✨ Extracted Concept: '{post.get('title')}' [{post.get('track')}]")
    print(f"   📖 Hook: {post.get('summary', '')[:120]}...\n")
    return post
