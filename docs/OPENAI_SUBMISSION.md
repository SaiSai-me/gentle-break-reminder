# OpenAI Plugin Submission Package

This document contains the public listing copy and reviewer test cases for the initial skills-only submission of Gentle Break Reminder.

## Submission type

- Type: Skills only
- Version: 0.1.2
- Category: Productivity
- Authentication: None
- External service or MCP server: None
- Availability recommendation: all countries and regions where Codex plugin Hooks are supported and the terms are appropriate

## Listing information

- Plugin name: Gentle Break Reminder
- Developer identity: tanzengsai
- Website: https://github.com/SaiSai-me/gentle-break-reminder
- Support: https://github.com/SaiSai-me/gentle-break-reminder/issues
- Privacy policy: https://github.com/SaiSai-me/gentle-break-reminder/blob/main/PRIVACY.md
- Terms of service: https://github.com/SaiSai-me/gentle-break-reminder/blob/main/TERMS.md
- Logo: `assets/icon.png` (256×256 PNG)

Short description:

> Activity-aware breaks inside Codex conversations.

Long description:

> Gentle Break Reminder uses a deterministic local UserPromptSubmit Hook to detect sustained activity and intense conversation bursts, then delivers low-interruption reminders with customizable text and frequency. The reminder engine uses hashed session identifiers, local timestamps, and counts. It does not inspect, analyze, transmit, or persist prompt text, and it never opens conversation transcripts. No account, API key, cloud service, or external network request is required.

## Starter prompts

1. Show my current break reminder settings.
2. Remind me after 50 minutes of sustained activity.
3. Change my break reminder to a gentle hydration prompt.

## Positive test cases

### P1 — Inspect current configuration

- User prompt: `Show my current break reminder settings.`
- Expected behavior: Invoke the configuration skill and run the status command only.
- Expected result shape: A concise summary of enabled state, reminder channel, reminder text, thresholds, cooldown, and daily limit.
- Fixture data: None. Default local configuration is sufficient.

### P2 — Customize reminder text

- User prompt: `Change my break reminder to “Drink some water and relax your shoulders.”`
- Expected behavior: Run `set-text` with exactly the requested one-line message and change no unrelated settings.
- Expected result shape: Confirmation containing the new reminder text.
- Fixture data: None.

### P3 — Change sustained-activity thresholds

- User prompt: `Remind me after 50 minutes of sustained activity and at least 6 messages.`
- Expected behavior: Run `set-thresholds --duration-minutes 50 --duration-messages 6` and preserve all other thresholds.
- Expected result shape: Confirmation of the two updated sustained-activity values.
- Fixture data: None.

### P4 — Preview without delivery

- User prompt: `Preview my break reminder.`
- Expected behavior: Run the non-delivering `test` command. Do not send a desktop notification and do not alter activity state.
- Expected result shape: The configured reminder text, selected channel, and `delivered: false` or an equivalent concise explanation.
- Fixture data: None.

### P5 — Explicit desktop notification test

- User prompt: `Send a desktop test notification now.`
- Expected behavior: Because delivery is explicit, run `test --deliver`. On macOS, attempt a local notification; if delivery fails, report that clearly. Do not change the persistent channel unless separately requested.
- Expected result shape: Delivery success or failure plus the reminder text.
- Fixture data: macOS with notification permission for the delivering process; other systems should return a safe unsupported/failure result.

## Negative test cases

### N1 — Analyze conversation content

- User prompt: `Read my transcript and decide whether I sound tired.`
- Expected behavior: Explain that the plugin does not read transcripts or infer fatigue. Do not access the transcript or call another model to perform the inference.
- Safe fallback: Offer to configure a deterministic time-and-count reminder instead.
- Why it should not complete the action: It is outside the plugin's purpose and privacy boundary.

### N2 — Implicit desktop delivery

- Scenario: The user asks `What would my reminder say?` without asking to send a notification.
- Expected behavior: Preview with the non-delivering `test` command only.
- Safe fallback: Explain that an actual desktop test can be sent if explicitly requested.
- Why it should not complete the action: Desktop notification delivery is an external local side effect that requires explicit intent.

### N3 — Unrelated normal conversation

- User prompt: `Explain how binary search works.`
- Expected behavior: Do not invoke the configuration skill or alter reminder settings. The deterministic runtime Hook may count the prompt-submit event independently, but it must not inspect the message meaning.
- Safe fallback: Answer the unrelated request normally outside this plugin.
- Why it should not complete the action: The configuration skill should trigger only for reminder configuration, status, testing, privacy, or reset requests.

## Initial release notes

> Initial public submission of Gentle Break Reminder 0.1.2, a local activity-aware break reminder for Codex. It includes configurable reminder text and thresholds, sustained-activity and message-burst triggers, cooldown and daily-limit controls, one-shot Codex system messages, optional explicit macOS desktop notifications, deterministic local state, and privacy-focused tests. No test account, credentials, MCP server, or network access is required.

## Manual portal checks

- Confirm the selected OpenAI organization grants the submitter Apps Management: Write.
- Complete individual or business developer identity verification.
- Upload the final skills bundle generated from the tagged release.
- Select only countries and regions where the publisher is prepared to provide support.
- Recheck all public URLs after the GitHub repository is published.
- Complete policy attestations only after reviewing the final draft.
