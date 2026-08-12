#!/usr/bin/env python3
"""Stable launcher for the Gentle Break Reminder Codex hook.

Codex may replace versioned plugin-cache directories while the app is running.
This launcher mirrors the executable hook into the plugin's persistent data
directory, so a command registered before a cache refresh never depends on a
deleted cache path.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterable


PLUGIN_NAME = "gentle-break-reminder"
RUNTIME_FILES = ("activity_engine.py", "codex_hook.py")


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


def default_cache_root() -> Path:
    override = os.environ.get("GENTLE_BREAK_PLUGIN_CACHE")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".codex" / "plugins" / "cache"


def _is_complete_scripts_dir(path: Path) -> bool:
    return all((path / name).is_file() for name in (*RUNTIME_FILES, "hook_launcher.py"))


def candidate_script_dirs(cache_root: Path) -> Iterable[Path]:
    if not cache_root.is_dir():
        return ()
    return (
        path.parent
        for path in cache_root.glob(f"*/{PLUGIN_NAME}/*/scripts/hook_launcher.py")
        if _is_complete_scripts_dir(path.parent)
    )


def latest_scripts_dir(cache_root: Path) -> Path | None:
    candidates = list(candidate_script_dirs(cache_root))
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime_ns, str(path)))


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_copy(source: Path, destination: Path) -> None:
    if destination.is_file() and _digest(source) == _digest(destination):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        try:
            temporary.chmod(0o700)
        except OSError:
            pass
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def sync_runtime(source_scripts: Path, data_dir: Path) -> Path:
    """Atomically mirror a complete plugin hook into persistent storage."""

    if not _is_complete_scripts_dir(source_scripts):
        raise FileNotFoundError(f"incomplete hook scripts directory: {source_scripts}")
    _atomic_copy(source_scripts / "hook_launcher.py", data_dir / "hook_launcher.py")
    runtime_dir = data_dir / "runtime"
    for name in RUNTIME_FILES:
        _atomic_copy(source_scripts / name, runtime_dir / name)
    return runtime_dir / "codex_hook.py"


def main() -> int:
    data_dir = default_data_dir()
    runtime_hook = data_dir / "runtime" / "codex_hook.py"

    source_scripts = latest_scripts_dir(default_cache_root())
    if source_scripts is None:
        own_scripts = Path(__file__).resolve().parent
        if _is_complete_scripts_dir(own_scripts):
            source_scripts = own_scripts

    if source_scripts is not None:
        try:
            runtime_hook = sync_runtime(source_scripts, data_dir)
        except OSError:
            # A previously mirrored runtime remains a safe fallback.
            pass

    if not runtime_hook.is_file():
        return 0
    os.execv(sys.executable, [sys.executable, str(runtime_hook)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
