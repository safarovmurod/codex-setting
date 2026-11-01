# Observed evidence — 2026-11-01

| Requirement | Observed result | Status |
|---|---|---|
| FR-01 private repository | safarovmurod/codex-setting created, private=true; main published; clean GitHub clone tests/hash scan passed | Verified |
| FR-02 owner snapshot | 35 personal skills, six disabled entries, 177 payload hashes; 12 removed plugins not reinstalled | Verified locally |
| FR-03 destination mapping | 80 config leaves classified; actual install read back 182 owned files, node_repl runtime command present. 29 app-managed leaves are not individually generated or checked by this installer; a clean host must be checked separately | Partial: current host file hashes verified; fresh-host runtime not verified |
| FR-04 actual personalization | Codex AGENTS.md installed and loaded; ChatGPT actual Custom Instructions saved, reopened and normalized text matched (1529 characters); nickname/occupation preserved | Verified desktop; Android sync not yet observed |
| FR-05 manual plugins | README lists all 31 remaining installed plugins, source state and install route | Implemented |
| FR-06 explicit consent | Explicit-only YAML; scoped ledger; unarmed/other-host/subagent fixtures reject activation or send | 60 unit/lifecycle tests pass |
| FR-07 real quota | Live official backend 0.166.0-alpha.5.1 reads numeric quota; pinned decoder fixtures for 5h/weekly/available/unknown pass | Read-only integration verified; natural reset pending |
| FR-08 duplicate/stop guards | Restart/ambiguous dispatch/competing watchers/Stop/off/completion/edited queue regressions pass; native backend loaded exact root chat with fresh projection | Locally verified, real dispatch not yet observed |
| FR-09 startup migration | CodexSetting.Autorun Running; CodexAutoStart.Local and .Recovery Disabled with saved task XML; no task armed automatically | Verified actual host |
| FR-10 Android Remote | Owner confirmed Android is paired and sees this same chat. AUTORUN account plugin uploaded and installed through ChatGPT UI; success notification and Manage link observed; plugin ID Plugin_24574ce1bf5c81918bdb0f28475453d1 | Account installation and Android selector verified from owner screenshot 8442.jpg; current-host activation verified for exact chat UUID, phone execution provenance not independently verified |
| FR-11 tests/rollback/security | 60 tests; PowerShell parser; payload secret/path scan; backup + user-change-preserving uninstall fixtures; partial runtime download/extraction repair tests | Local and fresh-clone pass; GitHub Actions run 41265233156 passed on Windows and Linux for commit 7fad9a0 |

The immutable vendor payload passed full archive/source verification. Skill creator quick_validate passed. No model inference, queue send, credit redemption or deliberate quota exhaustion was used for these probes. A live natural quota stop→reset→one exact continuation remains unverified; synthetic tests are not that evidence.

Actual installation is on the selected Windows host. Credentials, auth.json, raw desktop state, databases and session history are not in the repository. Own runtime receipts/backups stay outside it.

The source AGENTS.md snapshot remains hash-verified and unchanged. On installation its two known user-home paths and recovery location are rendered for the destination user; the resulting file is tracked by its own hash. This remapping is covered by a temporary-home test and has not itself proved a complete clean Windows installation. The installed recovery now lives at `D:/User/CodexAutoStart/CodexSetting/recovery`, beneath the canonical recovery directory. The prior `D:/User/CodexSetting` installation is retained for rollback. The transient watcher lock was not copied; the task ledger, exact task UUID and host UUID were retained and read back after restart.

The installed local AUTORUN plugin now resolves to the owned installation at `D:/User/CodexAutoStart/CodexSetting/app`, and repeated installation reported it present; doctor verified all 182 tracked files. The prior marketplace configuration was backed up before changing its path. The uninstall command currently retains the added marketplace registration and plugin cache: complete removal has not been verified. The local plugin does not establish Android availability.

Explicit task c9dc8698-ef98-4156-acaa-5b547354bf22 is armed for root chat 01a193db-4a6b-78d2-ac17-0a2949c395c0; zero dispatch attempts observed. The skill helper stdout/stderr regression is fixed and its live status output verified. No completion claim is made while clean-machine runtime, phone execution provenance, personalization sync and natural quota recovery acceptance checks remain.

Persistent chat consent (latest owner requirement): account plugin 1.1.0 uploaded and version read back; host controller installed and current chat connected=true until explicit off. Old task consent is not auto-upgraded. 60 tests cover followups, completion, Stop, off, restart, isolated hosts, missing-user evidence and concurrent watchers. The live history API positively classified the latest human turn (fresh projection), without a queue send. A later ordinary phone task and natural quota reset still need live observation.

2026-11-01 followup: the watcher adopted a real ordinary human followup in this connected chat as task fc457c8f-26b1-445b-abc3-02c7d41c65e6 (checkpoint 2614), without a repeated invocation. Live autoruoff returned off, then status read connected=false with zero pending cancellations. Reconnected explicitly after the authorized off/on verification; final connected=true. 61 tests pass, including offline autoruoff. Removed an unreachable duplicate watcher branch. No quota dispatch was induced.
