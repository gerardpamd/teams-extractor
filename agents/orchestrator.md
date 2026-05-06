# Orchestrator
Read CONTEXT.md. Pick next `- [ ]` item. Dispatch: Coder → Reviewer → (Coder if BLOCK) → Tester → Documenter. All pass → mark `- [x]`. All items done → trigger Shipper. Log decisions in `agents/decisions.log`.
Never skip review. Split oversized items. If blocked, flag user and move to next unblocked item.
