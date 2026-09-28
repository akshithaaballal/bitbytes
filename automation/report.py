"""
BitBytes RunReport Data Structure.
Captures end-to-end execution telemetry for each pipeline execution,
including discovery tiers, candidates, scraping attempts, curation results,
channel delivery statuses, and sanitized error traces.
"""

import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


def sanitize_secrets(text: str) -> str:
    """Removes API keys, tokens, and credentials from text strings."""
    if not text:
        return ""
    # Google API keys
    text = re.sub(r'AIza[0-9A-Za-z-_]{30,40}', '[REDACTED_API_KEY]', text)
    # Generic bearer tokens / secrets
    text = re.sub(r'(?:bearer|token|secret|password|key)[:=]\s*["\']?[0-9a-zA-Z\-_=]{12,}["\']?', '[REDACTED_CREDENTIAL]', text, flags=re.IGNORECASE)
    return text


@dataclass
class RunReport:
    run_id: str = field(default_factory=lambda: f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    trigger: str = "console"  # schedule | console | manual
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: str = ""
    stages: List[Dict[str, Any]] = field(default_factory=list)
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    chosen: Dict[str, Any] = field(default_factory=dict)
    fallback: Dict[str, Any] = field(default_factory=lambda: {"used": False, "reason": None})
    delivery: Dict[str, bool] = field(default_factory=lambda: {"telegram": False, "git": False})
    outcome: str = "pending"  # published | fallback_published | skipped | failed
    errors: List[str] = field(default_factory=list)

    def add_stage(self, name: str, status: str = "ok", ms: int = 0, detail: str = ""):
        self.stages.append({
            "name": name,
            "status": status,
            "ms": ms,
            "detail": sanitize_secrets(detail)
        })

    def add_error(self, error_message: str):
        clean_msg = sanitize_secrets(str(error_message))
        if clean_msg and clean_msg not in self.errors:
            self.errors.append(clean_msg)

    def finish(self, outcome: str):
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.outcome = outcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "trigger": self.trigger,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "stages": self.stages,
            "attempts": self.attempts,
            "chosen": self.chosen,
            "fallback": self.fallback,
            "delivery": self.delivery,
            "outcome": self.outcome,
            "errors": self.errors
        }
