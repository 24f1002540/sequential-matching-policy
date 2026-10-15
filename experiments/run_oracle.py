"""OFFLINE BOUNDING ANALYSIS ONLY. Never part of any submitted policy.
O_oracle: same targeted asks as the incumbent C, but pairs are chosen by max-weight matching on the TRUE expected
probability that a pair ends in MSMI (computed from simulator internals, integrating over the unobserved pair shock).
It bounds how much any ranking/allocation could add if pair quality were perfectly known (myopic, per day)."""
import json, sys, time, math
import networkx as nx
import numpy as np
from kit import Simulator, generate
from smp_core import feasible_edges, targeted_hard_asks
X, W = np.polynomial.hermite_e.hermegauss(9); W = W / W.sum()
def oracle_value(sim, a, b):
    ma, mb = sim.members[a], sim.members[b]; tot = 0.0
    for x, w in zip(X, W):
        s = .45 * x
        pm = ma['response_rate'] * mb['response_rate'] * sim._prob(ma, mb, s) * sim._prob(mb, ma, s)
        sec = 1.0
        for actor, other in ((ma, mb), (mb, ma)):
            p = 1 / (1 + math.exp(-(.15 + actor['second_bias'] + s + .4 * (actor['truth']['relationship_goal'] == other['truth']['relationship_goal']))))
            sec *= actor['response_rate'] * p * .6
        tot += w * pm * .78 * sec
    return tot
def oracle_match(sim, state):
    G = nx.Graph()
    for a, b, _ in feasible_edges(state): G.add_edge(a['member_id'], b['member_id'], weight=oracle_value(sim, a['member_id'], b['member_id']) + 1e-12)
    return sorted(sorted(p) for p in nx.max_weight_matching(G, maxcardinality=False))
def run(seed, variant):
    sim = Simulator(generate(seed, 200, 'evaluation', variant))
    for _ in range(60):
        sim.resolve_asks(targeted_hard_asks(sim.observe())[0]); sim.advance(oracle_match(sim, sim.observe()))
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    r = sim.metrics(); first = set()
    for it in sim.introductions: first.update((it['user_a'], it['user_b']))
    N = len(arrived); served = len(first & arrived)
    r.update(arm='O_oracle_global', seed=seed, variant=variant, arrived_members=N, msmi_per_100_arrived_members=100 * r['mutual_second_meeting_intention'] / max(1, N),
             coverage=served / max(1, N), mutual_acceptances_per_100=100 * r['mutual_acceptances'] / max(1, N))
    return r
if __name__ == '__main__':
    out = sys.argv[1]; seeds = [int(s) for s in sys.argv[2].split(',')]; variants = sys.argv[3].split(',')
    for s in seeds:
        for v in variants:
            t = time.time(); r = run(s, v); r['secs'] = round(time.time() - t, 1); open(out, 'a').write(json.dumps(r) + '\n')
            print(s, v, r['assignments'], r['mutual_acceptances'], r['dates'], r['mutual_second_meeting_intention'], r['ask_cost'], r['secs'], flush=True)
