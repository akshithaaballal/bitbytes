"""
Tech Radar Coordinator for BitBytes.
Orchestrates live tech/AI web crawling and technical extraction via LLM.
Strict source filtering, honest multi-domain clustering, and grounding gate validation.
"""

import os
import sys
import json
import re
import uuid
import logging
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

        # 2. Domain check
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


def load_candidate_tracker() -> dict:
    if os.path.exists(CANDIDATE_TRACKER_PATH):
        try:
            with open(CANDIDATE_TRACKER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_candidate_tracker(tracker: dict):
    try:
        with open(CANDIDATE_TRACKER_PATH, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save candidate tracker: {e}")


def update_and_prune_clusters(raw_leads: list, sources_config: dict = None) -> dict:
    """
    Honest clustering of leads:
    - Clusters stories by normalised-title token Jaccard >= 0.5.
    - source_count = number of DISTINCT registrable domains in trailing 7 days.
    - Prunes clusters older than 14 days.
    """
    tracker = load_candidate_tracker()
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    sources_cfg = sources_config or load_sources_config()

    # 1. Ingest verified leads
    for lead in raw_leads:
        u = lead.get("url", "")
        t = lead.get("title", "")
        if not is_verified_source(u, t, sources_cfg):
            continue

        canon_url = canonicalise_url(u)
        domain = get_registrable_domain(u)
        tokens = tokenize_title(t)
        if not tokens:
            continue

        matched_cluster_id = None
        for cid, cluster in tracker.items():
            cluster_tokens = tokenize_title(cluster.get("title", ""))
            if token_jaccard(tokens, cluster_tokens) >= 0.5:
                matched_cluster_id = cid
                break

        article_entry = {
            "url": canon_url,
            "title": t,
            "domain": domain,
            "seen_at": now_iso
        }

        if matched_cluster_id:
            cluster = tracker[matched_cluster_id]
            cluster["updated_at"] = now_iso
            articles = cluster.setdefault("articles", [])
            if not any(a.get("url") == canon_url for a in articles):
                articles.append(article_entry)
        else:
            new_id = str(uuid.uuid4())[:8]
            tracker[new_id] = {
                "cluster_id": new_id,
                "title": t,
                "created_at": now_iso,
                "updated_at": now_iso,
                "published": False,
                "articles": [article_entry]
            }

    # 2. Prune clusters older than 14 days and calculate honest source_count (trailing 7 days)
    pruned_tracker = {}
    fourteen_days_ago = now_utc - timedelta(days=14)
    seven_days_ago = now_utc - timedelta(days=7)

    for cid, cluster in tracker.items():
        try:
            updated_dt = datetime.fromisoformat(cluster.get("updated_at", now_iso))
            if updated_dt.tzinfo is None:
                updated_dt = updated_dt.replace(tzinfo=timezone.utc)
            if updated_dt < fourteen_days_ago:
                continue
        except Exception:
            pass

        # Calculate distinct domains in trailing 7 days
        articles = cluster.get("articles", [])
        recent_domains = set()
        for art in articles:
            try:
                seen_dt = datetime.fromisoformat(art.get("seen_at", now_iso))
                if seen_dt.tzinfo is None:
                    seen_dt = seen_dt.replace(tzinfo=timezone.utc)
                if seen_dt >= seven_days_ago and art.get("domain"):
                    recent_domains.add(art.get("domain"))
            except Exception:
                pass

        cluster["source_count"] = len(recent_domains)
        pruned_tracker[cid] = cluster

    save_candidate_tracker(pruned_tracker)
    return pruned_tracker


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


def harvest_autonomous_post(history: list = None, crawler=None, curator=None) -> tuple[dict, str]:
    """
    Candidate loop:
    1. Harvests leads from Firecrawl and Hacker News.
    2. Clusters stories and updates tracker.
    3. Ranks candidates by source_count and recency, trying up to 3 candidates.
    4. Scrapes article, rejects if cleaned text < 800 chars.
    5. Curates with LLM and tests grounding gate.
    6. Returns (post, cluster_id) on success, or (None, skipped_reason) on failure.
    """
    from crawlers.firecrawl_client import FirecrawlClient, fetch_trending_tech_leads
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

    print("🌐 Step 0 (Radar): Harvesting trending technical leads from live web...")
    firecrawl_leads = crawler.search_trending(
        query="trending AI systems compiler database operating systems research",
        limit=8
    ) if crawler.api_key else []

    hn_leads = fetch_trending_tech_leads(limit=30)
    raw_candidates = firecrawl_leads + hn_leads

    # Ingest and cluster leads
    tracker = update_and_prune_clusters(raw_candidates)

    # Filter qualified candidates:
    # 1. Not published
    # 2. source_count >= 4
    # 3. Canonical URL never in history
    # 4. Title not in last 30 posts
    qualified_clusters = []
    for cid, cluster in tracker.items():
        if cluster.get("published", False):
            continue
        if cluster.get("source_count", 0) < 4:
            continue

        articles = cluster.get("articles", [])
        if not articles:
            continue

        # Choose top article with canonical URL never seen before
        valid_article = None
        for art in reversed(articles):
            c_url = canonicalise_url(art.get("url", ""))
            if c_url and c_url not in past_canonical_urls:
                valid_article = art
                break

        if not valid_article:
            continue

        cluster_tokens = tokenize_title(cluster.get("title", ""))
        recent_overlap = any(
            token_jaccard(cluster_tokens, tokenize_title(pt)) >= 0.7
            for pt in past_titles[-30:]
        )
        if recent_overlap:
            continue

        qualified_clusters.append((cid, cluster, valid_article))

    # Rank candidates by source_count descending
    qualified_clusters.sort(key=lambda item: item[1].get("source_count", 0), reverse=True)

    if not qualified_clusters:
        return None, "No candidates reached the 4-source verification threshold across distinct domains in the trailing 7 days."

    # Try up to 3 candidates
    tried = 0
    rejection_reasons = []

    for cid, cluster, article in qualified_clusters[:3]:
        tried += 1
        target_url = article.get("url", "")
        target_title = article.get("title", cluster.get("title", ""))
        source_count = cluster.get("source_count", 4)

        print(f"\n🎯 Trying Candidate {tried}/3: '{target_title}' (Verified across {source_count} domains)")
        print(f"   URL: {target_url}")

        scrape_res = crawler.scrape_url(target_url)
        if not scrape_res.get("success"):
            err = scrape_res.get("error", "Scrape failed")
            print(f"   ⚠️ Candidate rejected: {err}")
            rejection_reasons.append(f"Candidate {tried}: {err}")
            continue

        markdown_content = scrape_res.get("markdown", "")
        scrape_engine = scrape_res.get("engine", "unknown")

        post = curator.curate_article(
            article_text=markdown_content,
            source_title=target_title,
            source_url=target_url,
            past_topics=past_titles
        )

        if not post:
            print("   ⚠️ LLM failed to return a lesson.")
            rejection_reasons.append(f"Candidate {tried}: LLM returned no lesson")
            continue

        is_valid, reason = validate_grounding(post, markdown_content, past_titles)
        if not is_valid:
            print(f"   ⚠️ Grounding gate rejected candidate: {reason}")
            rejection_reasons.append(f"Candidate {tried}: Grounding failed ({reason})")
            continue

        # Candidate passed grounding gate!
        now_utc = datetime.now(timezone.utc)
        post["id"] = f"radar_{now_utc.strftime('%Y%m%d_%H%M')}"
        post["day"] = now_utc.strftime("%A")
        canon_url = canonicalise_url(target_url)
        domain = get_registrable_domain(target_url)

        post["source"] = {
            "title": target_title,
            "url": canon_url,
            "domain": domain,
            "fetched_at": now_utc.isoformat()
        }
        post["references"] = []
        post["source_count"] = source_count
        post["engine"] = f"firecrawl ({scrape_engine})"
        post["source_url"] = canon_url
        post["source_headline"] = target_title

        print(f"   ✅ Candidate accepted and grounded in article! Concept: '{post.get('title')}'")
        return post, cid

    return None, f"All {tried} candidate(s) failed grounding gate: {'; '.join(rejection_reasons)}"


def mark_cluster_published(cluster_id: str):
    """Sets published=True on cluster ONLY after Telegram publishing succeeds."""
    if not cluster_id:
        return
    tracker = load_candidate_tracker()
    if cluster_id in tracker:
        tracker[cluster_id]["published"] = True
        save_candidate_tracker(tracker)
