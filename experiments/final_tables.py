import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))  # paths below are relative to experiments/
import glob, json, collections, random, statistics as st
FAM=['development','sparse','cold_start','delayed','shift','drift']
EXPL='results/eval2_results.jsonl'
def load(fs): return [json.loads(l) for f in fs for l in open(f)]
ex=load([EXPL]); co=load(sorted(glob.glob('results/conf_[01].jsonl')+glob.glob('results/conf2_[01].jsonl')+glob.glob('results/oracle_[01].jsonl')+glob.glob('results/s_[01].jsonl')))
def idx(rows):
    b=collections.defaultdict(dict)
    for r in rows: b[(r['seed'],r['variant'])][r['arm']]=r
    return b
EX,CO,ALL=idx(ex),idx(co),idx(ex+co)
LAB={'R_random':'R  random-feasible (supplied)','N_no_asks':'N  no clarification (supplied)','A_greedy':'A  baseline asks + supplied greedy (supplied)','C_targeted_greedy_crude':'C  targeted asks + supplied greedy (incumbent)','Fg_learned_greedy':'Fg learned values + soft asks, greedy','F_learned_global':'F  learned values + soft asks, global','G_learned_global_adaptive':'G  F + online adaptation','S_scarcity':'S  targeted asks + scarcity-weighted matching','O_oracle_global':'O  oracle ranking (offline bound, not a policy)'}
def seeds(b,arms): return sorted(s for s in {k[0] for k in b} if all(all(a in b.get((s,v),{}) for a in arms) for v in FAM))
def ps(b,a,k,S): return {s: st.mean(b[(s,v)][a][k] for v in FAM) for s in S}
def boot(x,n=10000,rng=random.Random(21)):
    bs=sorted(st.mean(rng.choices(x,k=len(x))) for _ in range(n)); return bs[int(.025*n)],bs[int(.975*n)-1]
def summary(b,arms,full=True):
    print('| Policy | Primary score (MSMI/100) | Coverage | Mutual acc. /100 | Ask cost | Introductions | Mutual acc. | Dates | MSMI events | Zero-MSMI episodes |'); print('|---|---|---|---|---|---|---|---|---|---|')
    for a in arms:
        S=seeds(b,[a]); g=lambda k: st.mean(ps(b,a,k,S).values()); R=[b[(s,v)][a] for s in S for v in FAM]
        print('| %s | %.3f | %.3f | %.2f | %.0f | %.1f | %.1f | %.1f | %d | %d / %d |'%(LAB[a],g('msmi_per_100_arrived_members'),g('coverage'),g('mutual_acceptances_per_100'),g('ask_cost'),g('assignments'),g('mutual_acceptances'),g('dates'),sum(r['mutual_second_meeting_intention'] for r in R),sum(r['mutual_second_meeting_intention']==0 for r in R),len(R)))
def cell(b,a,c,k,nd):
    S=seeds(b,[a,c]); pa,pc=ps(b,a,k,S),ps(b,c,k,S); d=[pa[s]-pc[s] for s in S]; lo,hi=boot(d)
    return ('%+.'+str(nd)+'f [%+.'+str(nd)+'f, %+.'+str(nd)+'f]')%(st.mean(d),lo,hi)
def contrasts(b,rows):
    print('| Contrast (first minus second) | Test | Mutual acceptances per episode | MSMI events per episode | Primary score (MSMI/100) | Seeds |'); print('|---|---|---|---|---|---|')
    for lab,a,c,t in rows:
        S=seeds(b,[a,c]); print('| %s | %s | %s | %s | %s | %d |'%(lab,t,cell(b,a,c,'mutual_acceptances',2),cell(b,a,c,'mutual_second_meeting_intention',2),cell(b,a,c,'msmi_per_100_arrived_members',3),len(S)))
C,A='C_targeted_greedy_crude','A_greedy'
print('### T1 confirmatory summary'); summary(CO,[A,C,'Fg_learned_greedy','F_learned_global','G_learned_global_adaptive','S_scarcity','O_oracle_global'])
print('\n### T2 exploratory summary'); summary(EX,['R_random','N_no_asks',A,C,'Fg_learned_greedy','F_learned_global','G_learned_global_adaptive'])
print('\n### T3 confirmatory contrasts')
contrasts(CO,[('C − A  targeted vs baseline asks',C,A,'K1, K2'),('Fg − C  learned values + soft asks vs incumbent','Fg_learned_greedy',C,'K3'),('F − Fg  global vs greedy, same learned values','F_learned_global','Fg_learned_greedy','K5'),('G − F  adaptive vs frozen','G_learned_global_adaptive','F_learned_global','K6'),('S − C  scarcity-weighted matching vs incumbent',  'S_scarcity',C,'K10, K11'),('O − C  oracle ranking vs incumbent (bound)','O_oracle_global',C,'K9')])
print('\n### T4 exploratory-only and pooled')
contrasts(EX,[('N − A  no clarification vs baseline asks','N_no_asks',A,'K7'),('A − R  baseline ranking vs random-feasible',A,'R_random','K8'),('C − A  targeted vs baseline asks (exploratory)',C,A,'K1, K2')])
print('| C − A pooled over seeds 101–125 | K1, K2 | %s | %s | %s | %d |'%(cell(ALL,C,A,'mutual_acceptances',2),cell(ALL,C,A,'mutual_second_meeting_intention',2),cell(ALL,C,A,'msmi_per_100_arrived_members',3),len(seeds(ALL,[C,A]))))
S=seeds(CO,[C,A]); d=[st.mean(CO[(s,v)][C]['ask_cost']-CO[(s,v)][A]['ask_cost'] for v in FAM) for s in S]; lo,hi=boot(d)
print('\nK4 ask cost C-A: %+.2f [%+.2f,%+.2f] units/episode; seeds C cheaper %d/%d'%(st.mean(d),lo,hi,sum(x<0 for x in d),len(d)))
S=seeds(CO,[C,'S_scarcity'])
for k in ['assignments','coverage']:
    d=[st.mean(CO[(s,v)]['S_scarcity'][k]-CO[(s,v)][C][k] for v in FAM) for s in S]; lo,hi=boot(d); print('K10 S-C %s: %+.3f [%+.3f,%+.3f] seeds up %d/%d'%(k,st.mean(d),lo,hi,sum(x>0 for x in d),len(d)))
