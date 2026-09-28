"""
BitBytes Daily Post Orchestrator.
Coordinates Autonomous Tiered Tech Radar (Firecrawl + HN -> RSS/Atom -> arXiv)
with Content Bank fallback, image generation, multi-channel publishing
(Telegram, GitHub, Instagram), static feed generation, and honest rotation tracking.
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import Publishers
from publishers.telegram_publisher import publish_to_telegram, build_telegram_message
from publishers.git_publisher import publish_to_git
from publishers.image_generator import render_social_card
from publishers.bridge_reporter import send_bridge_run_report, send_bridge_report
from report import RunReport

# Import Radar & Feed Generator
try:
    from crawlers.tech_radar import (
        harvest_tiered_post,
        harvest_autonomous_post,
        mark_cluster_published,
        validate_grounding,
        canonicalise_url,
        get_registrable_domain
    )
except Exception as e:
    harvest_tiered_post = None
    harvest_autonomous_post = None

from feed_generator import generate_feed_json


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
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []


def save_history(history_path: str, history: list):
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def pick_next_post(posts: list, history: list) -> dict:
    """
    Chooses the bank post posted longest ago (or never) by scanning the entire history.
    Never-posted posts come first.
    """
    if not posts:
        raise ValueError("No posts found in content_bank directory.")
    if not history:
        return posts[0]

    latest_index = {}
    for idx, h in enumerate(history):
        pid = h.get("post_id") or h.get("id")
        if pid:
            latest_index[pid] = idx

    # If any post has never been posted, pick the first unposted one
    unposted = [p for p in posts if p.get("id") not in latest_index]
    if unposted:
        return unposted[0]

    # Otherwise pick the post with the lowest last index (posted longest ago)
    oldest_post = min(posts, key=lambda p: latest_index.get(p.get("id"), -1))
    return oldest_post


def run_pipeline(
    dry_run: bool = False,
    specific_post_id: str = None,
    use_radar: bool = None,
    fixture_path: str = None,
    force_evergreen: bool = False,
    progress_callback = None
):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base_dir, ".env"))

    content_dir = os.path.join(base_dir, "content_bank")
    history_path = os.path.join(base_dir, "history.json")

    posts = get_all_posts(content_dir)
    history = load_history(history_path)

    # Radar defaults to true for all normal runs
    radar_env = os.getenv("USE_AI_RADAR", "true").lower() == "true"
    radar_enabled = use_radar if use_radar is not None else radar_env

    now_utc = datetime.now(timezone.utc)
    current_day = now_utc.strftime("%A")

    post = None
    cluster_id = None
    skipped_reason = None
    engine_used = "content_bank"
    fallback_used = False
    fallback_reason = None
    attempts = []
    bank_repeat_14d = False

    # A. Fixture Mode (for testing and offline verification)
    if fixture_path and os.path.exists(fixture_path):
        print(f"\n🧪 Mode: Fixture Evaluation ({fixture_path})")
        from crawlers.llm_curator import LLMCurator
        try:
            with open(fixture_path, "r", encoding="utf-8") as ff:
                fix_data = json.load(ff) if fixture_path.endswith(".json") else {"text": ff.read(), "title": "Fixture Article", "url": "https://example.com/fixture"}
        except Exception:
            with open(fixture_path, "r", encoding="utf-8") as ff:
                fix_data = {"text": ff.read(), "title": "Fixture Article", "url": "https://example.com/fixture"}

        article_text = fix_data.get("text") or fix_data.get("markdown", "")
        f_title = fix_data.get("title", "Fixture Article")
        f_url = fix_data.get("url", "https://example.com/fixture")

        curator = LLMCurator()
        past_titles = [h.get("title", "") for h in history if h.get("title")]
        candidate_post = curator.curate_article(article_text, source_title=f_title, source_url=f_url, past_topics=past_titles)

        if not candidate_post:
            skipped_reason = "Fixture was rejected by LLM (not teachable CS/AI concept)."
        else:
            is_valid, reason = validate_grounding(candidate_post, article_text, past_titles)
            if not is_valid:
                skipped_reason = f"Grounding gate rejected fixture: {reason}"
            else:
                post = candidate_post
                post["id"] = f"fixture_{now_utc.strftime('%Y%m%d_%H%M')}"
                post["day"] = current_day
                post["source"] = {
                    "title": f_title,
                    "url": canonicalise_url(f_url),
                    "domain": get_registrable_domain(f_url),
                    "fetched_at": now_utc.isoformat()
                }
                post["references"] = []
                post["source_count"] = fix_data.get("source_count", 4)
                engine_used = "fixture"

    # B. Specific Post ID (manual testing only)
    elif specific_post_id:
        target = next((p for p in posts if p.get("id") == specific_post_id), None)
        if not target:
            print(f"[ERROR] Post with id '{specific_post_id}' not found.")
            return {"success": False, "error": f"Post '{specific_post_id}' not found"}
        post = dict(target)
        post["day"] = current_day
        post["fallback_used"] = True
        fallback_used = True
        fallback_reason = f"specific_post:{specific_post_id}"
        engine_used = "content_bank"

    # C. Forced Evergreen Bank Mode (--evergreen flag for manual testing)
    elif force_evergreen:
        print("\n🌲 Mode: Forced Evergreen Content Bank (Manual Testing)")
        if not posts:
            print("[ERROR] No post templates found in content_bank.")
            return {"success": False, "error": "No post templates found"}
        post = dict(pick_next_post(posts, history))
        post["day"] = current_day
        post["fallback_used"] = True
        fallback_used = True
        fallback_reason = "forced_evergreen"
        engine_used = "content_bank_manual"

    # D. Normal Run: Scrape First (T1 Search/HN -> T2 RSS/Atom -> T3 arXiv), Bank ONLY as Last Resort
    elif radar_enabled and harvest_tiered_post:
        print("\n🛰️ Mode: Autonomous Tiered Tech Radar (Live Web Research First)")
        if progress_callback:
            progress_callback("crawling")
        post, tier_or_reason, attempts = harvest_tiered_post(history)

        if post:
            fallback_used = False
            fallback_reason = None
            engine_used = post.get("engine", "radar")
        else:
            # ONLY when all tiers are exhausted
            fallback_used = True
            fallback_reason = tier_or_reason
            print(f"ℹ️ Autonomous Radar notice: {tier_or_reason}")
            print("Falling back to Evergreen rotation bank (last resort)...")
            post = pick_next_post(posts, history) if posts else None
            if post:
                post = dict(post)
                post["day"] = current_day
                post["fallback_used"] = True
                engine_used = "content_bank_fallback"

    # E. Fallback if radar crawler is completely disabled or unavailable
    else:
        if not posts:
            print("[ERROR] No post templates found in content_bank.")
            return {"success": False, "error": "No post templates found"}
        post = dict(pick_next_post(posts, history))
        post["day"] = current_day
        post["fallback_used"] = True
        fallback_used = True
        fallback_reason = "radar_disabled_or_unavailable"
        engine_used = "content_bank"

    # 14-day repeat warning for bank lessons
    if post and fallback_used:
        fourteen_days_ago = now_utc - timedelta(days=14)
        for h in history:
            pid = h.get("id") or h.get("post_id")
            if pid == post.get("id") and h.get("timestamp"):
                try:
                    ts_str = h["timestamp"]
                    if ts_str.endswith("Z"):
                        ts_str = ts_str[:-1] + "+00:00"
                    h_time = datetime.fromisoformat(ts_str)
                    if h_time.tzinfo is None:
                        h_time = h_time.replace(tzinfo=timezone.utc)
                    if h_time >= fourteen_days_ago:
                        bank_repeat_14d = True
                        break
                except Exception:
                    pass
        if bank_repeat_14d:
            print(f"⚠️ [WARNING] Bank lesson '{post.get('id')}' was already sent in the last 14 days! Content bank needs more lessons.")

    # If nothing was selected/grounded
    if not post:
        if progress_callback:
            progress_callback("skipped")
        print(f"\n⚠️ No post published. Reason: {skipped_reason}")
        if not dry_run and skipped_reason:
            history.append({
                "timestamp": now_utc.isoformat(),
                "skipped_reason": skipped_reason,
                "engine": engine_used,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "attempts": attempts
            })
            save_history(history_path, history)
            generate_feed_json(base_dir)

        is_simulated = dry_run or os.getenv("SIMULATE_MODE", "").lower() == "true"
        bridge_res = None
        if not is_simulated:
            try:
                run_rep = RunReport(
                    trigger="console",
                    start_time=now_utc.isoformat(),
                    attempts=attempts,
                    fallback={"used": fallback_used, "reason": fallback_reason or skipped_reason},
                    delivery={"telegram": False, "git": False},
                    outcome="skipped"
                )
                run_rep.finish("skipped")
                bridge_res = send_bridge_run_report(
                    run_rep,
                    bank_repeat_14d=bank_repeat_14d,
                    telegram_link=""
                )
            except Exception as b_exc:
                print(f"⚠️ [Bridge] Could not send bridge telemetry: {b_exc}")

        return {"success": True, "skipped": True, "skipped_reason": skipped_reason}

    # Force compute day in code
    post["day"] = current_day

    print(f"\n=======================================================")
    print(f"🚀 BITBYTES PIPELINE: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Topic: {post.get('title')} [{post.get('track')}]")
    if post.get("source"):
        print(f"Source: {post['source'].get('title')} ({post['source'].get('domain')})")
    print(f"Fallback Used: {fallback_used}")
    print(f"=======================================================\n")

    if progress_callback:
        progress_callback("publishing")

    # 1. Image Generation (Optional via GENERATE_IMAGE=true)
    generate_image = os.getenv("GENERATE_IMAGE", "true").lower() == "true"
    image_path = None
    if generate_image:
        print("🎨 Step 1: Dynamically Rendering Social Card...")
        try:
            image_path = render_social_card(post)
            print(f"   ✅ Card rendered: {image_path}")
        except Exception as exc:
            print(f"   ⚠️ Could not render card: {exc}")
            image_path = None
    else:
        print("📝 Step 1: Image generation disabled (broadcasting clean rich technical note).")

    # 2. Telegram Broadcast
    is_simulated = dry_run or os.getenv("SIMULATE_MODE", "").lower() == "true"
    print("\n📱 Step 2: Broadcasting to Telegram Channel...")
    if is_simulated:
        print("   [DRY RUN] Simulating Telegram broadcast...")
        msg_preview = build_telegram_message(post)
        print(f"   Message length: {len(msg_preview)} chars (limit: 4096)")
        telegram_result = {
            "success": True,
            "simulated": True,
            "message_id": 999999,
            "photo_sent": bool(image_path),
            "telegram_url": "https://t.me/csbites/999999"
        }
    else:
        telegram_result = publish_to_telegram(post, image_path=image_path)
        if telegram_result.get("success"):
            print(f"   ✅ Telegram sent! Message ID: {telegram_result.get('message_id')}")
            if cluster_id:
                mark_cluster_published(cluster_id)
        elif telegram_result.get("skipped"):
            print(f"   ℹ️ Telegram skipped: {telegram_result.get('error')}")
        else:
            print(f"   ❌ Telegram failed: {telegram_result.get('error')}")

    telegram_ok = bool(telegram_result.get("success", False))
    post["telegram_url"] = telegram_result.get("telegram_url", "")

    # 3. Publish to Git / Archive (ONLY when Telegram ok and not dry-run / simulate)
    print("\n📚 Step 3: Archiving to GitHub Markdown & INDEX.md...")
    if is_simulated:
        print("   [DRY RUN] Simulating Git archive (no file written)...")
        git_result = {"success": True, "simulated": True, "relative_path": "archive/simulated.md"}
    elif not telegram_ok:
        print("   ⚠️ Skipped Git archive: Telegram publication was not successful.")
        git_result = {"success": False, "skipped": True, "error": "Telegram publication failed"}
    else:
        git_result = publish_to_git(
            post,
            base_dir,
            telegram_url=telegram_result.get("telegram_url", ""),
            fallback_used=fallback_used
        )
        print(f"   ✅ Archived file: {git_result.get('relative_path')}")

    # 5. Log History Entry
    if not dry_run:
        history.append({
            "id": post.get("id"),
            "timestamp": now_utc.isoformat(),
            "track": post.get("track"),
            "title": post.get("title"),
            "subtitle": post.get("subtitle", ""),
            "summary": post.get("summary", ""),
            "source": post.get("source"),
            "references": post.get("references", []),
            "source_count": post.get("source_count", 1),
            "engine": engine_used,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "attempts": attempts,
            "telegram": {
                "ok": telegram_result.get("success", False),
                "message_id": telegram_result.get("message_id"),
                "url": telegram_result.get("telegram_url", "")
            },
            "git": {
                "ok": git_result.get("success", False),
                "path": git_result.get("relative_path", "")
            },
            "skipped_reason": skipped_reason
        })
        save_history(history_path, history)
        print(f"\n💾 Rotation history updated ({len(history)} total posts recorded).")
        generate_feed_json(base_dir)
        print("📄 Static feed.json updated at frontend/public/feed.json.")

    # 6. Cosmitude Bridge Telemetry & Research Report (ONLY in real runs, not dry-run)
    bridge_res = None
    if not is_simulated:
        try:
            run_rep = RunReport(
                trigger="console",
                start_time=now_utc.isoformat(),
                attempts=attempts,
                chosen=post,
                fallback={"used": fallback_used, "reason": fallback_reason},
                delivery={
                    "telegram": telegram_ok,
                    "git": git_result.get("success", False)
                },
                outcome="published" if telegram_ok else "failed"
            )
            run_rep.finish("published" if telegram_ok else "failed")
            bridge_res = send_bridge_run_report(
                run_rep,
                bank_repeat_14d=bank_repeat_14d,
                telegram_link=telegram_result.get("telegram_url", "")
            )
        except Exception as b_exc:
            print(f"⚠️ [Bridge] Could not send bridge telemetry: {b_exc}")

    if progress_callback:
        progress_callback("done")

    print("\n🎉 Pipeline execution completed successfully!\n")
    return {
        "success": telegram_ok if not is_simulated else True,
        "post": post,
        "telegram": telegram_result,
        "git": git_result,
        "image_path": image_path,
        "bridge": bridge_res,
        "engine": engine_used,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "attempts": attempts
    }


def get_next_post_summary() -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    content_dir = os.path.join(base_dir, "content_bank")
    history_path = os.path.join(base_dir, "history.json")

    posts = get_all_posts(content_dir)
    history = load_history(history_path)

    if not posts:
        return {"error": "No posts found in content_bank"}

    next_p = pick_next_post(posts, history)
    return {
        "next_post": next_p,
        "history_count": len(history),
        "total_posts": len(posts)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BitBytes Daily Post Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publishing without external API calls")
    parser.add_argument("--post", type=str, help="Specify post ID to run (e.g. day_01)")
    parser.add_argument("--radar", action="store_true", help="Force autonomous radar mode")
    parser.add_argument("--evergreen", action="store_true", help="Force evergreen content bank mode (manual testing only)")
    parser.add_argument("--fixture", type=str, help="Path to fixture article for testing/verification")
    args = parser.parse_args()

    res = run_pipeline(
        dry_run=args.dry_run,
        specific_post_id=args.post,
        use_radar=args.radar if args.radar else None,
        fixture_path=args.fixture,
        force_evergreen=args.evergreen
    )

    # Write GITHUB_STEP_SUMMARY if running in GitHub Actions
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a", encoding="utf-8") as sf:
                sf.write("### BitBytes Pipeline Summary\n\n")
                sf.write(f"- **Engine**: `{res.get('engine', 'unknown')}`\n")
                sf.write(f"- **Fallback Used**: `{res.get('fallback_used', False)}`\n")
                if res.get("skipped"):
                    sf.write(f"- **Status**: Skipped\n")
                    sf.write(f"- **Skipped Reason**: {res.get('skipped_reason', 'N/A')}\n")
                else:
                    post_info = res.get("post", {})
                    source_info = post_info.get("source", {})
                    sf.write(f"- **Status**: Published\n")
                    sf.write(f"- **Topic**: {post_info.get('title', 'N/A')}\n")
                    if source_info:
                        sf.write(f"- **Source**: {source_info.get('title', 'N/A')} ({source_info.get('url', 'N/A')})\n")
                    sf.write(f"- **Source Count**: {post_info.get('source_count', 1)}\n")
        except Exception as e:
            print(f"[Warning] Could not write GITHUB_STEP_SUMMARY: {e}")

    # Fail the job on unexpected errors, not on a skipped run
    if not res.get("success") and not res.get("skipped"):
        sys.exit(1)
    sys.exit(0)
