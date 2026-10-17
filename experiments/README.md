# Experiment scripts (Round 1 and Round 2 evidence)

These scripts produced the numbers in REPORT.md. They are provided as-is for transparency, are **not** part of the submitted
policy or its container image, and use NumPy and NetworkX (BSD-3-Clause) in addition to the standard library.
The analysis scripts (`analyse_*.py`, `r2_analyse.py`, `build_tables.py`, `final_tables.py`) can be run from any directory and read `experiments/results/`. The run scripts need the repository root so that `kit.py` resolves, e.g. `PYTHONPATH=experiments python experiments/run_eval2.py results/x.jsonl 201 development A_greedy`.
`results/` holds the raw per-episode outputs (`conf_*`, `conf2_*`: seeds 106-125; `s_*`, `oracle_*`, `exp_*`: scarcity, oracle and
expected-outcome runs; `r2_*`: Round 2 adoption test, seeds 201-240) and the analysis outputs. `train_models.py` fits the learned
models used only for the Section 5.2 checks; no learned asset is shipped.
