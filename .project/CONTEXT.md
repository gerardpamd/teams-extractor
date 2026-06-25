# Teams Master Command — Project Context

Last updated: 2026-06-25
Updated by: Initialization

---

## Current State

| Field | Value |
|-------|-------|
| Chunks complete | 0 / 4 |
| Last completed chunk | none |
| Next chunk | Chunk 1 — `/teams` Skill Skeleton + File Picker |
| Skill file exists | No |
| Extension modified | No |

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

---

## What Comes Next

**Chunk 1 — `/teams` Skill Skeleton + File Picker**

Create `~/.claude/skills/teams/SKILL.md` with:
- Frontmatter (name, description, argument-hint, user-invokable)
- File picker: list data/*.md newest-first, ask user to pick
- Direct filename argument bypasses listing
- After selection: print loaded summary and stop
