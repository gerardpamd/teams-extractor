# Using Teams Extractor

This guide covers how to use every feature of Teams Extractor after it is installed. If you have not set it up yet, see [INSTALL.md](INSTALL.md) first.

**Before each session:** make sure the dot in the popup is green. If it is grey or red, the native host is not running — see the Troubleshooting section in INSTALL.md.

---

## The popup at a glance

Click the Teams Extractor icon in your Edge toolbar to open the popup. Here is what you see:

- **Colored dot** (top-right) — green means the native host is connected and ready. Grey or red means something is wrong.
- **Extract Chat** button — one-click extraction of the current Teams view.
- **Start Caption Capture / Stop Caption Capture** button — toggles live caption recording on and off.
- **Status message** — shows what happened after your last action (e.g., "Extraction complete — 42 messages").
- **Settings** — click the "Settings" row to expand a panel with options.

[screenshot: Teams Extractor popup showing all elements labeled — green dot, Extract Chat button, caption toggle, status message, Settings section]

---

## 1. Extracting a channel conversation

Use this when you are in a Teams channel and want to capture the messages visible in that channel.

1. In Microsoft Teams (browser, at `teams.microsoft.com`), navigate to the channel you want to capture.
2. Scroll up to load as many messages as you need — Teams only shows what is on screen unless you scroll.
3. Click the Teams Extractor icon in the Edge toolbar.
4. Click **Extract Chat**.
5. The button briefly disables while the extraction runs. The status message will update to show something like "Extraction complete — 38 messages".
6. Your file is saved to: `~/teams-extractor/data/channels/`

**Filename format (by-date, the default):**
`channel_YYYY-MM-DD_HHMMSS.md`

**Filename format (by-source):**
`channel_<channel-name>_YYYY-MM-DD.md`

[screenshot: Teams channel page with the Teams Extractor popup open and "Extraction complete" showing in the status area]

---

## 2. Extracting a 1:1 or group chat

The flow is identical to a channel extraction, but you navigate to a chat first.

1. In Teams, click on the **Chat** section in the left sidebar and open the 1:1 or group chat you want to capture.
2. Scroll up to load the messages you need.
3. Click the Teams Extractor icon.
4. Click **Extract Chat**.
5. Your file is saved to: `~/teams-extractor/data/chats/`

The extracted file includes a participant list pulled from the chat header.

[screenshot: Teams 1:1 chat page with extraction popup showing success]

---

## 3. Extracting a meeting chat

Meeting chat is the side panel that appears during or after a meeting. You can capture it either while the meeting is in progress or after it ends (Teams keeps the chat visible in the meeting recap).

**During a meeting:**
1. Open the meeting in Teams and make sure the chat panel is visible.
2. Click the Teams Extractor icon and click **Extract Chat**.
3. Your file is saved to: `~/teams-extractor/data/meetings/`

**After a meeting:**
1. Find the meeting in your Teams calendar or chat history and open the recap.
2. The meeting chat should be visible. Click the Teams Extractor icon and click **Extract Chat**.

[screenshot: Teams meeting view with chat panel open and extraction popup in the corner]

---

## 4. Capturing live captions

Caption capture is different from chat extraction — instead of reading what is already on the page, it watches the captions as they appear in real time and accumulates them into a file.

**Before you start:** you must enable live captions in Teams first. In a Teams meeting, click the three-dot menu (More) → Turn on live captions. Teams will start showing a captions bar at the bottom of the meeting window.

1. Once live captions are visible in the meeting, click the Teams Extractor icon.
2. Click **Start Caption Capture**. The button turns red to show recording is active. The popup will say "Caption capture active".
3. Close the popup — the extension keeps recording in the background even with the popup closed.
4. When you are done (end of meeting, or when you have captured enough), click the icon again.
5. Click **Stop Caption Capture** (the same button, now labeled differently).
6. Your file is saved to: `~/teams-extractor/data/meetings/`

**What the file contains:** each caption entry is saved with the speaker name and the text as it was finalized by Teams. The output looks like:

```
**Shashi Gandham** (14:03): We need to decide on the MI455 schedule this week.
**Gerard Pietryk** (14:03): I can have a draft ready by Thursday.
```

[screenshot: Teams meeting with live captions bar visible at the bottom]
[screenshot: Teams Extractor popup with "Stop Caption Capture" button highlighted in red]

---

## 5. Settings

Click the **Settings** row in the popup to expand the settings panel.

| Setting | What it does |
|---|---|
| **Output directory** | Where extracted files are saved. Default: `~/teams-extractor/data/`. Change this if you want files in a different location on your WSL filesystem. |
| **File naming** | **By date** names files with a timestamp (e.g., `chat_2026-05-04_143022.md`). **By source** names files using the channel or chat name (e.g., `chat_general-rccl_2026-05-04.md`). |
| **Scope** | **Current view** extracts only the messages currently visible on screen. **All loaded messages** extracts everything Teams has loaded into the page — useful if you scrolled up a long way. |

Click **Save** after making any changes. The popup will confirm "Settings saved." briefly.

[screenshot: Teams Extractor popup with Settings panel expanded, showing all three options]

---

## 6. Finding your extracted files

All extracted files land in your WSL home directory under `~/teams-extractor/data/`. The subfolder depends on what you extracted:

| Content type | Subfolder |
|---|---|
| Channel conversation | `~/teams-extractor/data/channels/` |
| 1:1 or group chat | `~/teams-extractor/data/chats/` |
| Meeting chat or captions | `~/teams-extractor/data/meetings/` |

**To view a file in WSL:**
```
ls ~/teams-extractor/data/channels/
```

**Example filename:** `channel_2026-05-04_143022.md`

**Each file starts with a header block** that captures metadata:
```
---
source: channel
name: general-rccl
participants: [Shashi Gandham, Gerard Pietryk, Marc, ...]
extracted: 2026-05-04T14:30:22Z
message_count: 42
---
```

Followed by the messages themselves, with speaker names and timestamps.

---

## 7. Running the agent pipeline

The agent pipeline is a set of five Claude Code skills that read your extracted `.md` files and turn them into useful outputs. You run them by typing a slash command in Claude Code after you have extracted a conversation from Teams.

**Output folders:**

| What it produces | Where it saves |
|---|---|
| Conversation summaries | `~/teams-extractor/output/summaries/` |
| Action item checklists | `~/teams-extractor/output/action-items/` |
| Weekly status report drafts | `~/teams-extractor/output/status-reports/` |
| JIRA ticket drafts | `~/teams-extractor/output/jira-drafts/` |

---

### Recommended workflow

The best way to get started is to run `/teams-digest` first. It covers the most common needs in a single command. Once you have your digest, you can use the individual skills to go deeper on any specific conversation.

```
Step 1: Extract a Teams conversation using the extension
         (click Extract Chat — file lands in ~/teams-extractor/data/)

Step 2: In Claude Code, run /teams-digest --new
         (processes any files that have not been analyzed yet)

Step 3: Review the summary, action items, and JIRA drafts in the output folders

Step 4: For any JIRA draft you want to file, run /jira-story, /jira-task, or /jira-bug
         (paste the draft content as context when prompted)
```

---

### /teams-digest — start here

`/teams-digest` runs the full pipeline in one pass. For each conversation file it processes, it produces a summary, an action item list, and (if there are enough messages with actionable content) JIRA ticket drafts.

**How to run it:**

| Command | What it does |
|---|---|
| `/teams-digest` | Processes only files that have not been analyzed yet (recommended for daily use) |
| `/teams-digest --new` | Same as above — `--new` is the default |
| `/teams-digest --all` | Re-processes every file in `data/`, including ones already analyzed |
| `/teams-digest channel_2026-05-06_143022.md` | Processes one specific file |

**Use `--new` day-to-day.** After you extract one or more conversations, run `/teams-digest --new` and Claude will pick up anything that has not been processed yet.

**Use `--all` when you want a fresh pass.** If you have updated a conversation file or want to regenerate everything from scratch, `--all` will reprocess all files.

**Example output in chat:**

```
# Teams Digest — 2026-05-06

## Files Processed: 1

---

### channel_2026-05-06_143022.md

**Summary:**
- MI450-MC scatter regression (~18% throughput drop on 8-node) was discovered
  in overnight CI; Marcus Webb submitted fix PR #1847 for review.
- Collective Ops API v2 timeout parameters are undocumented; Priya Nair will
  submit a docs PR by Wednesday.
- Q2 planning deck for Shashi is due May 15; all team leads to submit highlights
  and risks by EOD Wednesday.

**Action Items:**
- [ ] **Marcus Webb**: Merge PR #1847 after reviews *(by: Thursday 2026-05-08)*
- [ ] **Priya Nair**: Submit docs PR for API v2 timeout parameters *(by: Wednesday 2026-05-08)*
- [ ] **Gerard Pietryk**: Assemble Q2 NPI slides for Shashi *(by: Friday 2026-05-15)*

**JIRA Candidates:**
- MI450-MC Scatter Throughput Regression on 8-Node Configs (Type: Bug, Priority: High)
- Document Collective Ops API v2 Timeout Configuration Parameters (Type: Task, Priority: Medium)

**Output files written:**
- Summary: ~/teams-extractor/output/summaries/channel_2026-05-06_143022.md
- Action items: ~/teams-extractor/output/action-items/channel_2026-05-06_143022.md
- JIRA drafts: ~/teams-extractor/output/jira-drafts/channel_2026-05-06_143022-jira-drafts.md
```

---

### /teams-summarize — summary of a single conversation

`/teams-summarize` reads one conversation file and produces a 3-5 bullet point summary covering: key topics discussed, decisions made, notable conclusions, and any blockers or risks raised.

**How to run it:**

```
/teams-summarize channel_2026-05-06_143022.md
```

If you do not provide a filename, Claude will list the 10 most recent files in `data/` and ask you to pick one.

**Output** is saved to `~/teams-extractor/output/summaries/<filename>.md` and printed in the chat.

**Example output:**

```
# Summary: rccl-npi-general

**Source:** channel
**Date:** 2026-05-06
**Participants:** Sarah Chen, Marcus Webb, Priya Nair, Jordan Kim, Gerard Pietryk
**Messages:** 28

## Key Points

- A regression in MI450-MC scatter performance was discovered overnight, showing
  ~18% throughput degradation on 8-node configurations; Marcus Webb identified
  the root cause and raised fix PR #1847 for review.
- The Collective Ops API v2 documentation is missing timeout configuration
  parameters; Priya Nair committed to submitting a docs PR by Wednesday.
- The Q2 planning deck for Shashi is due May 15; all team leads to submit
  highlights and risks by EOD Wednesday.
```

---

### /teams-actions — action item checklist

`/teams-actions` reads one conversation file and pulls out everything that someone committed to doing — tasks, follow-ups, assignments, and deadlines — formatted as a checkbox checklist.

**How to run it:**

```
/teams-actions channel_2026-05-06_143022.md
```

If you do not provide a filename, Claude will list recent files and ask you to pick one.

**Output** is saved to `~/teams-extractor/output/action-items/<filename>.md` and printed in the chat.

**Example output:**

```
## Action Items

- [ ] **Marcus Webb**: Merge PR #1847 (scatter regression fix) after reviews *(by: Thursday 2026-05-08)*
- [ ] **Sarah Chen**: Review PR #1847 *(by: EOD 2026-05-06)*
- [ ] **Priya Nair**: Submit docs PR for Collective Ops API v2 timeout parameters *(by: Wednesday 2026-05-08)*
- [ ] **Gerard Pietryk**: Update the JIRA milestone ticket once PR #1847 CI passes *(by: Thursday 2026-05-07)*
- [ ] **Gerard Pietryk**: Assemble and submit Q2 NPI workstream slides for Shashi *(by: Friday 2026-05-15)*
```

---

### /teams-status — weekly TPM status report

`/teams-status` looks across all conversation files in a date range and compiles them into a single weekly status report in TPM format. This is the skill to use when you want a consolidated view of everything that happened in a given week, rather than a per-conversation breakdown.

**How to run it:**

| Command | What it covers |
|---|---|
| `/teams-status` | Last 7 days (default) |
| `/teams-status last-week` | The 7 days ending yesterday |
| `/teams-status today` | Today only |
| `/teams-status 2026-05-01:2026-05-06` | A specific date range |

**Output** is saved to `~/teams-extractor/output/status-reports/status-report-<start-date>.md` and printed in the chat.

The report includes: an executive summary paragraph, a breakdown by conversation, all decisions made that week, an open action item list, and any blockers or risks mentioned.

**When to use `/teams-status` vs. `/teams-digest`:**

- Use `/teams-digest` when you want to process new conversations right after extracting them. It handles one or a few files and gives you a per-conversation breakdown.
- Use `/teams-status` when you want a consolidated view across an entire week — for example, to draft a status update for your manager or to review the week before a planning meeting.

---

### /teams-jira — JIRA ticket drafts from a conversation

`/teams-jira` reads one conversation file and identifies up to 5 items that should become JIRA tickets — bugs, feature requests, or tasks — and drafts each one with a title, type, priority, description, and acceptance criteria.

**How to run it:**

```
/teams-jira channel_2026-05-06_143022.md
```

If you do not provide a filename, Claude will list recent files and ask you to pick one.

**Output** is saved to `~/teams-extractor/output/jira-drafts/<filename>-jira-drafts.md` and printed in the chat.

**Example draft ticket:**

```
## Draft Ticket: MI450-MC Scatter Throughput Regression on 8-Node Configs

**Type:** Bug
**Priority:** High
**Summary:** ~18% scatter throughput regression on 8-node MI450-MC configurations
             introduced by MSCCL buffer alignment change in commit a7f3c91.
**Description:**
Overnight benchmarking revealed an 18% throughput regression in scatter operations
on 8-node MI450-MC configurations. The regression was traced to commit a7f3c91,
which changed the MSCCL scheduler's memory pool allocator. Fix PR #1847 is under review.
**Acceptance Criteria:**
- [ ] test_allreduce_perf_8node passes in CI on 8-node MI450-MC configuration
- [ ] Scatter throughput on 8-node returns to baseline (≥42.3 GB/s)
- [ ] Fix is validated on both default and IB transport paths
**Mentioned by:** Sarah Chen, Marcus Webb, Priya Nair
```

This skill only produces drafts — it does not create anything in JIRA. To file a ticket, use `/jira-story`, `/jira-task`, or `/jira-bug` and paste the draft content as context.

Note: `/teams-digest` already includes JIRA drafts as part of its full-pipeline pass. Run `/teams-jira` separately only if you want to focus on one specific conversation or re-draft tickets for a file you have already processed.

---

### Skill quick-reference

| What you want | Command |
|---|---|
| Process everything new since your last run | `/teams-digest --new` |
| Process one specific file, all outputs | `/teams-digest channel_2026-05-06_143022.md` |
| Reprocess all files from scratch | `/teams-digest --all` |
| Summary of one conversation | `/teams-summarize channel_2026-05-06_143022.md` |
| Action item checklist for one conversation | `/teams-actions channel_2026-05-06_143022.md` |
| JIRA drafts for one conversation | `/teams-jira channel_2026-05-06_143022.md` |
| Weekly status report across multiple conversations | `/teams-status last-week` |

---

## Troubleshooting

### No file was created after clicking Extract Chat

Check the dot in the popup — if it is grey or red, the native host is not connected and no file can be written. Refer to INSTALL.md Troubleshooting for steps to fix the connection.

If the dot is green but no file appears, try:
1. Check that the output directory in Settings exists on your WSL filesystem. Open a WSL terminal and run `ls ~/teams-extractor/data/`.
2. Re-run the extraction once more and watch the status message carefully for any error text.

### The extracted file is empty or has very few messages

Teams loads messages progressively as you scroll. If you click Extract Chat before Teams has finished rendering the page, you may get an empty or partial file.

1. Wait for the Teams page to fully load (the spinning indicators in the message list should be gone).
2. Scroll up through the conversation to load the messages you need.
3. Then click Extract Chat.

### Captions are not being detected

Live caption capture requires that Teams' caption feature is actively running. If the capture runs but produces no output:

1. Make sure you enabled live captions in Teams before starting capture (meeting three-dot menu → Turn on live captions).
2. The captions bar must be visible at the bottom of the meeting window.
3. Teams occasionally updates its page structure, which can break caption detection. If this happens, check for an updated version of the extension.

### The status message shows an error in red text

Red text in the status area means the extraction attempted but something went wrong. Common messages:

- **"Content script did not respond"** — the extension could not communicate with the Teams tab. Make sure you are on a `teams.microsoft.com` page and Teams has fully loaded.
- **"Native host error"** — the Python script encountered a problem writing the file. Check that your output directory exists and that WSL is running.
