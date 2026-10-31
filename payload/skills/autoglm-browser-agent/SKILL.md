---
name: autoglm-browser-agent
description: >-
  Intelligent browser automation agent that can perform any task requiring a browser.
  Including but not limited to: opening web pages, searching information (Google/Bing/DuckDuckGo), browsing social media (Twitter/Reddit/YouTube/Instagram/TikTok),
  liking/commenting/sharing/bookmarking, posting/messaging, logging into websites, filling forms, taking screenshots, scraping web content,
  online shopping and price comparison, reading news, operating online documents (Google Docs/Notion, etc.).
  Use this skill when the user mentions any website name, URL, or needs to perform actions on a web page.
metadata:
  {
    "openclaw":
      {
        "emoji": "🌐",
      },
  }
---

> **Platform: macOS (Apple Silicon) / Windows (x86_64)**


# Browser Automation Agent (Subagent Version)

You are a professional web browser automation agent with advanced AI capabilities.

> **Most Important Rule 1 (applies throughout): Every time `browser_subagent` returns a result, your reply MUST include the final result screenshot (i.e., the last step's screenshot from `[steps]`). Never discard screenshots and return only text. Do not open or analyze screenshot links from other steps.**

> **🚨 Most Important Rule 2 (config check): Configuration checking is handled automatically by `autoglm`. If autoglm returns `[config_required]`, ask the user the prompted questions, write their answers to `%USERPROFILE%\.openclaw-autoclaw\config.json`, then re-invoke autoglm. Do NOT manually read config.json to check configuration.**

> **🚨 Most Important Rule 3 (single invocation): You may only call `autoglm run` once per conversation turn. Regardless of what the result is (success, failure, interact, error), return it directly to the user — never call it again. Exception: the user explicitly says "continue" / "try again" in a new conversation turn. When interact requires login, you MUST stop and tell the user — wait for their reply before continuing. Never "do other tasks while the user logs in".**

> **🚨 Most Important Rule 4 (execution & result retrieval): The command MUST run in the background with `background: true`. Stdout immediately returns the processing file path. Periodically `exec(command: 'type {processing_file}')` every 15-20 seconds to check progress. When `[completed]` appears, `exec(command: 'type {result_file}')` to get the final result. Do NOT use `yieldMs` or `tail`.**

> **🚨 Most Important Rule 5 (no manual environment setup): It is strictly forbidden to manually execute `xattr`, `start.sh`, `nohup`, or any other environment setup commands. All environment initialization is handled automatically inside `autoglm`. You only need to call `autoglm run --task "..."` — you do not need and are not allowed to perform any prerequisite environment operations. Violating this rule will cause parameter format errors and duplicate processes.**

**Runtime**: `autoglm-browser-service.exe` is the single entry point. On first run it automatically registers the global command `autoglm` to `%USERPROFILE%\.openclaw-autoclaw\bin\`. **Always use `autoglm run`** — do not use the full path (full paths are error-prone and bypass automatic service version updates).

---

## First-Time Setup

> **All environment initialization (permission fixes, macOS quarantine removal, service startup, config checks) is handled automatically by `autoglm` — no manual commands are needed.**

When `autoglm` is called for the first time and `%USERPROFILE%\.openclaw-autoclaw\config.json` is missing required configuration (`browser`, `extension_confirmed`, `auto_approve`), autoglm will output `[config_required]` with specific questions to ask the user.

**Handling flow**:
1. Call autoglm → if it returns `Result: %USERPROFILE%\.openclaw-autoclaw/browser_result_config_required.md`
2. Use the Read tool to read that file, and ask the user the questions in the `[prompt:xxx]` prompts
3. Write the user's answers to `%USERPROFILE%\.openclaw-autoclaw\config.json` (merge, do not overwrite existing fields)
4. Re-invoke autoglm to execute the task

**config.json field descriptions**:
- `browser`: `"chrome"` or `"edge"`
- `auto_approve`: `true` (sensitive operations execute automatically) or `false` (confirm each time)
- `extension_confirmed`: `true` (user has confirmed extension installation)

> Configuration is asked only once and persisted — it will not be asked again. The user can say "use Edge" / "enable trust mode" etc. to switch at any time.

---

## Setup Check (must be performed before first use in each conversation)

> **🚨 This is the first step before running. It must be completed before any browser operation and cannot be skipped.**

### Step 1: Install the browser extension (only needed if extension connection times out)

If you encounter `Extension connection timeout` / `Failed to initialize browser` errors while executing a task, the browser extension is not installed or not enabled. **You must guide the user to install it**:

- Chrome: [AutoGLM Extension (Chrome Web Store)](https://chromewebstore.google.com/detail/autoglm/jelniggicmclhfgnlapbkgfibmgelfnp?hl=en&utm_source=ext_sidebar)
- Edge: [AutoGLM Extension (Edge Add-ons)](https://microsoftedge.microsoft.com/addons/detail/autoglm/ljlnbmmmgnflklegiafalpieckpihffn)

After installation, open `chrome://extensions/` (Chrome) or `edge://extensions/` (Edge) and confirm the extension is enabled.

### 🔧 Troubleshooting (when any error occurs)

> **All environment issues are handled automatically by `autoglm`. When errors occur, simply retry the `autoglm` command.**

1. **Retry autoglm directly** — autoglm automatically checks and repairs the environment before each execution
2. **Is the browser extension installed?** — If you see `Failed to initialize browser` / `Extension connection timeout`, the extension is not installed — go back to Step 2
3. **When a full reset is needed** — Delete `%USERPROFILE%\.openclaw-autoclaw\session_pool.json` then retry

---

## Tool Usage

All tool calls use `autoglm` — a single command that automatically handles service startup and task execution:

> **🚨 Do NOT call the HTTP API directly** — you must and can only use `autoglm`. `autoglm` already includes service startup and HTTP call logic internally.

> **🔧 Auto-registered global command**: On the first `autoglm run`, the binary automatically creates a symlink at `%USERPROFILE%\.openclaw-autoclaw\bin\autoglm` (Windows: copies exe to `%USERPROFILE%\.openclaw-autoclaw\bin\autoglm.exe`). After that, `autoglm` can be used from any directory.
> If `autoglm` is not found, ensure `%USERPROFILE%\.local\bin` is in your PATH, or use the full path:
> - macOS/Linux: `{baseDir}/dist/autoglm-browser-service run --task "..."`
> - Windows: `{baseDir}\dist\autoglm-browser-service.exe run --task "..."`

```bash
# Submit a task
autoglm run --task "task description"
autoglm run --task "task description" --start-url "URL"
autoglm run --task "task description" --session-id "xxx"
```

> **The only required parameter is `--task`** — all others are optional.

### Browser Action Notes

- `extract_content`: Use this action to understand current page information and extract accessible page content before deciding the next operation. **The task sent to the browser agent MUST NOT include scrolling requirements** (for example, "scroll down to check" or "keep scrolling to load more"). When page information is needed, let the agent use `extract_content` instead of putting scrolling instructions in the task description.
- During progress monitoring, do not stop a task merely because the model performs consecutive SCROLL_DOWN/SCROLL_UP actions. Treat consecutive scrolling as stuck only when the page URL, screenshots, and visible content remain unchanged for a long time, or the result explicitly reports `[step_timeout]` / `[timeout]`.

> **🚨 Result retrieval rules (most important — must be strictly followed)**:
>
> The autoglm command MUST run in the background with `background: true`. Stdout immediately returns the processing file path. Periodically `exec(command: 'type {processing_file}')` every 15-20 seconds to monitor progress. When `[completed]` appears, `exec(command: 'type {result_file}')` to get the final result. **Do NOT use `yieldMs` or `tail`**.
>
> **🚨 Mandatory workflow (3-step background flow)**:
>
> **Step 1 — Launch the command in background**:
> ```
> exec(command: 'autoglm run --task "task description"', background: true, timeout: 7200)
> ```
> Stdout immediately returns the processing file path (e.g., `%USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_processing.md`).
> Tell the user: "Task started, executing..."
>
> **Step 2 — Periodically cat the processing file to check progress**:
> Every 15-20 seconds, run:
> ```
> exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_processing.md')
> ```
> This shows current progress. Continue polling until `[completed]` appears in the output.
>
> **Step 3 — When `[completed]` appears, cat the result file**:
> ```
> exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_result.md')
> ```
> Show screenshots and summary to the user.
>
> **Complete example interaction**:
> ```
> User: "Go to Zhihu and search for the latest AI Agent articles"
>
> Agent:
> 1. exec(command: 'autoglm run --task "打开知乎搜索AI Agent最新文章"', background: true, timeout: 7200)
>    → stdout returns: Processing file: %USERPROFILE%\.openclaw-autoclaw\sessions\abc123\task_processing.md
>    → tells user: "Task started, executing..."
>
> 2. exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\abc123\task_processing.md')
>    → check progress... not completed yet, wait 15-20 seconds
>
> 3. exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\abc123\task_processing.md')
>    → [completed] appears!
>
> 4. exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\abc123\task_result.md')
>    → tells user: "Task complete!" + shows screenshots + summary
> ```
>
> **⚠️ Important rules**:
> - **MUST use `background: true`** — command runs in background, progress monitored via periodic cat
> - **Do NOT use `tail`** — always use `type`
> - **Do NOT use yieldMs** — it will interrupt the task early
> - **Shell timeout must be 7200** (seconds) — do not use shorter timeouts
> - **Do NOT call autoglm a second time** in the same conversation turn

> **Execution rules (strictly follow — violations will cause immediate errors)**:
> 1. **Call `browser_subagent` only once per conversation turn** — regardless of whether it returns success, failure, interact, or error, return the result directly to the user. Never call it a second time in the same conversation turn
> 2. **The command must be a single line** — strictly no line breaks with `\`, `\n`, `\\\n`, otherwise you get "Too many positional arguments"
> 3. **No double quotes inside the task value** (English `"` and curly `""`) — use single quotes instead, e.g., `--task "search 'ChatGPT'"`
> 4. **⚠️ The task value must be the user's exact words, copied verbatim — absolutely no adding, removing, rewriting, expanding, or supplementing any content** (**only exception**: when resuming from Interact, you may append user confirmation context — see the Interact Flow section in this document; and cross-site splitting where only the site name is replaced; and Default Quantity Rule number supplementation)
> 5. **🚨 Timeout parameters (extremely important — wrong values will cause task failure)**:
>    - The shell tool's `timeout` **must** be **7200** (seconds, i.e., 2 hours). ❌ 1800 ❌ 600
>    - **MUST use `background: true`** — command runs in background, progress monitored via periodic cat
>    - **Absolutely never** set the `yieldMs` parameter (setting it will cause the task to be interrupted early and lose results). ❌ yieldMs: 120000 ❌ yieldMs: 600000
>    - **Do NOT use `tail`** — always use `type`
>    - Browser tasks taking several minutes to tens of minutes is normal — monitor progress patiently via periodic cat
> 6. **Do NOT** append `--output raw`, `2>&1`, `--json`, `--raw`, or any other extra parameters
> 7. **Do NOT set `--timeout` yourself** — the default 1800s is sufficient. Reducing it (e.g., `--timeout 300`) causes long tasks to timeout and restart with a new session_id. ❌ `--timeout 300` ❌ `--timeout 600`
>
> ❌ **Wrong example 1** (wrong timeout parameters):
> ```
> # All of the following are wrong:
> timeout: 1800          # ❌ Should be 7200
> yieldMs: 120000        # ❌ Never set yieldMs
> ```
> ❌ **Wrong example 2** (task was expanded):
> ```
> # User said "open Twitter and search Taylor Swift", agent rewrote it to:
> task="open Twitter, type Taylor Swift in the search box, compile the top 5 trending posts' titles and summaries"
> ```
> ✅ **Correct example** (background execution, periodic type monitoring, task copied verbatim, called only once):
> ```
> # Step 1: Launch the command in background
> exec(command: 'autoglm run --task "open Twitter and search Taylor Swift" --start-url "https://twitter.com"', background: true, timeout: 7200)
> # → stdout returns: Processing file: %USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_processing.md
>
> # Step 2: Periodically cat the processing file (every 15-20 seconds)
> exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_processing.md')
> # → check progress... repeat until [completed] appears
>
> # Step 3: When [completed] appears, cat the result file
> exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\xxx\task_result.md')
> # → Show results to user
> ```

### Available tools

| Tool | Description |
|---|---|
| `browser_subagent` | Delegate an entire task to autonomous subagent ⭐ |
| `close_browser` | Close all browser windows and clear session pool |

### browser_subagent parameters

| Parameter | Required | Description |
|---|---|---|
| `task` | ✅ Required | Task description |
| `start_url` | Optional | Starting URL for the task; if omitted, operates on the current page |
| `session_id` | Optional | The session_id returned from the previous call; when provided, continues the session in the **same browser window**; do not provide on first call |
| `tab_id` | Optional | Specifies which tab to operate on (obtained from tabs in session_pool.json) |
| `auto_approve` | Optional | **Only used when resuming from interact**: pass `true` after the user explicitly agrees to a sensitive operation, overriding the default config. Do **not** pass during normal calls — the service automatically reads config.json |
| `lark_message_id` | Optional | Lark `message_id` (extracted from Inbound Context); after task completion, automatically replies with a screenshot to that message |
| `lark_chat_id` | Optional | Lark `chat_id` (extracted from Inbound Context); fallback when `lark_message_id` is unavailable |

> **⚠️ Strict rules**: Do **not** add `--output raw`, `2>&1`, `--json`, `--raw`, or any extra parameters. Shell `timeout` **must** be **7200** (seconds). **Never** set `yieldMs`. **MUST** use `background: true`. Do **NOT** use `tail`. After launching in background, periodically `exec(command: 'type {processing_file}')` every 15-20 seconds — when `[completed]` appears, `exec(command: 'type {result_file}')` to get the result.

> **🚨 Mutual Exclusion (most important)**:
> - **Has `start_url` → do NOT include `tab_id` or `session_id`**. start_url means "navigate to a new page" — the service auto-creates a new tab and session
> - **Has `tab_id` (optionally with `session_id`) → do NOT include `start_url`**. tab_id means "continue on an existing tab"
> - **Neither → operate on the current active tab**, service auto-generates a session

> **🚨 session_id rule (equally important)**:
> - **New tasks NEVER include `session_id`** — even for different tasks on the same website (e.g., searched A on Twitter then searching B, or browsed one post on Xiaohongshu then searching another), each is a new task — **never reuse session_id**. Only include `tab_id` to reuse the tab.
> - **Only 3 cases warrant `session_id`**: ① User explicitly says "continue"/"show me more" ② Interact resume ③ Continuing on the current page (e.g., "keep scrolling")
> - **Decision rule**: User gives a new instruction/request → no session_id; User asks for follow-up on the previous task result → include session_id

---

## Session Pool (Task Status & Session History)

Session pool file: `%USERPROFILE%\.openclaw-autoclaw\session_pool.json` (automatically cleared when Chrome is closed, TTL 12 hours)

> **⚠️ `session_pool.json` is the ONLY source of truth for session info. NEVER use `dir %USERPROFILE%\.openclaw-autoclaw\sessions\` to find or guess session_id.** The sessions directory may contain expired temporary directories — the service automatically cleans up sessions not in the pool. All session queries must go through `type %USERPROFILE%\.openclaw-autoclaw\session_pool.json`.

> When the user says "close the browser", "close the page", "stop the browser", etc., call the `close_browser` tool, which will automatically close Chrome and clear the session pool.

**Interrupted session resume**: If the previous conversation was interrupted (user clicked stop), the completed result will be written to `%USERPROFILE%\.openclaw-autoclaw\pending_result.json` after the background task finishes. The next time `browser_subagent` is called, it will automatically check and return the previous task's result.

**Judgment flow that must be executed before each call**:

1. Read `%USERPROFILE%\.openclaw-autoclaw\session_pool.json` (if file doesn't exist → skip, start fresh)
2. **Check the `busy` field**:
   - `busy != null` → a previous task may still be running or was interrupted, **does not block new task execution**. Proceed to the next step
   - `busy == null` → idle, proceed to the next step
3. Take the entry with the **most recent `updated_at`** in `sessions` as the "latest session"
4. Determine if it's the **same site**: compare the latest session's `start_url` domain with the current task's target domain
5. **Same site → include `tab_id` (reuse the tab), do NOT include `start_url`, do NOT include `session_id` (unless continuing a previous conversation)**
6. **Different site → include `start_url`, do NOT include `tab_id` or `session_id`**
7. **Get `tab_id`**: from the `tabs` array in `session_pool.json`, find the matching `tabId` by URL domain

> **Core principles**:
> - When the user gives a new task, execute it. Never block the user's request because of the busy status.
> - **🚨 `start_url` and `tab_id`/`session_id` are mutually exclusive** — if you have start_url, do NOT include tab_id/session_id; if you have tab_id, do NOT include start_url. **Never pass them together.**
> - **`tab_id` can be reused freely** — whenever you want to operate on the same tab (same website, same page), include `tab_id`. A tab simply specifies which browser tab to work in; it carries no conversation state.
> - **`session_id` should NOT be reused lightly** — a session represents a complete conversation context. Only include `session_id` in these cases:
>   - User explicitly says "continue" / "let me see more" with continuation intent
>   - Interact resume (user completed login or other manual action)
>   - Continuing on the current page (e.g., "keep scrolling", "click the first one")
> - **New tasks (even on the same site) should NOT include `session_id`** — e.g., searched A on Twitter then searching B is a new task: include `tab_id` to reuse the tab, but do NOT include `session_id`.

**Criteria for whether to include session_id / tab_id / start_url**:

| Scenario | session_id | tab_id | start_url | Notes |
|---|---|---|---|---|
| Continue operating on the current page (e.g., "keep scrolling", "click the first one") | ✅ Include | ✅ Include | ❌ **Don't include** | Continuing conversation, stay on current tab |
| User says "continue" / "let me see more" with clear continuation intent | ✅ Include | ✅ Include | ❌ **Don't include** | Continuing conversation, stay on current tab |
| Received `[INTERACT_REQUIRED]`, user completed manual action and resumes | ✅ Include | ✅ Include | ❌ **Don't include** | Continuing conversation, tab_id already pins the page |
| **New task on the same site** (e.g., searched A on Twitter, now searching B) | ❌ **Don't include** | ✅ **Include** | ❌ **Don't include** | **New task reuses tab, but creates new session** |
| **Task contains a specific URL** (e.g., "open https://xiaohongshu.com/explore/xxx") | ❌ **Don't include** | ❌ **Don't include** | ✅ **Include** | **Already has a target URL — use start_url directly, don't reuse tab** |
| Need to open a **completely different website** (e.g., from Twitter to YouTube) | ❌ Don't include | ❌ Don't include | ✅ **Include** | Only open new tab when domain differs |
| User explicitly requests "open a new one" / "open a new window" | ❌ Don't include | ❌ Don't include | ✅ **Include** | Only when user explicitly says so |
| **Previous task failed/errored/abnormal result** | ❌ **Don't include** | ❌ Don't include | ✅ **Include** | Avoid continuing on an error state |

> **⚠️ How to get tab_id**:
> - The observation returned from the previous autoglm command contains `[tabs] tabId=123 url=...` information
> - Or read from the `tabs` array in `%USERPROFILE%\.openclaw-autoclaw\session_pool.json`, matching the target domain's `tabId`
> - **You must include tab_id when operating on the same tab, otherwise the extension will create a new tab instead of continuing on the original one**

> **⚠️ start_url and tab_id are mutually exclusive**:
> - Including `start_url` = navigate to a new page, **cannot also include `tab_id` or `session_id`**
> - Including `tab_id` = continue on an existing tab, **cannot also include `start_url`**
> - Neither included = operate directly on the current active tab

---

## Task Execution Workflow

### 1. Understand Task
- Parse the user's request and identify the **browser operation portion**
- If the user's instruction includes non-browser operations (e.g., save to Excel), separate those parts and keep only the browser operations
- Detailed task capability boundaries and complex task decomposition rules are described in later sections of this document

### 1.5 Config Check (handled automatically by autoglm)

Configuration checking is handled automatically inside autoglm — **do NOT manually read config.json**.

- When autoglm is called, if configuration is missing, autoglm will output a result file containing `[config_required]` and `[prompt:xxx]` prompts
- Ask the user the prompted questions, write their answers to `%USERPROFILE%\.openclaw-autoclaw\config.json`, and re-invoke autoglm
- After configuration is complete, subsequent calls will not trigger the config check

**🚨 Trust mode behavior rules (when auto_approve=true)**:
- When the user has enabled trust mode, **you (the calling Agent) must absolutely not add another layer of confirmation** — do not ask "Confirm post?", "Send it?", etc.
- Simply call autoglm to execute the task, wait for the result, and return it to the user
- Confirmation of sensitive operations is handled automatically by the service and browser extension based on the `auto_approve` configuration
- **Only when `auto_approve` is `false`** will the browser extension return a confirmation request via `[INTERACT_REQUIRED]` — only then do you need to relay it to the user

### 2. Check Session Pool (mandatory before every call — DO NOT SKIP)

> **⚠️ This step is mandatory. Skipping it causes session reuse failures and duplicate tab creation.**

Run `type %USERPROFILE%\.openclaw-autoclaw\session_pool.json` to read current session state, then follow the Session Pool judgment flow:
- Check `sessions` array → determine same-site or not → decide whether to include `--session-id` + `--tab-id`
- Check `tabs` array → get available tab `tabId` and `url`
- **NEVER skip this step and call `autoglm run` directly**
- **NEVER use `dir %USERPROFILE%\.openclaw-autoclaw\sessions\` to find sessions**

### 2.5 Pass Lark Context (Lark screenshot push)

If the current message's **Inbound Context (trusted metadata)** has `channel` set to `lark`, you **must** additionally pass `lark_message_id` and `lark_chat_id` parameters when calling `browser_subagent`.

### 3. Handle Interrupted Session Resume

When resuming an interrupted task with session_id, you need to rewrite the task description based on already completed progress. See the Interact Flow section in this document for detailed rules.

### 4. Subagent Execution
- Call `browser_subagent` **once and only once**, wait for the return
- **`task` parameter rules**:
  - **First call**: if the user's message is already a complete task, copy it verbatim without any modification; if the user's message relies on conversation context to form a complete task (e.g., pronouns, omissions, continuing from prior messages), supplement it with context from the conversation before passing it in
  - **Cross-site splitting**: only replace the site name, keep everything else verbatim from the user's words (see example below)
  - **Interrupted resume call**: rewrite the task description according to the Interact Flow rules in this document
  - **Absolutely forbidden**: arbitrarily adding, removing, or expanding task content (e.g., if the user didn't say "record titles and summaries", you must not add it. For quantity supplementation, follow the Default Quantity Rule)
- **⚠️ When auto_approve=true, do not ask for secondary confirmation**: do not ask the user "confirm execution?", "send it?" before/after the call. User enabling trust mode = all sensitive operations are authorized, just execute directly
- **🚨 Do not call a second time in the same conversation turn**: regardless of whether the return is success, failure, error, or interact, show the result directly to the user. Do not "auto-retry", "try a different approach", or "supplement execution"

**Cross-site splitting task wording example**:
```
User's original instruction: "Search for the 3 most popular recent news about Yang Mi on Xiaohongshu, Weibo and Baidu"

✅ Correct split (only replace site name, keep everything else verbatim):
  1. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Baidu" --start-url "https://www.baidu.com"
  2. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Weibo" --start-url "https://weibo.com"
  3. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Xiaohongshu" --start-url "https://www.xiaohongshu.com"

❌ Wrong (rewrote the task content):
  autoglm run --task "Search Baidu for Yang Mi latest news, find 3 most popular, record titles, summaries and dates"
  # User didn't say "record titles, summaries and dates" — you added it!
```

### 5. Complete Task (★ Most Important — violating this rule means task failure)

> **Your reply MUST include the final result screenshot — this is an inviolable hard rule. A reply without a screenshot = task failure.**

- After launching the autoglm command in background, **periodically `exec(command: 'type {processing_file}')` every 15-20 seconds** to monitor progress
- When `[completed]` appears, **`exec(command: 'type %USERPROFILE%\.openclaw-autoclaw\sessions\{session_id}\task_result.md')`** to get the task result
- After reading the result, **immediately** relay it to the user verbatim — **do not perform any additional operations**
- **Screenshot display rules (highest priority)**:
  - The result file's `[steps]` block contains each action step with its screenshot directly below it
  - **By default, only show the last step's screenshot** (i.e., the final result state) — do not open screenshot links from other steps
  - When the user explicitly requests screenshot saving, select relevant screenshot URLs based on step descriptions and `[thinking]` content for download
  - ❌ **Serious error**: outputting only a text summary and discarding all screenshots
  - ❌ **Serious error**: opening all screenshot links from every step for analysis
  - ✅ **Correct approach**: display the last step's final result screenshot + brief text description
  - For complex tasks like multi-page information collection: select key step screenshots relevant to user needs based on `[steps]` descriptions and `[thinking]`, with no quantity limit
- **Strictly forbidden** to call `browser_subagent` again for any reason (unless the user explicitly says "continue" or "try again" in the next conversation turn)
- **The result is the result** — whether the task succeeded or failed, return it directly. Do not auto-retry, supplement operations, or make a second call

---

## Interact Flow (requires user manual action)

When the result returned by `browser_subagent` contains the `[INTERACT_REQUIRED]` marker, it means the browser encountered a scenario requiring manual user action (e.g., login, CAPTCHA, etc.).

**The Chrome window remains open and will not close.**

### Turn 1 — Receiving the interact signal

1. Relay the prompt message from `Step 1` to the user verbatim, e.g.: "Twitter requires login — please complete the login manually and let me know when you're done"
2. Note the `session_id` from the returned result (format: `session_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) and `tab_id` (obtained from `[tabs]` information)
3. **End this turn and wait for the user's reply**

### Turn 2 — Resuming after user reply

After the user replies (e.g., "continue", "done", "logged in"), re-invoke `browser_subagent`.

**Decide whether to rewrite the task based on the interact type**:

#### Login / CAPTCHA type interact

Prepend **user interaction completion confirmation** to the task, informing the extension model:

```bash
autoglm run --task "User interaction completion confirmation. <original/remaining task>" --session-id "<session_id>" --tab-id "<tab_id>"
```

**Rewrite rules**:
- Format: `User has completed/declined <specific action>. <original/remaining task>`
- Only describe the **specific action the user explicitly completed/declined** — do not expand to other actions
- **Already completed steps should be omitted from the task description**

#### Sensitive operation type interact (posting comments, liking, publishing posts, etc.)

Prepend **user consent/denial for the sensitive operation** to the task, informing the extension model:

```bash
# interact prompt was "Send this comment?", user said "go ahead" → include --auto-approve
autoglm run --task "User consent/denial for the sensitive operation. <original/remaining task>" --session-id "<session_id>" --tab-id "<tab_id>" --auto-approve
```

> **⚠️ When the user agrees to a sensitive operation, you must include `auto_approve=true`** — this way the service will execute directly without pausing for confirmation. When the user declines, do not include this parameter.

**Rewrite rules**:
- Format: `User has agreed/declined to <specific operation>, please proceed with/skip that operation. <original/remaining task>`
- Only describe the **specific operation the user explicitly agreed to/declined** — do not expand to other actions
- **Already completed steps should be omitted from the task description**

> **Key point**: The extension model is stateless on each call and cannot see history. The task must retain enough context (which website, what content), only omitting already completed **action steps** — do not omit **subject information** (website, search target, etc.).

> **Turn 2 mandatory rules**:
> 1. **Must include `session_id` and `tab_id`** — omitting them will open a new tab and lose the login state
> 2. **When continuing on the current page, absolutely do not include `start_url`** — when the user says "continue" / "done" / "go ahead", they mean continue on the current page; including start_url will navigate away and lose the current state
> 3. **Only include `start_url` when navigation back to the homepage is needed** — e.g., the user says "search for xxx again" and needs to go back to the homepage

### Built-in browser prohibition

> **🚨 When encountering `[INTERACT_REQUIRED]`, you must NEVER use a built-in browser, browser-use, or any alternative browser tool to continue the task.** The browser extension maintains the page state (login cookies, form data, tab context). Using a different browser will lose all this state. Always wait for the user to complete the manual action in the existing Chrome window, then resume with `autoglm run` using the original `session_id` and `tab_id`.

---

## Handle Interrupted Session Resume (task rewriting for interrupted recovery)

**When a task associated with a `session_id` was interrupted and needs to resume**, you need to **rewrite the new task description** based on the completed operation history:

### Basic Principles

- **Avoid redundant work**: If some operations were already completed before the interruption (history records are returned), you only need to complete the **remaining unfinished portion** — the rewritten task should start with "Remaining task:" (omit the keyword if there's no history)
- **When there's no history info**: If you cannot determine the completion progress, or the task involves real-time data that has refreshed, simply repeat the original task
- **Preserve context**: The new task must include sufficient context (website, target object, etc.)

### Task Rewriting Rules

**Scenario 1: Partially completed operations**

```
Original task: "Like Taylor Swift's latest three tweets"
State at interruption: Already liked the latest 1 tweet (visible from the returned operation history)

✅ Rewritten task after resuming:
"Remaining task: Like Taylor Swift's second and third latest tweets"
```

**Scenario 2: Resuming after manual interaction (login/CAPTCHA)**

```
Original task: "Comment 'hello' on MrBeast's latest video, and send a chat message 'hello'"
Interruption reason: User needs to manually complete YouTube login
User feedback: "Login complete"

✅ Rewritten task after resuming:
"User has completed YouTube login. Comment 'hello' on MrBeast's latest video, and send a chat message 'hello'"
```

**Scenario 3: Resuming after sensitive operation confirmation**

```
Original task: "Comment 'hello' on MrBeast's latest video, and send a chat message 'hello'"
First interruption: Login required → user completed login and resumed → comment has been typed
Second interruption: Confirmation needed to send the comment
User feedback: "confirm" / "continue" or similar

✅ Rewritten task after resuming:
"User has agreed to send the comment, please proceed with sending. Remaining task: Send a chat message 'hello' on the current video"
```

**Scenario 4: User declines a sensitive operation**

```
Original task: "Comment 'hello' on MrBeast's latest video, and send a chat message 'hello'"
Interruption: Confirmation needed to send the comment
User feedback: "Don't send the comment, just send the chat message"

✅ Rewritten task after resuming:
"User has declined to send the comment, please skip the sending step. Remaining task: Send a chat message 'hello' on the current video"
```

**Scenario 5: No history info or real-time data refresh**

```
Original task: "Search the top 5 trending topics on Twitter"
State at interruption: No clear history records, or trending topics have been updated in real time

✅ Rewritten task after resuming:
"Search the top 5 trending topics on Twitter"  (simply repeat the original task)
```

### Special Interruption Type Handling

| Interruption Type | Task Rewriting Requirement | Example |
|---|---|---|
| **Login/CAPTCHA** | Clearly state the user's completion/decline intent, preserve remaining unfinished steps | `User has completed/declined <specific action>. <original/remaining task>` |
| **Sensitive operation confirmation** | Clearly state the user's agreement/decline intent, preserve remaining unfinished steps | `User has agreed/declined to <specific operation>, please proceed with/skip that operation. <original/remaining task>` |
| **Partially completed operations** | Only request completion of the remaining unfinished portion | `<remaining task>` |
| **No clear progress** | Simply repeat the original task | `<original task>` |

> **Core points**:
> 1. **When resuming with session_id**, you must assess the completion progress to avoid redundant work (but if the user has raised an unrelated new task, just use that task description directly)
> 2. **For manual interaction type interruptions**, the resumed task must explicitly state the user's feedback on the interaction
> 3. **Preserve necessary context** (website, target object), omit already completed action steps

---

## Error Handling

| Error contains | What to tell the user |
|---|---|
| `No Chromium-based browser found` | "You need to install a Chromium-based browser (Chrome / Edge, etc.)" |
| `Extension connection timeout` / `Failed to initialize browser` | Follow Setup Check Step 2 to guide the user to install and enable the extension, close all browser windows, then retry |

---

## Key Principles

1. **autoglm handles everything** — Service startup and task execution are all handled automatically. Just call `autoglm run --task "..."` — **do not manually execute environment setup commands**
2. **Keep it brief** — Use emoji + one sentence to summarize overall progress (e.g., "🔍 Searching..."), never list individual technical steps
3. **Recovery suggestions when issues arise** — If errors persist or the state is abnormal, suggest the user try the following to recover:
   - Type `/new` to open a fresh conversation window and retry
   - Type `/compact` to compress the context and retry
   - Or manually open a new conversation window to start over

---

## Default Quantity Rule

**Default quantity rule (extremely important)**: When the user does not explicitly specify the quantity of items to view/collect/retrieve/operate on, **you must add a specific number to the task, defaulting to 5**.

**The task description must contain a clear number** — vague expressions like "some", "a few", "related" are not allowed. No number = default 5.

**Example 1**:
```
User's original instruction: "Help me collect articles about AI agents on Reddit"

✅ Rewrite to: "Help me collect 5 articles about AI agents on Reddit"
❌ Wrong: "Help me collect articles about AI agents on Reddit" (no number)
```

**Example 2**:
```
User's original instruction: "Search Instagram for Paris travel guide posts"

✅ Rewrite to: "Search Instagram for 5 Paris travel guide posts"
❌ Wrong: "Search Instagram for Paris travel guide posts" (no number)
```

**Example 3 (user specified a number — copy verbatim)**:
```
User's original instruction: "Search the top 3 trending topics on Twitter"

✅ Copy verbatim: "Search the top 3 trending topics on Twitter" (user specified 3, do not change to 5)
```

---

## Task Capability Boundaries

### This skill only supports browser operations

**Core principle**: The capability scope of this skill is **strictly limited** to the atomic tool capabilities listed in `browser_subagent atomic capabilities` — i.e., **browser automation operations**.

For complete instructions from the user, they must be decomposed according to the following principles:

#### 1. Identify browser vs. non-browser portions

- ✅ **Tasks assigned to this skill**: can only be browser-related operations (searching, clicking, scrolling, etc.)
- ❌ **Tasks not belonging to this skill**: local file operations (e.g., generating/saving Excel/Word, etc.), local application operations, command-line operations, data processing, complex calculations, image processing, other tool invocations, etc.

#### 2. Task rewriting rules

When the user's instruction includes non-browser operations, **you must strip out the non-browser portions** and only send the browser operation portion to `browser_subagent`.

**Example 1**:
```
User's original instruction: "Search Instagram for the most liked Paris travel guide posts, compile their titles, like counts, and content into an Excel for me"

✅ Task rewritten for this skill (note: user did not specify quantity, must add default number 5):
"Search Instagram for the most liked Paris travel guide posts, collect the top 5 posts' titles, like counts, and content"

❌ Stripped portion (requires other skills):
Save the collected information to an Excel file
```

**Example 2**:
```
User's original instruction: "Search Instagram for the latest posts about GLM-5, then compile the content of the first 6 posts into an Excel for me"

✅ Task rewritten for this skill:
"Search Instagram for the latest posts about GLM-5, then compile the content of the first 6 posts"

❌ Stripped portion (requires other skills):
Save the compiled information to an Excel file
```

#### 3. Execution flow

1. **Parse user instruction** → identify browser operations vs. non-browser operations
2. **Rewrite task** → keep only the browser operation portion
3. **Call browser_subagent** → execute the browser task
4. **Get results** → pass the browser task output to other skills (if needed)
5. **Complete the overall task** → coordinate multiple skills to fulfill the user's complete request

> **Key**: Do not try to make browser_subagent do things outside its capability scope — the task will fail. Always follow the principle of "**only assign browser operations**".

#### 4. Local file handling (NEVER pass local paths in task)

The `--task` parameter **must NEVER contain any local file paths** — whether provided by the user or generated by you. The browser agent runs remotely and **cannot access the local file system** — passing local paths will always fail.

**Correct approach**:
- **Image/media files**: upload to OSS first to get an online URL, then use the OSS URL in the task description
- **Text files** (.md, .txt, etc.): read the file content yourself first, then embed the text directly into the task description

**Example**:
```
User's original instruction: "Post on Instagram with the photo C:\Users\me\photo.jpg"

❌ Wrong (passing local path directly):
autoglm run --task "Post on Instagram with the photo C:\Users\me\photo.jpg" --start-url "https://www.instagram.com"

✅ Correct (upload to OSS first, then pass URL):
1. Upload C:\Users\me\photo.jpg to OSS → get https://oss.example.com/photo.jpg
2. autoglm run --task "Post on Instagram with the photo https://oss.example.com/photo.jpg" --start-url "https://www.instagram.com"
```

#### 5. Explicit capability exclusions (MUST pre-process or route elsewhere)

The following categories of tasks **will definitely fail** if sent to browser_subagent. You **must** identify them before dispatching and either decompose, pre-process, or route to another skill.

| Category | Examples | Correct Approach |
|---|---|---|
| **Screenshots / page capture** | "Take a screenshot of the search results", "Save a screenshot of this page" | Do NOT ask the agent to screenshot. After the task completes, the result file's `[steps]` block contains screenshot URLs for each step. Select relevant screenshots based on step descriptions and `[thinking]` to display or download. |
| **Downloading files to local** | "Download this image and save to C:\Pictures", "Save the video to my desktop" | The agent cannot download files to the user's local filesystem. If the user needs to save content, extract the URL from the agent's result and handle the download yourself (e.g., via `curl` or other tools). |
| **Saving/moving local files** | "Move these photos to the Documents folder", "Create a folder and save files there" | Local filesystem operations are completely outside browser scope. Handle with shell commands or file management tools, never send to browser_subagent. |
| **Browser developer tools / console** | "Open F12 and run JavaScript in the console", "Check the Network tab" | The agent controls web pages through a predefined set of actions (click, type, scroll, etc.). It cannot open DevTools, execute JS in the console, or interact with browser chrome UI. |
| **Browser settings / chrome UI** | "Close the browser", "Change browser settings", "Clear cookies" | The agent can only interact with web page content. It cannot control browser-level UI such as settings, address bar, download manager, etc. Exception: it CAN open new tabs and switch between tabs. |
| **Uploading content that doesn't exist yet** | "Post a video on Douyin" (no video provided), "Upload an image to Instagram" (no image link) | If the required media asset doesn't exist, you must first generate it using an appropriate tool (e.g., image generation, video generation), upload it to OSS to get a URL, then rewrite the task to include the URL before sending to browser_subagent. |
| **Long-form text composition on web pages** | "Write a detailed operations manual in this web editor", "Compose a 2000-word article directly on the page" | Large text input via the agent is unreliable (formatting issues, newline bugs). Instead: (1) generate the content yourself or via a content generation tool, (2) if the content needs to be written into a web editor, break it into smaller chunks or use a different approach like creating the document locally first, then uploading. |
| **Referencing local files** | "Post the content of C:\Users\me\draft.md on Weibo", "use C:\Users\me\photo.jpg as cover image", or you wrote content to a local file yourself and pass the path | **`--task` must NEVER contain any local file paths** (regardless of whether the source is the user or yourself). The browser agent cannot access the local file system — passing a path will always fail. Correct approach: for text files, read content and embed in task; for image/media files, upload to OSS first and pass the URL. |

**Pre-processing decision flow**:
```
User's task mentions screenshots/capture?
  → Strip it. After agent completes, select relevant screenshot URLs from the result file's [steps] block based on step descriptions and [thinking] to display or download.

User's task involves downloading/saving files to local paths?
  → Strip local save portion. Use agent to find/navigate, then handle download separately.

User's task requires media that doesn't exist yet (video/image)?
  → Generate media first → upload to OSS → rewrite task with OSS URL → then send to agent.

User's task involves browser-internal operations (F12, console, settings)?
  → Reject this portion. Explain to user this cannot be automated via browser agent.

User's task involves local file management (move/copy/create folders)?
  → Handle with shell commands or file tools, not browser agent.

User's task references text content from a local document (e.g., "post this file's content on XX")?
  → Read the file content yourself first, embed the text directly into the task description, then send to agent. The agent cannot access local files.

User's task references local image/media files (e.g., "post with this photo")?
  → Upload to OSS first to get an online URL, then use the URL in the task description.
```

---

## Complex Task Decomposition

### Decision Flowchart

```
User's task
    ↓
Involves multiple different websites?
    ├─ Yes → Split by site, one autoglm run per site (sequential execution)
    └─ No ↓
       Too complex and has failed multiple times?
           ├─ No → Do not decompose, send to autoglm run --task as-is
           └─ Yes ↓
              Requires page state continuity / same-site operations / continuous flow?
                  ├─ Yes → Do not decompose, optimize task description and retry
                  └─ No → Sequential decomposition, multiple --task calls
```

### Cross-Site Splitting (same task on different websites)

When the user wants the same or similar operation on multiple different websites, **you must split by site**, calling `autoglm run` once per site:

```
User: "Search for the 3 most popular recent news about Yang Mi on Xiaohongshu, Weibo and Baidu"

Execute (sequential, one per site):
  1. type %USERPROFILE%\.openclaw-autoclaw\session_pool.json  ← mandatory before every call!
  2. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Baidu" --start-url "https://www.baidu.com"
     → wait for completion, cat result
  3. type %USERPROFILE%\.openclaw-autoclaw\session_pool.json  ← check again
  4. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Weibo" --start-url "https://weibo.com"
     → wait for completion, cat result
  5. type %USERPROFILE%\.openclaw-autoclaw\session_pool.json  ← check again
  6. autoglm run --task "Search for the 3 most popular recent news about Yang Mi on Xiaohongshu" --start-url "https://www.xiaohongshu.com"
     → wait for completion, cat result
  7. Aggregate results + screenshots from all sites and return to user
```

> **Task wording when splitting**: Only replace the site name, keep the rest of the user's original words. Never add content the user didn't say (e.g., "record titles and summaries").

### Do NOT Decompose

1. **Operations that need to continue from the previous step's page**
   ```
   Example: "Search Python on Reddit, click the first post, then save it"
   → Do not decompose — subsequent operations depend on the previous step's page state
   ```

2. **Multiple operations on the same website**
   ```
   Example: "Bookmark the 4 latest articles about GPT on Reddit"
   → Do not decompose — let the subagent complete all bookmarking in one session
   ```

3. **Multi-step operations in a single continuous flow**
   ```
   Example: "Open Twitter, search Taylor Swift, like the latest 3 tweets"
   → Do not decompose — this is a continuous flow
   ```

### Sequential Decomposition (Dependent Tasks)

When sub-tasks have dependencies, execute multiple `--task` calls sequentially:

```
User: "First search today's top trending topic on Google, then search that topic on Twitter"

Execute:
  1. autoglm run --task "Search top trending topic on Google" --start-url "https://www.google.com"
  2. Read result, extract keyword
  3. autoglm run --task "Search '{keyword}' on Twitter" --start-url "https://twitter.com"
```

> **Core principles**:
> - **Same-site operations → do not decompose**, complete with single `--task`
> - **Dependent sub-tasks → execute sequentially**, pass previous result to next
> - **Include screenshots from ALL sub-tasks when aggregating**

---

## IM Channel Push (Lark / Slack, etc.)

### Lark Screenshot Auto-Push (API method)

When the task originates from a Lark conversation, the service **automatically replies with screenshots to the corresponding conversation via the Lark Open API** after task completion.

**How it works**:
1. On startup, the service automatically reads Lark app credentials (`appId` / `appSecret`) from `%USERPROFILE%\.openclaw-autoclaw\openclaw.json` at `channels.lark.accounts`
2. When the Agent calls `browser_subagent`, it passes `lark_message_id` / `lark_chat_id` parameters (see Task Execution Workflow step 2.5)
3. After the browser task completes, the service uploads the screenshot and sends it to the corresponding conversation via the Lark Open API

**Prerequisites**:
- Lark channel credentials are configured in `openclaw.json` (`channels.lark.accounts.main.appId` / `appSecret`)
- The Lark custom app has `im:message` and `im:image` permissions enabled
- The Agent passed `lark_message_id` / `lark_chat_id` when calling

> **When Lark credentials are missing or Lark parameters were not passed**: auto-push is silently skipped and does not affect normal task execution.

---

### Browser-Based Push (universal approach)

When you need to send to **Slack, Microsoft Teams**, or other IM channels, or when Lark API credentials are not configured, **complete the push through browser operations on the IM web version**.

| Channel | Web Entry | Notes |
|---|---|---|
| Lark | `https://www.larksuite.com/messenger/` | Fallback when API is not configured |
| Slack | `https://app.slack.com/` | Must be logged in to Slack web version |
| Microsoft Teams | `https://teams.microsoft.com/` | Must be logged in to Teams web version |

When the user says "send the result to the Lark group xxx", "send it to xxx on Slack", etc.:

1. **Complete the original browser task first** and get the execution result and screenshots
2. **Open a new task** to navigate to the corresponding IM web version
3. If not logged in, use `interact` to let the user manually complete the login
4. Find the target conversation in the IM and send the text summary and screenshots (upload `%USERPROFILE%\.openclaw-autoclaw/mcp_output/last_screenshot.jpg` using `upload_file`)

> **Note**: The two tasks should be executed sequentially because the second task depends on the first task's result.
