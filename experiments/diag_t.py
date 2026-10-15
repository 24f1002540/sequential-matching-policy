from kit import Simulator, generate, baseline_match
from smp_core import targeted_hard_asks
from t_arm import completion_asks
diff=days=0
for v in ('development','cold_start'):
    for seed in (201,):
        sim=Simulator(generate(seed,200,'evaluation',v))
        for d in range(60):
            s=sim.observe(); a=targeted_hard_asks(s)[0]; b=completion_asks(s); days+=1
            if {x['member_id'] for x in a}!={x['member_id'] for x in b}: diff+=1
            sim.resolve_asks(a); s=sim.observe(); sim.advance(baseline_match(s))
print('days',days,'days where chosen member sets differ',diff)
