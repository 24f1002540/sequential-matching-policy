import glob, json, collections, math, statistics as st
FAM=['development','sparse','cold_start','delayed','shift','drift']
rows=[json.loads(l) for f in sorted(glob.glob('results/exp_[01].jsonl')) for l in open(f)]
by=collections.defaultdict(dict)
for r in rows: by[(r['seed'],r['variant'])][r['arm']]=r
ARMS=['A_greedy','C_targeted_greedy_crude','Fg_learned_greedy','S_scarcity','O_oracle_global']
LAB={'A_greedy':'A  baseline asks + supplied greedy','C_targeted_greedy_crude':'C  targeted asks + supplied greedy (incumbent)','Fg_learned_greedy':'Fg learned values + soft asks, greedy','S_scarcity':'S  targeted asks + scarcity-weighted matching','O_oracle_global':'O  ORACLE ranking (offline bound)'}
seeds=sorted(s for s in {k[0] for k in by} if all(all(a in by.get((s,v),{}) for a in ARMS) for v in FAM))
T={5:2.571}
def ps(arm,key,fams=FAM): return {s: st.mean(by[(s,v)][arm][key] for v in fams) for s in seeds}
print('\n**Offline expected-outcome measure, seeds 106–111 (36 episodes per policy)**\n')
print('| Policy | Expected MSMI per episode | Expected mutual acc. per episode | Introductions per episode | Realized MSMI events (expected) | Realized mutual acc. (expected) |')
print('|---|---|---|---|---|---|')
for a in ARMS:
    R=[by[(s,v)][a] for s in seeds for v in FAM]
    print('| %s | %.3f | %.2f | %.1f | %d (%.1f) | %d (%.1f) |'%(LAB[a],st.mean(r['expected_msmi'] for r in R),st.mean(r['expected_mutual'] for r in R),st.mean(r['assignments'] for r in R),sum(r['mutual_second_meeting_intention'] for r in R),sum(r['expected_msmi'] for r in R),sum(r['mutual_acceptances'] for r in R),sum(r['expected_mutual'] for r in R)))
print('\n| Contrast | Expected MSMI per episode (relative change) | Expected mutual acc. per episode | Introductions per episode |')
print('|---|---|---|---|')
def cell(a,b,key,rel=True):
    pa,pb=ps(a,key),ps(b,key); d=[pa[s]-pb[s] for s in seeds]; m=st.mean(d); se=st.stdev(d)/math.sqrt(len(d)); lo,hi=m-2.571*se,m+2.571*se; base=st.mean(pb.values())
    nd=3 if key=='expected_msmi' else 2
    s=('%+.'+str(nd)+'f [%+.'+str(nd)+'f, %+.'+str(nd)+'f]')%(m,lo,hi)
    return s+(' (%+.1f%%, [%+.1f%%, %+.1f%%])'%(100*m/base,100*lo/base,100*hi/base) if rel else '')
for lab,a,b in [('E1  C − A  (targeted vs baseline asks)','C_targeted_greedy_crude','A_greedy'),('E2  Fg − C  (learned values + soft asks)','Fg_learned_greedy','C_targeted_greedy_crude'),('E3  S − C  (scarcity-weighted matching)','S_scarcity','C_targeted_greedy_crude'),('E4  O − C  (oracle ranking, bound)','O_oracle_global','C_targeted_greedy_crude')]:
    print('| %s | %s | %s | %s |'%(lab,cell(a,b,'expected_msmi'),cell(a,b,'expected_mutual',False),cell(a,b,'assignments',False)))
