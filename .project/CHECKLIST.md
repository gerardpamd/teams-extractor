# Teams Master Command — Delivery Checklist

Overall Progress: 4/4 chunks (100%)

---

## Chunk 1 — `/teams` Skill Skeleton + File Picker
Status: [x]

**What to build:**
- Create `~/.claude/skills/teams/SKILL.md` with frontmatter and file picker logic
- List `.md` files in `~/teams-extractor/data/` newest-first, numbered, with extracted date
- Ask user to pick by number; wait for response
- Direct filename/path argument skips listing
- After selection: print loaded summary and stop

**Acceptance Criteria:**
- [x] `/teams` with no arg lists files and waits
- [x] `/teams <filename>` loads directly without listing
- [x] Empty data dir prints graceful error

**Tester Checks:**
- [x] Skill file exists at `~/.claude/skills/teams/SKILL.md`
- [x] Frontmatter has: name, description, argument-hint, user-invokable
- [x] List is sorted newest-first
- [x] Direct argument path documented clearly in skill

---

## Chunk 2 — Intent Detection + Digest Pipeline
Status: [x]

**What to build:**
- Extend `~/.claude/skills/teams/SKILL.md` with intent detection and digest pipeline
- Intent keywords: (none)=digest, actions, jira, status, natural language=focused summary
- Digest: summary + action items, both saved and printed
- All pipeline logic inline (no skill-calling-skill)

**Acceptance Criteria:**
- [x] No keyword → digest runs, both output files written
- [x] `actions` → action items only
- [x] `jira` → JIRA drafts only
- [x] `status` → weekly status (no file selection needed)
- [x] Natural language hint → focused summary

**Tester Checks:**
- [x] Summary written to `~/teams-extractor/output/summaries/<basename>.md`
- [x] Action items written to `~/teams-extractor/output/action-items/<basename>.md`
- [x] Each intent branch has clear conditional in skill

---

## Chunk 3 — Reply Drafting Pipeline
Status: [x]

**What to build:**
- Extend `~/.claude/skills/teams/SKILL.md` with reply intent branch
- Draft shown with [A]/[E]/[D] approval loop
- Approve → write plain text to `pending-reply.txt`
- Edit → revision loop
- Discard → clean stop

**Acceptance Criteria:**
- [x] Draft shown with correct `--- DRAFT REPLY ---` header
- [x] A → `pending-reply.txt` written as plain text
- [x] E → edit loop works, shows revised draft
- [x] D → exits without writing any file

**Tester Checks:**
- [x] `pending-reply.txt` path is `~/teams-extractor/output/pending-reply.txt`
- [x] File content is plain text, no markdown fences
- [x] `reply <hint>` passes hint into draft prompt

---

## Chunk 4 — Extension: Staged Reply Bar
Status: [x]

**What to build:**
- `teams_writer.py`: READ_PENDING_REPLY + DISCARD_PENDING_REPLY handlers
- `background.js`: GET_PENDING_REPLY + DISCARD_PENDING_REPLY routing
- `content.js`: 3-second poller + flat reply bar DOM injection above compose box

**Acceptance Criteria:**
- [x] Bar appears within 3s of `pending-reply.txt` being written
- [x] [Paste into chat →] injects text into compose box
- [x] [✕] deletes `pending-reply.txt` and removes bar
- [x] No duplicate bars (idempotent)

**Tester Checks:**
- [x] `echo '{"type":"READ_PENDING_REPLY"}' | python3 teams_writer.py` works (manual test)
- [x] background.js GET_PENDING_REPLY handler present in code review
- [x] content.js poller clears interval when bar is shown
- [x] Bar re-polls after dismiss
