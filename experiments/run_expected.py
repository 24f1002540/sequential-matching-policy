"""OFFLINE EVALUATION AID. Records, per episode, the simulator's TRUE expected number of mutual acceptances and MSMI for the pairs
the policy introduced (summing true pair probabilities integrated over the unobserved pair shock). Never used inside a policy."""
import json, sys, time, math
import numpy as np
import networkx as nx
import run_eval2
from kit import Simulator, generate
from smp_core import targeted_hard_asks, feasible_edges
from scarcity_arm import scarcity_match
from run_oracle import oracle_value, X, W
def p_mutual(sim, a, b):
    ma, mb = sim.members[a], sim.members[b]; tot = 0.0
    for x, w in zip(X, W):
        s = .45 * x; tot += w * ma['response_rate'] * mb['response_rate'] * sim._prob(ma, mb, s) * sim._prob(mb, ma, s)
    return tot
def oracle_match(sim, state):
    G = nx.Graph()
    for a, b, _ in feasible_edges(state): G.add_edge(a['member_id'], b['member_id'], weight=oracle_value(sim, a['member_id'], b['member_id']) + 1e-12)
    return sorted(sorted(p) for p in nx.max_weight_matching(G, maxcardinality=False))
ARMS = {k: run_eval2.ARMS[k] for k in ('A_greedy', 'C_targeted_greedy_crude', 'Fg_learned_greedy')}
ARMS['S_scarcity'] = (lambda s: targeted_hard_asks(s)[0], scarcity_match)
ARMS['O_oracle_global'] = (lambda s: targeted_hard_asks(s)[0], None)
def run(arm, seed, variant):
    ask_fn, match_fn = ARMS[arm]; sim = Simulator(generate(seed, 200, 'evaluation', variant)); em = ems = 0.0
    for _ in range(60):
        sim.resolve_asks(ask_fn(sim.observe())); st = sim.observe()
        pairs = oracle_match(sim, st) if arm == 'O_oracle_global' else match_fn(st)
        for p in pairs: em += p_mutual(sim, *p); ems += oracle_value(sim, *p)
        sim.advance(pairs)
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    r = sim.metrics(); first = set()
    for it in sim.introductions: first.update((it['user_a'], it['user_b']))
    N = len(arrived); r.update(arm=arm, seed=seed, variant=variant, arrived_members=N, expected_mutual=em, expected_msmi=ems,
        msmi_per_100_arrived_members=100 * r['mutual_second_meeting_intention'] / max(1, N), coverage=len(first & arrived) / max(1, N))
    return r
if __name__ == '__main__':
    out = sys.argv[1]; seeds = [int(s) for s in sys.argv[2].split(',')]; variants = sys.argv[3].split(','); arms = sys.argv[4].split(',')
    for s in seeds:
        for v in variants:
            for a in arms:
                t = time.time(); r = run(a, s, v); r['secs'] = round(time.time() - t, 1); open(out, 'a').write(json.dumps(r) + '\n')
                print(s, v, a, r['assignments'], r['mutual_acceptances'], r['mutual_second_meeting_intention'], round(r['expected_mutual'], 2), round(r['expected_msmi'], 3), r['secs'], flush=True)
