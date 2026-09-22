#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
ran=0

if [[ ! -f .dual-agent-kit.json ]]; then
  echo "[verify] Missing .dual-agent-kit.json" >&2
  exit 1
fi

if command -v python3 >/dev/null; then
  handoff_path="$({ python3 -c 'import json; print(json.load(open(".dual-agent-kit.json", encoding="utf-8"))["handoff"])'; } 2>/dev/null)" || {
    echo "[verify] Invalid manifest or missing handoff field" >&2
    exit 1
  }
else
  handoff_path="HANDOVER.md"
  echo "[verify] python3 unavailable; using manifest-time fallback" >&2
fi

if [[ ! -f "$handoff_path" ]]; then
  echo "[verify] Canonical handoff not found: $handoff_path" >&2
  exit 1
fi

if [[ "$handoff_path" == "HANDOVER.md" ]]; then
  for heading in \
    "## 1. Current State" \
    "## 2. Next Steps" \
    "## 3. Key Decisions and Contracts" \
    "## 4. Verification Evidence" \
    "## 5. Working Tree and Recovery" \
    "## 6. Direct Command for the Next Agent"; do
    grep -Fqx "$heading" "$handoff_path" || {
      echo "[verify] Missing Handover heading: $heading" >&2
      exit 1
    }
  done
  grep -Eq '^Writer: (RELEASED|.+\(ACTIVE[^)]*\))$' "$handoff_path" || {
    echo "[verify] Invalid Writer field in $handoff_path" >&2
    exit 1
  }
fi

if [[ -f Makefile ]] && grep -Eq '^verify:' Makefile; then
  echo "[verify] make verify"
  make verify
  ran=1
elif [[ -f Makefile ]] && grep -Eq '^test:' Makefile; then
  echo "[verify] make test"
  make test
  ran=1
fi

if [[ -f pyproject.toml && -d tests && "$ran" -eq 0 ]]; then
  echo "[verify] Python tests"
  python3 -m pytest -q
  ran=1
fi

if [[ -f package.json ]] && command -v node >/dev/null; then
  if node -e 'const p=require("./package.json"); process.exit(p.scripts?.test ? 0 : 1)'; then
    echo "[verify] JavaScript tests"
    if [[ -f pnpm-lock.yaml ]]; then pnpm test
    elif [[ -f yarn.lock ]]; then yarn test
    else npm test
    fi
    ran=1
  fi
fi

if [[ -f Cargo.toml ]]; then
  echo "[verify] Rust tests"
  cargo test
  ran=1
fi

if [[ -f go.mod ]]; then
  echo "[verify] Go tests"
  go test ./...
  ran=1
fi

if [[ "$ran" -eq 0 ]]; then
  echo "[verify] No project verification command detected." >&2
  echo "[verify] Edit scripts/verify.sh for this project before handoff." >&2
  exit 2
fi

echo "[verify] Patch whitespace"
git diff --check
echo "[verify] PASS"
