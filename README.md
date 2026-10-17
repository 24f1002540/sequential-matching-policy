# Sequential matching policy (IIT Madras x Romeo & Juliet, Round 2)

![container-check](https://github.com/24f1002540/sequential-matching-policy/actions/workflows/container-check.yml/badge.svg) ![verify](https://github.com/24f1002540/sequential-matching-policy/actions/workflows/verify.yml/badge.svg)

A reproducible decision policy for the synthetic sequential matching task (release 1.0.0). The policy reads only the
observable JSON request, keeps no persistent state outside the request/`memory` channel, and needs no network, GPU or
trained asset. The technical report is in [REPORT.md](REPORT.md).

## What the policy does
It applies the supplied clarification and matching rules inside an independent validity guard (the reasons are in REPORT.md sections 5.7 and 1).
1. **Feasibility:** the supplied reciprocal `eligibility()` rules, in both directions. Missing hard fields mean
   "needs clarification", never feasible; members who declined a hard field are never asked again and never matched.
2. **Clarification:** the supplied rule: available members with an unknown hard field and no declined hard field receive the
   3-unit hard-constraint bundle, in list order, until the 12-unit daily budget is spent.
3. **Allocation:** disjoint feasible, never-repeated pairs chosen by the supplied similarity-greedy matcher
   (see REPORT.md for the tested alternatives and why they are not used).
4. **Guard:** every ask and pair is re-validated; any exception while deciding returns an empty action (always valid). Malformed JSON that the official harness never sends exits with an error.

Our earlier candidate, a targeted clarification ranking, is kept as `mode='targeted'` in `policy.py` for the record; on 40 fresh seeds it scored lower (REPORT.md section 5.7).

## Requirements
Python 3.10+ (tested on 3.12 and 3.13; the image pins `python:3.12.7-slim`). Standard library only for the policy; `docker` for the container check.
Declared seeds: the shipped policy has no learned asset, is deterministic and uses no random numbers (inference seed: none). Research-only models in `experiments/` used training seeds 1000-1007 and validation seeds 2000-2002.

## Setup and evaluation commands
One command: `bash run_all.sh` (quick) or `bash run_all.sh full`. It writes fresh results to `results/repro/` and checks
them against the committed files in `results/` (identical `action_sha256` for every episode); it never overwrites committed results.
The individual commands (the committed evidence in `results/` used seeds 101 to 105):
```bash
python -m unittest -v                         # kit, policy, fuzz, trace and regression tests
python verify_data.py
python evaluate_method.py --seeds 101,102,103,104,105 --variants all --output results/repro/final.json
python evaluate.py --baseline greedy    --seeds 101,102,103,104,105 --variants all --output results/repro/baseline_greedy.json
python evaluate.py --baseline no_asks   --seeds 101,102,103,104,105 --variants all --output results/repro/baseline_no_asks.json
python evaluate.py --baseline random    --seeds 101,102,103,104,105 --variants all --output results/repro/baseline_random.json
python compare_results.py results/repro
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --variants all --output results/repro/container_check.json
```
**Important:** the unmodified supplied `evaluate.py` launches `policy.py --baseline greedy` in local mode, so running it
without `--image` evaluates the supplied *greedy baseline*, not this submission (the assessed container runs `policy.py`
with no arguments, which selects the submitted policy). Use `evaluate_method.py` (same code, no `--baseline` argument)
or `evaluate.py --image ...` to evaluate the submission. `policy.py` keeps the `--baseline` parser because the supplied runner requires it.

## Explaining decisions
`python explain_episode.py --seed 101 --variant development --days 20 --out trace/` replays an episode and writes
`decisions.txt` (readable) and `decisions.jsonl` (machine-readable). For every ask it records the member, field, cost,
credit and which pairs the answer could unlock; for every introduction it records the agreeing soft fields,
similarity score, and how many other options each member had. The trace is computed by `explain.py` outside the
submitted decision path, and `test_explain.py` checks that it never changes a decision.

## Robustness tests
`test_fuzz.py` (mutated and garbage inputs must give valid empty-or-legal actions), `test_scale.py` (time and size at
200/400 members; a full 200-member episode produces requests up to about 0.5 MB, so the harness's 1 MiB limit leaves about a 2x margin and is reached at roughly 400 members late in an episode, long before time matters), `test_regression.py` (the policy's actions on a committed episode must match the committed `action_sha256`), `test_policy.py` also checks that the submission's asks equal the supplied rule behind the guard.

## Files
`policy.py` (submission), `official_baselines.py` (supplied random baseline, used only for `--baseline random`),
`kit.py`/`evaluate.py` (supplied, unmodified), `test_policy.py`, `test_fuzz.py`, `test_scale.py`, `test_explain.py` (tests), `explain.py`/`explain_episode.py` (decision trace), `make_figures.py` (report figures), `run_all.sh` (one-command run), `results/` (machine-readable episode results),
`experiments/` (scripts and raw outputs behind the report; `run_r3.py`/`analyse_r3.py` are the final selection test), `REPORT.md`, `PRESPEC.txt`, `PRESPEC_R2.txt`, `PRESPEC_R3.txt` (pre-specifications).

## Provenance and licences
No external data, models or paid services. Standard-library Python only inside the image. Experiment scripts under
`experiments/` additionally use NumPy, NetworkX and scikit-learn (all BSD-3-Clause; see `requirements-dev.txt`) and were run offline. AI assistance (Claude, Anthropic)
was used to write and run experiments and draft this repository; see REPORT.md section 9. Code licence: see LICENSE (supplied kit licence applies to supplied files).
