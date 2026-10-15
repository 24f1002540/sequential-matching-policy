#!/usr/bin/env bash
# One command to reproduce the checks and the official-protocol evaluation.
# Usage: bash run_all.sh [quick|full]      quick (default): tests + seeds 101-102 (~10 min)
#                                          full: tests + seeds 101-105 and the baselines (~1 h)
set -euo pipefail
MODE="${1:-quick}"
if [ "$MODE" = full ]; then SEEDS=101,102,103,104,105; else SEEDS=101,102; fi
mkdir -p results
python -m unittest -v                       # supplied kit tests + policy, fuzz and trace tests
python verify_data.py
python test_scale.py 200 400                # time and size on larger populations
python evaluate_method.py --seeds "$SEEDS" --variants all --output results/final.json
if [ "$MODE" = full ]; then
  for b in greedy no_asks random; do
    python evaluate.py --baseline "$b" --seeds "$SEEDS" --variants all --output "results/baseline_${b}.json"
  done
fi
if command -v docker >/dev/null 2>&1; then
  docker build -t sequential-policy:submission .
  python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
else
  echo "docker not found: container check skipped (it also runs in GitHub Actions)"
fi
echo "Done. Results are in results/."
