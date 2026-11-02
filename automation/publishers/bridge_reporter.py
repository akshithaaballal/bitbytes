"""
BitBytes Cosmitude Bridge Telemetry Reporter.
Formats execution and research reports, sends them to Cosmitude Bridge via Bot.py
if connected, and persists to a durable queue (automation/reports/) for guaranteed delivery.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# Add agent directory to sys.path if not present
agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

QUEUE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
QUEUE_FILE = os.path.join(QUEUE_DIR, "pending_queue.json")


def ensure_queue_dir():
    os.makedirs(QUEUE_DIR, exist_ok=True)


def build_research_report(post_or_result: dict, execution_context: dict = None) -> dict:
    now_utc = datetime.now(timezone.utc).isoformat()
    ctx = execution_context or {}

    is_skipped = post_or_result.get("skipped", False)
    post = post_or_result.get("post") or post_or_result

    engine_name = post.get("engine") or ctx.get("engine", "autonomous_radar")
    origin = (
        "Content Bank Fallback"
        if "fallback" in str(engine_name) or "content_bank" in str(engine_name)
        else "Live Autonomous Research"
    )

    source_info = post.get("source") if isinstance(post.get("source"), dict) else {}

    report = {
        "report_id": f"rep_{int(time.time())}",
        "timestamp": now_utc,
        "status": "skipped" if is_skipped else "published",
        "origin": origin,
        "topic": post.get("title", "N/A"),
        "track": post.get("track", "Systems Engineering"),
        "engine": engine_name,
        "source": {
            "title": source_info.get("title") or post.get("source_headline"),
            "url": source_info.get("url") or post.get("source_url"),
            "domain": source_info.get("domain"),
            "source_count": post.get("source_count", 1),
        },
        "scraping": {
            "success": not is_skipped,
            "method": source_info.get("engine", "Firecrawl / HTTP Direct"),
        },
        "llm_generation": {
            "status": "success" if not is_skipped else "skipped",
            "model": os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
        },
        "publishing": {
            "telegram": ctx.get("telegram", True),
            "git": ctx.get("git", True),
            "instagram": ctx.get("instagram", False),
        },
        "skipped_reason": post_or_result.get("skipped_reason"),
        "error": post_or_result.get("error"),
    }
    return report


def send_report_to_bridge(report: dict) -> dict:
    """
    Attempts delivery to Cosmitude Bridge. If unavailable, queues locally.
    """
    ensure_queue_dir()

    # Save individual archive copy
    report_file = os.path.join(QUEUE_DIR, f"{report['report_id']}.json")
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"[Bridge-Reporter] Could not write report file: {e}")

    # Format human-readable summary message for Cosmitude Forum flow
    msg_lines = [
        f"BitBytes Research Report [{report['report_id']}]",
        f"Status: {report['status'].upper()}",
        f"Origin: {report['origin']}",
        f"Topic: {report['topic']} ({report['track']})",
    ]
    if report.get("source", {}).get("title"):
        msg_lines.append(f"Source: {report['source']['title']} ({report['source']['url']})")
    if report.get("skipped_reason"):
        msg_lines.append(f"Notice: {report['skipped_reason']}")

    message = "\n".join(msg_lines)

    # Attempt sending via Bot.py
    bridge_success = False
    bridge_result = None
    try:
        import Bot
        if getattr(Bot, "Sessionid", None):
            res = Bot.sendUserRequestBridge("BitBytesData_CompletionTracking", message)
            if res.get("success"):
                bridge_success = True
                bridge_result = res
                print(f"[Bridge-Reporter] Report successfully delivered to Cosmitude Bridge (ID: {res.get('bridgeId')})")
    except Exception as exc:
        print(f"[Bridge-Reporter] Bridge unavailable ({exc}). Queuing for retry.")

    if not bridge_success:
        # Enqueue for durable retry
        try:
            pending = []
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r", encoding="utf-8") as qf:
                    pending = json.load(qf)
            pending.append(report)
            with open(QUEUE_FILE, "w", encoding="utf-8") as qf:
                json.dump(pending, qf, indent=2)
            print(f"[Bridge-Reporter] Report safely queued locally ({len(pending)} pending in queue).")
        except Exception as e:
            print(f"[Bridge-Reporter] Queue error: {e}")

    return {
        "delivered": bridge_success,
        "bridge_result": bridge_result,
        "queued": not bridge_success,
        "report": report,
    }


def flush_pending_reports():
    """Flushes locally queued reports if Bridge session is active."""
    if not os.path.exists(QUEUE_FILE):
        return 0

    try:
        import Bot
        if not getattr(Bot, "Sessionid", None):
            return 0
    except Exception:
        return 0

    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as qf:
            pending = json.load(qf)
        if not pending:
            return 0

        flushed = []
        for rep in pending:
            msg = f"Flushed Report [{rep['report_id']}]: {rep['topic']} - Status: {rep['status']}"
            res = Bot.sendUserRequestBridge("BitBytesData_CompletionTracking", msg)
            if not res.get("success"):
                break
            flushed.append(rep)

        remaining = pending[len(flushed):]
        with open(QUEUE_FILE, "w", encoding="utf-8") as qf:
            json.dump(remaining, qf, indent=2)

        return len(flushed)
    except Exception as e:
        print(f"[Bridge-Reporter] Error flushing reports: {e}")
        return 0
