---
name: create-rule
description: Create or update persistent agent instructions for Codex, ChatGPT coding projects, or explicitly requested Cursor rules.
---

# Persistent project instructions

Use the actual target product and scope from the request. For Codex, inspect existing AGENTS.md files before editing. Put account-independent user guidance in `~/.codex/AGENTS.md`; put project guidance in the project's AGENTS.md. Preserve existing Spec Kit instructions and unrelated rules. Use AGENTS.override.md only when the user explicitly needs an override.

For a shared skill workflow use `~/.agents/skills/<name>/SKILL.md`. Local guidance stays with the Windows user when the ChatGPT account changes; it is not an automatic cloud ChatGPT upload. Never copy authentication, sessions, or databases between accounts.

Infer purpose and scope from the existing request; ask only when an essential scope choice remains unknown. Make the smallest clear edit, back up the file before replacement, and verify the target file and supported discovery path. Do not claim runtime loading based on file existence alone.

Only when the user specifically requests Cursor rules, read [Cursor rule format](references/cursor-rules.md) and use that product's established .mdc layout.
