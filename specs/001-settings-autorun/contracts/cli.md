# CLI contract
runner.py --install-root ABSOLUTE_ROOT install --source REPO --user-home OWNER --documents DOCUMENTS
runner.py --install-root ABSOLUTE_ROOT doctor|status|runtime-doctor|watch|uninstall
runner.py --install-root ABSOLUTE_ROOT autorun on --explicit --goal TASK
runner.py --install-root ABSOLUTE_ROOT autorun status|off
runner.py --install-root ABSOLUTE_ROOT autorun complete --task UUID --evidence ABSOLUTE_JSON
Activation requires the current CODEX_THREAD_ID, a nonempty task and an eligible current human desktop turn. No title/last/parent fallback. Evidence contains a nonempty checks array of actual check names with exit_code=0. JSON output uses escaped Unicode for Windows terminal compatibility. Errors exit nonzero. Doctor installation and runtime checks are separate from live UI/mobile/reset proof.
