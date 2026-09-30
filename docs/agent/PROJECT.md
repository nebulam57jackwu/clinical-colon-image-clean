# Project memory — clinical-colon-image-clean

This file stores stable context shared by Claude Code and Codex. Current work belongs only in
`HANDOVER.md`; durable decisions belong in `DECISIONS.md`.

## Purpose

This is a standalone, public-safe companion repository for preparing a traceable clinical
colon-image cleaning and annotation workflow. It helps a lab engineer export pseudonymous
candidates from the external `clinical-image-lake`, record expert visibility and quality
decisions, produce reviewed lesion masks, and eventually publish patient-separated training
manifests. The repository is a workflow contract plus early tooling, not a completed pipeline.

## Architecture

- External `clinical-image-lake`: read-only source of de-identified image files and DuckDB
  metadata. It is not copied into this repository.
- `scripts/export_lake_manifest.py`: implemented candidate exporter. It joins `images_master`
  with `image_quality_qc`, filters a `source_id`, validates patient keys and image paths, and
  writes candidate schema v0.1.
- `configs/pipeline.yaml`: planned configuration contract. The current exporter does not read it;
  `null` means not selected or calibrated.
- `schemas/records.md`: planned v0.2 CSV/JSONL contracts for integrity, review, masks, events,
  dispositions, and releases.
- `docs/00-overview.md`–`docs/07-annotation-format.md`: stage gates, operating SOPs, model and
  annotation plans, and release rules.
- `docs/08-image-classification-experiments.md`: literature-grounded CRC LST invasion-depth
  classification plan covering ROI/context, modality pairing, class imbalance, lesion aggregation,
  device shift, and fixed-endpoint evaluation.
- Classification metadata is a planned v0.2 sidecar/manifest extension. It must preserve the v0.1
  exporter contract and add traceable `lesion_group_id`, modality, magnification, device, ROI and
  label provenance rather than guessing them from paths.
- `outputs/`, `data/`, masks, databases, and model artifacts: local/ignored runtime material;
  never publish them with the public repository.

The intended flow is:

```text
external lake → candidate export → integrity/partition → expert visibility/quality
→ prompts and mask review → finalization → patient-separated release
```

## Technical baseline

- Python 3.11+ and Bash.
- Runtime dependency: DuckDB, installed from `requirements.txt` or supplied by the lake
  environment. GPU/model environments are separate and must be recorded per run.
- Verification entry point: `./scripts/verify.sh`, which calls `make verify`.
- `make verify` runs Python compilation, local `unittest` contract tests, and `git diff --check`.
  DuckDB-backed synthetic export tests run when DuckDB is installed; safety tests do not require
  clinical data or DuckDB.
- There is currently no package build, web service, database writer, or automatic annotation CLI.

## Invariants

- Existing user changes are out of scope unless the handoff explicitly includes them.
- One writer may modify a working tree at a time; parallel writers use separate branches/worktrees.
- The external lake and its DuckDB are opened read-only by this repository's exporter.
- Candidate image paths must be relative, must resolve under the approved lake root, and must not
  escape through `..` or symlinks. Existing candidate outputs are never overwritten.
- `image_id` is the image join key; `patient_key` controls patient-level partitioning. Never join
  by CSV row order or infer labels from folder names/pathology.
- Model experiments must not split adjacent frames from one patient or `lesion_group_id` across
  train/test. Frame-level scores are not independent cases; lesion/patient aggregation and their
  denominators must be explicit.
- Do not claim cross-paper accuracy ranking without matching endpoint, data distribution, split,
  and aggregation. Do not synthesize NBI/IEE images when the source modality is unavailable.
- `uncertain`, missing, corrupt, pending, or unknown values stay unknown/pending; they are not
  converted to negative or usable by default.
- Clinical images, raw source trees, identifiable/private lineage, masks, model weights, local
  databases, and generated manifests are not committed or uploaded.
- Every released image must have a frozen revision, valid hashes, expert sign-off, completed
  instance review, and a patient-separated split; release directories must not be overwritten.

## Shared-memory governance

- `PROJECT.md` changes only when stable architecture or invariants change.
- `HANDOVER.md` is the only source of truth for active work.
- `DECISIONS.md` records durable decisions and reasons.
- `AGENTS.md` and `CLAUDE.md` are thin tool-specific entry points.
