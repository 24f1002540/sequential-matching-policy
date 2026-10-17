"""Pooled (exploratory seeds 101-105 + confirmatory seeds 106-125) contrasts and power, seed-cluster bootstrap.
Also reports the exploratory-only and confirmatory-only estimates side by side, and the minimum detectable effect."""
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))  # paths below are relative to experiments/
import glob, json, collections, random, statistics as st, math

FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
EXPL = 'results/eval2_results.jsonl'
rows = [dict(json.loads(l), phase='exploratory') for l in open(EXPL)]
for f in sorted(glob.glob('results/conf_*.jsonl') + glob.glob('results/conf2_*.jsonl') + glob.glob('results/conf3_*.jsonl')):
    rows += [dict(json.loads(l), phase='confirmatory') for l in open(f)]
by = collections.defaultdict(dict)
for r in rows:
    by[(r['seed'], r['variant'])][r['arm']] = r
ALLSEEDS = sorted({k[0] for k in by})

def ok(arms, seeds):
    return [s for s in seeds if all(all(a in by.get((s, v), {}) for a in arms) for v in FAM)]

def per_seed(arm, key, seeds):
    return {s: st.mean(by[(s, v)][arm][key] for v in FAM) for s in seeds}

def boot(xs, n=10000, rng=random.Random(5)):
    bs = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return bs[int(.025 * n)], bs[int(.975 * n) - 1]

def line(label, a, b, key, seeds):
    seeds = ok([a, b], seeds)
    if len(seeds) < 3:
        return
    pa, pb = per_seed(a, key, seeds), per_seed(b, key, seeds)
    d = [pa[s] - pb[s] for s in seeds]
    lo, hi = boot(d)
    print('%-34s %-30s n=%2d  %+7.3f [%+7.3f,%+7.3f]  SD of per-seed diff %.3f' % (label, key, len(seeds), st.mean(d), lo, hi, st.stdev(d)))

EX = [s for s in ALLSEEDS if s <= 105]; CO = [s for s in ALLSEEDS if s >= 106]
A, C, Fg, F, G = 'A_greedy', 'C_targeted_greedy_crude', 'Fg_learned_greedy', 'F_learned_global', 'G_learned_global_adaptive'
for key in ['mutual_acceptances', 'mutual_second_meeting_intention', 'msmi_per_100_arrived_members']:
    print('\n#### %s' % key)
    for lab, a, b in [('C - A (targeted vs baseline asks)', C, A), ('Fg - C (learned vs crude)', Fg, C), ('Fg - A', Fg, A),
                      ('F - Fg (global vs greedy)', F, Fg), ('G - F (adaptive vs frozen)', G, F),
                      ('N - A (no asks vs baseline)', 'N_no_asks', A), ('A - R (baseline vs random)', A, 'R_random')]:
        for nm, S in (('expl 101-105', EX), ('conf 106-125', CO), ('pooled', ALLSEEDS)):
            line('%s [%s]' % (lab, nm), a, b, key, S)

print('\n#### Power: SD of per-seed primary-score difference vs minimum detectable difference (80% power, two-sided 5%)')
for lab, a, b in [('C - A', C, A), ('Fg - A', Fg, A)]:
    S = ok([a, b], CO)
    d = [per_seed(a, 'msmi_per_100_arrived_members', S)[s] - per_seed(b, 'msmi_per_100_arrived_members', S)[s] for s in S]
    sd = st.stdev(d)
    for n in (20, 40, 100):
        print('%-8s SD %.3f -> MDE with %3d seeds per family: %.3f MSMI/100' % (lab, sd, n, 2.8 * sd / math.sqrt(n)))
for a in (A, C, Fg):
    S = ok([a], CO)
    v = list(per_seed(a, 'msmi_per_100_arrived_members', S).values())
    print('%-26s per-seed primary score: mean %.3f SD %.3f -> SE of a 20-seed mean %.3f' % (a, st.mean(v), st.stdev(v), st.stdev(v) / math.sqrt(len(v))))
print('\nFunnel (confirmatory seeds):')
for a in (A, C, Fg, F, G, 'N_no_asks', 'R_random'):
    S = ok([a], CO)
    if not S:
        continue
    R = [by[(s, v)][a] for s in S for v in FAM]
    asg, mut, dat, ms = (sum(r[k] for r in R) for k in ('assignments', 'mutual_acceptances', 'dates', 'mutual_second_meeting_intention'))
    print('%-26s n_ep=%3d assign %5d -> mutual %4d (%.1f%%) -> dates %4d (%.0f%% of mutual) -> MSMI %3d (%.0f%% of dates); zero-MSMI episodes %d' % (
        a, len(R), asg, mut, 100 * mut / asg, dat, 100 * dat / max(1, mut), ms, 100 * ms / max(1, dat), sum(r['mutual_second_meeting_intention'] == 0 for r in R)))
