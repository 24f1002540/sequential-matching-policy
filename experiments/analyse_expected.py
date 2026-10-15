"""Offline expected-outcome analysis (seeds 106-111). Intervals: paired differences averaged within seed over the six families,
then a t-interval over the six seed-level values (conservative: the families of one seed share a population)."""
import glob, json, collections, math, statistics as st

FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
rows = [json.loads(l) for f in sorted(glob.glob('results/exp_[01].jsonl')) for l in open(f)]
by = collections.defaultdict(dict)
for r in rows: by[(r['seed'], r['variant'])][r['arm']] = r
ARMS = ['A_greedy', 'C_targeted_greedy_crude', 'Fg_learned_greedy', 'S_scarcity', 'O_oracle_global']
NM = {'A_greedy': 'A', 'C_targeted_greedy_crude': 'C', 'Fg_learned_greedy': 'Fg', 'S_scarcity': 'S', 'O_oracle_global': 'O'}
seeds = sorted(s for s in {k[0] for k in by} if all(all(a in by.get((s, v), {}) for a in ARMS) for v in FAM))
print('complete seeds:', seeds)
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306}
def per_seed(arm, key): return {s: st.mean(by[(s, v)][arm][key] for v in FAM) for s in seeds}
print('\n== Calibration of the expected-outcome measure (totals over %d episodes per arm) ==' % (len(seeds) * 6))
print('%-4s %12s %12s %10s %12s %12s' % ('arm', 'realized MSMI', 'expected MSMI', 'ratio', 'realized mut', 'expected mut'))
for a in ARMS:
    R = [by[(s, v)][a] for s in seeds for v in FAM]
    rm, em = sum(r['mutual_second_meeting_intention'] for r in R), sum(r['expected_msmi'] for r in R)
    rmu, emu = sum(r['mutual_acceptances'] for r in R), sum(r['expected_mutual'] for r in R)
    print('%-4s %12d %12.1f %10.2f %12d %12.1f   (Poisson SE of realized MSMI ~ %.1f)' % (NM[a], rm, em, rm / em, rmu, emu, math.sqrt(max(rm, 1))))
print('\n== Per-episode means ==')
print('%-4s %9s %9s %9s %9s %9s %9s' % ('arm', 'exp MSMI', 'exp mut', 'assign', 'coverage', 'real MSMI', 'real mut'))
for a in ARMS:
    g = lambda k: st.mean(per_seed(a, k).values())
    print('%-4s %9.3f %9.2f %9.1f %9.3f %9.3f %9.2f' % (NM[a], g('expected_msmi'), g('expected_mutual'), g('assignments'), g('coverage'), g('mutual_second_meeting_intention'), g('mutual_acceptances')))
def contrast(a, b, key, fams=FAM):
    pa = {s: st.mean(by[(s, v)][a][key] for v in fams) for s in seeds}; pb = {s: st.mean(by[(s, v)][b][key] for v in fams) for s in seeds}
    d = [pa[s] - pb[s] for s in seeds]; m = st.mean(d); n = len(d)
    if n < 3: return m, float('nan'), float('nan'), 0, 0, n, 0.0
    se = st.stdev(d) / math.sqrt(n); t = T95.get(n - 1, 1.96)
    return m, m - t * se, m + t * se, sum(x > 0 for x in d), sum(x < 0 for x in d), n, st.mean(pb.values())
print('\n== Paired contrasts (seed-level t-intervals); relative change = difference / second arm ==')
for lab, a, b in [('E1 C - A', 'C_targeted_greedy_crude', 'A_greedy'), ('E2 Fg - C', 'Fg_learned_greedy', 'C_targeted_greedy_crude'),
                  ('E3 S - C', 'S_scarcity', 'C_targeted_greedy_crude'), ('E4 O - C (bound)', 'O_oracle_global', 'C_targeted_greedy_crude')]:
    for key in ['expected_msmi', 'expected_mutual', 'assignments', 'coverage']:
        m, lo, hi, up, dn, n, base = contrast(a, b, key)
        print('%-18s %-16s %+8.3f [%+7.3f,%+7.3f]  %+6.1f%%  seeds up/down %d/%d (n=%d)' % (lab, key, m, lo, hi, 100 * m / base if base else float('nan'), up, dn, n))
print('\n-- E-contrasts by family, expected MSMI per episode --')
for lab, a, b in [('C - A', 'C_targeted_greedy_crude', 'A_greedy'), ('S - C', 'S_scarcity', 'C_targeted_greedy_crude'), ('O - C', 'O_oracle_global', 'C_targeted_greedy_crude')]:
    for v in FAM:
        m, lo, hi, up, dn, n, base = contrast(a, b, 'expected_msmi', [v])
        print('%-8s %-12s %+7.3f [%+7.3f,%+7.3f]  (%+5.1f%%)' % (lab, v, m, lo, hi, 100 * m / base if base else float('nan')))
