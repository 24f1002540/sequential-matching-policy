"""Pilot policy components (observable-state only). Used for Round-1 pilot ablations.
Nothing here reads simulator hidden fields (truth, bias, response_rate, seeds)."""
import itertools
import networkx as nx
from kit import HARD, SOFT, eligibility, baseline_asks, baseline_match

def _past(state):
    return {tuple(sorted((i['user_a'], i['user_b']))) for i in state['introductions']}

def unresolvable(m):
    """A declined hard field stays unknown forever -> member can never be matched."""
    return any(m['field_status'][k] == 'declined' and m['fields'][k] is None for k in HARD)

def sim_score(a, b):
    return sum(a['fields'].get(k) is not None and a['fields'].get(k) == b['fields'].get(k) for k in SOFT)

def feasible_edges(state):
    ms = [m for m in state['members'] if m['available']]
    past = _past(state)
    out = []
    for a, b in itertools.combinations(ms, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key in past:
            continue
        if eligibility(a, b)['status'] == 'feasible':
            out.append((a, b, key))
    return out

def targeted_hard_asks(state):
    """Value-of-information style: ask hard-constraint bundles where the answer can unlock pairs
    not already known infeasible, scored per unit of budget; never ask unresolvable members."""
    budget = state['ask_budget_remaining']
    ms = [m for m in state['members'] if m['available']]
    byid = {m['member_id']: m for m in ms}
    past = _past(state)
    score = {}
    for a, b in itertools.combinations(ms, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key in past:
            continue
        e = eligibility(a, b)
        if e['status'] != 'needs_clarification':
            continue
        need = {x.split(':')[0] for x in e['missing']}
        if any(unresolvable(byid[i]) for i in need):
            continue  # a declined field makes this pair permanently blocked
        v = 1.0 + 0.1 * sim_score(a, b)
        for i in need:
            score[i] = score.get(i, 0.0) + v / len(need)
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))
    asks = []
    for i, _ in ranked:
        if budget < 3:
            break
        asks.append({'member_id': i, 'field': 'constraints'})
        budget -= 3
    return asks, budget

def soft_asks(state, budget, fields=('relationship_goal', 'relationship_pace', 'lifestyle', 'conversations')):
    """Spend leftover budget (1 unit each) on unknown soft fields of members who have feasible partners."""
    asks = []
    deg = {}
    for a, b, _ in feasible_edges(state):
        deg[a['member_id']] = deg.get(a['member_id'], 0) + 1
        deg[b['member_id']] = deg.get(b['member_id'], 0) + 1
    byid = {m['member_id']: m for m in state['members']}
    for i, _ in sorted(deg.items(), key=lambda kv: (-kv[1], kv[0])):
        for f in fields:
            if budget < 1:
                return asks
            m = byid[i]
            if m['fields'][f] is None and m['field_status'][f] == 'not_asked':
                asks.append({'member_id': i, 'field': f})
                budget -= 1
    return asks

def global_match(state):
    """Max-weight matching on the feasible graph (same similarity score as the greedy baseline)."""
    G = nx.Graph()
    for a, b, _ in feasible_edges(state):
        G.add_edge(a['member_id'], b['member_id'], weight=1 + sim_score(a, b))
    M = nx.max_weight_matching(G, maxcardinality=False)
    return sorted([sorted(p) for p in M])

ARMS = {
    'A_baseline':        (lambda s: baseline_asks(s),                       baseline_match),
    'N_no_asks':         (lambda s: [],                                     baseline_match),
    'B_global_only':     (lambda s: baseline_asks(s),                       global_match),
    'C_targeted_only':   (lambda s: targeted_hard_asks(s)[0],               baseline_match),
    'D_targeted_global': (lambda s: targeted_hard_asks(s)[0],               global_match),
    'E_full':            (lambda s: (lambda r: r[0] + soft_asks(s, r[1]))(targeted_hard_asks(s)), global_match),
}
