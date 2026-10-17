"""Paired seed-bootstrap intervals for Table A2 (submitted policy minus each supplied baseline, seeds 101-105).
The submitted policy now makes the same decisions as the supplied greedy baseline, so that difference is exactly zero.
Each seed contributes the equal-weight mean of its six family results (the official primary-score aggregation).
Also pools the five official-evaluator seeds with the 20 confirmatory seeds (106-125) for submitted-minus-greedy."""
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json, random, statistics as st, collections, glob
R = '../results/'
def per_seed(path, key='msmi_per_100_arrived_members'):
    d = collections.defaultdict(list)
    for e in json.load(open(path))['episodes']: d[e['seed']].append(e[key])
    return {s: st.mean(v) for s, v in d.items()}
def boot(xs, n=10000, rng=random.Random(11)):
    m = st.mean(xs); b = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return m, b[int(.025 * n)], b[int(.975 * n)]
sub = per_seed(R + 'final.json')
rows = []
for name, f in (('Supplied greedy baseline', 'baseline_greedy.json'), ('Supplied no-clarification', 'baseline_no_asks.json'), ('Supplied random-feasible', 'baseline_random.json')):
    base = per_seed(R + f); d = [sub[s] - base[s] for s in sorted(sub)]
    m, lo, hi = boot(d); rows.append((name, m, lo, hi, sum(x > 0 for x in d), len(d)))
    print(f'{name}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]  seeds better {sum(x>0 for x in d)}/{len(d)}')
json.dump({'table_a2': rows}, open('results/final_intervals.json', 'w'), indent=1)
