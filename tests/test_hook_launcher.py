from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from hook_launcher import latest_scripts_dir, sync_runtime  # noqa: E402


class HookLauncherTests(unittest.TestCase):
    def test_sync_runtime_survives_deleted_plugin_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            cache_scripts = (
                temporary
                / "cache"
                / "personal"
                / "gentle-break-reminder"
                / "0.1.3+codex.test"
                / "scripts"
            )
            cache_scripts.mkdir(parents=True)
            for name in ("activity_engine.py", "codex_hook.py", "hook_launcher.py"):
                (cache_scripts / name).write_text((SCRIPTS / name).read_text(), encoding="utf-8")

            data_dir = temporary / "persistent-data"
            runtime_hook = sync_runtime(cache_scripts, data_dir)
            self.assertTrue(runtime_hook.is_file())
            self.assertTrue((data_dir / "runtime" / "activity_engine.py").is_file())
            self.assertTrue((data_dir / "hook_launcher.py").is_file())

            for path in cache_scripts.iterdir():
                path.unlink()
            cache_scripts.rmdir()

            self.assertTrue(runtime_hook.is_file())
            self.assertIn("UserPromptSubmit", runtime_hook.read_text(encoding="utf-8"))

    def test_latest_scripts_dir_ignores_incomplete_and_prefers_newest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            cache_root = Path(temporary_name)
            older = cache_root / "personal" / "gentle-break-reminder" / "0.1.2" / "scripts"
            newer = cache_root / "personal" / "gentle-break-reminder" / "0.1.3" / "scripts"
            incomplete = cache_root / "other" / "gentle-break-reminder" / "9.9.9" / "scripts"
            for directory in (older, newer, incomplete):
                directory.mkdir(parents=True)
            for directory in (older, newer):
                for name in ("activity_engine.py", "codex_hook.py", "hook_launcher.py"):
                    (directory / name).write_text(name, encoding="utf-8")
            (incomplete / "hook_launcher.py").write_text("incomplete", encoding="utf-8")
            for path in older.iterdir():
                path.touch()
            for path in newer.iterdir():
                path.touch()
            older.touch()
            newer.touch()

            self.assertEqual(latest_scripts_dir(cache_root), newer)


if __name__ == "__main__":
    unittest.main()
