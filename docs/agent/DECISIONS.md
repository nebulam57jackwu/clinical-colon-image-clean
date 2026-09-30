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

## 2026-09-23 — Collaboration-readiness baseline

Context: The repository is being prepared for handoff to a junior lab engineer while the
clinical image lake remains an external, read-only dependency.

Decision: Keep this repository public-safe and code/documentation-only. Local lake-derived
manifests, clinical images, masks, model weights, databases, and generated outputs remain
ignored. Add a contributor guide, synthetic contract tests, and exporter safeguards before
starting the manual pilot.

Consequences: A new contributor can validate the repository without access to clinical data;
data-connected smoke tests remain explicitly separate and require an approved lake root.

## 2026-09-30 — Literature-guided CRC LST classification plan

Context: Related CRC invasion-depth studies use different endpoints, class distributions,
image/lesion aggregation rules, modalities and external validation designs. The user-provided
comparison and the 2023 meta-analysis show high heterogeneity; raw accuracy is not a valid
cross-paper ranking.

Decision: Add a separate classification experiment specification. The first ablation order is
patient-level split → full-frame/tight-ROI/ROI+context inputs → moderate training-only augmentation
→ focal loss or patient/lesion-level balancing → lesion-level aggregation → localization/attention
→ real paired WLI+NBI/IEE fusion. Device/time/source holdouts and fixed-specificity sensitivity,
AUROC, NPV, calibration and lesion/patient-level denominators are required for interpretation.

Decision: Keep the existing v0.1 candidate exporter unchanged. Add modality, magnification,
de-identified device, ROI provenance/coordinates, `frame_group_id`, `lesion_group_id` and label
provenance through a planned v0.2 sidecar or manifest. `lesion_group_id` must be curated or
protocol-derived; it cannot be inferred from paths or filenames.

Consequences: The repo can be shared publicly as a code/documentation collaboration surface,
while clinical images, masks, manifests, model weights and lake-derived data remain outside GitHub.
No accuracy improvement is claimed until an independent patient-level holdout is evaluated.
