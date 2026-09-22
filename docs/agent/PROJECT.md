# Project memory — clinical-colon-image-clean

This file stores stable context shared by Claude Code and Codex. Current work belongs only in
`HANDOVER.md`; durable decisions belong in `DECISIONS.md`.

## Purpose

TODO: Describe the product, users, and primary outcome.

## Architecture

TODO: List major components, data flow, and important directories.

## Technical baseline

TODO: Record runtimes, package managers, build commands, and dependencies.

The standard verification entry point is `./scripts/verify.sh`.

## Invariants

- Existing user changes are out of scope unless the handoff explicitly includes them.
- One writer may modify a working tree at a time; parallel writers use separate branches/worktrees.
- Do not commit secrets, credentials, private datasets, or generated sensitive artifacts.
- TODO: Add public interfaces, data contracts, safety rules, and files that must not be modified.

## Shared-memory governance

- `PROJECT.md` changes only when stable architecture or invariants change.
- `HANDOVER.md` is the only source of truth for active work.
- `DECISIONS.md` records durable decisions and reasons.
- `AGENTS.md` and `CLAUDE.md` are thin tool-specific entry points.
