"""
Telegram Channel Publisher for BitBytes Daily Engineering Posts.
Sends formatted educational content directly to a Telegram Channel or Group.
"""

import os
import requests
import html

def format_telegram_html(post: dict) -> str:
    """Formats a post dictionary into clean Telegram-compatible HTML."""
    track = html.escape(post.get("track", "Engineering Daily"))
    day = html.escape(post.get("day", ""))
    title = html.escape(post.get("title", ""))
    subtitle = html.escape(post.get("subtitle", ""))
    summary = html.escape(post.get("summary", ""))
    
    lines = [
        f"🚀 <b>BitBytes Daily • {day} [{track}]</b>",
        f"<b>{title}</b>",
        f"<i>{subtitle}</i>\n" if subtitle else "",
        f"📌 <b>Summary:</b>\n{summary}\n",
        "💡 <b>Key Highlights:</b>"
    ]
    
    for point in post.get("key_points", []):
        lines.append(f"• {html.escape(point)}")
    
    if post.get("code_snippet"):
        code = html.escape(post.get("code_snippet"))
        lines.append(f"\n💻 <b>Code Example:</b>\n<pre><code>{code}</code></pre>")
        
    complexity = post.get("complexity", {})
    if complexity:
        lines.append("\n⚡ <b>Complexity & Performance:</b>")
        for k, v in complexity.items():
            k_fmt = k.replace("_", " ").title()
            lines.append(f"• <b>{html.escape(k_fmt)}:</b> <code>{html.escape(str(v))}</code>")
            
    if post.get("interview_tip"):
        tip = html.escape(post.get("interview_tip"))
        lines.append(f"\n🎯 <b>Interview & Placement Tip:</b>\n<blockquote>{tip}</blockquote>")
        
    tags = " ".join(post.get("tags", []))
    if tags:
        lines.append(f"\n{html.escape(tags)}")
        
    return "\n".join(lines)


def publish_to_telegram(post: dict, bot_token: str = None, channel_id: str = None, image_path: str = None) -> dict:
    """
    Publishes the post to a Telegram Channel.
    If image_path is provided and exists, sends as a photo with caption;
    otherwise sends as a text message.
    """
    bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")
    
    if not bot_token or not channel_id:
        return {
            "success": False,
            "error": "TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be provided.",
            "skipped": True
        }
        
    message_text = format_telegram_html(post)
    
    try:
        # If image is available and caption fits Telegram's 1024 char caption limit
        if image_path and os.path.exists(image_path) and len(message_text) <= 1024:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, "rb") as photo_file:
                payload = {
                    "chat_id": channel_id,
                    "caption": message_text,
                    "parse_mode": "HTML"
                }
                files = {"photo": photo_file}
                res = requests.post(url, data=payload, files=files, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": channel_id,
                "text": message_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            res = requests.post(url, json=payload, timeout=30)
            
        data = res.json()
        if not data.get("ok"):
            return {"success": False, "error": data.get("description", "Unknown Telegram API error")}
            
        return {
            "success": True,
            "message_id": data["result"]["message_id"],
            "chat": data["result"]["chat"]["title"] if "title" in data["result"]["chat"] else channel_id
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
