"""Confirmatory analysis for seeds 106-125 (pre-specified in results/PRESPEC.txt).
Inputs: results/conf_*.jsonl (arms A, C, Fg) and results/conf2_*.jsonl (arms F, G).
Bootstrap resamples SEEDS (clusters of the six scenario families), not single episodes."""
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))  # paths below are relative to experiments/
import glob, json, collections, random, statistics as st, sys

FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
NAME = {'A_greedy': 'A', 'C_targeted_greedy_crude': 'C', 'Fg_learned_greedy': 'Fg',
        'F_learned_global': 'F', 'G_learned_global_adaptive': 'G'}
rows = []
for f in sorted(glob.glob('results/conf_*.jsonl') + glob.glob('results/conf2_*.jsonl')):
    rows += [json.loads(l) for l in open(f)]
if not rows: sys.exit('no rows found in results/conf_*.jsonl')
by = collections.defaultdict(dict)                    # (seed, family) -> arm -> row
for r in rows:
    by[(r['seed'], r['variant'])][r['arm']] = r

def complete_seeds(arms):
    return sorted(s for s in {k[0] for k in by}
                  if all(all(a in by.get((s, v), {}) for a in arms) for v in FAM))

def per_seed(arm, key, seeds, fams=FAM):
    return {s: st.mean(by[(s, v)][arm][key] for v in fams) for s in seeds}

def boot(d, n=10000, rng=random.Random(11)):
    xs = list(d.values()); m = st.mean(xs)
    bs = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return m, bs[int(.025 * n)], bs[int(.975 * n) - 1]

def contrast(a, b, key, seeds, fams=FAM):
    pa, pb = per_seed(a, key, seeds, fams), per_seed(b, key, seeds, fams)
    d = {s: pa[s] - pb[s] for s in seeds}
    m, lo, hi = boot(d)
    return m, lo, hi, sum(x > 0 for x in d.values()), sum(x < 0 for x in d.values()), len(d)

def show(label, a, b, key, seeds, fams=FAM):
    m, lo, hi, up, dn, n = contrast(a, b, key, seeds, fams)
    print('%-52s %-32s %+8.3f [%+7.3f,%+7.3f]  seeds better/worse/tied %d/%d/%d (n=%d)' % (label, key, m, lo, hi, up, dn, n - up - dn, n))

arms1 = ['A_greedy', 'C_targeted_greedy_crude', 'Fg_learned_greedy']
S1 = complete_seeds(arms1)
print('batch-1 complete seeds:', len(S1), S1)
if S1:
    print('\n== ARM SUMMARY (confirmatory seeds; per-episode means, equal-weight over families) ==')
    print('%-4s %9s %9s %10s %9s %7s %7s %7s %7s %9s %8s' % ('arm', 'MSMI/100', 'coverage', 'mutual/100', 'askcost', 'assign', 'mutual', 'dates', 'MSMI', 'zeroMSMI', 'events'))
    for a in [x for x in NAME if all(x in by.get((s, v), {}) for s in S1 for v in FAM)]:
        g = lambda k: st.mean(per_seed(a, k, S1).values())
        zero = sum(by[(s, v)][a]['mutual_second_meeting_intention'] == 0 for s in S1 for v in FAM)
        ev = sum(by[(s, v)][a]['mutual_second_meeting_intention'] for s in S1 for v in FAM)
        print('%-4s %9.3f %9.3f %10.2f %9.1f %7.1f %7.1f %7.1f %7.2f %6d/%d %8d' % (NAME[a], g('msmi_per_100_arrived_members'), g('coverage'), g('mutual_acceptances_per_100'), g('ask_cost'),
              g('assignments'), g('mutual_acceptances'), g('dates'), g('mutual_second_meeting_intention'), zero, len(S1) * 6, ev))
    sd = {a: st.stdev(per_seed(a, 'msmi_per_100_arrived_members', S1).values()) for a in arms1}
    print('SD across seeds of the primary score:', {NAME[a]: round(v, 3) for a, v in sd.items()})
    print('\n== MSMI per 100 by family ==')
    print('%-4s' % 'arm', *['%11s' % v[:11] for v in FAM])
    for a in arms1:
        print('%-4s' % NAME[a], *['%11.3f' % st.mean(by[(s, v)][a]['msmi_per_100_arrived_members'] for s in S1) for v in FAM])
    print('\n== PRE-SPECIFIED CONTRASTS K1-K4 (seed-cluster bootstrap 95% CI) ==')
    A, C, Fg = arms1
    show('K1  C - A', C, A, 'mutual_acceptances', S1)
    show('K2  C - A', C, A, 'mutual_second_meeting_intention', S1)
    show('K3  Fg - C', Fg, C, 'mutual_second_meeting_intention', S1)
    show('K4  C - A', C, A, 'ask_cost', S1)
    print('\n-- headline metric (primary score = mean over families of MSMI per 100 arrived) --')
    show('C - A', C, A, 'msmi_per_100_arrived_members', S1)
    show('Fg - C', Fg, C, 'msmi_per_100_arrived_members', S1)
    show('Fg - A', Fg, A, 'msmi_per_100_arrived_members', S1)
    print('\n-- secondary descriptive --')
    for key in ['dates', 'coverage', 'mutual_acceptances']:
        show('C - A', C, A, key, S1); show('Fg - C', Fg, C, key, S1)
    print('\n-- per-family C - A, MSMI events per episode --')
    for v in FAM:
        show('  ' + v, C, A, 'mutual_second_meeting_intention', S1, [v])

arms2 = ['Fg_learned_greedy', 'F_learned_global', 'G_learned_global_adaptive']
S2 = complete_seeds(arms2)
print('\nbatch-2 complete seeds:', len(S2))
if len(S2) >= 3:
    print('== K5 (H3) global vs greedy, same learned weights; K6 (H4) adaptive vs frozen ==')
    for key in ['mutual_acceptances', 'dates', 'mutual_second_meeting_intention', 'msmi_per_100_arrived_members']:
        show('K5  F - Fg', 'F_learned_global', 'Fg_learned_greedy', key, S2)
    for key in ['mutual_acceptances', 'dates', 'mutual_second_meeting_intention', 'msmi_per_100_arrived_members']:
        show('K6  G - F', 'G_learned_global_adaptive', 'F_learned_global', key, S2)
    for v in ['shift', 'drift', 'development', 'cold_start', 'delayed', 'sparse']:
        show('K6 within ' + v + ' G - F', 'G_learned_global_adaptive', 'F_learned_global', 'mutual_acceptances', S2, [v])
    print('\narm summary on batch-2 seeds:')
    for a in arms2:
        print('%-4s MSMI/100 %.3f mutual/episode %.2f events %d' % (NAME[a], st.mean(per_seed(a, 'msmi_per_100_arrived_members', S2).values()),
              st.mean(per_seed(a, 'mutual_acceptances', S2).values()), sum(by[(s, v)][a]['mutual_second_meeting_intention'] for s in S2 for v in FAM)))
