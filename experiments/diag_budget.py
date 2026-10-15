import sys, itertools
from kit import Simulator, generate, eligibility
from smp_core import past_pairs, unresolvable
from kit import baseline_match
def cand_scores(state):
    ms=[m for m in state['members'] if m['available']]; byid={m['member_id']:m for m in ms}; past=past_pairs(state); sc={}
    for a,b in itertools.combinations(ms,2):
        if tuple(sorted((a['member_id'],b['member_id']))) in past: continue
        e=eligibility(a,b)
        if e['status']!='needs_clarification': continue
        need={x.split(':')[0] for x in e['missing']}
        if any(unresolvable(byid[i]) for i in need): continue
        for i in need: sc[i]=sc.get(i,0)+1.0/len(need)
    return sc
tot_days=bind=0; unasked=0; asked=0
for v in ('development','cold_start','delayed'):
    for seed in (201,202):
        sim=Simulator(generate(seed,200,'evaluation',v))
        for d in range(60):
            s=sim.observe(); sc=cand_scores(s); n=len(sc); cap=s['ask_budget_remaining']//3
            ranked=sorted(sc.items(),key=lambda kv:(-kv[1],kv[0])); asks=[{'member_id':i,'field':'constraints'} for i,_ in ranked[:cap]]
            tot_days+=1; asked+=len(asks)
            if n>cap: bind+=1; unasked+=n-cap
            sim.resolve_asks(asks); s=sim.observe(); sim.advance(baseline_match(s))
print('days',tot_days,'days with more askable members than budget',bind,'members left unasked on those days',unasked,'asked total',asked)
