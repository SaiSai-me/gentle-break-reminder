# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added

- GitHub-backed `saisai-plugins` repo Marketplace for direct Codex installation.
- A complete Chinese installation guide with CLI, desktop, ZIP, verification, update, uninstall, security review, and troubleshooting instructions.

### Changed

- Added a concise Marketplace installation path and explicit post-install verification steps to the README.

## [0.1.2] - 2026-08-12

### Added

- Public release metadata, MIT license, privacy policy, terms, security policy, and contribution guide.
- OpenAI plugin submission checklist and reviewer-ready positive and negative test cases.
- GitHub Actions test workflow.

### Changed

- Clarified that the local Hook deserializes the submitted event but does not inspect, analyze, transmit, or persist prompt text and never opens transcripts.
- Normalized the public release version to `0.1.2` without a local Codex cache-buster suffix.

### Verified

- Sustained-activity and conversation-burst detection.
- Cooldown, daily limits, idle reset, and cross-session behavior.
- Custom configuration and notification fallback.
- Hashed session identifiers and absence of prompt or transcript data in persisted state.
