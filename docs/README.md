# Teams Extractor

Teams Extractor is a Microsoft Edge browser extension that captures conversations from Microsoft Teams — channels, chats, meeting chat, and live captions — and saves them as plain-text Markdown files on your WSL filesystem. Once captured, a set of Claude Code agent skills can process those files automatically, turning raw conversations into meeting summaries, action item lists, weekly status report drafts, and JIRA ticket drafts.

---

## Architecture

```
Edge Browser                    Windows Bridge              WSL Filesystem
┌─────────────────────┐         ┌──────────────┐         ┌────────────────────────┐
│ Teams Web (tab)     │         │ run_host.bat │         │ native-host/           │
│   content.js        │  Native │   (calls     │  stdin/ │   teams_writer.py      │
│   background.js ───►│ Msg ───►│   wsl.exe)   │─stdout─►│                        │
│   popup.html/js     │         └──────────────┘         │ ~/teams-extractor/     │
└─────────────────────┘                                   │   data/                │
                                                          │     channels/          │
                                                          │     chats/             │
                                                          │     meetings/          │
                                                          │   output/              │
                                                          │     summaries/         │
                                                          │     action-items/      │
                                                          │     status-reports/    │
                                                          │     jira-drafts/       │
                                                          └────────────────────────┘
                                                                    │
                                                                    ▼
                                                          Agent Pipeline
                                                          (5 Claude Code skills — Phase 2 complete)
```

**How the pieces connect:** The extension runs inside Edge on Windows. When you click Extract Chat, it reads the Teams page and sends the conversation data to a small Python script living in WSL. That script writes a `.md` file to your WSL home directory. Agent skills then read those files and produce structured outputs.

---

## What you get

- **Conversation files** — raw transcripts saved as Markdown, one file per extraction, stored in `data/`
- **Summaries** — concise topic-grouped meeting summaries in `output/summaries/`
- **Action item lists** — decisions, to-dos, owners, and deadlines in `output/action-items/`
- **Status report drafts** — weekly TPM-format status reports in `output/status-reports/`
- **JIRA ticket drafts** — draft bugs, tasks, and stories ready to review and file in `output/jira-drafts/`

---

## Quickstart

1. **Install** — Load the extension in Edge and register the native messaging host. See [INSTALL.md](INSTALL.md) for the full step-by-step.
2. **Extract** — Navigate to any Teams channel or chat, click the Teams Extractor icon in your toolbar, and click **Extract Chat**. See [USAGE.md](USAGE.md) for all extraction types.
3. **Process** — In Claude Code, run `/teams-digest --new` to process any newly extracted files. See [USAGE.md — Running the agent pipeline](USAGE.md#7-running-the-agent-pipeline) for all skills and options.

---

## Agent Pipeline (Phase 2 — complete)

Five Claude Code skills are available for processing extracted conversation files. Run them by typing a slash command in Claude Code.

| Skill | Command | What it does |
|---|---|---|
| teams-digest | `/teams-digest [--new\|--all\|file]` | **Recommended starting point.** Runs the full pipeline in one pass — summary, action items, and JIRA drafts for each file. |
| teams-summarize | `/teams-summarize [file]` | 3–5 bullet point summary of a single conversation. |
| teams-actions | `/teams-actions [file]` | Extracts action items with owners and deadlines as a checkbox checklist. |
| teams-status | `/teams-status [date-range]` | Consolidated weekly TPM status report across all conversations in a date range. |
| teams-jira | `/teams-jira [file]` | Drafts up to 5 JIRA ticket candidates (Bugs, Stories, Tasks) from a single conversation. |

For full usage details and examples, see [USAGE.md — Running the agent pipeline](USAGE.md#7-running-the-agent-pipeline).

---

## Folder structure

```
teams-extractor/
├── extension/              Edge extension source (load this folder in Edge)
│   ├── manifest.json       Extension definition
│   ├── content.js          Reads the Teams page DOM
│   ├── background.js       Routes messages, talks to native host
│   ├── popup.html/js/css   The toolbar popup UI
│   └── icons/              Extension icons
│
├── native-host/            The Windows-side bridge to WSL
│   ├── teams_writer.py     Python script that writes .md files (runs in WSL)
│   ├── register.ps1        One-time setup script (run in PowerShell)
│   ├── run_host.bat        Generated by register.ps1 — do not edit
│   └── com.teams_extractor.writer.json   Native messaging manifest
│
├── data/                   Extracted conversation files land here
│   ├── channels/
│   ├── chats/
│   └── meetings/
│
├── output/                 Agent pipeline outputs land here
│   ├── summaries/
│   ├── action-items/
│   ├── status-reports/
│   └── jira-drafts/
│
├── agents/                 Agent role definitions (for Claude Code multi-agent workflow)
├── tests/                  Automated tests for the native host
└── docs/                   You are here
```

---

## Troubleshooting

See the troubleshooting sections in [INSTALL.md](INSTALL.md) and [USAGE.md](USAGE.md).
