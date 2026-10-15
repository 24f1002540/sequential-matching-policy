"""OFFLINE BOUNDING ANALYSIS ONLY (uses simulator truth; never part of any policy).
Counts pairs that would be feasible if every non-declined hard field were known, among members who arrive by day 59."""
import copy, itertools, json, sys
from kit import generate, eligibility, HARD
def run(seed, variant):
    w = generate(seed, 200, 'evaluation', variant); ms = [m for m in w['members'] if m['arrived_day'] <= 59]
    declined = lambda m: any(m['field_status'][k] == 'declined' for k in HARD)
    full = []
    for m in ms:
        c = copy.deepcopy(m); c['fields'] = copy.deepcopy(m['truth']); full.append(c)
    n = 0; members = set()
    for i, j in itertools.combinations(range(len(ms)), 2):
        if declined(ms[i]) or declined(ms[j]): continue
        if eligibility(full[i], full[j])['status'] == 'feasible': n += 1; members.update((i, j))
    return dict(seed=seed, variant=variant, oracle_feasible_pairs=n, oracle_members_with_a_pair=len(members), arrived=len(ms), declined_members=sum(declined(m) for m in ms))
for v in sys.argv[2].split(','):
    for s in sys.argv[1].split(','): print(json.dumps(run(int(s), v)), flush=True)
