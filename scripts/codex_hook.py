#!/usr/bin/env python3
"""Content-blind Codex UserPromptSubmit adapter for Gentle Break Reminder."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from typing import Any

from activity_engine import Decision, record_activity


def inline_output(decision: Decision) -> dict[str, Any]:
    """Legacy channel alias that now emits a one-shot conversation message."""

    return system_message_output(decision)


def system_message_output(decision: Decision) -> dict[str, Any]:
    return {"systemMessage": decision.reminder_text}


def send_desktop_notification(text: str) -> bool:
    if platform.system() != "Darwin" or not os.path.exists("/usr/bin/osascript"):
        return False
    script = (
        "on run argv\n"
        "display notification (item 1 of argv) with title (item 2 of argv)\n"
        "end run"
    )
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script, text, "休息一下"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def delivery_output(decision: Decision) -> dict[str, Any] | None:
    if decision.channel == "inline":
        return inline_output(decision)
    if decision.channel == "system-message":
        return system_message_output(decision)
    if decision.channel == "desktop":
        if send_desktop_notification(decision.reminder_text):
            return None
        return system_message_output(decision)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "UserPromptSubmit":
            return 0
        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return 0

        # Intentionally do not read payload["prompt"] or payload["transcript_path"].
        decision = record_activity(session_id)
        if not decision.due:
            return 0
        output = delivery_output(decision)
        if output is not None:
            print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as error:
        if os.environ.get("GENTLE_BREAK_DEBUG") == "1":
            print(f"gentle-break-reminder: {error}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
