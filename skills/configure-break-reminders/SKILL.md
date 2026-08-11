---
name: configure-break-reminders
description: Configure, enable, disable, test, reset, or inspect Gentle Break Reminder, an activity-aware break reminder inside Codex conversations. Use when the user asks to customize reminder content or frequency, tune sustained-activity or conversation-intensity thresholds, choose a delivery channel, inspect privacy or status, or preview a reminder. Do not use for normal work conversations; the deterministic UserPromptSubmit hook handles runtime reminders without loading this skill.
---

# Configure Break Reminders

Manage the plugin through its CLI. Keep setup minimal: change only the settings the user requests. Do not edit persisted JSON by hand and do not inspect message content or transcripts.

The runtime hook observes prompt-submit events, not conversation meaning. It uses a hashed session identifier plus local timestamps and counts to detect sustained activity or a burst of conversation, then applies cooldown and daily-limit rules before delivering the user's configured message.

## Resolve the CLI

Resolve the plugin root as two directories above this `SKILL.md`, then run:

```bash
python3 <plugin-root>/scripts/reminder_cli.py <command>
```

## Commands

- Show configuration and aggregate state: `status`
- Enable reminders: `enable`
- Disable reminders and clear active streaks: `disable`
- Reset activity state without changing configuration: `reset-state`
- Restore default configuration and clear state: `reset-all`
- Choose one-shot conversation delivery with `set-channel system-message`, or desktop delivery with `set-channel desktop`
- `set-channel inline` remains a backward-compatible alias for the one-shot system message; it no longer injects model context
- Change thresholds: `set-thresholds` with only the requested flags
- Change the one-line reminder to any user-provided break message: `set-text "..."`
- Preview the configured reminder without changing state: `test`
- Deliver a desktop test notification when explicitly requested: `test --deliver`

Supported threshold flags:

```text
--duration-minutes
--duration-messages
--burst-window-minutes
--burst-messages
--continuity-gap-minutes
--idle-reset-minutes
--cooldown-minutes
--daily-limit
```

## Response policy

- Run the minimum command needed for the request.
- Summarize the resulting setting or status concisely.
- Explain that runtime detection uses only hashed session identifiers, local timestamps, and counts when privacy or the hook mechanism is asked about.
- Describe `duration_minutes` plus `duration_messages` as the sustained-activity trigger, and `burst_window_minutes` plus `burst_messages` as the conversation-intensity trigger.
- Never claim to measure typing time, screen time, fatigue, hydration, or actual work duration.
- Never enable desktop notifications or deliver a test notification without an explicit user request.
- Do not call an LLM, inspect prompt text, or read the conversation transcript to configure reminders.
