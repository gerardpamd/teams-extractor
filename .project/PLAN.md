# Teams Master Command — Design Reference

## Goal

Replace 5 separate `/teams-*` skills with a single `/teams` command that:
1. Lists available conversation files and asks the user to pick one
2. Detects intent from the argument (digest, reply, actions, jira, status, or natural language)
3. Runs the appropriate pipeline inline
4. For `reply` intent: drafts a reply, gets approval, writes `pending-reply.txt`
5. Extension picks up `pending-reply.txt` and shows a staged reply bar above the Teams compose box

---

## Chunk Definitions

### Chunk 1 — `/teams` Skill Skeleton + File Picker
**Files:** `~/.claude/skills/teams/SKILL.md`

File picker logic:
- List all `.md` files in `~/teams-extractor/data/`, sorted newest first, numbered
- Show filename + extracted date (from `extracted:` frontmatter field)
- Ask: "Which conversation? (enter number)"
- Wait for user response
- Exception: if argument is a filename or path, use it directly without listing
- After selection: print "Loaded: `<filename>` — `<N>` messages, extracted `<date>`" and stop

Acceptance criteria:
- `/teams` lists files and waits for selection
- `/teams <filename>` skips listing and loads directly
- Empty data dir → "No conversation files found in ~/teams-extractor/data/. Extract a chat first."

---

### Chunk 2 — Intent Detection + Digest Pipeline
**Files:** `~/.claude/skills/teams/SKILL.md` (extend)

Intent detection (from argument, after file selection):
- No keyword → digest: summary (3–5 bullets) + action items checklist
- `actions` → action items only
- `jira` → JIRA ticket drafts (up to 5)
- `status` → weekly status (date range from argument or last 7 days; no file needed)
- Natural language (no keyword match) → focused summary on that topic/person

Digest output:
- Summary saved to `~/teams-extractor/output/summaries/<basename>.md`
- Action items saved to `~/teams-extractor/output/action-items/<basename>.md`
- Both printed to chat

Acceptance criteria:
- Each intent branch reachable and correct
- Output files written to correct paths
- Natural language hint used to focus the summary

---

### Chunk 3 — Reply Drafting Pipeline
**Files:** `~/.claude/skills/teams/SKILL.md` (extend)

`reply` intent:
1. Identify most recent exchange needing a response (last 5–10 messages + open questions directed at Gerard)
2. Draft reply: 2–4 sentences, Gerard's voice (TPM: factual, action-oriented, first-person, no fluff)
3. Show draft with [A] Approve / [E] Edit / [D] Discard
4. A → write plain text to `~/teams-extractor/output/pending-reply.txt`
5. E → user describes revision → revise → loop back
6. D → stop cleanly, no file written

`reply <hint>` → same but hint steers draft focus

Acceptance criteria:
- Draft shown with correct header/footer
- A → file written as plain text (no markdown fences)
- E → edit loop works
- D → exits without writing file

---

### Chunk 4 — Extension: Staged Reply Bar
**Files:** `extension/content.js`, `extension/background.js`, `native-host/teams_writer.py`

`teams_writer.py`:
- New message type `READ_PENDING_REPLY`: read + delete `pending-reply.txt`, return text
- New message type `DISCARD_PENDING_REPLY`: delete `pending-reply.txt` if exists

`background.js`:
- Route `GET_PENDING_REPLY` → native host READ_PENDING_REPLY → return to sender
- Route `DISCARD_PENDING_REPLY` → native host DISCARD_PENDING_REPLY

`content.js`:
- Poll `GET_PENDING_REPLY` via background every 3 seconds
- On reply found: inject flat bar above Teams compose box
- Bar shows reply text + [Paste into chat →] + [✕]
- Paste: focus compose box, inject via execCommand('insertText') + dispatch input event, remove bar
- Dismiss: send DISCARD_PENDING_REPLY, remove bar
- Idempotent: only one bar at a time

Compose box selector: must be found via DevTools diagnostic after code is written.

Acceptance criteria:
- Bar appears within 3s of pending-reply.txt being written
- Paste injects text into compose box
- Dismiss deletes pending-reply.txt and removes bar
- No duplicate bars

---

## File Paths Reference

| Purpose | Path |
|---------|------|
| Master skill | `~/.claude/skills/teams/SKILL.md` |
| Orchestration skill | `~/.claude/skills/dev-teams/SKILL.md` |
| Conversation files | `~/teams-extractor/data/*.md` |
| Summaries output | `~/teams-extractor/output/summaries/` |
| Action items output | `~/teams-extractor/output/action-items/` |
| JIRA drafts output | `~/teams-extractor/output/jira-drafts/` |
| Pending reply | `~/teams-extractor/output/pending-reply.txt` |
| Extension content script | `~/teams-extractor/extension/content.js` |
| Extension background | `~/teams-extractor/extension/background.js` |
| Native host Python | `~/teams-extractor/native-host/teams_writer.py` |
