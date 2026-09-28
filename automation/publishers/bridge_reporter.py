"""
BitBytes Cosmitude Bridge Telemetry & Research Reporter.
Formats execution and research telemetry into structured flow records
and sends them to the Cosmitude Bridge forum via agent/Bot.py:
  1. DataProcessing
  2. ProcessingStages (StageName = "Pipeline run")
  3. CompletionTracking
  4. FailureManagement (conditionally on skip, fail, or bank repeat)

Follows strict field-level encoding rules and a 30s total budget to ensure
that Bridge unavailability never blocks or fails the pipeline.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timezone

from report import sanitize_secrets

BRIDGE_ENCODING = {
    "CHECKBOX_TRUE": "1",
    "CHECKBOX_FALSE": "0",
    "PROCESS_TYPE": "AutomatedCuration",
    "SOURCE_SYSTEM": "TechRadar-Pipeline",
    "STAGE_NAME_RUN": "Pipeline run",
    "STAGE_NAME_PUB": "Publishing",
    "STATUS_COMPLETED": "Completed",
    "STATUS_FAILED": "Failed",
    "STATUS_SKIPPED": "Skipped",
    "FINAL_SUCCESS": "Success",
    "FINAL_FAILED": "Failed",
    "FINAL_SKIPPED": "Skipped",
    "VERIFIED": "Verified",
    "UNVERIFIED": "Unverified",
    "INCIDENT_RESOLUTION_OPEN": "Open",
    "SEVERITY_HIGH": "High",
    "SEVERITY_MEDIUM": "Medium",
    "ERROR_SCRAPE_EXHAUSTION": "ScrapeExhaustion",
    "ERROR_GROUNDING_REJECTION": "GroundingRejection",
    "ERROR_PUBLISH_ERROR": "PublishError",
    "ERROR_BANK_WARNING": "BankWarning",
    "TEXTAREA_MAX_CHARS": 1800,
    "ERROR_MSG_MAX_CHARS": 500,
}

QUEUE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bridge_queue.json")


def truncate_textarea(text: str, max_chars: int = 1800) -> str:
    """Caps textarea string before encoding to stay safely within bridge limits."""
    if not text:
        return ""
    text_str = str(text)
    if len(text_str) > max_chars:
        return text_str[:max_chars - 3] + "..."
    return text_str


def _get_bot():
    """Dynamically import Bot from agent/ directory."""
    try:
        agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import Bot
        return Bot
    except Exception as e:
        print(f"[Bridge-Reporter] Could not import Bot: {e}")
        return None


def send_bridge_run_report(
    report,
    bank_repeat_14d: bool = False,
    telegram_link: str = ""
) -> dict:
    """
    Sends structured execution records for a pipeline run to Cosmitude Bridge:
      a. DataProcessing
      b. ProcessingStages
      c. CompletionTracking
      d. FailureManagement (on skip, fail, or bank repeat within 14 days)
    Guaranteed not to block: runs within a 30s total budget. If Cosmitude is down
    or unreachable, logs a warning and returns without failing the pipeline.
    """
    bot = _get_bot()
    if not bot or not hasattr(bot, "send_record"):
        msg = "Cosmitude Bot agent or send_record helper unavailable; skipping bridge telemetry."
        print(f"[Bridge-Reporter] ⚠️ {msg}")
        return {"success": False, "error": msg, "records_sent": []}

    # Normalize report to dict if RunReport dataclass
    if hasattr(report, "to_dict"):
        data = report.to_dict()
    elif isinstance(report, dict):
        data = report
    else:
        data = {}

    attempts = data.get("attempts", [])
    outcome = (data.get("outcome") or "pending").lower()
    fallback = data.get("fallback") or {}
    fallback_used = bool(fallback.get("used", False))
    delivery = data.get("delivery") or {}
    telegram_ok = bool(delivery.get("telegram", False))

    now_iso = datetime.now(timezone.utc).isoformat()
    start_iso = data.get("start_time") or now_iso
    end_iso = data.get("end_time") or now_iso

    # Calculate run duration in ms
    try:
        t0 = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        exec_ms = max(0, int((t1 - t0).total_seconds() * 1000))
    except Exception:
        exec_ms = 0

    epoch = int(time.time())
    rnd = uuid.uuid4().hex[:4]

    data_input_id = f"DP-{epoch}-{rnd}"
    stage_id = f"STG-{epoch}-{rnd}"
    completion_id = f"CMP-{epoch}-{rnd}"
    incident_id = f"INC-{epoch}-{rnd}"

    # Outcome mappings
    if outcome in ("published", "fallback_published", "success"):
        proc_status = BRIDGE_ENCODING["STATUS_COMPLETED"]
        stage_status = BRIDGE_ENCODING["STATUS_COMPLETED"]
        final_status = BRIDGE_ENCODING["FINAL_SUCCESS"]
    elif outcome in ("skipped",):
        proc_status = BRIDGE_ENCODING["STATUS_SKIPPED"]
        stage_status = BRIDGE_ENCODING["STATUS_SKIPPED"]
        final_status = BRIDGE_ENCODING["FINAL_SKIPPED"]
    else:
        proc_status = BRIDGE_ENCODING["STATUS_FAILED"]
        stage_status = BRIDGE_ENCODING["STATUS_FAILED"]
        final_status = BRIDGE_ENCODING["FINAL_FAILED"]

    record_count = len(attempts)
    success_count = 1 if (proc_status == BRIDGE_ENCODING["STATUS_COMPLETED"]) else 0
    rejected_count = sum(1 for a in attempts if a.get("reject_reason"))
    error_count = rejected_count + (1 if proc_status == BRIDGE_ENCODING["STATUS_FAILED"] else 0)

    log_data_raw = json.dumps(attempts)
    log_data = truncate_textarea(sanitize_secrets(log_data_raw), BRIDGE_ENCODING["TEXTAREA_MAX_CHARS"])

    # Verification status
    verification_status = BRIDGE_ENCODING["VERIFIED"] if (telegram_ok and (not fallback_used or not bank_repeat_14d)) else BRIDGE_ENCODING["UNVERIFIED"]

    # Details summary
    chosen = data.get("chosen") or {}
    if fallback_used:
        details_summary = f"Bank fallback: {chosen.get('id', 'unknown')}"
    elif chosen.get("title"):
        details_summary = f"Accepted: {chosen.get('title')[:60]}"
    else:
        details_summary = f"Status: {proc_status}"

    result_summary = telegram_link or (fallback.get("reason") or outcome)

    # 30-second budget enforcement
    deadline = time.time() + 30.0
    records_sent = []
    errors = []

    def call_with_budget(flow_name: str, values: dict):
        if time.time() > deadline:
            print(f"[Bridge-Reporter] ⚠️ Time budget (30s) exceeded; skipping flow {flow_name}")
            return None
        try:
            res = bot.send_record(flow_name, values)
            if res.get("success"):
                records_sent.append({"flow": flow_name, "bridgeId": res.get("bridgeId")})
                return res
            else:
                err = res.get("error") or f"ErrorCode {res.get('errorCode')}"
                errors.append(f"{flow_name}: {err}")
                print(f"[Bridge-Reporter] ⚠️ Bridge send to {flow_name} returned error: {err}")
                return res
        except Exception as exc:
            clean_exc = sanitize_secrets(str(exc))
            errors.append(f"{flow_name}: {clean_exc}")
            print(f"[Bridge-Reporter] ⚠️ Exception sending to {flow_name}: {clean_exc}")
            return None

    # a. DataProcessing
    call_with_budget("DataProcessing", {
        1: data_input_id,
        2: BRIDGE_ENCODING["SOURCE_SYSTEM"],
        3: BRIDGE_ENCODING["PROCESS_TYPE"],
        4: proc_status,
        5: str(record_count),
        6: str(success_count),
        7: str(error_count),
        8: str(exec_ms),
        9: log_data
    })

    # b. ProcessingStages
    call_with_budget("ProcessingStages", {
        1: stage_id,
        2: data_input_id,
        3: "1",
        4: BRIDGE_ENCODING["STAGE_NAME_RUN"],
        5: stage_status,
        6: start_iso,
        7: end_iso,
        8: details_summary
    })

    # c. CompletionTracking
    call_with_budget("CompletionTracking", {
        1: completion_id,
        2: data_input_id,
        3: BRIDGE_ENCODING["PROCESS_TYPE"],
        4: BRIDGE_ENCODING["STAGE_NAME_PUB"],
        5: final_status,
        6: end_iso,
        7: result_summary,
        8: verification_status
    })

    # d. FailureManagement (ONLY on failed/skipped OR bank fallback / 14-day repeat)
    should_send_failure = (
        (proc_status in (BRIDGE_ENCODING["STATUS_FAILED"], BRIDGE_ENCODING["STATUS_SKIPPED"])) or
        (fallback_used and bank_repeat_14d) or
        fallback_used
    )

    if should_send_failure:
        if bank_repeat_14d:
            error_type = BRIDGE_ENCODING["ERROR_BANK_WARNING"]
        elif not telegram_ok and proc_status == BRIDGE_ENCODING["STATUS_FAILED"]:
            error_type = BRIDGE_ENCODING["ERROR_PUBLISH_ERROR"]
        elif any("grounding_rejected" in str(a.get("reject_reason", "")) for a in attempts):
            error_type = BRIDGE_ENCODING["ERROR_GROUNDING_REJECTION"]
        else:
            error_type = BRIDGE_ENCODING["ERROR_SCRAPE_EXHAUSTION"]

        severity = BRIDGE_ENCODING["SEVERITY_HIGH"] if (proc_status == BRIDGE_ENCODING["STATUS_FAILED"]) else BRIDGE_ENCODING["SEVERITY_MEDIUM"]

        raw_err = fallback.get("reason") or (data.get("errors", ["Run failed or fell back"])[0] if data.get("errors") else "Research tiers exhausted")
        clean_err = sanitize_secrets(str(raw_err))[:BRIDGE_ENCODING["ERROR_MSG_MAX_CHARS"]]

        context_data = truncate_textarea(sanitize_secrets(json.dumps({
            "attempts": attempts,
            "fallback": fallback,
            "bank_repeat_14d": bank_repeat_14d
        })), BRIDGE_ENCODING["TEXTAREA_MAX_CHARS"])

        call_with_budget("FailureManagement", {
            1: incident_id,
            2: BRIDGE_ENCODING["SOURCE_SYSTEM"],
            3: error_type,
            4: severity,
            5: clean_err,
            6: BRIDGE_ENCODING["INCIDENT_RESOLUTION_OPEN"],
            7: end_iso,
            8: context_data
        })

    return {
        "success": len(errors) == 0 and len(records_sent) > 0,
        "records_sent": records_sent,
        "errors": errors
    }


def send_bridge_report(report: dict) -> dict:
    """
    Backwards compatibility wrapper for send_bridge_report.
    Delegates to send_bridge_run_report.
    """
    return send_bridge_run_report(report)
