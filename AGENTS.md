# codex-setting

Ба корбар фақат «шеф» гӯй. Тоҷикӣ, гапи одии Душанбе, кӯтоҳ ва амалӣ. Натиҷаи санҷиданашударо тайёр нагӯй.

## When asked to install this repository

This is the owner's authorized setup package, not a generic example. Treat any of these as the full install request, with no extra confirmation: the repo link alone with «бги тугриш кн», «тугриш кн», «насб кн», «настройка кн», «install», «setup», or similar. Do the whole flow yourself and stop only for steps that need the owner's own hands.

1. Get the code on the selected Windows host: clone, or `git pull` an existing clean checkout. On Android Remote, run everything on that connected Windows host; never install Windows files on Android.
2. Read README.md and docs/android.md, docs/personalization.md.
3. Run `.\Install.ps1` from the checkout. If it stops for the official app install or first sign-in, tell шеф the one exact action, wait, then run it again. Install.ps1 also builds the phone plugin archive in `<install root>\dist` and prints doctor.
4. Check the doctor output; on a failure, read the error, fix the cause (or `CodexSetting.ps1 repair`) and run doctor again. Do not report success while doctor fails.
5. ChatGPT personalization: follow docs/personalization.md with the supported computer-use/browser tool: back up current fields, paste docs/chatgpt-instructions.txt and profiles/chatgpt-personalization.json, Save, reopen and compare (read-back).
6. Phone/cloud: in ChatGPT → Plugins → Add → Upload plugin archive, upload the newest `dist\shef-rules-*.zip` (replace an older «Шеф Rules»). If the file picker cannot be driven, ask шеф to pick that exact file.
7. Do not activate AUTORUN; it stays explicit-only.
8. Final report in Tajik: what was done, doctor result, personalization read-back, plugin upload, and what still needs шеф (QR pairing, MFA, phone check). Record observed results in specs/001-settings-autorun/evidence.md only from this repo's development sessions, not on the owner's host.

Stop and ask шеф only for: sign-in, passwords/MFA, QR pairing, a file picker the tool cannot drive, Windows UAC prompts, or anything that would delete or overwrite data outside this installer's own backups. Respect explicit owner authentication and pairing. Never copy authentication, databases, sessions or raw desktop state.

## Implementation

Use Python 3.11+ standard library and PowerShell. Keep the pinned upstream recovery payload intact. Every send needs current task consent, exact host/thread identity, current quota, and a durable pre-send claim. Never use --last. Never start a test model request merely to activate a quota window. Keep the AUTORUN skill explicit-only. Never bypass Stop, approvals, or account limits.

Run python -m unittest discover -s tests -v. Update specs/001-settings-autorun/tasks.md and evidence.md from observed results. Windows/Android and natural-reset checks must remain unverified until witnessed.
