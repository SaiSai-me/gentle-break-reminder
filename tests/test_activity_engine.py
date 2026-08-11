from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from activity_engine import DEFAULT_REMINDER_TEXT, Config, Decision, load_state, record_activity, save_config, status  # noqa: E402
from codex_hook import delivery_output, send_desktop_notification  # noqa: E402


class ActivityEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temporary.name)
        self.start = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def record(self, minute: int, session: str = "session-secret"):
        return record_activity(session, now=self.start + timedelta(minutes=minute), data_dir=self.data_dir)

    def test_default_reminder_text_is_general_and_concise(self) -> None:
        self.assertEqual(
            DEFAULT_REMINDER_TEXT,
            "⏸️ 轻轻休息一下：喝口水、看看远处或活动肩颈，再舒服地继续吧。",
        )
        self.assertLessEqual(len(DEFAULT_REMINDER_TEXT), 240)
        self.assertEqual(Config().channel, "system-message")

    def test_default_duration_rule_triggers_at_five_messages_and_forty_five_minutes(self) -> None:
        for minute in (0, 12, 24, 36):
            self.assertFalse(self.record(minute).due)
        decision = self.record(45)
        self.assertTrue(decision.due)
        self.assertEqual(decision.reason, "active-duration")
        self.assertEqual(decision.active_message_count, 5)
        self.assertEqual(decision.active_minutes, 45)

    def test_burst_rule_triggers_on_tenth_message_in_thirty_minutes(self) -> None:
        decisions = [self.record(minute) for minute in range(0, 20, 2)]
        self.assertFalse(any(item.due for item in decisions[:-1]))
        self.assertTrue(decisions[-1].due)
        self.assertEqual(decisions[-1].reason, "message-burst")

    def test_custom_message_and_frequency_are_used_by_the_hook_decision(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=30,
                burst_messages=2,
                reminder_text="站起来走两分钟，再回来继续。",
            ),
            self.data_dir,
        )
        self.assertFalse(self.record(0).due)
        decision = self.record(1)
        self.assertTrue(decision.due)
        self.assertEqual(decision.reason, "message-burst")
        self.assertEqual(decision.reminder_text, "站起来走两分钟，再回来继续。")

    def test_idle_gap_resets_the_active_streak(self) -> None:
        for minute in (0, 12, 24, 36):
            self.record(minute)
        decision = self.record(56)
        self.assertFalse(decision.due)
        self.assertEqual(decision.active_message_count, 1)
        self.assertEqual(decision.active_minutes, 0)

    def test_ambiguous_gap_is_not_counted_as_active_time(self) -> None:
        self.record(0)
        decision = self.record(18)
        self.assertEqual(decision.active_message_count, 2)
        self.assertEqual(decision.active_minutes, 0)

    def test_cooldown_suppresses_repeated_burst(self) -> None:
        for minute in range(10):
            decision = self.record(minute)
        self.assertTrue(decision.due)
        for minute in range(10, 20):
            self.assertFalse(self.record(minute).due)
        for minute in (29, 39, 49, 59):
            self.assertFalse(self.record(minute).due)
        self.assertTrue(self.record(69).due)

    def test_cooldown_is_global_across_sessions(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=120,
                burst_messages=2,
                cooldown_minutes=60,
                daily_limit=3,
            ),
            self.data_dir,
        )
        self.assertFalse(self.record(0, session="session-a").due)
        self.assertTrue(self.record(1, session="session-a").due)
        self.assertFalse(self.record(2, session="session-b").due)
        self.assertFalse(self.record(3, session="session-b").due)
        self.assertFalse(self.record(60, session="session-b").due)
        self.assertTrue(self.record(61, session="session-b").due)

    def test_idle_reset_does_not_clear_global_cooldown(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=120,
                burst_messages=2,
                cooldown_minutes=60,
            ),
            self.data_dir,
        )
        self.assertFalse(self.record(0).due)
        self.assertTrue(self.record(1).due)
        self.assertFalse(self.record(30).due)
        self.assertFalse(self.record(31).due)

    def test_version_one_state_migrates_latest_reminder_to_global_cooldown(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=120,
                burst_messages=2,
                cooldown_minutes=60,
            ),
            self.data_dir,
        )
        legacy_state = {
            "version": 1,
            "sessions": {
                "legacy-a": {"last_reminder_at": (self.start + timedelta(minutes=10)).isoformat()},
                "legacy-b": {"last_reminder_at": (self.start + timedelta(minutes=20)).isoformat()},
            },
            "daily": {"date": self.start.date().isoformat(), "count": 1},
        }
        (self.data_dir / "state.json").write_text(json.dumps(legacy_state), encoding="utf-8")

        self.assertFalse(self.record(30, session="new-session").due)
        self.assertFalse(self.record(31, session="new-session").due)
        migrated = load_state(self.data_dir)
        self.assertEqual(migrated["version"], 2)
        self.assertEqual(
            migrated["global"]["last_reminder_at"],
            (self.start + timedelta(minutes=20)).isoformat(timespec="seconds"),
        )
        self.assertTrue(
            all("last_reminder_at" not in session for session in migrated["sessions"].values())
        )

    def test_version_one_state_uses_latest_activity_when_reminder_time_was_lost(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=120,
                burst_messages=2,
                cooldown_minutes=60,
            ),
            self.data_dir,
        )
        latest_activity = self.start + timedelta(minutes=20)
        legacy_state = {
            "version": 1,
            "sessions": {
                "legacy": {
                    "last_activity_at": latest_activity.isoformat(),
                    "active_seconds": 0,
                    "active_message_count": 1,
                    "recent_activity": [latest_activity.isoformat()],
                    "last_reminder_at": None,
                },
            },
            "daily": {"date": self.start.date().isoformat(), "count": 1},
        }
        (self.data_dir / "state.json").write_text(json.dumps(legacy_state), encoding="utf-8")

        self.assertFalse(self.record(30, session="new-session").due)
        self.assertFalse(self.record(31, session="new-session").due)
        self.assertEqual(
            load_state(self.data_dir)["global"]["last_reminder_at"],
            latest_activity.isoformat(timespec="seconds"),
        )

    def test_daily_limit_is_enforced(self) -> None:
        save_config(
            Config(
                duration_minutes=999,
                burst_window_minutes=120,
                burst_messages=2,
                cooldown_minutes=1,
                daily_limit=2,
            ),
            self.data_dir,
        )
        self.assertFalse(self.record(0).due)
        self.assertTrue(self.record(1).due)
        self.assertTrue(self.record(2).due)
        self.assertFalse(self.record(3).due)

    def test_disabled_mode_does_not_track_activity(self) -> None:
        save_config(Config(enabled=False), self.data_dir)
        self.assertFalse(self.record(0).due)
        self.assertEqual(status(self.data_dir)["state"]["tracked_sessions"], 0)

    def test_state_hashes_session_id_and_stores_no_prompt(self) -> None:
        self.record(0, session="raw-private-session-id")
        serialized = json.dumps(load_state(self.data_dir))
        self.assertNotIn("raw-private-session-id", serialized)
        self.assertNotIn("prompt", serialized.lower())

    def test_hook_is_silent_until_due_and_never_persists_prompt(self) -> None:
        save_config(
            Config(duration_minutes=999, burst_window_minutes=30, burst_messages=2),
            self.data_dir,
        )
        environment = {**os.environ, "GENTLE_BREAK_DATA_DIR": str(self.data_dir)}
        payload = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "hook-session",
            "prompt": "TOP SECRET PROMPT CONTENT",
            "transcript_path": "/private/transcript.jsonl",
        }
        first = subprocess.run(
            [sys.executable, str(SCRIPTS / "codex_hook.py")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            check=True,
        )
        self.assertEqual(first.stdout, "")
        second = subprocess.run(
            [sys.executable, str(SCRIPTS / "codex_hook.py")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            check=True,
        )
        output = json.loads(second.stdout)
        self.assertEqual(output, {"systemMessage": DEFAULT_REMINDER_TEXT})
        self.assertNotIn("additionalContext", second.stdout)
        persisted = "".join(path.read_text() for path in self.data_dir.glob("*.json"))
        self.assertNotIn("TOP SECRET PROMPT CONTENT", persisted)
        self.assertNotIn("/private/transcript.jsonl", persisted)

    def test_legacy_inline_channel_is_a_one_shot_system_message(self) -> None:
        decision = Decision(
            due=True,
            channel="inline",
            reminder_text="one-shot reminder",
        )
        self.assertEqual(delivery_output(decision), {"systemMessage": "one-shot reminder"})

    @mock.patch("codex_hook.subprocess.run", side_effect=subprocess.TimeoutExpired("osascript", 1))
    @mock.patch("codex_hook.os.path.exists", return_value=True)
    @mock.patch("codex_hook.platform.system", return_value="Darwin")
    def test_desktop_timeout_returns_false_for_system_message_fallback(
        self,
        _system: mock.Mock,
        _exists: mock.Mock,
        _run: mock.Mock,
    ) -> None:
        self.assertFalse(send_desktop_notification("reminder"))


if __name__ == "__main__":
    unittest.main()
