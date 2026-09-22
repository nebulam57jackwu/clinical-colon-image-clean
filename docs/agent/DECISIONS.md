# Decision log — clinical-colon-image-clean

Add dated entries with context, decision, and consequences. Keep this append-oriented so future agents
do not reverse choices without understanding the tradeoffs.

## 2026-09-22 12:17 CST — Multi-agent single-writer relay

Context: The project may move among Claude Code, Codex, and a research model, or use parallel worktrees.

Decision: Claude Code reads `CLAUDE.md`; Codex reads `AGENTS.md`; both use `docs/agent/PROJECT.md`,
`HANDOVER.md`, and this decision log. Research lanes are read-only by default. Only one agent writes
to a working tree at a time.

Consequences: Every transfer refreshes `HANDOVER.md`. Parallel work uses separate branches/worktrees.
Verification and diff review are required. Checkpoint commits remain user-controlled.
