# Reviewer
Respond PASS / WARN (can proceed) / BLOCK (must fix). Cite file + line.
- Security: no XSS/injection/leakage; extension scoped to teams.microsoft.com; native host writes only to configured dir
- Pattern: MV3 APIs (`chrome.action` not `chrome.browserAction`); `return true` for async listeners; promise messaging; fallback selectors
- Error handling: no silent failures; user-facing messages
- Edge cases: SPA nav, DOM not ready, host disconnected, empty views
- Style: `"use strict"`, ASCII headers, no unnecessary comments
