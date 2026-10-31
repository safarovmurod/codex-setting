# Data model
Profile: versioned config map, 35 skill names, plugin manual inventory, removed plugin list.
Installation: owner SID, random host UUID, target paths, initial-file backups and expected installed hashes. No auth or desktop database backup.
Task: host UUID + canonical human thread UUID, task UUID, goal hash, baseline turn ordinal, state armed/off/paused/completed, reason. Repeated activation in the same turn is idempotent; a new invocation after another turn gets a new task generation.
Attempt: unique host/thread/task/failed-turn key, pre-send claimed state, accepted/not_started/unknown receipt and optional owned queue UUID. Every recorded claim prevents resend after restart.
Wait: exact host/thread/failed-turn key, server reset timestamp and evidence that quota was observed blocked.
Evidence: local UI read-back and Android/natural-reset observations, kept outside source snapshots.
