#!/usr/bin/env python3
"""Configuration CLI for Gentle Break Reminder."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from activity_engine import Config, default_data_dir, reset_all, reset_state, status, update_config
from codex_hook import send_desktop_notification


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure private, activity-aware break reminders.")
    parser.add_argument("--data-dir", type=Path, help="Override the local data directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("enable")
    subparsers.add_parser("disable")
    subparsers.add_parser("reset-state")
    subparsers.add_parser("reset-all")

    channel = subparsers.add_parser("set-channel")
    channel.add_argument("channel", choices=["inline", "system-message", "desktop"])

    text = subparsers.add_parser("set-text")
    text.add_argument("text")

    thresholds = subparsers.add_parser("set-thresholds")
    thresholds.add_argument("--duration-minutes", type=int)
    thresholds.add_argument("--duration-messages", type=int)
    thresholds.add_argument("--burst-window-minutes", type=int)
    thresholds.add_argument("--burst-messages", type=int)
    thresholds.add_argument("--continuity-gap-minutes", type=int)
    thresholds.add_argument("--idle-reset-minutes", type=int)
    thresholds.add_argument("--cooldown-minutes", type=int)
    thresholds.add_argument("--daily-limit", type=int)

    test = subparsers.add_parser("test")
    test.add_argument("--deliver", action="store_true", help="Deliver only when the configured channel is desktop.")
    return parser


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    args = _parser().parse_args()
    data_dir = args.data_dir or default_data_dir()

    if args.command == "status":
        _print(status(data_dir))
        return 0
    if args.command == "enable":
        _print(asdict(update_config({"enabled": True}, data_dir)))
        return 0
    if args.command == "disable":
        config = update_config({"enabled": False}, data_dir)
        reset_state(data_dir)
        _print(asdict(config))
        return 0
    if args.command == "reset-state":
        reset_state(data_dir)
        _print({"reset": "state", "data_dir": str(data_dir)})
        return 0
    if args.command == "reset-all":
        _print(asdict(reset_all(data_dir)))
        return 0
    if args.command == "set-channel":
        _print(asdict(update_config({"channel": args.channel}, data_dir)))
        return 0
    if args.command == "set-text":
        _print(asdict(update_config({"reminder_text": args.text}, data_dir)))
        return 0
    if args.command == "set-thresholds":
        names = (
            "duration_minutes",
            "duration_messages",
            "burst_window_minutes",
            "burst_messages",
            "continuity_gap_minutes",
            "idle_reset_minutes",
            "cooldown_minutes",
            "daily_limit",
        )
        changes = {name: getattr(args, name) for name in names if getattr(args, name) is not None}
        if not changes:
            raise SystemExit("set-thresholds requires at least one threshold option")
        _print(asdict(update_config(changes, data_dir)))
        return 0
    if args.command == "test":
        config = Config.from_mapping(status(data_dir)["config"])
        delivered = False
        if args.deliver:
            if config.channel != "desktop":
                raise SystemExit("--deliver is only available when channel is desktop")
            delivered = send_desktop_notification(config.reminder_text)
        _print({"channel": config.channel, "reminder_text": config.reminder_text, "delivered": delivered})
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
