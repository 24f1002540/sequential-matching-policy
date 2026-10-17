import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))  # paths below are relative to experiments/
import json, random, statistics as st, collections
FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
def load(f): return [json.loads(l) for l in open(f)]
C, S = load('results/r2_c.jsonl'), load('results/r2_s.jsonl')
def idx(rows):
    d = collections.defaultdict(dict)
    for r in rows: d[r['seed']][r['variant']] = r
    return d
ci, si = idx(C), idx(S)
seeds = sorted(s for s in ci if s in si and all(v in ci[s] and v in si[s] for v in FAM))
print('complete seeds', len(seeds))
rng = random.Random(7)
def boot(d, n=10000):
    b = sorted(st.mean(rng.choices(d, k=len(d))) for _ in range(n)); return b[int(.025*n)], b[int(.975*n)-1]
def per(idx_, key): return {s: st.mean(idx_[s][v][key] for v in FAM) for s in seeds}
rows = [('assignments', 'introductions'), ('mutual_acceptances', 'mutual acceptances'), ('dates', 'dates'), ('mutual_second_meeting_intention', 'MSMI events'),
        ('coverage', 'coverage'), ('ask_cost', 'ask cost'), ('msmi_per_100_arrived_members', 'primary score (MSMI/100)')]
res = {}
for k, lab in rows:
    a, b = per(si, k), per(ci, k); d = [a[s] - b[s] for s in seeds]; lo, hi = boot(d)
    res[k] = (st.mean(d), lo, hi); print('%-26s S-C %+8.3f [%+8.3f, %+8.3f]  S mean %.3f  C mean %.3f  seeds up/down %d/%d' % (lab, st.mean(d), lo, hi, st.mean(a.values()), st.mean(b.values()), sum(x > 0 for x in d), sum(x < 0 for x in d)))
tot = lambda i, k: sum(i[s][v][k] for s in seeds for v in FAM)
print('MSMI events total: C %d  S %d ; zero-MSMI episodes C %d S %d of %d' % (tot(ci,'mutual_second_meeting_intention'), tot(si,'mutual_second_meeting_intention'),
      sum(ci[s][v]['mutual_second_meeting_intention']==0 for s in seeds for v in FAM), sum(si[s][v]['mutual_second_meeting_intention']==0 for s in seeds for v in FAM), len(seeds)*6))
print('max call secs C %.2f S %.2f' % (max(ci[s][v]['max_call_seconds'] for s in seeds for v in FAM), max(si[s][v]['max_call_seconds'] for s in seeds for v in FAM)))
g2 = res['assignments'][1] > 0; g3 = res['mutual_second_meeting_intention'][1] > -0.10; g4 = res['mutual_acceptances'][0] >= 0; g5 = res['ask_cost'][2] <= 1.0
print('GATES  G2 intro lower>0: %s | G3 MSMI lower>-0.10: %s | G4 mutual point>=0: %s | G5 cost diff upper<=1: %s' % (g2, g3, g4, g5))
print('ADOPT S:', g2 and g3 and g4 and g5)
