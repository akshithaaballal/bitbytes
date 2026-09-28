"""
Git & GitHub Publisher for BitBytes Daily Engineering Posts.
Generates structured Markdown files with YAML front-matter and updates INDEX.md with Source column.
Ensures:
  1. Archive files and INDEX.md rows are written ONLY upon successful Telegram delivery.
  2. Exactly one archive note per bank lesson: re-sent bank lessons append
     `> **Re-sent on:** <date>` rather than creating duplicate files.
  3. Every note contains YAML front-matter with fallback_used flag and a standard `## Source` section.
"""

import os
import re
from datetime import datetime, timezone


def format_github_markdown(post: dict, telegram_url: str = "", fallback_used: bool = False) -> str:
    """Formats the post into a full GitHub Flavored Markdown document with YAML front-matter."""
    track = post.get("track", "Engineering")
    day = post.get("day", "")
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    summary = post.get("summary", "")

    source = post.get("source") or {}
    source_url = source.get("url") or post.get("source_url", "")
    source_title = source.get("title") or post.get("source_headline", "")
    source_domain = source.get("domain", "")
    references = post.get("references") or []

    is_fallback = fallback_used or bool(post.get("fallback_used", False)) or (not source_url and bool(references))

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Escape double quotes for YAML front-matter
    yaml_title = title.replace('"', '\\"')
    yaml_source_title = source_title.replace('"', '\\"') if source_title else ""

    md_lines = [
        "---",
        f'title: "{yaml_title}"',
        f'track: "{track}"',
        f'date: "{date_str}"',
        f'source_url: "{source_url}"',
        f'source_title: "{yaml_source_title}"',
        f'source_domain: "{source_domain}"',
        f'telegram_url: "{telegram_url}"',
        f'fallback_used: {str(is_fallback).lower()}',
        "---\n",
        f"# {title}",
        f"> **Track:** {track} | **Day:** {day} | **Date:** {date_str}\n",
        f"**{subtitle}**\n" if subtitle else "",
        f"## 📌 Overview\n{summary}\n",
        "## 💡 Key Highlights"
    ]

    for point in post.get("key_points", []):
        md_lines.append(f"- {point}")

    if post.get("code_snippet"):
        code = post.get("code_snippet")
        lang = "python" if "def " in code or "import " in code else "sql" if "SELECT" in code else ""
        md_lines.append(f"\n## 💻 Code Example\n```{lang}\n{code}\n```")

    complexity = post.get("complexity", {})
    if complexity:
        md_lines.append("\n## ⚡ Complexity & Performance")
        for k, v in complexity.items():
            k_fmt = k.replace("_", " ").title()
            md_lines.append(f"- **{k_fmt}:** `{v}`")

    if post.get("interview_tip"):
        tip = post.get("interview_tip")
        md_lines.append(f"\n## 🎯 Interview Tip\n> [!TIP]\n> {tip}")

    # Standardized ## Source section
    md_lines.append("\n## Source")
    if source_url:
        domain_label = f" ({source_domain})" if source_domain else ""
        md_lines.append(f"- Link: [{source_title or source_url}]({source_url}){domain_label}")
        md_lines.append(f"- Retrieved: {date_str}")
    elif references:
        md_lines.append("- Origin: Content Bank Fallback")
        md_lines.append("- References:")
        for ref in references:
            if ref.get("url"):
                md_lines.append(f"  - [{ref.get('title', 'Reference')}]({ref.get('url')})")
    else:
        md_lines.append("- Origin: Content Bank Fallback")

    tags = " ".join([f"`{t}`" for t in post.get("tags", [])])
    if tags:
        md_lines.append(f"\n---\n**Tags:** {tags}")

    return "\n".join(md_lines) + "\n"


def publish_to_git(post: dict, base_dir: str = None, telegram_url: str = "", fallback_used: bool = False) -> dict:
    """
    Writes the post as a Markdown file in `archive/` directory
    and appends an entry to the Knowledge Base Index in `INDEX.md`.

    For content bank fallback posts (day_*.json), maintains exactly ONE note:
    subsequent runs append `\n> **Re-sent on:** <date>\n` to the existing file.
    Autonomous radar posts remain one file per post.
    """
    base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archive_dir = os.path.join(base_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M")
    date_code = now_utc.strftime("%Y-%m-%d_%H%M")
    post_id = str(post.get("id", "post"))

    is_bank_lesson = fallback_used or bool(post.get("fallback_used", False)) or post_id.startswith("day_")

    existing_file = None
    existing_filename = None

    if is_bank_lesson:
        # Search for any existing file created for this bank lesson
        for fname in os.listdir(archive_dir):
            if fname.endswith(f"_{post_id}.md") or fname == f"{post_id}.md":
                existing_file = os.path.join(archive_dir, fname)
                existing_filename = fname
                break

    if existing_file:
        # Bank note already exists: append re-sent banner rather than creating duplicate file
        with open(existing_file, "a", encoding="utf-8") as f:
            f.write(f"\n> **Re-sent on:** {timestamp_str}\n")
        file_path = existing_file
        filename = existing_filename
    else:
        # Create new markdown file
        filename = f"{date_code}_{post_id}.md"
        file_path = os.path.join(archive_dir, filename)
        content = format_github_markdown(post, telegram_url=telegram_url, fallback_used=is_bank_lesson)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Source column formatting
    source = post.get("source") or {}
    source_url = source.get("url") or post.get("source_url", "")
    source_domain = source.get("domain", "")
    if source_url and source_domain:
        source_col = f"[{source_domain}]({source_url})"
    elif source_url:
        source_col = f"[Source]({source_url})"
    else:
        source_col = "Content Bank"

    index_path = os.path.join(base_dir, "INDEX.md")
    index_entry = f"| {timestamp_str} | **{post.get('day', '')}** | {post.get('track', '')} | [{post.get('title', '')}](archive/{filename}) | {source_col} |\n"

    header = "# 📚 BitBytes Engineering Knowledge Archive\n\n| Timestamp | Track Day | Track | Topic | Source |\n| :--- | :--- | :--- | :--- | :--- |\n"
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(header + index_entry)
    else:
        with open(index_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if "| Source |" not in existing:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(header + index_entry)
        else:
            with open(index_path, "a", encoding="utf-8") as f:
                f.write(index_entry)

    return {
        "success": True,
        "archive_file": file_path,
        "index_file": index_path,
        "relative_path": f"archive/{filename}"
    }
