"""Generate the Markdown evidence tables for the note directly from raw results (no manual transcription)."""
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))  # paths below are relative to experiments/
import glob, json, collections, random, statistics as st, math

FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
EXPL = 'results/eval2_results.jsonl'
LAB = {'R_random': 'R  random-feasible (supplied)', 'N_no_asks': 'N  no clarification (supplied)', 'A_greedy': 'A  baseline asks + greedy (supplied)',
       'C_targeted_greedy_crude': 'C  targeted asks + supplied greedy', 'Fg_learned_greedy': 'Fg learned values + soft asks, greedy',
       'F_learned_global': 'F  learned values + soft asks, global', 'G_learned_global_adaptive': 'G  F + online adaptation', 'S_scarcity': 'S  targeted asks + scarcity-weighted matching', 'O_oracle_global': 'O  ORACLE bound (offline only)'}
ORDER = list(LAB)

def load(files, phase):
    out = []
    for f in files:
        out += [dict(json.loads(l), phase=phase) for l in open(f)]
    return out
ex = load([EXPL], 'exploratory')
co = load(sorted(glob.glob('results/conf_*.jsonl') + glob.glob('results/conf2_*.jsonl') + glob.glob('results/conf3_*.jsonl')), 'confirmatory')
orc = load(sorted(glob.glob('results/oracle_[01].jsonl')) + sorted(glob.glob('results/s_[01].jsonl')), 'confirmatory')
co += orc

def index(rows):
    by = collections.defaultdict(dict)
    for r in rows: by[(r['seed'], r['variant'])][r['arm']] = r
    return by
BY = {'exploratory': index(ex), 'confirmatory': index(co)}
BYALL = index(ex + co)

def seeds_for(by, arms):
    ss = {k[0] for k in by}
    return sorted(s for s in ss if all(all(a in by.get((s, v), {}) for a in arms) for v in FAM))

def per_seed(by, arm, key, seeds): return {s: st.mean(by[(s, v)][arm][key] for v in FAM) for s in seeds}
def boot(xs, n=10000, rng=random.Random(3)):
    bs = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(n)); return bs[int(.025 * n)], bs[int(.975 * n) - 1]

def summary_table(by, title):
    arms = [a for a in ORDER if seeds_for(by, [a])]
    print('\n**%s**\n' % title)
    print('| Policy | seeds | Primary score (MSMI/100) | Coverage | Mutual acc. /100 | Ask cost | Assign. | Mutual | Dates | MSMI events | Zero-MSMI episodes |')
    print('|---|---|---|---|---|---|---|---|---|---|---|')
    for a in arms:
        S = seeds_for(by, [a]); g = lambda k: st.mean(per_seed(by, a, k, S).values())
        R = [by[(s, v)][a] for s in S for v in FAM]
        print('| %s | %d | %.3f | %.3f | %.2f | %.0f | %.1f | %.1f | %.1f | %d | %d / %d |' % (LAB[a], len(S), g('msmi_per_100_arrived_members'), g('coverage'), g('mutual_acceptances_per_100'), g('ask_cost'),
              g('assignments'), g('mutual_acceptances'), g('dates'), sum(r['mutual_second_meeting_intention'] for r in R), sum(r['mutual_second_meeting_intention'] == 0 for r in R), len(R)))

def fmt(m, lo, hi, nd=2): return ('%+.' + str(nd) + 'f [%+.' + str(nd) + 'f, %+.' + str(nd) + 'f]') % (m, lo, hi)
def contrast_row(label, a, b, hyp):
    cells = []
    for nm, by in (('exploratory', BY['exploratory']), ('confirmatory', BY['confirmatory']), ('pooled', BYALL)):
        S = seeds_for(by, [a, b])
        if len(S) < 3: cells.append('n/a'); continue
        row = []
        for key, nd in (('mutual_acceptances', 2), ('mutual_second_meeting_intention', 2), ('msmi_per_100_arrived_members', 3)):
            pa, pb = per_seed(by, a, key, S), per_seed(by, b, key, S); d = [pa[s] - pb[s] for s in S]; lo, hi = boot(d)
            row.append(fmt(st.mean(d), lo, hi, nd))
        cells.append('<br>'.join(row) + '<br>(n=%d seeds)' % len(S))
    print('| %s | %s | %s | %s | %s |' % (label, hyp, cells[0], cells[1], cells[2]))

def contrast_table():
    print('\n| Contrast (first minus second) | Test | Exploratory seeds 101–105 | **Confirmatory seeds 106–125** | Pooled seeds 101–125 |')
    print('|---|---|---|---|---|')
    print('| *each cell: mutual acceptances per episode; MSMI events per episode; primary score (MSMI/100); 95% CI from resampling seeds* | | | | |')
    C, A = 'C_targeted_greedy_crude', 'A_greedy'
    contrast_row('N − A: no clarification vs baseline asks', 'N_no_asks', A, 'K7')
    contrast_row('C − A: targeted vs baseline asks', C, A, 'K1, K2')
    contrast_row('A − R: baseline ranking vs random-feasible', A, 'R_random', 'K8')
    contrast_row('Fg − C: learned values + soft asks vs incumbent', 'Fg_learned_greedy', C, 'K3')
    contrast_row('F − Fg: global vs greedy, same learned values', 'F_learned_global', 'Fg_learned_greedy', 'K5')
    contrast_row('G − F: adaptive vs frozen', 'G_learned_global_adaptive', 'F_learned_global', 'K6')
    contrast_row('S − C: scarcity-weighted matching vs incumbent', 'S_scarcity', C, 'K10, K11')
    contrast_row('O − C: oracle ranking vs incumbent (bound)', 'O_oracle_global', C, 'K9')

import sys
which = sys.argv[1] if len(sys.argv) > 1 else 'all'
if which in ('summary', 'all'):
    summary_table(BY['confirmatory'], 'Confirmatory seeds 106–125 (20 seeds × 6 families = 120 episodes per policy)')
    summary_table(BY['exploratory'], 'Exploratory seeds 101–105 (5 seeds × 6 families = 30 episodes per policy)')
if which in ('contrast', 'all'):
    contrast_table()
