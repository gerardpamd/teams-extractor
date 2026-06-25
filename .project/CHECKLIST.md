# Teams Master Command — Delivery Checklist

Overall Progress: 0/4 chunks (0%)

---

## Chunk 1 — `/teams` Skill Skeleton + File Picker
Status: [ ]

**What to build:**
- Create `~/.claude/skills/teams/SKILL.md` with frontmatter and file picker logic
- List `.md` files in `~/teams-extractor/data/` newest-first, numbered, with extracted date
- Ask user to pick by number; wait for response
- Direct filename/path argument skips listing
- After selection: print loaded summary and stop

**Acceptance Criteria:**
- [ ] `/teams` with no arg lists files and waits
- [ ] `/teams <filename>` loads directly without listing
- [ ] Empty data dir prints graceful error

**Tester Checks:**
- [ ] Skill file exists at `~/.claude/skills/teams/SKILL.md`
- [ ] Frontmatter has: name, description, argument-hint, user-invokable
- [ ] List is sorted newest-first
- [ ] Direct argument path documented clearly in skill

---

## Chunk 2 — Intent Detection + Digest Pipeline
Status: [ ]

**What to build:**
- Extend `~/.claude/skills/teams/SKILL.md` with intent detection and digest pipeline
- Intent keywords: (none)=digest, actions, jira, status, natural language=focused summary
- Digest: summary + action items, both saved and printed
- All pipeline logic inline (no skill-calling-skill)

**Acceptance Criteria:**
- [ ] No keyword → digest runs, both output files written
- [ ] `actions` → action items only
- [ ] `jira` → JIRA drafts only
- [ ] `status` → weekly status (no file selection needed)
- [ ] Natural language hint → focused summary

**Tester Checks:**
- [ ] Summary written to `~/teams-extractor/output/summaries/<basename>.md`
- [ ] Action items written to `~/teams-extractor/output/action-items/<basename>.md`
- [ ] Each intent branch has clear conditional in skill

---

## Chunk 3 — Reply Drafting Pipeline
Status: [ ]

**What to build:**
- Extend `~/.claude/skills/teams/SKILL.md` with reply intent branch
- Draft shown with [A]/[E]/[D] approval loop
- Approve → write plain text to `pending-reply.txt`
- Edit → revision loop
- Discard → clean stop

**Acceptance Criteria:**
- [ ] Draft shown with correct `--- DRAFT REPLY ---` header
- [ ] A → `pending-reply.txt` written as plain text
- [ ] E → edit loop works, shows revised draft
- [ ] D → exits without writing any file

**Tester Checks:**
- [ ] `pending-reply.txt` path is `~/teams-extractor/output/pending-reply.txt`
- [ ] File content is plain text, no markdown fences
- [ ] `reply <hint>` passes hint into draft prompt

---

## Chunk 4 — Extension: Staged Reply Bar
Status: [ ]

**What to build:**
- `teams_writer.py`: READ_PENDING_REPLY + DISCARD_PENDING_REPLY handlers
- `background.js`: GET_PENDING_REPLY + DISCARD_PENDING_REPLY routing
- `content.js`: 3-second poller + flat reply bar DOM injection above compose box

**Acceptance Criteria:**
- [ ] Bar appears within 3s of `pending-reply.txt` being written
- [ ] [Paste into chat →] injects text into compose box
- [ ] [✕] deletes `pending-reply.txt` and removes bar
- [ ] No duplicate bars (idempotent)

**Tester Checks:**
- [ ] `echo '{"type":"READ_PENDING_REPLY"}' | python3 teams_writer.py` works (manual test)
- [ ] background.js GET_PENDING_REPLY handler present in code review
- [ ] content.js poller clears interval when bar is shown
- [ ] Bar re-polls after dismiss
