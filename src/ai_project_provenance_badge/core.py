from __future__ import annotations
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

PROJECT = "ai-project-provenance-badge"
REQUIRED_FIELDS = ["project","assistance_level","supervision","tests_passed","evidence_url"]

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)

def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)

def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def render_badge(record: dict[str, Any]) -> str:
    if not _text(record["project"]) or record["assistance_level"] not in {"none", "assisted", "generated"}:
        raise ValueError("project and assistance level are invalid")
    if record["supervision"] not in {"human-reviewed", "human-approved", "independent-review"}:
        raise ValueError("explicit supervision is required")
    if not _integer(record["tests_passed"]) or record["tests_passed"] <= 0:
        raise ValueError("tests_passed must be a positive integer")
    if not isinstance(record["evidence_url"], str) or not record["evidence_url"].startswith("https://"):
        raise ValueError("evidence URL must use HTTPS")
    label = f"AI {record['assistance_level']} | {record['supervision']} | {record['tests_passed']} tests"
    return f"[![{label}](https://img.shields.io/badge/provenance-verified-blue)]({record['evidence_url']})"

def evaluate(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    artifact: Any = None
    if missing:
        status = "blocked"
        reason = "missing required fields: " + ", ".join(missing)
    else:
        try:
            artifact = render_badge(record)
            status = "passed"
            reason = "render_badge completed"
        except (TypeError, ValueError, KeyError) as exc:
            status = "failed"
            reason = str(exc)
    receipt = {"project": PROJECT, "status": status, "reason": reason, "record": record, "badge_markdown": artifact}
    receipt["evidence_sha256"] = sha256(_canonical(receipt).encode()).hexdigest()
    return receipt

