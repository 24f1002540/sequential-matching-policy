import json, collections, statistics as st
d=[json.loads(l) for l in open('results/diag_supply.jsonl')]
o={(r['seed'],r['variant']):r for r in map(json.loads,open('results/oracle_supply.jsonl'))}
fam=collections.defaultdict(list)
for r in d: fam[r['variant']].append(r)
NAMES={'development':'standard','sparse':'sparse geography','cold_start':'cold start','delayed':'delayed dates','shift':'shifted weights','drift':'changing conditions'}
print('| Scenario family | Pairs feasible at some point | Introduced (share) | Offline supply bound (all non-declined constraints known) | Feasible pairs available per day | Member-days idle with an available option |')
print('|---|---|---|---|---|---|')
def row(name, rs):
    ef=st.mean(r['ever_feasible'] for r in rs); it=st.mean(r['introduced'] for r in rs); orc=st.mean(o[(r['seed'],r['variant'])]['oracle_feasible_pairs'] for r in rs)
    idle=sum(r['member_days_idle_with_option'] for r in rs)/sum(r['member_days_available'] for r in rs)
    print('| %s | %.1f | %.1f (%.0f%%) | %.1f (reached %.0f%%) | %.2f | %.2f%% |'%(name,ef,it,100*it/ef,orc,100*ef/orc,st.mean(r['mean_feasible_edges_per_day'] for r in rs),100*idle))
for v in NAMES: row(NAMES[v], fam[v])
row('**All 24 episodes**', d)
