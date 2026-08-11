# Privacy Policy

Effective date: August 12, 2026

Gentle Break Reminder is a local, activity-aware reminder plugin for Codex. This policy explains what the plugin processes, what it stores, and what it does not do.

## Summary

The plugin uses local prompt-submit event timing and counts to decide whether a configured break reminder is due. It does not use an external service, send activity data over the network, analyze conversation meaning, or open conversation transcript files.

## Event processing

Codex supplies the local Hook process with a `UserPromptSubmit` JSON event. That event may contain fields such as the submitted prompt and a transcript path. The Hook deserializes the event locally, then its application logic reads only:

- `hook_event_name`, to confirm the event type; and
- `session_id`, to associate activity events with a session.

The implementation does not query, analyze, log, return, or persist the `prompt` field. It does not access `transcript_path` or open the referenced transcript. Because the full event is deserialized before fields are selected, prompt text present in the event may exist transiently in the Hook process memory and is discarded when the process exits.

## Data stored locally

The plugin stores only the information needed for deterministic reminder rules:

- a truncated SHA-256 hash of the session identifier;
- local prompt-submit timestamps and message counts;
- an estimated active duration derived from eligible gaps between events;
- the last reminder time and the number of reminders sent that day; and
- configuration explicitly changed by the user, such as reminder text and thresholds.

Raw session identifiers are not stored. Hashing is a data-minimization measure and should not be treated as complete anonymization.

## Data not collected or stored

The plugin does not collect or store:

- submitted prompt text;
- Agent response text;
- transcript content or transcript paths;
- project source code, filenames, or file contents;
- keyboard, mouse, camera, microphone, or screen data;
- health, fatigue, emotion, or hydration inferences;
- account credentials, API keys, or advertising identifiers.

## Network access and sharing

The plugin makes no network requests and does not send activity or configuration data to the developer or any third party. When the user explicitly selects desktop notifications on macOS, the plugin invokes the local `/usr/bin/osascript` executable; this does not change the plugin's data-sharing behavior.

## Storage location and retention

Configuration and state are stored in the operating system's local application-data directory:

- macOS: `~/Library/Application Support/gentle-break-reminder`
- Windows: `%LOCALAPPDATA%/gentle-break-reminder`
- Linux: `$XDG_STATE_HOME/gentle-break-reminder`, or `~/.local/state/gentle-break-reminder`

Inactive session entries are automatically removed after seven days. User configuration remains until it is reset, removed, or the local data directory is deleted.

Users can clear activity state with `reset-state`, or restore defaults and clear state with `reset-all`, through the plugin's configuration workflow.

## Children

The plugin is a general productivity utility and is not designed to collect personal information from children. It does not create user accounts or transmit data to the developer.

## Changes

Material changes to this policy will be documented in the repository and release notes. The effective date above will be updated when appropriate.

## Contact

For privacy questions, use the maintainer contact options on the [GitHub profile](https://github.com/SaiSai-me). Do not post sensitive personal information in a public GitHub issue.
