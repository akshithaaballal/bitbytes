"""
Static Feed Generator for BitBytes.
Generates frontend/public/feed.json from history and archive markdown files.
The public website reads ONLY /feed.json and never depends on middleware/agent.
"""

import os
import re
import json
import glob
from datetime import datetime, timezone
from urllib.parse import urlparse


def parse_archive_markdown(file_path: str) -> dict:
    """Extracts structured fields from an archive markdown file."""
    data = {
        "title": "",
        "track": "",
        "subtitle": "",
        "summary": "",
        "key_points": [],
        "code_snippet": "",
        "complexity": {},
        "interview_tip": "",
        "source_url": "",
        "source_title": "",
        "source_domain": "",
        "telegram_url": ""
    }
    if not os.path.exists(file_path):
        return data

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML front-matter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front_matter = parts[1]
                body = parts[2]
                for line in front_matter.strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in data:
                            data[k] = v
                content = body

        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.M)
        if title_match and not data["title"]:
            data["title"] = title_match.group(1).strip()

        # Extract track
        track_match = re.search(r"\*\*Track:\*\*\s*([^|]+)", content)
        if track_match and not data["track"]:
            data["track"] = track_match.group(1).strip()

        # Extract subtitle
        sub_match = re.search(r">\s*\*\*Track:[^\n]+\n\n\*\*([^*]+)\*\*", content)
        if sub_match and not data["subtitle"]:
            data["subtitle"] = sub_match.group(1).strip()

        # Extract Overview/Summary
        overview_match = re.search(r"##\s*📌?\s*Overview\s*\n+([\s\S]+?)(?=\n##|$)", content)
        if overview_match:
            data["summary"] = overview_match.group(1).strip()

        # Extract Key Highlights
        highlights_match = re.search(r"##\s*💡?\s*Key Highlights\s*\n+([\s\S]+?)(?=\n##|$)", content)
        if highlights_match:
            points = []
            for line in highlights_match.group(1).split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    points.append(line.lstrip("-•").strip())
            data["key_points"] = points

        # Extract Code
        code_match = re.search(r"##\s*💻?\s*Code Example\s*\n+```[a-z]*\n([\s\S]+?)\n```", content)
        if code_match:
            data["code_snippet"] = code_match.group(1)

        # Extract Complexity
        comp_match = re.search(r"##\s*⚡?\s*Complexity & Performance\s*\n+([\s\S]+?)(?=\n##|$)", content)
        if comp_match:
            comp = {}
            for line in comp_match.group(1).split("\n"):
                m = re.search(r"-\s*\*\*([^:]+):\*\*\s*`([^`]+)`", line)
                if m:
                    comp[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
            data["complexity"] = comp

        # Extract Interview Tip
        tip_match = re.search(r"##\s*🎯?\s*Interview Tip\s*\n+(?:>\s*\[!TIP\]\s*\n)?(?:>\s*)?([\s\S]+?)(?=\n---|\n##|$)", content)
        if tip_match:
            clean_tip = re.sub(r"^>\s*", "", tip_match.group(1), flags=re.M).strip()
            data["interview_tip"] = clean_tip

    except Exception as e:
        pass

    return data


def generate_feed_json(base_dir: str = None) -> str:
    """
    Builds frontend/public/feed.json containing total count and last 100 posts newest first.
    """
    base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    history_path = os.path.join(base_dir, "history.json")
    archive_dir = os.path.join(base_dir, "archive")
    content_bank_dir = os.path.join(base_dir, "content_bank")
    public_dir = os.path.join(project_root, "frontend", "public")
    feed_path = os.path.join(public_dir, "feed.json")

    os.makedirs(public_dir, exist_ok=True)

    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    # Map archive files by post_id
    archive_files = glob.glob(os.path.join(archive_dir, "*.md"))
    archive_map = {}
    for af in archive_files:
        bn = os.path.basename(af)
        # Pattern: YYYY-MM-DD_HHMM_<post_id>.md or YYYY-MM-DD_<post_id>.md
        archive_map[bn] = af
        # Also map by base id
        for h in history:
            pid = h.get("post_id") or h.get("id")
            if pid and pid in bn:
                archive_map[pid] = af

    # Map content bank files
    content_bank = {}
    for cf in glob.glob(os.path.join(content_bank_dir, "day_*.json")):
        try:
            with open(cf, "r", encoding="utf-8") as f:
                cb_post = json.load(f)
                if cb_post.get("id"):
                    content_bank[cb_post["id"]] = cb_post
        except Exception:
            pass

    posts_list = []
    # Process newest first
    reversed_history = list(reversed(history))

    for h in reversed_history[:100]:
        post_id = h.get("post_id") or h.get("id", "")
        # Find parsed content
        md_file = archive_map.get(post_id)
        parsed_md = parse_archive_markdown(md_file) if md_file else {}
        cb_item = content_bank.get(post_id, {})

        title = h.get("title") or parsed_md.get("title") or cb_item.get("title", "Untitled Note")
        track = h.get("track") or parsed_md.get("track") or cb_item.get("track", "Systems Engineering")
        subtitle = h.get("subtitle") or parsed_md.get("subtitle") or cb_item.get("subtitle", "")
        summary = h.get("summary") or parsed_md.get("summary") or cb_item.get("summary", "")
        key_points = parsed_md.get("key_points") or cb_item.get("key_points", [])
        code_snippet = parsed_md.get("code_snippet") or cb_item.get("code_snippet", "")
        complexity = parsed_md.get("complexity") or cb_item.get("complexity", {})
        interview_tip = parsed_md.get("interview_tip") or cb_item.get("interview_tip", "")

        # Format Source
        raw_source = h.get("source")
        source = {}
        if isinstance(raw_source, dict):
            source = raw_source
        else:
            s_url = h.get("source_url") or parsed_md.get("source_url", "")
            s_title = h.get("source_headline") or parsed_md.get("source_title", "")
            if s_url:
                parsed_url = urlparse(s_url)
                host = parsed_url.netloc.lower()
                parts = host.split(".")
                domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
                source = {
                    "title": s_title or title,
                    "url": s_url,
                    "domain": domain,
                    "fetched_at": h.get("timestamp", "")
                }

        references = h.get("references") or cb_item.get("references", [])
        source_count = h.get("source_count")
        if source_count is None and source.get("url"):
            # If not tracked, check if mentions existed or default to 1
            source_count = 1

        # Telegram URL
        telegram_data = h.get("telegram")
        telegram_url = ""
        if isinstance(telegram_data, dict):
            telegram_url = telegram_data.get("url", "")
        elif parsed_md.get("telegram_url"):
            telegram_url = parsed_md.get("telegram_url")

        # Archive URL (GitHub blob)
        archive_url = ""
        if md_file:
            rel_name = os.path.basename(md_file)
            archive_url = f"https://github.com/akshithaaballal/bitbytes/blob/main/automation/archive/{rel_name}"

        # Word count for read_minutes
        word_count = len(f"{summary} {' '.join(key_points)} {code_snippet}".split())
        read_minutes = max(1, round(word_count / 200))

        posts_list.append({
            "id": post_id,
            "date": h.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "track": track,
            "title": title,
            "subtitle": subtitle,
            "summary": summary,
            "key_points": key_points,
            "code_snippet": code_snippet,
            "complexity": complexity,
            "interview_tip": interview_tip,
            "source": source if source else None,
            "references": references,
            "source_count": source_count,
            "telegram_url": telegram_url,
            "archive_url": archive_url,
            "read_minutes": read_minutes
        })

    feed_data = {
        "total": len(history),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "posts": posts_list
    }

    with open(feed_path, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, indent=2)

    return feed_path
