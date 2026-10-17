"""R3 analysis (pre-specified in PRESPEC_R3.txt): C minus A on seeds 5001-5040, and pooled over all fresh paired blocks.
Teammate blocks are entered from their recorded summaries (block mean difference, 40 seeds each); the standard error of the pooled
mean uses the per-seed standard deviation of the difference measured in our own blocks."""
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json, glob, random, statistics as st, collections, math
FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
def diffs(files, a, c):
    by = collections.defaultdict(dict)
    for f in files:
        for l in open(f):
            r = json.loads(l); by[(r['seed'], r['arm'])][r['variant']] = r['msmi_per_100_arrived_members']
    seeds = sorted({s for s, _ in by if len(by[(s, a)]) == 6 and len(by[(s, c)]) == 6})
    return [st.mean(by[(s, c)].values()) - st.mean(by[(s, a)].values()) for s in seeds]
def boot(xs, n=10000, rng=random.Random(11)):
    b = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n)); return st.mean(xs), b[int(.025 * n)], b[int(.975 * n)]
r3 = diffs(sorted(glob.glob('results/r3_*.jsonl')), 'A_greedy', 'C_submitted')
conf = diffs(sorted(glob.glob('results/conf_*.jsonl')), 'A_greedy', 'C_targeted_greedy_crude')
m, lo, hi = boot(r3)
print(f'R3 seeds 5001-5040: {len(r3)} seeds, C minus A = {m:+.3f} [{lo:+.3f}, {hi:+.3f}]; C better on {sum(x>0 for x in r3)} seeds, worse on {sum(x<0 for x in r3)}')
print(f'   condition (1) point estimate negative: {m < 0}')
m2, lo2, hi2 = boot(conf); print(f'Confirmatory 106-125: {len(conf)} seeds, C minus A = {m2:+.3f} [{lo2:+.3f}, {hi2:+.3f}]')
team = [('401-440', -0.044), ('601-640', 0.371 - 0.319), ('801-840', 0.0), ('1101-1140', 0.323 - 0.463), ('1301-1340', 0.371 - 0.429), ('3201-3240', 0.327 - 0.362)]
means = [(len(r3), m), (len(conf), m2)] + [(40, d) for _, d in team]
N = sum(n for n, _ in means); pooled = sum(n * d for n, d in means) / N
sd = st.pstdev(r3 + conf); se = sd / math.sqrt(N)
print(f'Per-seed SD of C minus A (own blocks): {sd:.3f}')
print(f'POOLED over {N} seeds ({len(means)} blocks): {pooled:+.3f} [{pooled-1.96*se:+.3f}, {pooled+1.96*se:+.3f}]')
print(f'   condition (2) upper bound < 0: {pooled + 1.96 * se < 0}')
print('   without 1101-1140 (largest gap):', f'{(sum(n*d for n,d in means) - 40*(0.323-0.463)) / (N-40):+.3f}')

# Funnel measures, seeds 5001-5040 (per episode, mean over 240 episodes per arm) and paired seed-bootstrap differences
KEYS = [('assignments', 'Introductions'), ('mutual_acceptances', 'Mutual acceptances'), ('dates', 'Dates'),
        ('mutual_second_meeting_intention', 'MSMI events'), ('ask_cost', 'Ask cost (units)')]
rows = [json.loads(l) for f in sorted(glob.glob('results/r3_*.jsonl')) for l in open(f)]
by = collections.defaultdict(list)
for r in rows: by[(r['seed'], r['arm'])].append(r)
seeds = sorted({s for s, _ in by})
print('\nMeasure | A (supplied asks) | C (targeted asks) | C minus A [95% over seeds]')
for k, name in KEYS:
    a = [st.mean(r[k] for r in by[(s, 'A_greedy')]) for s in seeds]; c = [st.mean(r[k] for r in by[(s, 'C_submitted')]) for s in seeds]
    d = [y - x for x, y in zip(a, c)]; m_, l_, h_ = boot(d)
    print(f'{name} | {st.mean(a):.2f} | {st.mean(c):.2f} | {m_:+.2f} [{l_:+.2f}, {h_:+.2f}]')
za = sum(r['mutual_second_meeting_intention'] == 0 for r in rows if r['arm'] == 'A_greedy'); zc = sum(r['mutual_second_meeting_intention'] == 0 for r in rows if r['arm'] == 'C_submitted')
print(f'Zero-MSMI episodes: A {za} / 240, C {zc} / 240')
pa = st.mean(st.mean(r['msmi_per_100_arrived_members'] for r in by[(s, 'A_greedy')]) for s in seeds); pc = st.mean(st.mean(r['msmi_per_100_arrived_members'] for r in by[(s, 'C_submitted')]) for s in seeds)
print(f'Primary score: A {pa:.3f}, C {pc:.3f}')
