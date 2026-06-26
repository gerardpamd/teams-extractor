# Teams Master Command — Project Context

Last updated: 2026-06-26
Updated by: Doc agent (Chunk 4 complete)

---

## Current State

| Field | Value |
|-------|-------|
| Chunks complete | 4 / 4 |
| Last completed chunk | Chunk 4 — Extension: Staged Reply Bar |
| Next chunk | ALL DONE |
| Skill file exists | Yes |
| Extension modified | Yes |

---

## Project Root

- Skill: `~/.claude/skills/teams/SKILL.md`
- Extension: `~/teams-extractor/extension/`
- Native host: `~/teams-extractor/native-host/`
- State files: `~/teams-extractor/.project/`
- Design ref: `~/teams-extractor/.project/PLAN.md`

---

## Key Decisions

| Date | Decision | Reason |
|------|----------|--------|
| 2026-06-25 | Always ask user to pick file — no auto-detection | Safer, avoids wrong-file mistakes |
| 2026-06-25 | Inline all pipeline logic — no skill-calling-skill | More reliable in Claude Code |
| 2026-06-25 | pending-reply.txt as bridge between Claude Code and extension | Simplest IPC; native host already bridges WSL↔Edge |
| 2026-06-25 | No auto-send | Gerard always hits Enter himself; no accidental sends |
| 2026-06-25 | Staged reply bar injected above compose box (not popup) | Contextual, flat, matches Teams UI; JIRA assistant was inspiration |

---

## Changelog

| Date | Chunk | Description |
|------|-------|-------------|
| 2026-06-25 | — | Project initialized, state files created |
| 2026-06-25 | Chunk 1 — /teams Skill Skeleton + File Picker | Created SKILL.md with frontmatter, file picker (newest-first), direct arg bypass, graceful empty-dir error, and load confirmation |
| 2026-06-26 | Chunk 2 — Intent Detection + Digest Pipeline | Added intent router (Step 3) and six inline pipeline sections: Digest, Action Items Only, JIRA Drafts, Status, Focused Summary, Reply placeholder |
| 2026-06-26 | Chunk 3 — Reply Drafting Pipeline | Added full reply pipeline: hint extraction, TPM-voice draft, A/E/D approval loop, plain-text pending-reply.txt write |
| 2026-06-26 | Chunk 4 — Extension: Staged Reply Bar | Added READ/DISCARD_PENDING_REPLY to teams_writer.py, GET/DISCARD_PENDING_REPLY routing to background.js, 3-second poller + idempotent reply bar injection to content.js |

---

## What Comes Next

All chunks complete. Reload extension in Edge (edge://extensions), open Teams, and test with `/teams reply`.
