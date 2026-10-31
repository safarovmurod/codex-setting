# Implementation Plan: codex-setting
## Technical Context
PowerShell on Windows x64; Python 3.11+ standard library, with immutable upstream 0.6.17 embedded Python runtime. No new web server or model-backed polling. Existing owner GitHub access is used for a private repository.
## Constitution Check
Pass: exact consent, immutable vendor payload, no credentials exported, backed-up owner files, bounded evidence and honest live acceptance gates.
## Design
Export reviewed preferences/skills and hash manifest. Installer bootstraps vendor runtime, installs source and preferences transactionally, installs explicit AUTORUN skill and starts a single scheduled watcher. Runtime reuses upstream LocalSource, Backend discovery, quota parser, app pairing and official queue. Own SQLite stores only task UUIDs, hashes, states and queue receipts. Stop/complete and dispatch share a per-thread lock. Durable pre-send claims make uncertain delivery non-retryable.
## Changes
CLI entry points: install, doctor, runtime-doctor, status, autorun on/off/status/complete, watch, uninstall. Repair reuses the idempotent installer. Public skill display name AUTORUN; allow_implicit_invocation=false.
## Validation
unittest fixtures cover installation lifecycle and recovery races; live read-only doctor verifies current backend; UI evidence and Android/natural-reset observations remain separate release gates.
## Project Structure
src/codex_setting: installer, preferences, store, runtime, controller, CLI. payload: owner rules and 35 skills. skills/autorun: explicit entrypoint. profiles: portable config, settings map and byte hashes. docs: actual personalization and Android flows. tests: meaningful lifecycle/dispatch checks.
