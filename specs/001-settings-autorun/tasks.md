# Tasks: codex-setting
## Setup
- [x] T001 Initialize Spec Kit, constitution and design in .specify/ and specs/001-settings-autorun/.
- [x] T002 Export cleaned settings and 35 personal skills with hashes in profiles/ and payload/.
## US1 — portable setup
- [x] T003 [US1] Implement backed-up idempotent install, repair and uninstall in src/codex_setting/installation.py and Install.ps1.
- [x] T004 [US1] Verify clean/repeated install and user-change-safe rollback in tests/test_installation.py.
## US2 — exact recovery
- [x] T005 [US2] Implement consent ledger, current quota checks and durable dispatch claims in src/codex_setting/autorun.py and store.py.
- [x] T006 [US2] Verify scoped activation, reset waits, stop, duplicate suppression and restart in tests/test_autorun.py.
- [x] T007 [US2] Install the explicit skill and single owned watcher; disable superseded tasks using Install.ps1.
## US3 — real UI and Android
- [x] T008 [US3] Save and read back actual Codex/ChatGPT personalization using docs/personalization.md.
- [ ] T009 [US3] Verify desktop slash and Android same-chat invocation using docs/android.md.
- [ ] T010 [US3] Witness natural quota exhaustion/reset and exact single continuation; record evidence.md.
## Delivery
- [x] T011 Publish the private GitHub repository and inspect remote contents and checks.
- [x] T012 Finish README manual plugin inventory and eleven-requirement evidence report.

- [x] T013 Preserve stdout/stderr and exit status through the hidden Windows skill helper; regression test and live status read-back.
- [x] T014 Place the installed recovery beneath the canonical CodexAutoStart folder; retain prior installation as rollback backup and verify task identity after migration.
- [x] T015 Confirm Android selector availability from the owner's screenshot; account plugin installed. Phone-origin execution provenance remains separate from current-host command verification.
Dependencies: T001→T002→US1/US2→T007→US3. Local fixture tests are independent; actual device/reset gates are separate. No extra agents are required for implementation.
- [x] T016 Add explicit persistent chat connections, task adoption, off/Stop/completion behavior and regression coverage.
- [x] T017 Install updated host entrypoints and upload account plugin 1.1.0; verify positive latest-human classification on the real host without a model request.
- [x] T018 Consolidate payload AGENTS.md, align stack to JSX + MUI, limit Spec Kit to large work, enable mansur-frontend-mentor; tests and release scan pass on Linux.
- [ ] T019 Re-run Install.ps1/doctor on the Windows host and re-save ChatGPT Custom Instructions from the updated profile; record read-back.
- [x] T020 Remove autoglm-browser-agent and its executable from payload/export; keep disabled config entry; add auto-recommended choice and verification rules to AGENTS.md.
- [ ] T021 On the Windows host, delete any leftover ~/.agents/skills/autoglm-browser-agent and ~/.openclaw-autoclaw only after owner review.
