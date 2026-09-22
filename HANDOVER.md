# Project Handover Status — clinical-colon-image-clean

Updated: 2026-09-22 12:17 CST
From: project initialization
To: Claude Code or Codex
Mode: pipeline
Writer: RELEASED
Checkpoint: 305a71a Initialize clinical-colon-image-clean standalone repo
Expected tree: clean after initial checkpoint; inspect Git status before assuming

## 1. Current State

### 2026-09-22 — Split repository initialized

Moved the task project out of `clinical-image-lake` into this standalone repository. The lake is an external read-only dependency; set `--lake-root /home/a01949/projects/clinical-image-lake` or `CLINICAL_IMAGE_LAKE_ROOT` when running the exporter. The project contains documentation, review contracts, templates, and a read-only candidate exporter. No clinical images, generated CSV outputs, or model weights are committed.

### Objective and acceptance

Define one concrete, observable outcome before implementation.

### Completed with evidence

- [x] Multi-agent relay initialized.
- [x] Moved out of the parent lake repo and committed as standalone Git repository.
- [x] `make verify`, `./scripts/verify.sh`, and a 3-row exporter smoke test using `--lake-root /home/a01949/projects/clinical-image-lake` passed.

### Touched paths and symbols

- None yet. Prefer paths plus symbols/test names over fragile line numbers.

## 2. Next Steps

1. Commit this standalone repo, then run the exporter against the lake with an explicit `--lake-root`.
2. Implement the manual pilot work packages described in `docs/06-implementation-plan.md`.
3. Add a remote only when the user provides or authorizes its URL.

### Exact next action

- [ ] Replace this item with one implementation action and its acceptance criterion.

### Known bugs or risks

- Verification has not been configured or recorded yet.

### Out of scope

- Record adjacent work here instead of expanding the active objective.

## 3. Key Decisions and Contracts

- Preserve unrelated user changes.
- Keep one writer per working tree; use separate branches/worktrees for parallel writers.
- Add project-specific invariants from `docs/agent/PROJECT.md`.

## 4. Verification Evidence

2026-09-22: `make verify` PASS; `./scripts/verify.sh` PASS; exporter produced 3 pseudonymous rows from the external lake with an explicit `--lake-root`; no output CSV or clinical artifacts are tracked.

```text
Command: ./scripts/verify.sh
Last result: NOT RUN
Checked at: 2026-09-22 12:17 CST
Pre-existing failures: unknown
```

## 5. Working Tree and Recovery

- The source directory was moved from the parent repository. The parent repository must record the deletion and pointer update separately.
- `outputs/` and clinical artifacts are ignored; recover source from this Git repository after the initial commit.

- Branch: inspect before work
- Starting checkpoint: `NO COMMITS`
- Staged changes: inspect before work
- Unstaged changes: inspect before work
- Untracked files: inspect before work
- Recovery: preserve unknown changes; never reset or discard them without user approval.

## 6. Direct Command for the Next Agent

> Read `.dual-agent-kit.json` and this Handover, confirm `Writer: RELEASED`, inspect Git state, and run
> `./scripts/verify.sh`. Claim the writer, execute only the Exact next action, preserve the contracts,
> refresh this Handover, then release the writer. Do not commit unless the user explicitly asks.
