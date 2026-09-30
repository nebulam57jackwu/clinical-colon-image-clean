# Project Handover Status — clinical-colon-image-clean

Updated: 2026-09-30 13:45 CST
From: Codex — literature-guided image-classification collaboration update
To: Claude Code or Codex
Mode: pipeline
Writer: RELEASED
Checkpoint: 8535edf Record synchronized GitHub handoff
Expected tree: clean; origin/main is synchronized through the final handoff refresh

## 1. Current State

### 2026-09-22 — Split repository initialized

Moved the task project out of `clinical-image-lake` into this standalone repository. The lake is an external read-only dependency; set `--lake-root /home/a01949/projects/clinical-image-lake` or `CLINICAL_IMAGE_LAKE_ROOT` when running the exporter. The project contains documentation, review contracts, templates, and a read-only candidate exporter. No clinical images, generated CSV outputs, or model weights are committed.

### Objective and acceptance

Prepare the repository for safe handoff to a junior lab engineer: a new contributor can
find the setup, privacy, branching, verification, and first-task instructions without
guessing; the exporter refuses accidental overwrite; and the verification command covers
the safety behavior with local synthetic data only.

### Completed with evidence

- [x] Multi-agent relay initialized.
- [x] Moved out of the parent lake repo and committed as standalone Git repository.
- [x] `make verify`, `./scripts/verify.sh`, and a 3-row exporter smoke test using `--lake-root /home/a01949/projects/clinical-image-lake` passed.
- [x] Created and pushed public GitHub remote `https://github.com/nebulam57jackwu/clinical-colon-image-clean` on `main`.
- [x] Added `DATA_CATALOG.md` with source cohorts, index-date selection, quarantine, processing lineage, quality/task states, and explicit statistic denominators.
- [x] Added `CONTRIBUTING.md`, filled stable project context, and added local data/privacy ignore rules for junior-engineer onboarding.
- [x] Added synthetic exporter contract tests and made the exporter reject existing outputs and symlink escapes.
- [x] Added `docs/08-image-classification-experiments.md` with the literature table, five processing priorities, ablation order, evaluation guardrails, and public-safe metadata contract.
- [x] Updated README, CONTRIBUTING, implementation plan, schema, PROJECT, DECISIONS, and preparation guidance so a junior collaborator can start from the public GitHub repository.

### Touched paths and symbols

- Collaboration guide, stable project context, README onboarding, ignore rules, and local test entry point.
- `docs/08-image-classification-experiments.md` and `schemas/records.md` classification metadata extension.
- `scripts/export_lake_manifest.py:export_manifest` overwrite/path safety.
- `tests/test_export_lake_manifest.py` synthetic exporter contract tests.

## 2. Next Steps

1. Share `https://github.com/nebulam57jackwu/clinical-colon-image-clean` and have the junior engineer read `CONTRIBUTING.md` and `docs/08-image-classification-experiments.md`.
2. Have the junior engineer run the local verification and review the planned v0.2 classification sidecar without accessing clinical data.
3. Implement the first patient-split WLI/full-frame, tight-ROI, and ROI+context baseline work package.

### Exact next action

- [ ] Have the next contributor clone the public repo, run `PYTHON=.venv/bin/python make verify`, and review the classification contract; acceptance is PASS with no clinical or lake-derived artifacts written by tests.

### Known bugs or risks

- The exporter still depends on the external lake's DuckDB schema and runtime; this repository does not contain a complete environment lock or the lake data.
- The local data snapshot under `data/` is ignored and must never be committed or uploaded with the public repository.
- The v0.2 classification sidecar is planned documentation only; modality, device, ROI and `lesion_group_id` are not yet emitted by the exporter.

### Out of scope

- Record adjacent work here instead of expanding the active objective.

## 3. Key Decisions and Contracts

- Preserve unrelated user changes.
- Keep one writer per working tree; use separate branches/worktrees for parallel writers.
- Add project-specific invariants from `docs/agent/PROJECT.md`.
- Treat endpoint, patient/lesion split, aggregation and denominator as part of every classification experiment identity.
- Never synthesize NBI/IEE or infer lesion groups from paths; keep unknown and pending values explicit.

## 4. Verification Evidence

2026-09-23 collaboration-readiness pass:

- `make verify` PASS with system Python; 3 local safety tests PASS and 1 DuckDB test SKIP because system Python has no DuckDB.
- `PYTHON=../clinical-image-lake/.venv/bin/python make verify` PASS; all 4 tests PASS.
- External-lake smoke export PASS with explicit `--lake-root` and `--limit 3`; output was written to a temporary directory outside the repository.
- Markdown local-link check PASS; `git diff --check` PASS.
- The ignored lake-derived CSV under `data/` was preserved and not added to Git.

2026-09-30 literature-guided collaboration update:

- `./scripts/verify.sh` PASS; local safety tests PASS and DuckDB-backed test SKIP under system Python because DuckDB is optional.
- `git diff --check` PASS.
- New documentation was checked for required local targets; no clinical or lake-derived artifact is included.
- Checkpoint commit `2ad659d` contains the public collaboration and classification documentation changes.
- `git push origin main` completed; the public repository is synchronized before this final handoff refresh.

## 5. Working Tree and Recovery

- The source directory was moved from the parent repository. The parent repository must record the deletion and pointer update separately.
- `outputs/` and clinical artifacts are ignored; recover source from this Git repository after the initial commit.

- Branch: `main`
- Starting checkpoint: `2ad659d`
- Staged changes: none
- Unstaged changes: none
- Untracked files: none expected
- Recovery: preserve unknown changes; never reset or discard them without user approval.

Expected changed paths after checkpoint: none; the committed paths are listed in commit `2ad659d`.

## 6. Direct Command for the Next Agent

> Read `.dual-agent-kit.json` and this Handover, confirm `Writer: RELEASED`, inspect Git state, and run
> `./scripts/verify.sh`. Review the public collaboration and classification experiment changes,
> then start the patient-split WLI/full-frame, tight-ROI, and ROI+context baseline work package.
> Preserve the contracts, refresh this Handover, then release the writer. Do not commit unless the user explicitly asks.
