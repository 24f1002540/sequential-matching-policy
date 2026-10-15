"""Offline T1 analysis, v2: feature selection on TRAIN pools only (|z|>=2 on agree-vs-disagree yes-rate gap),
then fit, tune C on VALIDATION pools, report once on DEV-TEST pools. Leakage control as in v1."""
import json, numpy as np, collections
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from kit import SOFT
man = json.load(open('data_manifest.json'))['splits']

def known(m, k, day):
    v = m['fields'].get(k); d = m['field_observed_day'].get(k)
    return v if (v is not None and d is not None and d <= day) else None
def raw_rows(pools):
    out = []
    for p in pools:
        st = json.load(open(f'data/{p}/state.json')); mem = {m['member_id']: m for m in st['members']}
        ev = {(e['introduction_id'], e['member_id']): e for e in st['feedback'] if e['event'] == 'introduction_response'}
        for it in st['introductions']:
            for a, b in ((it['user_a'], it['user_b']), (it['user_b'], it['user_a'])):
                e = ev.get((it['introduction_id'], a))
                if e is None: continue
                st_ = {}
                for k in SOFT:
                    x, z = known(mem[a], k, it['assigned_day']), known(mem[b], k, it['assigned_day'])
                    st_[k] = None if (x is None or z is None) else int(x == z)
                out.append((st_, int(e['value'] == 'yes')))
    return out
tr, va, te = raw_rows(man['train']), raw_rows(man['validation']), raw_rows(man['development_test'])
# --- feature selection on TRAIN only
sel = []
print('TRAIN-only screening (agree vs disagree, both fields known):')
for k in SOFT:
    a = [y for s, y in tr if s[k] == 1]; d = [y for s, y in tr if s[k] == 0]
    ra, rd = np.mean(a), np.mean(d); se = np.sqrt(ra*(1-ra)/len(a) + rd*(1-rd)/len(d)); z = (ra-rd)/se
    print('  %-24s n=%3d/%3d gap %+.3f z=%+.2f' % (k, len(a), len(d), ra-rd, z))
    if abs(z) >= 2: sel.append(k)
print('selected on train:', sel)
def X(rows):
    cols = []
    for k in sel: cols += [[1.0 if s[k] == 1 else 0.0 for s, _ in rows], [1.0 if s[k] == 0 else 0.0 for s, _ in rows]]
    return np.array(cols).T, np.array([y for _, y in rows])
Xtr, ytr = X(tr); Xva, yva = X(va); Xte, yte = X(te); base = ytr.mean()
best = None
for C in [0.03, 0.1, 0.3, 1, 3, 10]:
    m = LogisticRegression(C=C, max_iter=2000).fit(Xtr, ytr); ll = log_loss(yva, m.predict_proba(Xva)[:, 1])
    print('C=%-5s val logloss %.4f' % (C, ll))
    if best is None or ll < best[0]: best = (ll, C, m)
_, C, m = best; print('chosen C =', C)
def rep(name, X_, y_):
    p = m.predict_proba(X_)[:, 1]
    print('%-9s n=%d AUC %.3f | Brier %.4f (const %.4f) | logloss %.4f (const %.4f)' % (name, len(y_), roc_auc_score(y_, p), brier_score_loss(y_, p),
          brier_score_loss(y_, np.full_like(p, base)), log_loss(y_, p), log_loss(y_, np.full_like(p, base))))
    return p
rep('VALID', Xva, yva); p = rep('DEV-TEST', Xte, yte)
# bootstrap CI for dev-test AUC & Brier improvement
rng = np.random.default_rng(1); aucs = []; dbr = []
for _ in range(3000):
    i = rng.integers(0, len(yte), len(yte))
    if len(set(yte[i])) > 1:
        aucs.append(roc_auc_score(yte[i], p[i])); dbr.append(brier_score_loss(yte[i], np.full(len(i), base)) - brier_score_loss(yte[i], p[i]))
print('DEV-TEST AUC 95%% CI [%.3f, %.3f]; Brier improvement over constant 95%% CI [%+.4f, %+.4f]' % (*np.quantile(aucs, [.025, .975]), *np.quantile(dbr, [.025, .975])))
print('Reliability (dev-test, split at median predicted):')
o = np.argsort(p); h = len(p)//2
for nm, s in (('lower half', o[:h]), ('upper half', o[h:])): print('  %s n=%d mean_pred=%.3f observed=%.3f' % (nm, len(s), p[s].mean(), yte[s].mean()))
print('coefficients:', {f'{sel[i//2]}:{"agree" if i%2==0 else "disagree"}': round(float(c), 3) for i, c in enumerate(m.coef_[0])}, 'intercept', round(float(m.intercept_[0]), 3))
