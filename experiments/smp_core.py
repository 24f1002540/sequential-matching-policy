"""Round-1 prototype policy core. Observable-state only: reads state['members'|'introductions'|'feedback'] and a
declared training asset (model JSON). Never touches simulator hidden fields, seeds or IDs."""
import itertools, json, math
import numpy as np
import networkx as nx
from kit import HARD, SOFT, eligibility

LAMBDA_VALUE = 0.1   # small weight on mutual acceptance in the edge value (variance-reduction; declared, not tuned)

def known(m, k, day=None):
    v = m['fields'].get(k)
    if v is None: return None
    if day is not None:
        d = m['field_observed_day'].get(k)
        if d is None or d > day: return None
    return v

def pair_feats(a, b, day=None):
    f = []
    for k in SOFT:
        x, y = known(a, k, day), known(b, k, day)
        ok = x is not None and y is not None
        f += [1.0 if ok and x == y else 0.0, 1.0 if ok and x != y else 0.0]
    return f

def sig(z): return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
def dot(w, f): return sum(wi * fi for wi, fi in zip(w, f + [1.0]))

def past_pairs(state):
    return {tuple(sorted((i['user_a'], i['user_b']))) for i in state['introductions']}

def feasible_edges(state):
    ms = [m for m in state['members'] if m['available']]
    past = past_pairs(state); out = []
    for a, b in itertools.combinations(ms, 2):
        key = tuple(sorted((a['member_id'], b['member_id'])))
        if key not in past and eligibility(a, b)['status'] == 'feasible':
            out.append((a, b, key))
    return out

def unresolvable(m):
    return any(m['field_status'][k] == 'declined' and m['fields'][k] is None for k in HARD)

def refit_w1(state, w0, lam=5.0, tau=20.0, iters=6):
    """Online adaptation of the directional-accept model: ridge toward the pre-trained prior, recency-weighted.
    Uses only matured responses already in feedback and fields visible at each assignment day."""
    day = state['day']; M = {m['member_id']: m for m in state['members']}
    resp = {(e['introduction_id'], e['member_id']): e for e in state['feedback'] if e['event'] == 'introduction_response'}
    X, y, wt = [], [], []
    for it in state['introductions']:
        for actor, partner in ((it['user_a'], it['user_b']), (it['user_b'], it['user_a'])):
            e = resp.get((it['introduction_id'], actor))
            if e is None or actor not in M or partner not in M: continue
            X.append(pair_feats(M[actor], M[partner], it['assigned_day']) + [1.0])
            y.append(1.0 if e['value'] == 'yes' else 0.0); wt.append(math.exp(-(day - it['assigned_day']) / tau))
    if len(y) < 8: return list(w0)
    X, y, wt, w0a = np.array(X), np.array(y), np.array(wt), np.array(w0); w = w0a.copy()
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        g = X.T @ (wt * (p - y)) + lam * (w - w0a)
        H = (X * (wt * p * (1 - p))[:, None]).T @ X + lam * np.eye(len(w))
        w = w - np.linalg.solve(H, g)
    return [float(v) for v in w]

class Model:
    def __init__(self, path):
        d = json.load(open(path)); self.w1, self.w4 = d['w1'], d['w4']
        self.p_date, self.kappa = d['p_date'], d['kappa']
        imp = {k: abs(self.w1[2*i] - self.w1[2*i+1]) + abs(self.w4[2*i] - self.w4[2*i+1]) for i, k in enumerate(SOFT)}
        self.importance = imp
    def edge_value(self, a, b, w1=None):
        f = pair_feats(a, b); p1 = sig(dot(w1 or self.w1, f)); pm = min(1.0, self.kappa * p1 * p1)
        p4 = sig(dot(self.w4, f)); return pm * (self.p_date * p4 + LAMBDA_VALUE)

def targeted_hard_asks(state):
    budget = state['ask_budget_remaining']; ms = [m for m in state['members'] if m['available']]
    byid = {m['member_id']: m for m in ms}; past = past_pairs(state); score = {}
    for a, b in itertools.combinations(ms, 2):
        if tuple(sorted((a['member_id'], b['member_id']))) in past: continue
        e = eligibility(a, b)
        if e['status'] != 'needs_clarification': continue
        need = {x.split(':')[0] for x in e['missing']}
        if any(unresolvable(byid[i]) for i in need): continue
        for i in need: score[i] = score.get(i, 0.0) + 1.0 / len(need)
    asks = []
    for i, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0])):
        if budget < 3: break
        asks.append({'member_id': i, 'field': 'constraints'}); budget -= 3
    return asks, budget

def voi_soft_asks(state, budget, model, top=3):
    """Ask a soft field only where the partner's answer is already known, so the answer changes an edge value;
    field priority comes from the learned importance, not from a hand-set list."""
    fields = [k for k, _ in sorted(model.importance.items(), key=lambda kv: -kv[1])][:top]
    score = {}
    for a, b, _ in feasible_edges(state):
        for k in fields:
            ka, kb = a['fields'][k], b['fields'][k]
            for x, y in ((a, b), (b, a)):
                if x['fields'][k] is None and x['field_status'][k] == 'not_asked' and y['fields'][k] is not None:
                    score[(x['member_id'], k)] = score.get((x['member_id'], k), 0.0) + model.importance[k]
    asks = []
    for (i, k), _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0])):
        if budget < 1: break
        asks.append({'member_id': i, 'field': k}); budget -= 1
    return asks

def asks_policy(state, model):
    hard, left = targeted_hard_asks(state)
    return hard + voi_soft_asks(state, left, model)

def match_policy(state, model, allocation='global', adaptive=False):
    w1 = refit_w1(state, model.w1) if adaptive else model.w1
    edges = [(model.edge_value(a, b, w1), a['member_id'], b['member_id']) for a, b, _ in feasible_edges(state)]
    if allocation == 'greedy':
        used, out = set(), []
        for v, a, b in sorted(edges, key=lambda t: (-t[0], t[1], t[2])):
            if a not in used and b not in used: out.append(sorted([a, b])); used.update((a, b))
        return sorted(out)
    G = nx.Graph()
    for v, a, b in edges: G.add_edge(a, b, weight=v + 1e-9)
    return sorted(sorted(p) for p in nx.max_weight_matching(G, maxcardinality=False))
