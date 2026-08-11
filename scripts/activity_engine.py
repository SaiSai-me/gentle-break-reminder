#!/usr/bin/env python3
"""Deterministic conversation-activity tracking with no content processing."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Mapping


PLUGIN_NAME = "gentle-break-reminder"
VALID_CHANNELS = {"inline", "system-message", "desktop"}
DEFAULT_REMINDER_TEXT = "⏸️ 轻轻休息一下：喝口水、看看远处或活动肩颈，再舒服地继续吧。"


@dataclass(frozen=True)
class Config:
    enabled: bool = True
    channel: str = "system-message"
    duration_minutes: int = 45
    duration_messages: int = 5
    burst_window_minutes: int = 30
    burst_messages: int = 10
    continuity_gap_minutes: int = 15
    idle_reset_minutes: int = 20
    cooldown_minutes: int = 60
    daily_limit: int = 3
    reminder_text: str = DEFAULT_REMINDER_TEXT

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Config":
        defaults = asdict(cls())
        merged = {**defaults, **dict(values)}
        config = cls(**{key: merged[key] for key in defaults})
        config.validate()
        return config

    def validate(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean")
        if self.channel not in VALID_CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(sorted(VALID_CHANNELS))}")
        integer_fields = (
            "duration_minutes",
            "duration_messages",
            "burst_window_minutes",
            "burst_messages",
            "continuity_gap_minutes",
            "idle_reset_minutes",
            "cooldown_minutes",
            "daily_limit",
        )
        for field_name in integer_fields:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
        if self.continuity_gap_minutes >= self.idle_reset_minutes:
            raise ValueError("continuity_gap_minutes must be smaller than idle_reset_minutes")
        if not isinstance(self.reminder_text, str) or not self.reminder_text.strip():
            raise ValueError("reminder_text must be a non-empty string")
        if len(self.reminder_text) > 240:
            raise ValueError("reminder_text must be 240 characters or fewer")


@dataclass(frozen=True)
class Decision:
    due: bool
    reason: str | None = None
    active_minutes: int = 0
    active_message_count: int = 0
    messages_in_window: int = 0
    channel: str = "inline"
    reminder_text: str = DEFAULT_REMINDER_TEXT


def default_data_dir() -> Path:
    override = os.environ.get("GENTLE_BREAK_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / PLUGIN_NAME
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / PLUGIN_NAME
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home).expanduser() / PLUGIN_NAME
    return Path.home() / ".local" / "state" / PLUGIN_NAME


def _config_path(data_dir: Path) -> Path:
    return data_dir / "config.json"


def _state_path(data_dir: Path) -> Path:
    return data_dir / "state.json"


def _read_json(path: Path, default: Mapping[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        try:
            os.chmod(temporary_name, 0o600)
        except OSError:
            pass
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


@contextmanager
def _storage_lock(data_dir: Path) -> Iterator[None]:
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = data_dir / ".lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            import fcntl  # type: ignore[import-not-found]

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            fcntl = None  # type: ignore[assignment]
        try:
            yield
        finally:
            if fcntl is not None:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass


def load_config(data_dir: Path | None = None) -> Config:
    selected_dir = data_dir or default_data_dir()
    return Config.from_mapping(_read_json(_config_path(selected_dir), {}))


def save_config(config: Config, data_dir: Path | None = None) -> None:
    config.validate()
    selected_dir = data_dir or default_data_dir()
    with _storage_lock(selected_dir):
        _write_json(_config_path(selected_dir), asdict(config))


def update_config(changes: Mapping[str, Any], data_dir: Path | None = None) -> Config:
    selected_dir = data_dir or default_data_dir()
    with _storage_lock(selected_dir):
        current = Config.from_mapping(_read_json(_config_path(selected_dir), {}))
        updated = Config.from_mapping({**asdict(current), **dict(changes)})
        _write_json(_config_path(selected_dir), asdict(updated))
    return updated


def _empty_state() -> dict[str, Any]:
    return {
        "version": 2,
        "sessions": {},
        "global": {"last_reminder_at": None},
        "daily": {"date": None, "count": 0},
    }


def _migrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """Normalize persisted state and migrate per-session cooldowns to one global cooldown."""

    is_legacy_state = state.get("version") != 2
    sessions = state.get("sessions")
    if not isinstance(sessions, dict):
        sessions = {}
        state["sessions"] = sessions

    global_state = state.get("global")
    if not isinstance(global_state, dict):
        global_state = {}

    last_reminder_at = _parse_time(global_state.get("last_reminder_at"))
    latest_activity_at: datetime | None = None
    for session in sessions.values():
        if not isinstance(session, dict):
            continue
        session_last_activity_at = _parse_time(session.get("last_activity_at"))
        if session_last_activity_at is not None and (
            latest_activity_at is None or session_last_activity_at > latest_activity_at
        ):
            latest_activity_at = session_last_activity_at
        legacy_last_reminder_at = _parse_time(session.pop("last_reminder_at", None))
        if legacy_last_reminder_at is not None and (
            last_reminder_at is None or legacy_last_reminder_at > last_reminder_at
        ):
            last_reminder_at = legacy_last_reminder_at

    daily = state.get("daily")
    legacy_daily_count = daily.get("count", 0) if isinstance(daily, dict) else 0
    if (
        is_legacy_state
        and last_reminder_at is None
        and isinstance(legacy_daily_count, int)
        and not isinstance(legacy_daily_count, bool)
        and legacy_daily_count > 0
    ):
        last_reminder_at = latest_activity_at

    state["version"] = 2
    state["global"] = {
        "last_reminder_at": _iso(last_reminder_at) if last_reminder_at else None,
    }
    return state


def load_state(data_dir: Path | None = None) -> dict[str, Any]:
    selected_dir = data_dir or default_data_dir()
    return _read_json(_state_path(selected_dir), _empty_state())


def reset_state(data_dir: Path | None = None) -> None:
    selected_dir = data_dir or default_data_dir()
    with _storage_lock(selected_dir):
        _write_json(_state_path(selected_dir), _empty_state())


def reset_all(data_dir: Path | None = None) -> Config:
    selected_dir = data_dir or default_data_dir()
    config = Config()
    with _storage_lock(selected_dir):
        _write_json(_config_path(selected_dir), asdict(config))
        _write_json(_state_path(selected_dir), _empty_state())
    return config


def _normalized_time(value: datetime | None) -> datetime:
    selected = value or datetime.now().astimezone()
    return selected.astimezone() if selected.tzinfo is None else selected


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.astimezone()


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _session_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]


def _clean_old_sessions(sessions: dict[str, Any], now: datetime) -> None:
    cutoff = now - timedelta(days=7)
    expired = []
    for key, value in sessions.items():
        last_activity = _parse_time(value.get("last_activity_at")) if isinstance(value, dict) else None
        if last_activity is None or last_activity < cutoff:
            expired.append(key)
    for key in expired:
        sessions.pop(key, None)


def record_activity(
    session_id: str,
    *,
    now: datetime | None = None,
    data_dir: Path | None = None,
) -> Decision:
    """Record one prompt-submit event and return a deterministic break decision."""

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be a non-empty string")

    selected_dir = data_dir or default_data_dir()
    event_time = _normalized_time(now)

    with _storage_lock(selected_dir):
        config = Config.from_mapping(_read_json(_config_path(selected_dir), {}))
        if not config.enabled:
            return Decision(due=False, channel=config.channel, reminder_text=config.reminder_text)

        state = _migrate_state(_read_json(_state_path(selected_dir), _empty_state()))
        sessions = state.setdefault("sessions", {})
        if not isinstance(sessions, dict):
            sessions = {}
            state["sessions"] = sessions
        _clean_old_sessions(sessions, event_time)

        daily = state.setdefault("daily", {"date": None, "count": 0})
        if not isinstance(daily, dict):
            daily = {"date": None, "count": 0}
            state["daily"] = daily
        current_date = event_time.date().isoformat()
        if daily.get("date") != current_date:
            daily.update({"date": current_date, "count": 0})

        key = _session_key(session_id)
        session = sessions.get(key)
        if not isinstance(session, dict):
            session = {}

        last_activity = _parse_time(session.get("last_activity_at"))
        gap_seconds = (event_time - last_activity).total_seconds() if last_activity else None
        reset_streak = gap_seconds is None or gap_seconds < 0 or gap_seconds >= config.idle_reset_minutes * 60

        if reset_streak:
            active_seconds = 0
            active_message_count = 1
            recent_activity: list[str] = []
        else:
            active_seconds = max(0, int(session.get("active_seconds", 0)))
            if gap_seconds <= config.continuity_gap_minutes * 60:
                active_seconds += int(gap_seconds)
            active_message_count = max(0, int(session.get("active_message_count", 0))) + 1
            recent_activity = [item for item in session.get("recent_activity", []) if isinstance(item, str)]

        window_start = event_time - timedelta(minutes=config.burst_window_minutes)
        recent_times = [
            parsed
            for item in recent_activity
            if (parsed := _parse_time(item)) is not None and parsed >= window_start
        ]
        recent_times.append(event_time)
        messages_in_window = len(recent_times)

        duration_due = active_seconds >= config.duration_minutes * 60 and active_message_count >= config.duration_messages
        burst_due = messages_in_window >= config.burst_messages
        global_state = state["global"]
        last_reminder_at = _parse_time(global_state.get("last_reminder_at"))
        cooldown_ready = last_reminder_at is None or event_time - last_reminder_at >= timedelta(minutes=config.cooldown_minutes)
        daily_count = max(0, int(daily.get("count", 0)))
        daily_ready = daily_count < config.daily_limit

        reason: str | None = None
        if duration_due:
            reason = "active-duration"
        elif burst_due:
            reason = "message-burst"
        due = reason is not None and cooldown_ready and daily_ready

        if due:
            last_reminder_at = event_time
            global_state["last_reminder_at"] = _iso(event_time)
            daily["count"] = daily_count + 1

        sessions[key] = {
            "last_activity_at": _iso(event_time),
            "active_seconds": active_seconds,
            "active_message_count": active_message_count,
            "recent_activity": [_iso(item) for item in recent_times],
        }
        _write_json(_state_path(selected_dir), state)

    return Decision(
        due=due,
        reason=reason if due else None,
        active_minutes=active_seconds // 60,
        active_message_count=active_message_count,
        messages_in_window=messages_in_window,
        channel=config.channel,
        reminder_text=config.reminder_text,
    )


def status(data_dir: Path | None = None) -> dict[str, Any]:
    selected_dir = data_dir or default_data_dir()
    with _storage_lock(selected_dir):
        config = Config.from_mapping(_read_json(_config_path(selected_dir), {}))
        state = _migrate_state(_read_json(_state_path(selected_dir), _empty_state()))
    sessions = state.get("sessions", {})
    global_state = state.get("global", {})
    daily = state.get("daily", {})
    return {
        "data_dir": str(selected_dir),
        "config": asdict(config),
        "state": {
            "tracked_sessions": len(sessions) if isinstance(sessions, dict) else 0,
            "last_reminder_at": global_state.get("last_reminder_at") if isinstance(global_state, dict) else None,
            "daily_date": daily.get("date") if isinstance(daily, dict) else None,
            "reminders_today": daily.get("count", 0) if isinstance(daily, dict) else 0,
        },
        "privacy": {
            "stores_prompt_text": False,
            "reads_transcript": False,
            "uses_semantic_inference": False,
            "session_ids_hashed": True,
        },
    }
