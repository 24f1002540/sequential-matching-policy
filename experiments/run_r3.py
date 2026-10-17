"""R3 confirmation: arms A (supplied baseline asks) and C (submitted targeted asks), in-process replica of evaluate.episode.
Usage (from repo root): python experiments/run_r3.py OUT.jsonl SEED_FROM SEED_TO"""
import hashlib, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kit import Simulator, generate, VERSION
import policy

def episode(world, mode):
    sim, memory, dg = Simulator(world), None, hashlib.sha256()
    for _ in range(60):
        for phase in ('ask', 'match'):
            req = json.loads(json.dumps({'schema_version': VERSION, 'phase': phase, 'state': sim.observe(), 'memory': memory}))
            out = policy.decide(req, mode); memory = out['memory']
            act = out['asks' if phase == 'ask' else 'pairs']
            dg.update(json.dumps([phase, sim.day, act], sort_keys=True).encode())
            sim.resolve_asks(act) if phase == 'ask' else sim.advance(act)
    arrived = {m['member_id'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    r = sim.metrics()
    r.update(msmi_per_100_arrived_members=100 * r['mutual_second_meeting_intention'] / max(1, len(arrived)), action_sha256=dg.hexdigest())
    return r

out, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
FAM = ['development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift']
with open(out, 'a') as f:
    for seed in range(lo, hi + 1):
        for fam in FAM:
            w = generate(seed, 200, 'evaluation', fam)
            for arm, mode in (('A_greedy', 'greedy'), ('C_submitted', 'submission')):
                r = episode(w, mode); r.update(seed=seed, variant=fam, arm=arm)
                f.write(json.dumps(r) + '\n'); f.flush()
