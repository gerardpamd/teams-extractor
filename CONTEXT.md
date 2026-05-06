# Teams Extractor — Project Context & Requirements

## Purpose
Edge browser extension that extracts Microsoft Teams web conversations (channels, 1:1/group chats, meeting chat, live captions) and saves them as Markdown files to the WSL filesystem via a Native Messaging Host. Downstream Claude Code agents then process the extracted files into action items, status reports, and JIRA ticket drafts.

## Architecture

```
Edge Browser                          WSL Filesystem
┌──────────────────────┐              ┌──────────────────────────┐
│ Teams Web            │              │ native-host/             │
│  ↓ content.js        │   Native     │   teams_writer.py        │
│  ↓ background.js ────┼── Messaging ─┼──→ ~/teams-extractor/    │
│  ↓ popup.html/js     │   (stdin/    │      data/               │
└──────────────────────┘   stdout)    │        channels/         │
                                      │        chats/            │
                                      │        meetings/         │
                                      │      output/             │
                                      │        summaries/        │
                                      │        action-items/     │
                                      │        status-reports/   │
                                      │        jira-drafts/      │
                                      └──────────────────────────┘
```

## Tech Stack
- **Extension**: Manifest V3, vanilla JS (no framework), Edge-compatible
- **Native Messaging Host**: Python 3 (already available in WSL)
- **Agent Pipeline**: Claude Code skills (`.claude/skills/`)
- **Patterns**: Follow conventions from `~/jira-quality-guard/` (Gerard's existing extension)

---

## Requirements Checklist

### Phase 1: Extension Core

#### 1.1 Manifest & Scaffolding
- [x] `manifest.json` — Manifest V3 with `service_worker`
- [x] `host_permissions` for `https://teams.microsoft.com/*`
- [x] `permissions`: `storage`, `nativeMessaging`
- [x] Content script injected at `document_idle`
- [x] Popup page for settings and trigger buttons

#### 1.2 Content Script — DOM Scraping
- [x] Detect current Teams context (channel / chat / meeting)
- [x] **Channel extraction**: scrape message list from channel view
  - Speaker name, timestamp, message body, reactions
  - Thread/reply detection
- [x] **Chat extraction**: scrape 1:1 and group chat messages
  - Speaker name, timestamp, message body
  - Participant list from chat header
- [x] **Meeting chat extraction**: scrape meeting chat sidebar
- [x] **Live captions**: MutationObserver on captions container
  - Capture speaker + caption text as they appear
  - Accumulate until user stops capture
- [x] Resilient selectors with fallback chains (Teams DOM changes frequently)
- [x] SPA navigation detection (setInterval polling)
- [x] Avoid double-extraction via data attributes

#### 1.3 Background Service Worker
- [x] Message router: receive extraction requests from popup, forward to content script
- [x] Receive extracted data from content script
- [x] Send data to Native Messaging Host via `chrome.runtime.connectNative()`
- [x] Handle connection errors gracefully (host not running, etc.)
- [x] Status tracking: extraction in progress / complete / error

#### 1.4 Popup UI
- [x] Settings panel:
  - [x] Output directory path (default: `~/teams-extractor/data/`)
  - [x] File naming convention toggle (by-date vs by-source)
  - [x] Extraction scope selector (current view / all loaded messages)
- [x] Action buttons:
  - [x] "Extract Chat" — one-shot extraction of current view
  - [x] "Start Caption Capture" / "Stop Caption Capture" — toggle for live captions
- [x] Status indicator: connected to native host (green/red dot)
- [x] Last extraction timestamp and result count

#### 1.5 Native Messaging Host
- [x] `teams_writer.py` — Python script that:
  - Reads JSON from stdin (Native Messaging protocol: 4-byte length prefix + JSON)
  - Converts JSON messages to Markdown format
  - Writes .md files to the configured output directory
  - Returns success/failure response via stdout
- [x] `com.teams_extractor.writer.json` — Native Messaging Host manifest
  - Points to `teams_writer.py` path
  - Declares `allowed_origins` matching extension ID
- [x] Windows registry entry setup script (required for Edge to find the host)
- [x] Markdown output format:
  ```markdown
  ---
  source: channel | chat | meeting-chat | meeting-captions
  name: <channel/chat/meeting name>
  participants: [list]
  extracted: 2026-05-01T14:30:00Z
  message_count: N
  ---

  **Speaker Name** (14:30): Message text here

  **Another Speaker** (14:31): Reply text here
  > Quoted/threaded reply
  ```

### Phase 2: Agent Pipeline

#### 2.1 Summarizer Agent
- [x] Claude Code skill at `~/.claude/skills/teams-summarize/SKILL.md`
- [x] Reads .md files from `data/` directory
- [x] Groups messages by topic/thread
- [x] Produces concise summary → `output/summaries/`

#### 2.2 Action Item Extractor
- [x] Claude Code skill at `~/.claude/skills/teams-actions/SKILL.md`
- [x] Identifies decisions, to-dos, follow-ups, deadlines
- [x] Extracts owner + due date when mentioned
- [x] Outputs structured checklist → `output/action-items/`

#### 2.3 Status Report Drafter
- [x] Claude Code skill at `~/.claude/skills/teams-status/SKILL.md`
- [x] Aggregates summaries from a date range
- [x] Produces weekly status report in Gerard's TPM format
- [x] Output → `output/status-reports/`

#### 2.4 JIRA Ticket Drafter
- [x] Claude Code skill at `~/.claude/skills/teams-jira/SKILL.md`
- [x] Identifies discussed bugs, feature requests, tasks
- [x] Produces draft ticket Markdown → `output/jira-drafts/`
- [x] Format compatible with existing JIRA skills for ticket creation

#### 2.5 Pipeline Orchestrator
- [x] Claude Code skill at `~/.claude/skills/teams-digest/SKILL.md`
- [x] Single entry point: reads new files from `data/`
- [x] Routes to appropriate agents based on content type
- [x] Produces combined digest output

### Phase 3: Polish & Ship

#### 3.1 Testing
- [ ] Content script: manual testing on Teams web against all 4 content types
- [ ] Native host: unit tests for JSON→Markdown conversion
- [ ] Agent pipeline: test with sample .md files
- [ ] End-to-end: extract → file → agent → output

#### 3.2 Documentation
- [ ] README.md — project overview, architecture, quickstart
- [ ] INSTALL.md — step-by-step setup (extension load, native host register, registry)
- [ ] USAGE.md — how to use each feature
- [ ] Agent docs in each skill's SKILL.md

#### 3.3 Ship to GitHub
- [ ] Create GitHub repo
- [ ] .gitignore (data/, output/, credentials)
- [ ] Initial commit with full project
- [ ] Tag v1.0.0

---

## Development Workflow — Multi-Agent

This project is built using a multi-agent Claude Code workflow:

### Agent Roles
| Agent | Definition | Responsibility |
|-------|-----------|----------------|
| **Orchestrator** | `agents/orchestrator.md` | Sequences phases, tracks checklist, resolves blockers |
| **Coder** | `agents/coder.md` | Writes implementation code from specs |
| **Reviewer** | `agents/reviewer.md` | Code quality, security, pattern consistency |
| **Tester** | `agents/tester.md` | Writes tests, runs validation |
| **Documenter** | `agents/documenter.md` | README, install guide, user docs |
| **Shipper** | `agents/shipper.md` | Security scan, .gitignore enforcement, commit + push to GitHub |

### Workflow per feature
Orchestrator → Coder → Reviewer → (Coder if BLOCK) → Tester → Documenter → mark `[x]` in CONTEXT.md

### Ship trigger
Shipper runs once after all checklist items are `[x]`. It enforces .gitignore, scans for secrets/personal data, then commits and pushes.

---

## Key Technical Notes

### Native Messaging on WSL
- Edge runs on Windows, native host runs in WSL
- The registry entry must point to a Windows-side `.bat` wrapper that calls `wsl.exe python3 /path/to/teams_writer.py`
- This is the standard pattern for WSL native messaging hosts

### Teams DOM Considerations
- Teams is a React SPA — DOM structure changes between updates
- Use multiple selector fallbacks (same pattern as jira-quality-guard)
- Use `data-tid` attributes where available (Teams uses these)
- Live captions container: watch for `[data-tid="closed-captions-renderer"]` or similar

### Existing Extension Patterns to Reuse (from ~/jira-quality-guard/)
- Promise-wrapped `chrome.storage.local` access
- `return true` in message listeners for async responses
- SPA navigation detection via setInterval + location.href polling
- ASCII section headers in code for readability
- Error messages that are user-facing and actionable
- Credential indicator dots (green/red) in popup

### Security
- No credentials stored (no Teams auth needed — uses existing session)
- Native host only writes to configured directory
- .gitignore excludes data/ and output/ directories
- Extension only activates on teams.microsoft.com
