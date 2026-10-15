import json, sys, time, math
from kit import Simulator, generate, baseline_match
import policy as official
from smp_core import Model, asks_policy, match_policy, targeted_hard_asks
MODEL = Model('model_v1.json')
def off(mode):
    return (lambda s: official.decide({'phase': 'ask', 'state': s, 'memory': None}, mode)['asks'],
            lambda s: official.decide({'phase': 'match', 'state': s, 'memory': None}, mode)['pairs'])
ARMS = {
    'R_random':   off('random'),
    'N_no_asks':  off('no_asks'),
    'A_greedy':   off('greedy'),
    'C_targeted_greedy_crude': (lambda s: targeted_hard_asks(s)[0], baseline_match),
    'Fg_learned_greedy': (lambda s: asks_policy(s, MODEL), lambda s: match_policy(s, MODEL, 'greedy', False)),
    'F_learned_global':  (lambda s: asks_policy(s, MODEL), lambda s: match_policy(s, MODEL, 'global', False)),
    'G_learned_global_adaptive': (lambda s: asks_policy(s, MODEL), lambda s: match_policy(s, MODEL, 'global', True)),
}
def run(arm, seed, variant):
    ask_fn, match_fn = ARMS[arm]; sim = Simulator(generate(seed, 200, 'evaluation', variant)); t_call = 0.0; max_req = 0
    for _ in range(60):
        s = sim.observe(); max_req = max(max_req, len(json.dumps(s))); t = time.perf_counter(); asks = ask_fn(s); t_call = max(t_call, time.perf_counter() - t)
        sim.resolve_asks(asks); s = sim.observe(); t = time.perf_counter(); pairs = match_fn(s); t_call = max(t_call, time.perf_counter() - t); sim.advance(pairs)
    arrived = {m['member_id']: m['arrived_day'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40): sim.advance([])
    r = sim.metrics(); first = {}
    for it in sim.introductions:
        for m in (it['user_a'], it['user_b']): first.setdefault(m, it['assigned_day'])
    waits = sorted(first[i] - arrived[i] for i in first if i in arrived); N = len(arrived)
    r.update(arm=arm, seed=seed, variant=variant, arrived_members=N, msmi_per_100_arrived_members=100 * r['mutual_second_meeting_intention'] / max(1, N),
             served=len([i for i in first if i in arrived]), unserved=N - len([i for i in first if i in arrived]), coverage=len([i for i in first if i in arrived]) / max(1, N),
             mutual_acceptances_per_100=100 * r['mutual_acceptances'] / max(1, N), median_first_wait=waits[len(waits) // 2] if waits else None,
             max_call_seconds=round(t_call, 3), max_request_bytes=max_req)
    return r
if __name__ == '__main__':
    out = sys.argv[1]; seeds = [int(s) for s in sys.argv[2].split(',')]; variants = sys.argv[3].split(','); arms = sys.argv[4].split(',') if len(sys.argv) > 4 else list(ARMS)
    import os
    done = set()
    if os.path.exists(out):
        for l in open(out):
            x = json.loads(l); done.add((x['seed'], x['variant'], x['arm']))
    for s in seeds:
        for v in variants:
            for a in arms:
                if (s, v, a) in done: continue
                t = time.time(); r = run(a, s, v); r['secs'] = round(time.time() - t, 1)
                open(out, 'a').write(json.dumps(r) + '\n')
                print(s, v, a, r['assignments'], r['mutual_acceptances'], r['dates'], r['mutual_second_meeting_intention'], r['ask_cost'], r['max_call_seconds'], r['secs'], flush=True)
