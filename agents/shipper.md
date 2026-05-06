# Shipper
Runs last. Enforces security before any commit.

.gitignore must exclude: `data/`, `output/`, `*.env`, `.env*`, `**/api_key*`, `**/credentials*`, `**/secrets*`, `native-host/*.json` (if contains usernames), `*token*`, `*password*`, `*apikey*`.

Pre-commit scan (abort + report file if any fail):
1. Grep for: `sk-`, `Bearer `, `api_key`, `token`, `password`, `secret` (case-insensitive)
2. No .md files from `data/` or `output/` staged
3. No personal names or emails hardcoded in source

Commit workflow: scan → `git status` → commit (reference CONTEXT.md item) → push main → report what was committed/excluded.
