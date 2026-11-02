"""
BitBytes Cosmitude Bridge Telemetry & Research Reporter.
Formats execution and research reports, sends them to Cosmitude Bridge via agent/Bot.py,
and provides a durable local retry queue when the Bridge is offline.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# Path to local durable queue
QUEUE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bridge_queue.json")


def _load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_queue(queue):
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)
    except Exception as e:
        print(f"[Bridge-Reporter] Warning: Could not save queue: {e}")


def _get_bot():
    """Dynamically import Bot from agent/ directory."""
    try:
        agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import Bot
        return Bot
    except Exception as e:
        return None


def send_bridge_report(report: dict) -> dict:
    """
    Attempts delivery to Cosmitude Bridge.
    If unavailable, persists report to local durable queue for retry.
    """
    report["timestamp"] = report.get("timestamp") or datetime.now(timezone.utc).isoformat()
    
    # 1. Format payload
    summary_line = f"[{report.get('status', 'RUN').upper()}] {report.get('topic') or report.get('title') or 'Research Run'}"
    formatted_msg = (
        f"BitBytes Research Report\n"
        f"• Timestamp: {report['timestamp']}\n"
        f"• Status: {report.get('status', 'unknown')}\n"
        f"• Topic: {report.get('topic') or report.get('title') or 'N/A'}\n"
        f"• Engine: {report.get('engine', 'autonomous_radar')}\n"
        f"• Source: {report.get('source_url', 'N/A')}\n"
        f"• Source Count: {report.get('source_count', 1)}\n"
        f"• Telegram: {report.get('telegram_status', 'pending')}\n"
        f"• Git Archive: {report.get('git_status', 'pending')}\n"
        f"• Instagram: {report.get('instagram_status', 'pending')}\n"
    )
    if report.get("skipped_reason"):
        formatted_msg += f"• Skipped Reason: {report['skipped_reason']}\n"
    if report.get("summary"):
        formatted_msg += f"• Summary: {report['summary'][:200]}...\n"

    # 2. Try sending via Bot
    bot = _get_bot()
    delivered = False
    bridge_id = None
    delivery_error = None

    if bot and hasattr(bot, "sendUserRequestBridge"):
        try:
            res = bot.sendUserRequestBridge("BitBytesData_DataProcessing", formatted_msg)
            if res.get("success"):
                delivered = True
                bridge_id = res.get("bridgeId")
                print(f"[Bridge-Reporter] Report successfully delivered to Cosmitude Bridge (ID: {bridge_id})")
            else:
                delivery_error = res.get("error", "Unknown error from Bridge")
        except Exception as exc:
            delivery_error = str(exc)
    else:
        delivery_error = "Cosmitude Bot agent not initialized or credentials missing"

    # 3. If delivered, flush any older queued reports
    if delivered:
        queue = _load_queue()
        if queue:
            print(f"[Bridge-Reporter] Flushing {len(queue)} pending reports from local queue...")
            remaining = []
            for item in queue:
                try:
                    q_res = bot.sendUserRequestBridge("BitBytesData_DataProcessing", item.get("message", ""))
                    if not q_res.get("success"):
                        remaining.append(item)
                except Exception:
                    remaining.append(item)
            _save_queue(remaining)
        return {
            "delivered": True,
            "bridgeId": bridge_id,
            "queued": False
        }

    # 4. If delivery failed, queue locally
    queue = _load_queue()
    queue.append({
        "timestamp": report["timestamp"],
        "report": report,
        "message": formatted_msg,
        "failed_reason": delivery_error
    })
    # Keep queue bounded to last 100 items
    if len(queue) > 100:
        queue = queue[-100:]
    _save_queue(queue)
    print(f"[Bridge-Reporter] Bridge unavailable ({delivery_error}). Report safely queued locally ({len(queue)} pending).")

    return {
        "delivered": False,
        "queued": True,
        "reason": delivery_error,
        "pending_count": len(queue)
    }
