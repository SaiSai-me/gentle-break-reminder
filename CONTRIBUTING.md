# Contributing

Contributions to Gentle Break Reminder are welcome. Please keep changes small, testable, and consistent with the plugin's privacy-first design.

## Development setup

Requirements:

- Python 3.10 or later
- a Codex environment that supports plugin Hooks for end-to-end testing

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

Run a syntax check:

```bash
python3 -m py_compile scripts/*.py tests/*.py
```

## Privacy invariants

Changes must preserve these boundaries unless a future major version explicitly discloses and obtains user consent for a different design:

- Do not inspect, analyze, log, transmit, or persist prompt text.
- Do not open or store conversation transcripts or transcript paths.
- Do not store raw session identifiers.
- Do not add network calls or external analytics.
- Do not infer fatigue, hydration, health, or emotion from conversation content.
- Do not deliver desktop notifications or change their channel without explicit user intent.

Add or update tests whenever behavior changes. Privacy-sensitive changes should include a test demonstrating that sentinel prompt and transcript values are absent from output and persisted state.

## Pull requests

Describe what changed, why it changed, user-visible impact, and the checks you ran. Keep unrelated changes in separate pull requests. By contributing, you agree that your contribution is licensed under the repository's MIT License.
