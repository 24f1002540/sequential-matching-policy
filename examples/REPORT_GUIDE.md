# Technical report guide

A complete report explains the claim and supplies evidence rather than presenting only a score.

1. State the hypothesis and the policy's decision objective. Describe reciprocal eligibility, allocation, waiting and clarification. Probability estimates are optional; if reported, define each directional and joint prediction target and its observation window.
2. Define the observations used at each decision. Explain missingness, declined answers, delayed feedback, selective labels and leakage prevention.
3. Describe training, inference assets, randomness, dependencies, external data, models and coding-tool use.
4. Compare your method with all three supplied baselines on identical seeds and all six scenario families. Include full JSON results and commands.
5. Show the outcome funnel, MSMI per 100 arrived members, distinct-member coverage, first-introduction waits, unserved members, clarification cost and missing feedback. Report variation across seeds.
6. Test at least one causal design claim with a focused ablation. Explain when the change helps or hurts.
7. Examine sparse supply, incompatible candidates, withheld constraints, cold starts, delays and shifts. Explain uncertainty and low event counts.
8. State what these invented outcomes cannot establish about real people. Describe the adapter and validation needed for later authorised product use.

The reference runs in `baseline_results/` demonstrate the result format. They use public seed 101 and are smoke-test comparisons, not statistically reliable performance claims or the private competition leaderboard.
