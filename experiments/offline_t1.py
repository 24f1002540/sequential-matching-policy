"""Offline analysis of the static day-30 snapshots (Round 1 research).
Target T1: directional 'recorded Yes by the response deadline'.
Leakage control: member fields count as known only if field_observed_day <= assigned_day.
Right-censoring: introductions whose response event is not yet observable at day 30 are excluded.
Split: official manifest pools (train 01-06, validation 07-08, development-test 09-10)."""
import json, numpy as np, collections
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from kit import SOFT

man = json.load(open('data_manifest.json'))['splits']
def load(pool):
    return json.load(open(f'data/{pool}/state.json'))

def known(m, k, day):
    v = m['fields'].get(k); d = m['field_observed_day'].get(k)
    return v if (v is not None and d is not None and d <= day) else None

def feats(actor, partner, day):
    x = []
    for k in SOFT:
        a, b = known(actor, k, day), known(partner, k, day)
        x += [1.0 if (a is not None and b is not None and a == b) else 0.0,
              1.0 if (a is not None and b is not None and a != b) else 0.0]
    return x

def rows(pools):
    X, y, g, meta = [], [], [], collections.Counter()
    for p in pools:
        st = load(p); mem = {m['member_id']: m for m in st['members']}
        ev = collections.defaultdict(dict)
        for e in st['feedback']:
            if e['event'] == 'introduction_response': ev[e['introduction_id']][e['member_id']] = e
        for it in st['introductions']:
            for actor_id, partner_id in ((it['user_a'], it['user_b']), (it['user_b'], it['user_a'])):
                e = ev[it['introduction_id']].get(actor_id)
                if e is None:                 # response not yet observable at day 30 -> censored, excluded
                    meta['censored_excluded'] += 1; continue
                lab = 1 if e['value'] == 'yes' else 0   # no response => 'Yes did not occur' (not dislike)
                X.append(feats(mem[actor_id], mem[partner_id], it['assigned_day'])); y.append(lab); g.append(p)
                meta['rows'] += 1; meta['yes'] += lab; meta['no_response'] += (e['value'] is None)
    return np.array(X), np.array(y), np.array(g), meta

res = {}
Xtr, ytr, gtr, mtr = rows(man['train']); Xva, yva, _, mva = rows(man['validation']); Xte, yte, _, mte = rows(man['development_test'])
print('rows  train/val/test:', len(ytr), len(yva), len(yte))
print('Yes-rate train/val/test: %.3f %.3f %.3f' % (ytr.mean(), yva.mean(), yte.mean()))
print('censored excluded (train/val/test):', mtr['censored_excluded'], mva['censored_excluded'], mte['censored_excluded'])
print('share of rows with any known soft agreement info (train):', round((Xtr.sum(1) > 0).mean(), 3))
print('mean #agree / #disagree per row (train): %.2f / %.2f' % (Xtr[:, 0::2].sum(1).mean(), Xtr[:, 1::2].sum(1).mean()))

def report(name, p, y, base):
    out = {'auc': roc_auc_score(y, p), 'brier': brier_score_loss(y, p), 'brier_base': brier_score_loss(y, np.full_like(p, base)),
           'logloss': log_loss(y, np.clip(p, 1e-6, 1-1e-6)), 'logloss_base': log_loss(y, np.full_like(p, base))}
    print(name, {k: round(v, 4) for k, v in out.items()}); return out

best = None
for C in [0.01, 0.03, 0.1, 0.3, 1, 3]:
    m = LogisticRegression(C=C, max_iter=2000).fit(Xtr, ytr)
    pv = m.predict_proba(Xva)[:, 1]
    ll = log_loss(yva, pv)
    print('C=%-5s val logloss %.4f auc %.3f' % (C, ll, roc_auc_score(yva, pv)))
    if best is None or ll < best[0]: best = (ll, C, m)
_, C, m = best
print('chosen C =', C, '(by validation log-loss only; test pools untouched until now)')
base = ytr.mean()
res['validation'] = report('VALIDATION', m.predict_proba(Xva)[:, 1], yva, base)
res['dev_test'] = report('DEV-TEST  ', m.predict_proba(Xte)[:, 1], yte, base)
# reliability on dev-test
p = m.predict_proba(Xte)[:, 1]
edges = np.quantile(p, [0, .25, .5, .75, 1.0]); idx = np.digitize(p, edges[1:-1])
print('reliability (dev-test, quartiles of predicted):')
for q in range(4):
    s = idx == q; print('  q%d n=%d mean_pred=%.3f observed=%.3f' % (q+1, s.sum(), p[s].mean(), yte[s].mean()))
names = [f'{k}:{t}' for k in SOFT for t in ('agree', 'disagree')]
print('coefficients (log-odds):')
for n, c in sorted(zip(names, m.coef_[0]), key=lambda t: -abs(t[1]))[:8]: print('  %-34s %+.3f' % (n, c))
json.dump({k: {a: float(b) for a, b in v.items()} for k, v in res.items()} | {'C': C, 'n_train': int(len(ytr)), 'n_val': int(len(yva)), 'n_test': int(len(yte))},
          open('results/offline_t1.json', 'w'), indent=1)
