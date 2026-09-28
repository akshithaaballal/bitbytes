"""
Tech Radar Coordinator for BitBytes.
Orchestrates tiered live tech/AI web discovery and technical extraction via LLM:
  Tier 1: Firecrawl search + Hacker News (Algolia single request)
  Tier 2: RSS/Atom feeds from trusted publishers in sources.json
  Tier 3: arXiv API (cs.OS, cs.DC, cs.DB, cs.NI, cs.LG)
Strict filtering, deduplication against history, grounding gate validation,
and detailed attempt telemetry.
"""

import os
import sys
import json
import re
import uuid
import logging
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("tech_radar")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE_PATH = os.path.join(BASE_DIR, "sources.json")
CANDIDATE_TRACKER_PATH = os.path.join(BASE_DIR, "candidate_tracker.json")

STOPWORDS = {
    "a", "an", "the", "in", "on", "for", "and", "or", "of", "to", "with", "is",
    "at", "by", "from", "as", "how", "why", "what", "we", "our", "it", "its", "are"
}


def load_sources_config() -> dict:
    if os.path.exists(SOURCES_FILE_PATH):
        try:
            with open(SOURCES_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load sources.json: {e}")
    return {
        "verified_domains": [],
        "allowed_github_orgs": [],
        "rss_feeds": [],
        "tech_keywords": [],
        "negative_keywords": []
    }


def canonicalise_url(url: str) -> str:
    """Strips query parameters, utm tags, fragments, and trailing slashes."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"


def get_registrable_domain(url: str) -> str:
    """Extracts the registrable domain (e.g. blog.cloudflare.com -> cloudflare.com)."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "org", "ac", "gov", "com", "net") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def is_verified_source(url: str, title: str, sources_config: dict = None) -> bool:
    """
    Validates whether a candidate story comes from an authoritative domain
    and is genuinely about computer science, AI, or systems engineering.
    Matches keywords with word-boundary regex and removes blanket github.com.
    """
    if not url or not title:
        return False

    sources = sources_config or load_sources_config()
    negative_keywords = sources.get("negative_keywords", [])
    verified_domains = sources.get("verified_domains", [])
    allowed_github_orgs = sources.get("allowed_github_orgs", [])
    tech_keywords = sources.get("tech_keywords", [])

    # 1. Negative keywords filter (word boundaries)
    for neg in negative_keywords:
        if re.search(r"\b" + re.escape(neg) + r"\b", title, re.IGNORECASE):
            return False

    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().split(":")[0]

        # 2. Domain check: host == d or host.endswith("." + d)
        is_verified_domain = False
        if host == "github.com":
            # Allow only listed GitHub organizations
            path_parts = [p for p in parsed.path.split("/") if p]
            if path_parts:
                org = path_parts[0].lower()
                if org in [o.lower() for o in allowed_github_orgs]:
                    is_verified_domain = True
        else:
            is_verified_domain = any(host == d or host.endswith("." + d) for d in verified_domains)

        if not is_verified_domain:
            return False

        # 3. Technical keywords check (word boundaries)
        has_tech_keyword = any(
            re.search(r"\b" + re.escape(kw) + r"\b", title, re.IGNORECASE)
            for kw in tech_keywords
        )

        return has_tech_keyword and len(title.split()) >= 3
    except Exception:
        return False


def tokenize_title(title: str) -> set:
    """Tokenizes and normalizes title tokens for Jaccard comparison."""
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def token_jaccard(tokens1: set, tokens2: set) -> float:
    """Calculates Jaccard similarity between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


def validate_grounding(post: dict, article_text: str, past_titles: list) -> tuple[bool, str]:
    """
    Grounding gate in code:
    reject if:
    - reject is true
    - any quote in source_claims is not found in whitespace/case-normalised article text
    - relevance.score < 0.7
    - the title duplicates a recent title (last 30 posts)
    """
    if not post or not isinstance(post, dict):
        return False, "Empty or invalid post object"

    if post.get("reject") is True:
        return False, f"LLM rejected article: {post.get('reject_reason', 'Not teachable CS/AI concept')}"

    norm_article = " ".join(article_text.lower().split())

    # Check source_claims quotes verbatim presence
    claims = post.get("source_claims", [])
    if not claims or not isinstance(claims, list):
        return False, "Missing or invalid source_claims in LLM output"

    for item in claims:
        quote = item.get("quote", "").strip()
        if not quote:
            return False, "Empty quote in source_claims"
        norm_quote = " ".join(quote.lower().split())
        if norm_quote not in norm_article:
            return False, f"Quote hallucinated (not found in article text): '{quote[:50]}...'"

    # Check relevance score >= 0.7
    relevance = post.get("relevance", {})
    score = relevance.get("score", 0) if isinstance(relevance, dict) else 0
    try:
        score = float(score)
    except (ValueError, TypeError):
        score = 0.0

    if score < 0.7:
        reason = relevance.get("reason", "Low relevance") if isinstance(relevance, dict) else "Low relevance"
        return False, f"Relevance score {score} < 0.7: {reason}"

    # Check title deduplication against last 30 posts
    title = post.get("title", "").strip().lower()
    if not title:
        return False, "Missing concept title"

    title_tokens = tokenize_title(title)
    for past_t in (past_titles or [])[-30:]:
        past_norm = past_t.strip().lower()
        if title == past_norm:
            return False, f"Title exactly matches recent post: '{past_t}'"
        past_tokens = tokenize_title(past_norm)
        if token_jaccard(title_tokens, past_tokens) >= 0.7:
            return False, f"Title too similar to recent post '{past_t}' (Jaccard >= 0.7)"

    return True, "Passed grounding gate"


# =========================================================================
# Tiered Lead Harvesters
# =========================================================================

def fetch_tier_1_leads(crawler=None) -> list:
    """
    Tier 1: Firecrawl search + Hacker News front page (Algolia API).
    """
    from crawlers.firecrawl_client import FirecrawlClient, fetch_trending_tech_leads

    crawler = crawler or FirecrawlClient()
    leads = []

    # 1. Firecrawl search if configured
    if crawler.api_key:
        try:
            fc_leads = crawler.search_trending(
                query="trending AI systems compiler database operating systems research",
                limit=8
            )
            leads.extend(fc_leads)
        except Exception as e:
            logger.warning(f"Tier 1 Firecrawl search failed: {e}")

    # 2. Hacker News via single Algolia call
    try:
        hn_leads = fetch_trending_tech_leads(limit=30)
        leads.extend(hn_leads)
    except Exception as e:
        logger.warning(f"Tier 1 HN search failed: {e}")

    return leads


def fetch_tier_2_leads(sources_config: dict = None) -> list:
    # // DEBT: Uses stdlib xml.etree and urllib to avoid adding feedparser dependency
    """
    Tier 2: RSS/Atom feeds from trusted publishers listed in automation/sources.json.
    Direct HTTP, no API key required.
    """
    sources_cfg = sources_config or load_sources_config()
    feeds = sources_cfg.get("rss_feeds", [])
    leads = []
    headers = {"User-Agent": "BitBytes/1.0 (Mozilla/5.0 direct http)"}

    for feed in feeds:
        url = feed.get("url")
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                content = resp.read()
            root = ET.fromstring(content)

            # Check RSS <item>
            items = []
            for it in root.findall(".//item"):
                t = it.find("title")
                l = it.find("link")
                if t is not None and l is not None and t.text and l.text:
                    items.append({"title": t.text.strip(), "url": l.text.strip()})

            # Check Atom <entry>
            if not items:
                for it in root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(".//atom:entry", {"atom": "http://www.w3.org/2005/Atom"}):
                    t = it.find("{http://www.w3.org/2005/Atom}title") or it.find("atom:title", {"atom": "http://www.w3.org/2005/Atom"})
                    l = it.find("{http://www.w3.org/2005/Atom}link") or it.find("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
                    link_href = l.attrib.get("href") if l is not None else ""
                    if not link_href:
                        id_el = it.find("{http://www.w3.org/2005/Atom}id") or it.find("atom:id", {"atom": "http://www.w3.org/2005/Atom"})
                        link_href = id_el.text.strip() if id_el is not None and id_el.text else ""
                    if t is not None and t.text and link_href:
                        items.append({"title": t.text.strip().replace("\n", " "), "url": link_href.strip()})

            leads.extend(items)
        except Exception as exc:
            logger.warning(f"Tier 2 feed fetch error for {feed.get('name')}: {exc}")

    return leads


def fetch_tier_3_leads() -> list:
    """
    Tier 3: arXiv API - latest Computer Science research papers in
    cs.OS, cs.DC, cs.DB, cs.NI, cs.LG from the last 7 days.
    """
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.OS+OR+cat:cs.DC+OR+cat:cs.DB+OR+cat:cs.NI+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=30"
    leads = []
    headers = {"User-Agent": "BitBytes/1.0 (arXiv query)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            id_el = entry.find("atom:id", ns)
            if title_el is not None and id_el is not None and title_el.text and id_el.text:
                raw_title = title_el.text.strip().replace("\n", " ")
                paper_url = id_el.text.strip()
                leads.append({
                    "title": raw_title,
                    "url": paper_url
                })
    except Exception as exc:
        logger.warning(f"Tier 3 arXiv query error: {exc}")

    return leads


# =========================================================================
# Tiered Harvest & Attempt Runner
# =========================================================================

def filter_and_dedupe_candidates(raw_leads: list, sources_config: dict, past_canonical_urls: set, past_titles: list) -> tuple[list, str]:
    """
    Applies word-boundary keyword filtering, domain allowlist checks,
    canonical URL deduplication, and recent title deduplication.
    Returns (qualified_candidates, reason_if_none).
    """
    if not raw_leads:
        return [], "no_candidates"

    verified = [
        lead for lead in raw_leads
        if is_verified_source(lead.get("url", ""), lead.get("title", ""), sources_config)
    ]
    if not verified:
        return [], "filtered_out"

    # Deduplicate against past URLs and recent titles
    qualified = []
    seen_in_batch = set()

    for lead in verified:
        c_url = canonicalise_url(lead.get("url", ""))
        if not c_url or c_url in past_canonical_urls or c_url in seen_in_batch:
            continue
        seen_in_batch.add(c_url)

        lead_tokens = tokenize_title(lead.get("title", ""))
        if not lead_tokens:
            continue

        overlap = any(
            token_jaccard(lead_tokens, tokenize_title(pt)) >= 0.7
            for pt in past_titles[-30:]
        )
        if overlap:
            continue

        qualified.append(lead)

    if not qualified:
        return [], "all_seen_or_deduped"

    # Rank: prefer higher score if available, otherwise preserve order
    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)
    return qualified, "ok"


def attempt_candidates_in_tier(tier_label: str, candidates: list, crawler, curator, past_titles: list, max_candidates: int = 5) -> tuple[dict, list]:
    """
    Attempts up to max_candidates in a tier.
    An attempt = scrape -> check 800+ chars -> curate with LLM -> validate grounding.
    Returns (post, attempts_list).
    """
    attempts = []

    for idx, candidate in enumerate(candidates[:max_candidates], start=1):
        target_url = candidate.get("url", "")
        target_title = candidate.get("title", "")
        target_domain = get_registrable_domain(target_url)

        print(f"\n🎯 [{tier_label}] Attempt {idx}/{min(len(candidates), max_candidates)}: '{target_title[:60]}...'")
        print(f"   URL: {target_url}")

        # 1. Scrape (Firecrawl, then direct HTTP fallback)
        scrape_res = crawler.scrape_url(target_url)
        markdown_content = scrape_res.get("markdown", "")
        scrape_engine = scrape_res.get("engine", "unknown")
        clean_len = len(markdown_content.strip())

        if not scrape_res.get("success"):
            err_msg = scrape_res.get("error", "scrape_failed")
            reason = "thin_content" if ("under 800" in err_msg or "characters" in err_msg) else "scrape_failed"
            print(f"   ⚠️ Scrape failed: {err_msg}")
            attempts.append({
                "url": target_url,
                "domain": target_domain,
                "engine": scrape_engine,
                "chars": clean_len,
                "reject_reason": reason
            })
            continue

        if clean_len < 800:
            print(f"   ⚠️ Rejected: article text under 800 characters ({clean_len} chars)")
            attempts.append({
                "url": target_url,
                "domain": target_domain,
                "engine": scrape_engine,
                "chars": clean_len,
                "reject_reason": "thin_content"
            })
            continue

        # 2. Curate with Gemini Curator
        try:
            post = curator.curate_article(
                article_text=markdown_content,
                source_title=target_title,
                source_url=target_url,
                past_topics=past_titles
            )
        except Exception as exc:
            # Sanitize error message to ensure no API keys or tokens are logged
            clean_err = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED]', str(exc))
            print(f"   ⚠️ LLM curation exception: {clean_err}")
            attempts.append({
                "url": target_url,
                "domain": target_domain,
                "engine": scrape_engine,
                "chars": clean_len,
                "reject_reason": f"llm_error: {clean_err}"
            })
            continue

        if not post:
            print("   ⚠️ LLM returned empty lesson or rejected.")
            attempts.append({
                "url": target_url,
                "domain": target_domain,
                "engine": scrape_engine,
                "chars": clean_len,
                "reject_reason": "llm_error: rejected or empty output"
            })
            continue

        # 3. Grounding Gate
        is_valid, reason = validate_grounding(post, markdown_content, past_titles)
        if not is_valid:
            print(f"   ⚠️ Grounding gate rejected: {reason}")
            attempts.append({
                "url": target_url,
                "domain": target_domain,
                "engine": scrape_engine,
                "chars": clean_len,
                "reject_reason": f"grounding_rejected: {reason}"
            })
            continue

        # Candidate accepted!
        now_utc = datetime.now(timezone.utc)
        post["id"] = f"radar_{now_utc.strftime('%Y%m%d_%H%M')}"
        post["day"] = now_utc.strftime("%A")
        canon_url = canonicalise_url(target_url)

        post["source"] = {
            "title": target_title,
            "url": canon_url,
            "domain": target_domain,
            "fetched_at": now_utc.isoformat()
        }
        post["references"] = []
        post["source_count"] = 1
        post["engine"] = f"{tier_label.lower()} ({scrape_engine})"
        post["source_url"] = canon_url
        post["source_headline"] = target_title

        attempts.append({
            "url": target_url,
            "domain": target_domain,
            "engine": scrape_engine,
            "chars": clean_len,
            "reject_reason": None
        })

        print(f"   ✅ Candidate accepted and grounded in article! Concept: '{post.get('title')}'")
        return post, attempts

    return None, attempts


def harvest_tiered_post(history: list = None, crawler=None, curator=None, max_candidates: int = None) -> tuple[dict, str, list]:
    """
    Tiered live web research:
    Never starts from the content bank. Starts with live discovery in tiers,
    stopping at the first tier that yields an accepted lesson:
      T1: Firecrawl search + Hacker News (Algolia)
      T2: RSS/Atom feeds of trusted publishers in sources.json
      T3: arXiv API (cs.OS, cs.DC, cs.DB, cs.NI, cs.LG)
    Returns (post, tier_or_reason, all_attempts).
    """
    from crawlers.firecrawl_client import FirecrawlClient
    from crawlers.llm_curator import LLMCurator

    history = history or []
    past_canonical_urls = {
        canonicalise_url(h.get("source_url") or (h.get("source", {}).get("url") if isinstance(h.get("source"), dict) else ""))
        for h in history if h
    }
    past_canonical_urls.discard("")
    past_titles = [h.get("title", "") for h in history if h.get("title")]

    crawler = crawler or FirecrawlClient()
    curator = curator or LLMCurator()
    sources_cfg = load_sources_config()

    env_max = int(os.getenv("MAX_CANDIDATES", "5"))
    effective_max = max_candidates if max_candidates is not None else env_max

    all_attempts = []
    tier_failures = []

    # =========================================================================
    # TIER 1: Firecrawl search + Hacker News
    # =========================================================================
    print("\n📡 Tier 1 Discovery: Firecrawl Search + Hacker News (Algolia)...")
    t1_raw = fetch_tier_1_leads(crawler)
    t1_candidates, t1_filter_status = filter_and_dedupe_candidates(
        t1_raw, sources_cfg, past_canonical_urls, past_titles
    )

    if t1_candidates:
        post, attempts = attempt_candidates_in_tier(
            "T1_LiveSearch", t1_candidates, crawler, curator, past_titles, effective_max
        )
        all_attempts.extend(attempts)
        if post:
            return post, "T1_LiveSearch", all_attempts
        tier_failures.append(f"T1 attempts exhausted ({len(attempts)} tried)")
    else:
        tier_failures.append(f"T1 {t1_filter_status} ({len(t1_raw)} raw leads)")

    # =========================================================================
    # TIER 2: RSS/Atom Feeds of Trusted Publishers
    # =========================================================================
    print("\n📰 Tier 2 Discovery: Trusted Engineering RSS/Atom Feeds...")
    t2_raw = fetch_tier_2_leads(sources_cfg)
    t2_candidates, t2_filter_status = filter_and_dedupe_candidates(
        t2_raw, sources_cfg, past_canonical_urls, past_titles
    )

    if t2_candidates:
        post, attempts = attempt_candidates_in_tier(
            "T2_RSSFeeds", t2_candidates, crawler, curator, past_titles, effective_max
        )
        all_attempts.extend(attempts)
        if post:
            return post, "T2_RSSFeeds", all_attempts
        tier_failures.append(f"T2 attempts exhausted ({len(attempts)} tried)")
    else:
        tier_failures.append(f"T2 {t2_filter_status} ({len(t2_raw)} raw leads)")

    # =========================================================================
    # TIER 3: arXiv API (cs.OS, cs.DC, cs.DB, cs.NI, cs.LG)
    # =========================================================================
    print("\n🔬 Tier 3 Discovery: arXiv Research Papers (cs.OS, cs.DC, cs.DB, cs.NI, cs.LG)...")
    t3_raw = fetch_tier_3_leads()
    t3_candidates, t3_filter_status = filter_and_dedupe_candidates(
        t3_raw, sources_cfg, past_canonical_urls, past_titles
    )

    if t3_candidates:
        post, attempts = attempt_candidates_in_tier(
            "T3_arXiv", t3_candidates, crawler, curator, past_titles, effective_max
        )
        all_attempts.extend(attempts)
        if post:
            return post, "T3_arXiv", all_attempts
        tier_failures.append(f"T3 attempts exhausted ({len(attempts)} tried)")
    else:
        tier_failures.append(f"T3 {t3_filter_status} ({len(t3_raw)} raw leads)")

    failure_reason = f"All tiers exhausted: {'; '.join(tier_failures)}"
    return None, failure_reason, all_attempts


# Backwards compatibility alias
def harvest_autonomous_post(history: list = None, crawler=None, curator=None) -> tuple[dict, str]:
    post, reason_or_tier, _ = harvest_tiered_post(history, crawler, curator)
    return post, reason_or_tier


def mark_cluster_published(cluster_id: str):
    """Sets published=True on cluster ONLY after Telegram publishing succeeds."""
    if not cluster_id:
        return
    if os.path.exists(CANDIDATE_TRACKER_PATH):
        try:
            with open(CANDIDATE_TRACKER_PATH, "r", encoding="utf-8") as f:
                tracker = json.load(f)
            if cluster_id in tracker:
                tracker[cluster_id]["published"] = True
                with open(CANDIDATE_TRACKER_PATH, "w", encoding="utf-8") as f:
                    json.dump(tracker, f, indent=2)
        except Exception:
            pass
