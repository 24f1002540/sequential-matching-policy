#!/usr/bin/env bash
# One command to reproduce the checks and the official-protocol evaluation.
# Usage: bash run_all.sh [quick|full]
#   quick (default): tests + seeds 101-102 for the submitted policy (about 15 min)
#   full:            tests + seeds 101-105 for the submitted policy and the three baselines (about 1 h)
# Fresh results go to results/repro/ and are compared with the committed files in results/;
# nothing committed is overwritten. Use python3 if your system has no `python`.
set -euo pipefail
PY="${PYTHON:-python}"
MODE="${1:-quick}"
if [ "$MODE" = full ]; then SEEDS=101,102,103,104,105; else SEEDS=101,102; fi
OUT=results/repro
mkdir -p "$OUT"
$PY -m unittest -v                          # kit, policy, fuzz, trace and regression tests
$PY verify_data.py
$PY test_scale.py 200 400                   # time and size on larger populations
# Note: the unmodified evaluate.py launches policy.py with --baseline greedy (local runner),
# so it evaluates the BASELINE. evaluate_method.py runs the submitted policy; --image runs the container.
$PY evaluate_method.py --seeds "$SEEDS" --variants all --output "$OUT/final.json"
if [ "$MODE" = full ]; then
  for b in greedy no_asks random; do
    $PY evaluate.py --baseline "$b" --seeds "$SEEDS" --variants all --output "$OUT/baseline_${b}.json"
  done
fi
$PY compare_results.py "$OUT"
if command -v docker >/dev/null 2>&1; then
  docker build -t sequential-policy:submission .
  $PY evaluate.py --image sequential-policy:submission --seeds 101 --variants all --output "$OUT/container_check.json"
else
  echo "docker not found: container check skipped (it also runs in GitHub Actions)"
fi
echo "Done. Fresh results are in $OUT/ (committed results in results/ were not touched)."
