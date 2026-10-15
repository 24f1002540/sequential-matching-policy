"""Train the stage models from SIMULATOR ROLLOUTS (declared training assets).
Logging policy: targeted hard asks + generic-order soft asks + RANDOM feasible matching (uniform among feasible pairs).
Pre-action observations only: features are taken from the state the policy saw before advance().
Training seeds 1000-1007 and validation seeds 2000-2002; evaluation seeds 101+ never used here.
The 'shift' family is deliberately excluded so adaptation can be tested on a world the model never saw."""
import json, random, sys, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from kit import Simulator, generate, SOFT
from smp_core import pair_feats, feasible_edges, targeted_hard_asks, past_pairs

VARS = ['development', 'sparse', 'cold_start', 'delayed', 'drift']

def generic_soft_asks(state, budget, fields=('relationship_goal', 'relationship_pace', 'lifestyle', 'conversations')):
    deg = {}
    for a, b, _ in feasible_edges(state):
        for i in (a['member_id'], b['member_id']): deg[i] = deg.get(i, 0) + 1
    byid = {m['member_id']: m for m in state['members']}; out = []
    for i, _ in sorted(deg.items(), key=lambda kv: (-kv[1], kv[0])):
        for f in fields:
            if budget < 1: return out
            m = byid[i]
            if m['fields'][f] is None and m['field_status'][f] == 'not_asked': out.append({'member_id': i, 'field': f}); budget -= 1
    return out

def rollout(seed, variant):
    sim = Simulator(generate(seed, 200, 'evaluation', variant)); log = []
    for day in range(60):
        st = sim.observe(); hard, left = targeted_hard_asks(st)
        sim.resolve_asks(hard + generic_soft_asks(st, left))
        st = sim.observe(); M = {m['member_id']: m for m in st['members']}
        edges = [(a['member_id'], b['member_id']) for a, b, _ in feasible_edges(st)]
        random.Random(seed * 1000 + day).shuffle(edges); used, pairs = set(), []
        for a, b in edges:
            if a not in used and b not in used: pairs.append(sorted([a, b])); used.update((a, b))
        for a, b in pairs: log.append({'a': a, 'b': b, 'day': day, 'f': pair_feats(M[a], M[b])})
        sim.advance(pairs)
    for _ in range(40): sim.advance([])
    idmap = {(i['user_a'], i['user_b'], i['assigned_day']): i['introduction_id'] for i in sim.introductions}
    ev = {}
    for e in sim.events: ev.setdefault(e['introduction_id'], []).append(e)
    rows = []
    for r in log:
        iid = idmap[(min(r['a'], r['b']), max(r['a'], r['b']), r['day'])]; es = ev.get(iid, [])
        resp = {e['member_id']: e for e in es if e['event'] == 'introduction_response'}
        yes = [1 if resp[m]['value'] == 'yes' else 0 for m in (r['a'], r['b'])]
        date = [e for e in es if e['event'] == 'date_happened' and e['value'] is True]
        dated = bool(date) and date[0]['occurred_day'] - r['day'] <= 30
        sec = [e for e in es if e['event'] == 'second_meeting_intention']
        both2 = dated and len(sec) == 2 and all(e['value'] == 'yes' and e['occurred_day'] - date[0]['occurred_day'] <= 3 for e in sec)
        rows.append({'f': r['f'], 'yes': yes, 'mutual': int(all(yes)), 'dated': int(dated), 'both2': int(both2), 'variant': variant, 'seed': seed})
    return rows

def collect(seeds):
    rows = []
    for s in seeds:
        for v in VARS: rows += rollout(s, v); print('rolled', s, v, len(rows), flush=True)
    return rows

if __name__ == '__main__':
    tr = collect(range(1000, 1008)); va = collect(range(2000, 2003))
    json.dump({'train': tr, 'val': va}, open('results/train_rollouts.json', 'w'))
    def d1(rows): return np.array([r['f'] for r in rows for _ in (0, 1)]), np.array([y for r in rows for y in r['yes']])
    Xtr, ytr = d1(tr); Xva, yva = d1(va)
    best = None
    for C in [0.03, 0.1, 0.3, 1, 3]:
        m = LogisticRegression(C=C, max_iter=3000).fit(Xtr, ytr); p = m.predict_proba(Xva)[:, 1]
        ll = -np.mean(yva * np.log(p) + (1 - yva) * np.log(1 - p)); print('M1 C=%s val logloss %.4f' % (C, ll))
        if best is None or ll < best[0]: best = (ll, C, m)
    _, C1, m1 = best; p1 = m1.predict_proba(Xva)[:, 1]
    print('M1 chosen C=%s | VAL AUC %.3f Brier %.4f (const %.4f)' % (C1, roc_auc_score(yva, p1), brier_score_loss(yva, p1), brier_score_loss(yva, np.full_like(p1, ytr.mean()))))
    ptr = m1.predict_proba(Xtr[::2])[:, 1]; mut_tr = np.array([r['mutual'] for r in tr])
    kappa = float(mut_tr.mean() / np.mean(ptr ** 2))
    pva = m1.predict_proba(Xva[::2])[:, 1]; mut_va = np.array([r['mutual'] for r in va])
    print('kappa=%.3f | VAL mutual: predicted mean %.4f observed %.4f' % (kappa, np.mean(np.minimum(1, kappa * pva ** 2)), mut_va.mean()))
    dtr = [r for r in tr if r['mutual']]; p_date = float(np.mean([r['dated'] for r in dtr])); print('P(date within 30d | mutual) = %.3f (n=%d)' % (p_date, len(dtr)))
    d4tr = [r for r in tr if r['dated']]; d4va = [r for r in va if r['dated']]
    X4, y4 = np.array([r['f'] for r in d4tr]), np.array([r['both2'] for r in d4tr]); X4v, y4v = np.array([r['f'] for r in d4va]), np.array([r['both2'] for r in d4va])
    best4 = None
    for C in [0.03, 0.1, 0.3, 1]:
        m = LogisticRegression(C=C, max_iter=3000).fit(X4, y4); p = m.predict_proba(X4v)[:, 1]
        ll = -np.mean(y4v * np.log(p) + (1 - y4v) * np.log(1 - p)); print('M4 C=%s val logloss %.4f' % (C, ll))
        if best4 is None or ll < best4[0]: best4 = (ll, C, m)
    _, C4, m4 = best4; p4 = m4.predict_proba(X4v)[:, 1]
    print('M4 chosen C=%s n_train=%d n_val=%d | VAL AUC %.3f Brier %.4f (const %.4f)' % (C4, len(y4), len(y4v), roc_auc_score(y4v, p4) if len(set(y4v)) > 1 else float('nan'), brier_score_loss(y4v, p4), brier_score_loss(y4v, np.full_like(p4, y4.mean()))))
    json.dump({'w1': list(map(float, m1.coef_[0])) + [float(m1.intercept_[0])], 'w4': list(map(float, m4.coef_[0])) + [float(m4.intercept_[0])],
               'p_date': p_date, 'kappa': kappa, 'C1': C1, 'C4': C4, 'train_seeds': '1000-1007', 'val_seeds': '2000-2002', 'variants': VARS,
               'n_train_intros': len(tr), 'n_train_dates': len(d4tr), 'n_train_mutual': len(dtr)}, open('model_v1.json', 'w'), indent=1)
    print('saved model_v1.json')
