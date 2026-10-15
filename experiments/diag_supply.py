"""Diagnostic (observable state only): is the system pair-supply-limited? For the incumbent C policy, track the set of
pairs that were EVER feasible (per supplied eligibility, among available members at a match step) vs pairs introduced."""
import itertools, sys, json, statistics as st
from kit import Simulator, generate, baseline_match, eligibility
from smp_core import targeted_hard_asks

def run(seed, variant):
    sim = Simulator(generate(seed, 200, 'evaluation', variant))
    ever = set(); first_day = {}; days_feasible = {}; intro = set(); util = []; idle_with_options = 0; avail_days = 0; backlog_end = None
    for day in range(60):
        sim.resolve_asks(targeted_hard_asks(sim.observe())[0])
        s = sim.observe(); ms = [m for m in s['members'] if m['available']]
        past = {tuple(sorted((i['user_a'], i['user_b']))) for i in s['introductions']}
        feas = []
        for a, b in itertools.combinations(ms, 2):
            k = tuple(sorted((a['member_id'], b['member_id'])))
            if k not in past and eligibility(a, b)['status'] == 'feasible':
                feas.append(k)
        ever.update(feas)
        for k in feas:
            first_day.setdefault(k, day); days_feasible[k] = days_feasible.get(k, 0) + 1
        pairs = baseline_match(s)
        for p in pairs: intro.add(tuple(sorted(p)))
        with_opt = {i for k in feas for i in k}; matched = {i for p in pairs for i in p}
        idle_with_options += len(with_opt - matched); avail_days += len(ms)
        util.append((len(feas), len(pairs)))
        sim.advance(pairs)
    late = sum(1 for k in ever - intro if first_day[k] >= 52)
    persistent = sum(1 for k in ever - intro if days_feasible[k] >= 5)
    return dict(never_introduced_first_feasible_from_day52=late, never_introduced_but_feasible_5plus_days=persistent, seed=seed, variant=variant, ever_feasible=len(ever), introduced=len(intro),
                never_introduced=len(ever - intro), share_introduced=round(len(intro) / max(1, len(ever)), 3),
                mean_feasible_edges_per_day=round(st.mean(u[0] for u in util), 1), mean_pairs_per_day=round(st.mean(u[1] for u in util), 2),
                member_days_idle_with_option=idle_with_options, member_days_available=avail_days)
if __name__ == '__main__':
    for v in sys.argv[2].split(','):
        for s in sys.argv[1].split(','):
            r = run(int(s), v); print(json.dumps(r), flush=True)
