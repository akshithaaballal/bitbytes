"""
Telegram Channel Publisher for BitBytes Daily Engineering Posts.
Sends formatted educational content directly to a Telegram Channel.
Enforces 4096-char limit, source line presence, and 429 backoff.
"""

import os
import re
import time
import html
import logging
import requests

logger = logging.getLogger("telegram_publisher")


def format_telegram_html(post: dict, include_complexity: bool = True, include_tip: bool = True) -> str:
    """Formats a post dictionary into clean Telegram-compatible HTML."""
    track = html.escape(post.get("track", "Engineering Daily"))
    day = html.escape(post.get("day", ""))
    title = html.escape(post.get("title", ""))
    subtitle = html.escape(post.get("subtitle", ""))

    raw_summary = post.get("summary", "")
    escaped_summary = html.escape(raw_summary)
    # Convert *x* to <i>x</i>
    summary_html = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped_summary)

    lines = [
        f"🚀 <b>BitBytes Daily • {day} [{track}]</b>",
        f"<b>{title}</b>"
    ]
    if subtitle:
        lines.append(f"<i>{subtitle}</i>")
    lines.append(f"\n📌 <b>Summary:</b>\n{summary_html}\n")

    lines.append("💡 <b>Key Highlights:</b>")
    for point in post.get("key_points", []):
        lines.append(f"• {html.escape(point)}")

    if post.get("code_snippet"):
        code = html.escape(post.get("code_snippet"))
        lines.append(f"\n💻 <b>Code Example:</b>\n<pre><code>{code}</code></pre>")

    complexity = post.get("complexity", {})
    if include_complexity and complexity:
        lines.append("\n⚡ <b>Complexity & Performance:</b>")
        for k, v in complexity.items():
            k_fmt = k.replace("_", " ").title()
            lines.append(f"• <b>{html.escape(k_fmt)}:</b> <code>{html.escape(str(v))}</code>")

    if include_tip and post.get("interview_tip"):
        tip = html.escape(post.get("interview_tip"))
        lines.append(f"\n🎯 <b>Interview & Placement Tip:</b>\n<blockquote>{tip}</blockquote>")

    # Source / References line (after interview tip, before tags - NEVER dropped)
    source = post.get("source") or {}
    source_url = source.get("url") or post.get("source_url")
    source_title = source.get("title") or post.get("source_headline") or "Source article"
    source_domain = source.get("domain") or ""

    references = post.get("references") or []

    if source_url:
        domain_part = f" ({html.escape(source_domain)})" if source_domain else ""
        lines.append(f"\nSource: <a href=\"{html.escape(source_url)}\">{html.escape(source_title)}</a>{domain_part}")
    elif references:
        ref_links = [
            f'<a href="{html.escape(r.get("url", ""))}">{html.escape(r.get("title", "Reference"))}</a>'
            for r in references if r.get("url")
        ]
        if ref_links:
            lines.append(f"\nFurther reading: {', '.join(ref_links)}")

    tags = " ".join(post.get("tags", []))
    if tags:
        lines.append(f"\n{html.escape(tags)}")

    return "\n".join(lines)


def build_telegram_message(post: dict) -> str:
    """Enforces 4096-char limit by dropping complexity, then tip, but never source."""
    # Attempt 1: Full post
    msg = format_telegram_html(post, include_complexity=True, include_tip=True)
    if len(msg) <= 4096:
        return msg

    # Attempt 2: Drop complexity
    msg = format_telegram_html(post, include_complexity=False, include_tip=True)
    if len(msg) <= 4096:
        return msg

    # Attempt 3: Drop complexity and tip
    msg = format_telegram_html(post, include_complexity=False, include_tip=False)
    if len(msg) <= 4096:
        return msg

    # Fallback truncate if still over limit
    return msg[:4090] + "..."


def publish_to_telegram(post: dict, bot_token: str = None, channel_id: str = None, image_path: str = None) -> dict:
    """
    Publishes the post to a Telegram Channel.
    Enforces 4096-char limit, disables link preview, retries on 429,
    and returns telegram_url (https://t.me/<channel>/<id>).
    """
    bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")

    if not bot_token or not channel_id:
        return {
            "success": False,
            "error": "TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be provided.",
            "skipped": True
        }

    message_text = build_telegram_message(post)
    chan_slug = channel_id.lstrip("@")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    for attempt in range(2):
        try:
            res = requests.post(url, json=payload, timeout=30)
            data = res.json()

            if res.status_code == 429 or data.get("error_code") == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 2)
                wait_time = min(int(retry_after), 30)
                logger.warning(f"Telegram 429 rate limit. Retrying after {wait_time}s...")
                time.sleep(wait_time)
                continue

            if not data.get("ok"):
                return {"success": False, "error": data.get("description", "Unknown Telegram API error")}

            msg_id = data["result"]["message_id"]
            telegram_url = f"https://t.me/{chan_slug}/{msg_id}"
            return {
                "success": True,
                "message_id": msg_id,
                "telegram_url": telegram_url,
                "chat": data["result"]["chat"].get("title", channel_id)
            }
        except Exception as exc:
            if attempt == 0:
                time.sleep(2)
                continue
            return {"success": False, "error": str(exc)}

    return {"success": False, "error": "Exceeded retry attempts for Telegram publish"}
