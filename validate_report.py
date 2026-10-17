"""Validate REPORT.md Section 6 tables against the committed results files.

Regenerates Table A and Table B with the same methodology as
experiments/report_tables.py (mean-of-family-means aggregation), then asserts
every generated row appears verbatim in REPORT.md. Also checks the evaluation
contract the tables depend on: seeds 101-105, all six scenario families,
30/30 valid episodes per policy, and primary score equal to the official
equal-weight-of-family-means aggregation.
Fails loudly on any mismatch; prints the evidence gap list otherwise.
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'
FILES = [('Submitted policy', 'final.json'),
         ('Supplied greedy baseline', 'baseline_greedy.json'),
         ('Supplied no-clarification', 'baseline_no_asks.json'),
         ('Supplied random-feasible', 'baseline_random.json')]
FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
NAME = {'development': 'standard', 'sparse': 'sparse geography',
        'cold_start': 'cold start', 'delayed': 'delayed dates',
        'shift': 'shifted weights', 'drift': 'changing conditions'}
EXPECTED_SEEDS = [101, 102, 103, 104, 105]

failures = []


def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


D = {}
for lab, f in FILES:
    D[lab] = json.loads((RESULTS / f).read_text())
report = (ROOT / 'REPORT.md').read_text()

# Structural contract.
for lab, d in D.items():
    E = d['episodes']
    check(len(E) == 30, '%s: 30 episodes (got %d)' % (lab, len(E)))
    check(sorted(set(e['seed'] for e in E)) == EXPECTED_SEEDS,
          '%s: seeds exactly 101-105' % lab)
    check(sorted(set(e['variant'] for e in E)) == sorted(FAM),
          '%s: all six scenario families' % lab)
    check(all(e.get('valid') for e in E), '%s: 30/30 valid' % lab)
    fam_means = [mean([e['msmi_per_100_arrived_members'] for e in E
                       if e['variant'] == v]) for v in FAM]
    check(abs(mean(fam_means) - d['summary']['primary_score']) < 1e-9,
          '%s: primary == equal-weight family mean (%.3f)' %
          (lab, d['summary']['primary_score']))

# Table A regeneration.
rows_a = []
for lab, d in D.items():
    E = d['episodes']
    fm = lambda k: mean([mean([e[k] for e in E if e['variant'] == v]) for v in FAM])
    rows_a.append('| %s | %d / %d | %.3f | %.3f | %.2f | %.0f | %.1f | %d |' % (
        lab, sum(e['valid'] for e in E), len(E), fm('msmi_per_100_arrived_members'),
        fm('coverage'), fm('mutual_acceptances_per_100'),
        mean([e['ask_cost'] for e in E]), mean([e['inference_seconds'] for e in E]),
        sum(e['mutual_second_meeting_intention'] for e in E)))
if '--write' in sys.argv:           # refresh the table rows in REPORT.md from the committed results
    lines = report.split('\n')
    for lab, r in zip(D.keys(), rows_a):
        idx = [i for i, l in enumerate(lines) if l.startswith('| %s | ' % lab) and l.count('|') == r.count('|') and ' / ' in l.split('|')[2]]
        assert len(idx) == 1, lab
        lines[idx[0]] = r
    report = '\n'.join(lines)
for r in rows_a:
    if '--write' in sys.argv: continue
    check(r in report, 'Table A row present verbatim: %s...' % r[:60])

# Table B regeneration.
n_b = 0
for v in FAM:
    for lab, d in D.items():
        E = [e for e in d['episodes'] if e['variant'] == v]
        mw = mean([st.median(e['first_introduction_wait_days'])
                   if e['first_introduction_wait_days'] else float('nan') for e in E])
        row = ('| %s | %s | %.1f | %.1f | %.1f | %.2f | %.3f | %.1f | %.1f | %.1f | %.0f |' % (
            NAME[v], lab, mean([e['assignments'] for e in E]),
            mean([e['mutual_acceptances'] for e in E]), mean([e['dates'] for e in E]),
            mean([e['mutual_second_meeting_intention'] for e in E]),
            mean([e['coverage'] for e in E]), mw,
            mean([e['unserved_members'] for e in E]),
            mean([e['missing_feedback'] for e in E]), mean([e['ask_cost'] for e in E])))
        n_b += 1
        if '--write' in sys.argv:
            pre = '| %s | %s | ' % (NAME[v], lab); li = [i for i, l in enumerate(lines) if l.startswith(pre)]; assert len(li) == 1, pre; lines[li[0]] = row; continue
        check(row in report, 'Table B row present verbatim: %s / %s' % (NAME[v], lab))
check(n_b == 24, 'Table B has all 24 scenario rows')

if '--write' in sys.argv:
    (ROOT / 'REPORT.md').write_text('\n'.join(lines)); print('REPORT.md tables refreshed'); sys.exit(0)

# Documented evidence gaps (checked, not fixable from this checkout).
print('GAPS (known, out of scope for this script):')
print('- PRESPEC.txt timing is self-attested: it has an unexpanded $(date) stamp and entered')
print('  git history together with the results it describes, so order cannot be re-proven.')
print('- Section 5 tables are regenerated by experiments/final_tables.py, analyse_conf.py and')
print('  r2_analyse.py from the raw logs in experiments/results (run from any directory).')
print('- Section 5.6 (ten further studies) rests on recorded summaries; its raw outputs are not in this repository.')
print('- results/container_check.json is not committed; the container path is validated by the')
print('  GitHub Actions container-check workflow, not by this script.')

if failures:
    print('\n%d CHECK(S) FAILED' % len(failures))
    sys.exit(1)
print('\nALL REPORT TABLE CHECKS PASSED')
