# Feature Specification: Portable settings and explicit AUTORUN
Created: 2026-11-01. Status: implementation. Owner: шеф.

## User Scenarios & Testing
### US1 — Restore preferences on another Windows PC (P1)
Given the owner asks to install the private repository, the setup restores every portable setting and all 35 personal skills to their supported locations. Re-running setup creates no duplicates. Existing changes have a recoverable backup. Device-specific settings are remapped and every omitted private/runtime setting is classified, never silently skipped.
### US2 — Continue this task after a real usage-limit reset (P1)
Given an explicit AUTORUN invocation in one human chat, only that unfinished task may resume after current account quota is available. Other chats, subagents and new tasks do not inherit consent. Stop, pause, off and completion stop further sends. Unknown delivery never produces a duplicate.
### US3 — Android Remote and personalization (P1)
The paired Android device uses the same online Windows host and chat. The owner activates AUTORUN through slash if available or @AUTORUN. Personalization is saved in actual Codex/ChatGPT settings and verified; a text file alone is not success.
### Edge cases
Missing sign-in/pairing; offline host; stale history; unloaded chat; changed backend; queued message; simultaneous watchers; crash before/after dispatch; already completed task; different human turn; exhausted weekly and five-hour buckets; unknown model quota; future reset; failed install; changed files during uninstall.

## Requirements
FR-01: Publish a private safarovmurod/codex-setting repository with a single documented installer.
FR-02: Restore current cleaned preferences, all 35 personal skills and six disabled states without restoring the 12 removed plugins.
FR-03: Classify every source configuration leaf, discover target runtime/device paths and verify destinations.
FR-04: Save the owner's informal Dushanbe Tajik personalization in real Codex and ChatGPT settings, with read-back evidence.
FR-05: Keep third-party plugins manual and document names, purpose and enabled state.
FR-06: AUTORUN is explicit-only and scoped to host, canonical chat UUID and task generation.
FR-07: Read real quota, wait for reset evidence and resume only an eligible, idle, loaded, unfinished quota-failed task.
FR-08: Persist claims before queue delivery, preserve model/reasoning, avoid duplicate/ambiguous sends and obey stops.
FR-09: Restore the watcher after Windows sign-in; remove old global auto-recovery/warm-up behavior from the active path.
FR-10: Android Remote uses the same task/host/settings; pairing is an owner action.
FR-11: Backups, repair, uninstall, tests and a requirement-by-requirement evidence report are mandatory.

## Key Entities
Portable profile; classified setting; installed-file receipt; explicitly armed task; per-turn delivery claim; numeric quota snapshot; UI/mobile evidence.

## Success Criteria
SC-01: All 35 skill folders and payload bytes are accounted for, with six disabled skills unchanged.
SC-02: Clean and repeated installations pass read-back checks; uninstall restores unchanged owned files and refuses to overwrite later user changes.
SC-03: An unarmed second chat receives zero continuation messages; each armed failed turn gets at most one dispatch attempt.
SC-04: A witnessed natural quota stop/reset resumes the exact chat once and eventually records completed task checks.
SC-05: Desktop activation, Android activation and both personalization settings are independently verified in the actual UI.
SC-06: No credential/session/database file or secret is included in the published repository.

## Assumptions
Windows x64 and Android; host remains awake/online. Owner handles login, QR pairing and optional plugins. Tests never deliberately exhaust quota. Native Android slash is optional; @AUTORUN is accepted. A later human turn conservatively requires explicit rearming.
# Accepted change — persistent chat connection (2026-11-01)
The owner's latest request supersedes task-only consent: an explicit AUTORUN invocation connects the exact host/chat until off, even with no current task. Later ordinary human turns are adopted automatically as separate task generations. Completion and Stop/Pause stop current work without disconnecting; only a new human turn can start later work. No completed/stopped task is resumed on its own. Unconnected chats/forks/hosts remain excluded. Existing task-only records must not silently become persistent consent. Quota evidence and exactly-once dispatch remain required.
