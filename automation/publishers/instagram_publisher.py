"""
Instagram Graph API Publisher for BitBytes Daily Engineering Posts.
Publishes images/carousels to Instagram Professional accounts via Meta Graph API.
Strictly caps caption at 2200 chars, max 30 hashtags, and runs only when per-post image URL exists.
"""

import os
import requests


def format_instagram_caption(post: dict) -> str:
    """Formats a clean Instagram caption ending with 'Source: <domain> - full link in bio'."""
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    summary = post.get("summary", "")
    track = post.get("track", "")
    source = post.get("source") or {}
    domain = source.get("domain") or "bitbytes.dev"

    caption_lines = [
        f"BitBytes Daily • {track}",
        f"{title}",
        f"{subtitle}\n" if subtitle else "",
        f"Overview:\n{summary}\n",
        "Key Highlights:"
    ]
    for pt in post.get("key_points", []):
        caption_lines.append(f"• {pt}")

    if post.get("interview_tip"):
        caption_lines.append(f"\nInterview Tip: {post.get('interview_tip')}")

    caption_lines.append(f"\nSource: {domain} - full link in bio")

    tags = post.get("tags", [])
    hashtags = [t for t in tags if t.startswith("#")][:30]
    if hashtags:
        caption_lines.append(" ".join(hashtags))

    full_caption = "\n".join(caption_lines)
    return full_caption[:2200]


def publish_to_instagram(post: dict, post_image_url: str = None, access_token: str = None, account_id: str = None) -> dict:
    """
    Publishes an image post to an Instagram Business/Creator account.
    Runs ONLY when a per-post image URL exists, otherwise records status 'skipped'.
    """
    per_post_url = post_image_url or post.get("image_url")
    if not per_post_url:
        return {
            "success": False,
            "skipped": True,
            "error": "No per-post image URL provided; skipping Instagram."
        }

    access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")

    if not access_token or not account_id:
        return {
            "success": False,
            "error": "INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID are required.",
            "skipped": True
        }

    caption = format_instagram_caption(post)

    try:
        container_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
        container_payload = {
            "image_url": per_post_url,
            "caption": caption,
            "access_token": access_token
        }
        res1 = requests.post(container_url, data=container_payload, timeout=30)
        data1 = res1.json()

        if "id" not in data1:
            return {"success": False, "error": f"Failed to create media container: {data1}"}

        creation_id = data1["id"]

        publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token
        }
        res2 = requests.post(publish_url, data=publish_payload, timeout=30)
        data2 = res2.json()

        if "id" not in data2:
            return {"success": False, "error": f"Failed to publish media: {data2}"}

        return {
            "success": True,
            "post_id": data2["id"],
            "caption_length": len(caption)
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
