# Agent workflow

Shared sources of truth:

1. `.dual-agent-kit.json` declares the canonical handoff.
2. `PROJECT.md` contains stable architecture and invariants.
3. `HANDOVER.md` contains the only active work state.
4. `DECISIONS.md` contains durable decisions and reasons.

Transfer sequence:

1. Confirm `Writer: RELEASED`, inspect Git state, and run `./scripts/verify.sh`.
2. Claim writer ownership before editing.
3. Work only on the stated objective and review the complete diff.
4. Refresh `HANDOVER.md`, including verification and dirty files.
5. Set `Writer: RELEASED` and stop writing.
6. Commit only when the user requests a checkpoint.

Run `./scripts/agent-handoff.sh` for a read-only readiness report. Use separate branches/worktrees for
parallel writers.
