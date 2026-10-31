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
- [ ] T011 Publish the private GitHub repository and inspect remote contents and checks.
- [ ] T012 Finish README manual plugin inventory and eleven-requirement evidence report.
Dependencies: T001→T002→US1/US2→T007→US3. Local fixture tests are independent; actual device/reset gates are separate. No extra agents are required for implementation.
