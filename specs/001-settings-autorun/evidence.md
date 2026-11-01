# Observed evidence — 2026-11-01

| Requirement | Observed result | Status |
|---|---|---|
| FR-01 private repository | safarovmurod/codex-setting created, private=true; main published; clean GitHub clone tests/hash scan passed | Verified |
| FR-02 owner snapshot | 35 personal skills, six disabled entries, 177 payload hashes; 12 removed plugins not reinstalled | Verified locally |
| FR-03 destination mapping | 80 config leaves classified; actual install read back 182 owned files, node_repl runtime command present. 29 app-managed leaves are not individually generated or checked by this installer; a clean host must be checked separately | Partial: current host file hashes verified; fresh-host runtime not verified |
| FR-04 actual personalization | Codex AGENTS.md installed and loaded; ChatGPT actual Custom Instructions saved, reopened and normalized text matched (1529 characters); nickname/occupation preserved | Verified desktop; Android sync not yet observed |
| FR-05 manual plugins | README lists all 31 remaining installed plugins, source state and install route | Implemented |
| FR-06 explicit consent | Explicit-only YAML; scoped ledger; unarmed/other-host/subagent fixtures reject activation or send | 49 unit/lifecycle tests pass |
| FR-07 real quota | Live official backend 0.166.0-alpha.5.1 reads numeric quota; pinned decoder fixtures for 5h/weekly/available/unknown pass | Read-only integration verified; natural reset pending |
| FR-08 duplicate/stop guards | Restart/ambiguous dispatch/competing watchers/Stop/off/completion/edited queue regressions pass; native backend loaded exact root chat with fresh projection | Locally verified, real dispatch not yet observed |
| FR-09 startup migration | CodexSetting.Autorun Running; CodexAutoStart.Local and .Recovery Disabled with saved task XML; no task armed automatically | Verified actual host |
| FR-10 Android Remote | Owner confirmed Android is paired and sees this same chat | Pairing confirmed; desktop AUTORUN visible in owner screenshot; Android picker lacked local skill; account plugin packaging added, upload/test pending |
| FR-11 tests/rollback/security | 49 tests; PowerShell parser; payload secret/path scan; backup + user-change-preserving uninstall fixtures; partial runtime download/extraction repair tests | Local and fresh-clone pass; GitHub Actions run 41265233156 passed on Windows and Linux for commit 7fad9a0 |

The immutable vendor payload passed full archive/source verification. Skill creator quick_validate passed. No model inference, queue send, credit redemption or deliberate quota exhaustion was used for these probes. A live natural quota stop→reset→one exact continuation remains unverified; synthetic tests are not that evidence.

Actual installation is on the selected Windows host. Credentials, auth.json, raw desktop state, databases and session history are not in the repository. Own runtime receipts/backups stay outside it.

The source AGENTS.md snapshot remains hash-verified and unchanged. On installation its two known user-home paths are rendered for the destination user; the resulting file is tracked by its own hash. This remapping is covered by a temporary-home test and has not itself proved a complete clean Windows installation. The user's instruction names `D:/User/CodexAutoStart` for recovery, while this installation uses `D:/User/CodexSetting/recovery`; the instruction has been preserved and this location discrepancy remains unresolved, including on hosts without a D: drive.

The installed local AUTORUN plugin now resolves to the owned installation at `D:/User/CodexSetting/app`, and repeated installation reported it present; doctor verified all 182 tracked files. The prior marketplace configuration was backed up before changing its path. The uninstall command currently retains the added marketplace registration and plugin cache: complete removal has not been verified. The local plugin does not establish Android availability.
