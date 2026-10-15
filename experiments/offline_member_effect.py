"""Do members differ in propensity to say Yes? Time-ordered, leakage-safe test on static snapshots.
For each directional response, use ONLY the same actor's earlier responses observable by the assignment day
(event observed_day <= assigned_day). Compare AUC of 'actor's shrunk past yes-rate' vs chance."""
import json, collections, numpy as np
from sklearn.metrics import roc_auc_score
man = json.load(open('data_manifest.json'))['splits']
pools = man['train'] + man['validation'] + man['development_test']
P, Y, N, PRIOR = [], [], [], 0.37
for pool in pools:
    st = json.load(open(f'data/{pool}/state.json'))
    intro = {i['introduction_id']: i for i in st['introductions']}
    resp = [e for e in st['feedback'] if e['event'] == 'introduction_response']
    by_actor = collections.defaultdict(list)
    for e in resp: by_actor[e['member_id']].append(e)
    for actor, evs in by_actor.items():
        for e in evs:
            a_day = intro[e['introduction_id']]['assigned_day']
            past = [x for x in evs if x is not e and x['observed_day'] <= a_day]
            n = len(past); yes = sum(x['value'] == 'yes' for x in past)
            if n == 0: continue
            P.append((yes + PRIOR * 2) / (n + 2)); Y.append(int(e['value'] == 'yes')); N.append(n)
P, Y = np.array(P), np.array(Y)
print('rows with >=1 earlier observable response by same member:', len(Y), ' yes-rate %.3f' % Y.mean())
if len(set(Y)) > 1: print('AUC of member past-yes-rate -> next response: %.3f' % roc_auc_score(Y, P))
rng = np.random.default_rng(0); a = []
for _ in range(2000):
    idx = rng.integers(0, len(Y), len(Y))
    if len(set(Y[idx])) > 1: a.append(roc_auc_score(Y[idx], P[idx]))
print('bootstrap 95%% CI for AUC: [%.3f, %.3f]' % tuple(np.quantile(a, [.025, .975])))
