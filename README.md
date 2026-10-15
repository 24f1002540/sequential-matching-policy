# Sequential matching policy (IIT Madras x Romeo & Juliet, Round 2)

A reproducible decision policy for the synthetic sequential matching task (release 1.0.0). The policy reads only the
observable JSON request, keeps no persistent state outside the request/`memory` channel, and needs no network, GPU or
trained asset. The technical report is in [REPORT.md](REPORT.md).

## What the policy does
1. **Feasibility:** the supplied reciprocal `eligibility()` rules, in both directions. Missing hard fields mean
   "needs clarification", never feasible; members who declined a hard field are never asked again and never matched.
2. **Clarification:** each day, pairs that still need clarification give credit 1/(members who must answer) to those
   members; the highest-credit available members receive the 3-unit hard-constraint bundle until the 12-unit budget is spent.
3. **Allocation:** disjoint feasible, never-repeated pairs chosen by the supplied similarity-greedy matcher
   (see REPORT.md for the tested alternatives and why they are not used).
4. **Guard:** every ask and pair is re-validated; any exception returns an empty action (always valid).

## Requirements
Python 3.10+ (tested on 3.12 and 3.13). Standard library only for the policy; `docker` for the container check.
Declared seeds: no training seeds (no learned asset); the policy is deterministic and uses no random numbers (inference seed: none).

## Setup and evaluation commands
```bash
python -m unittest -v                         # kit tests and policy tests
python verify_data.py
python evaluate_method.py --seeds 101,102,103 --variants all --output results/final.json
python evaluate.py --baseline greedy    --seeds 101,102,103 --variants all --output results/baseline_greedy.json
python evaluate.py --baseline no_asks   --seeds 101,102,103 --variants all --output results/baseline_no_asks.json
python evaluate.py --baseline random    --seeds 101,102,103 --variants all --output results/baseline_random.json
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
```
`evaluate_method.py` is the supplied `evaluate.py` with one change: it launches `policy.py` with no `--baseline`
argument, so the submitted method (not the greedy baseline) runs.

## Files
`policy.py` (submission), `official_baselines.py` (supplied random baseline, used only for `--baseline random`),
`kit.py`/`evaluate.py` (supplied, unmodified), `test_policy.py` (policy tests), `results/` (machine-readable episode results),
`experiments/` (scripts and raw outputs behind the report), `REPORT.md`, `PRESPEC.txt` (pre-specifications).

## Provenance and licences
No external data, models or paid services. Standard-library Python only inside the image. Experiment scripts under
`experiments/` additionally use NumPy and NetworkX (BSD-3-Clause) and were run offline. AI assistance (Claude, Anthropic)
was used to write and run experiments and draft this repository; see REPORT.md section 9. Code licence: see LICENSE (supplied kit licence applies to supplied files).
