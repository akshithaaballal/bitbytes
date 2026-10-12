"""
BitBytes Daily Post Orchestrator.
Coordinates content selection, image generation, and multi-channel publishing
(Telegram, GitHub, Instagram) with rotation tracking and dry-run testing.
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Import Publishers
from publishers.telegram_publisher import publish_to_telegram
from publishers.git_publisher import publish_to_git
from publishers.image_generator import render_social_card
from publishers.instagram_publisher import publish_to_instagram

def load_post_by_path(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_posts(content_dir: str) -> list:
    files = sorted(glob.glob(os.path.join(content_dir, "day_*.json")))
    return [load_post_by_path(f) for f in files]

def load_history(history_path: str) -> list:
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history_path: str, history: list):
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def pick_next_post(posts: list, history: list) -> dict:
    if not posts:
        raise ValueError("No posts found in content_bank directory.")
    if not history:
        return posts[0]
        
    last_posted_id = history[-1].get("post_id")
    # Find index of last posted
    for idx, post in enumerate(posts):
        if post.get("id") == last_posted_id:
            next_idx = (idx + 1) % len(posts)
            return posts[next_idx]
            
    return posts[0]

def run_pipeline(dry_run: bool = False, specific_post_id: str = None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base_dir, ".env"))
    
    content_dir = os.path.join(base_dir, "content_bank")
    history_path = os.path.join(base_dir, "history.json")
    
    posts = get_all_posts(content_dir)
    if not posts:
        print("[ERROR] No post templates found in content_bank.")
        return
        
    if specific_post_id:
        target = next((p for p in posts if p.get("id") == specific_post_id), None)
        if not target:
            print(f"[ERROR] Post with id '{specific_post_id}' not found.")
            return
        post = target
    else:
        history = load_history(history_path)
        post = pick_next_post(posts, history)
        
    print(f"\n=======================================================")
    print(f"🚀 BITBYTES DAILY PIPELINE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Topic: {post.get('title')} [{post.get('track')}]")
    print(f"=======================================================\n")
    
    # 1. Generate Social Card
    print("🎨 Step 1: Rendering 1080x1080 Social Infographic Card...")
    try:
        image_path = render_social_card(post)
        print(f"   ✅ Card generated successfully at: {image_path}")
    except Exception as exc:
        print(f"   ⚠️ Could not render card: {exc}")
        image_path = None
        
    # 2. Publish to Git / Knowledge Base
    print("\n📚 Step 2: Archiving to GitHub Markdown & INDEX.md...")
    git_result = publish_to_git(post, base_dir)
    print(f"   ✅ Archived file: {git_result.get('relative_path')}")
    
    # 3. Publish to Telegram
    print("\n📱 Step 3: Broadcasting to Telegram Channel...")
    if dry_run or os.getenv("SIMULATE_MODE", "").lower() == "true":
        print("   [DRY RUN] Skipping actual Telegram network request.")
        telegram_result = {"success": True, "simulated": True}
    else:
        telegram_result = publish_to_telegram(post, image_path=image_path)
        if telegram_result.get("success"):
            print(f"   ✅ Telegram sent! Message ID: {telegram_result.get('message_id')}")
        elif telegram_result.get("skipped"):
            print(f"   ℹ️ Telegram skipped: {telegram_result.get('error')}")
        else:
            print(f"   ❌ Telegram failed: {telegram_result.get('error')}")
            
    # 4. Publish to Instagram
    print("\n📸 Step 4: Dispatching to Instagram...")
    if dry_run or os.getenv("SIMULATE_MODE", "").lower() == "true":
        print("   [DRY RUN] Skipping actual Instagram network request.")
        instagram_result = {"success": True, "simulated": True}
    else:
        public_url = os.getenv("PUBLIC_IMAGE_URL") # Required for IG Graph API
        instagram_result = publish_to_instagram(post, public_image_url=public_url)
        if instagram_result.get("success"):
            print(f"   ✅ Instagram posted! Post ID: {instagram_result.get('post_id')}")
        elif instagram_result.get("skipped"):
            print(f"   ℹ️ Instagram skipped: {instagram_result.get('error')}")
        else:
            print(f"   ❌ Instagram failed: {instagram_result.get('error')}")
            
    # 5. Log History
    if not dry_run:
        history = load_history(history_path)
        history.append({
            "timestamp": datetime.now().isoformat(),
            "post_id": post.get("id"),
            "track": post.get("track"),
            "title": post.get("title"),
            "git": git_result.get("success", False),
            "telegram": telegram_result.get("success", False),
            "instagram": instagram_result.get("success", False)
        })
        save_history(history_path, history)
        print(f"\n💾 Rotation history updated ({len(history)} total posts recorded).")

    print("\n🎉 Pipeline execution completed successfully!\n")
    return {
        "success": True,
        "post": post,
        "telegram": telegram_result,
        "git": git_result,
        "instagram": instagram_result,
        "image_path": image_path
    }

def get_next_post_summary() -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    content_dir = os.path.join(base_dir, "content_bank")
    history_path = os.path.join(base_dir, "history.json")
    posts = get_all_posts(content_dir)
    history = load_history(history_path)
    next_post = pick_next_post(posts, history)
    return {
        "id": next_post.get("id"),
        "title": next_post.get("title"),
        "track": next_post.get("track"),
        "subtitle": next_post.get("subtitle", ""),
        "summary": next_post.get("summary", ""),
        "tags": next_post.get("tags", []),
        "history_count": len(history)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BitBytes Daily Post Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publishing without external API calls")
    parser.add_argument("--post", type=str, help="Specify post ID to run (e.g. day_01)")
    args = parser.parse_args()
    
    run_pipeline(dry_run=args.dry_run, specific_post_id=args.post)
