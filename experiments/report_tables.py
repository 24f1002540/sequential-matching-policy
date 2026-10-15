import json, statistics as st, sys
R = '/home/claude/sub/results/'
FILES = [('Submitted policy', 'final.json'), ('Supplied greedy baseline', 'baseline_greedy.json'), ('Supplied no-clarification', 'baseline_no_asks.json'), ('Supplied random-feasible', 'baseline_random.json')]
FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
NAME = {'development': 'standard', 'sparse': 'sparse geography', 'cold_start': 'cold start', 'delayed': 'delayed dates', 'shift': 'shifted weights', 'drift': 'changing conditions'}
D = {}
for lab, f in FILES:
    try: D[lab] = json.load(open(R + f))
    except Exception: pass
def fam_rows(d, v): return [e for e in d['episodes'] if e['variant'] == v]
def mean(xs): return sum(xs) / len(xs) if xs else float('nan')
print('**Table A. Primary score and ranking measures (official evaluator output, seeds 101 to 105, %d episodes per policy).**\n' % len(next(iter(D.values()))['episodes']))
print('| Policy | Valid episodes | Primary score (MSMI/100) | Coverage | Mutual acc. /100 | Ask cost | Mean inference s/episode | MSMI events |')
print('|---|---|---|---|---|---|---|---|')
for lab, d in D.items():
    E = d['episodes']; fm = lambda k: mean([mean([e[k] for e in fam_rows(d, v)]) for v in FAM])
    print('| %s | %d / %d | %.3f | %.3f | %.2f | %.0f | %.1f | %d |' % (lab, sum(e['valid'] for e in E), len(E), fm('msmi_per_100_arrived_members'), fm('coverage'), fm('mutual_acceptances_per_100'), mean([e['ask_cost'] for e in E]), mean([e['inference_seconds'] for e in E]), sum(e['mutual_second_meeting_intention'] for e in E)))
print('\n**Table B. Scenario-level outcomes (means per episode).**\n')
print('| Scenario family | Policy | Introductions | Mutual acc. | Dates | MSMI events | Coverage | Median first wait (days) | Unserved members | Missing feedback | Ask cost |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for v in FAM:
    for lab, d in D.items():
        E = fam_rows(d, v)
        mw = mean([st.median(e['first_introduction_wait_days']) if e['first_introduction_wait_days'] else float('nan') for e in E])
        print('| %s | %s | %.1f | %.1f | %.1f | %.2f | %.3f | %.1f | %.1f | %.1f | %.0f |' % (NAME[v], lab, mean([e['assignments'] for e in E]), mean([e['mutual_acceptances'] for e in E]), mean([e['dates'] for e in E]),
              mean([e['mutual_second_meeting_intention'] for e in E]), mean([e['coverage'] for e in E]), mw, mean([e['unserved_members'] for e in E]), mean([e['missing_feedback'] for e in E]), mean([e['ask_cost'] for e in E])))
