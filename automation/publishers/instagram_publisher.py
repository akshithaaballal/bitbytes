"""
Instagram Graph API Publisher for BitBytes Daily Engineering Posts.
Publishes images/carousels to Instagram Professional accounts via Meta Graph API.
"""

import os
import requests

def format_instagram_caption(post: dict) -> str:
    """Formats a clean Instagram caption with bullet points and relevant hashtags."""
    title = post.get("title", "")
    subtitle = post.get("subtitle", "")
    summary = post.get("summary", "")
    track = post.get("track", "")
    
    caption_lines = [
        f"🚀 {title}",
        f"📌 {subtitle}\n" if subtitle else "",
        f"Today's {track} breakdown:\n{summary}\n",
        "Key Highlights:"
    ]
    for pt in post.get("key_points", []):
        caption_lines.append(f"• {pt}")
        
    if post.get("interview_tip"):
        caption_lines.append(f"\n🎯 Interview Insight: {post.get('interview_tip')}")
        
    caption_lines.append("\n💾 Save this post for your placement & exam revision!")
    caption_lines.append("Follow @bitbytes.daily for daily Computer Science & Engineering concepts.\n")
    
    tags = " ".join(post.get("tags", [])) + " #ComputerScience #EngineeringStudents #SoftwareEngineer #CodingLife"
    caption_lines.append(tags)
    
    return "\n".join(caption_lines)


def publish_to_instagram(post: dict, public_image_url: str, access_token: str = None, account_id: str = None) -> dict:
    """
    Publishes an image post to an Instagram Business/Creator account.
    Requires a publicly accessible HTTPS image URL.
    """
    access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
    
    if not access_token or not account_id:
        return {
            "success": False,
            "error": "INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID are required.",
            "skipped": True
        }
        
    if not public_image_url:
        return {
            "success": False,
            "error": "Instagram Graph API requires a publicly accessible image URL (e.g. hosted on S3 or Cloudinary)."
        }
        
    caption = format_instagram_caption(post)
    
    try:
        # Step 1: Create media container
        container_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
        container_payload = {
            "image_url": public_image_url,
            "caption": caption,
            "access_token": access_token
        }
        res1 = requests.post(container_url, data=container_payload, timeout=30)
        data1 = res1.json()
        
        if "id" not in data1:
            return {"success": False, "error": f"Failed to create media container: {data1}"}
            
        creation_id = data1["id"]
        
        # Step 2: Publish media container
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
