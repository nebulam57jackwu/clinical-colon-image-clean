#!/usr/bin/env bash
set -uo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
handoff_path="$({ python3 -c 'import json; print(json.load(open(".dual-agent-kit.json", encoding="utf-8"))["handoff"])'; } 2>/dev/null)" || handoff_path="HANDOVER.md"
head_sha="$(git rev-parse --short HEAD 2>/dev/null || true)"
[[ -n "$head_sha" ]] || head_sha="NO COMMITS"
branch="$(git branch --show-current)"
[[ -n "$branch" ]] || branch="DETACHED"

echo "[handoff] Repository: $repo_root"
echo "[handoff] Branch: $branch"
echo "[handoff] HEAD: $head_sha"
echo "[handoff] Canonical handoff: $handoff_path"
echo

if ./scripts/verify.sh; then verification=PASS; else verification=FAIL; fi
if [[ -f "$handoff_path" ]] && grep -Eq '^Writer:[[:space:]]+RELEASED[[:space:]]*$' "$handoff_path"; then
  writer=RELEASED
else
  writer="NOT RELEASED"
fi

echo
echo "[handoff] Verification: $verification"
echo "[handoff] Writer: $writer"
echo "[handoff] Working tree:"
git status --short
echo
echo "[handoff] Staged diff stat:"
git diff --cached --stat
echo "[handoff] Unstaged diff stat:"
git diff --stat
echo
echo "[handoff] This command did not stage, commit, or modify files."

[[ "$verification" == PASS && "$writer" == RELEASED ]]
