"""Scale test: the policy must stay valid, under 10 s per call and under 1 MiB per
request/response on populations larger than the public 200 members.
Run: python test_scale.py [n_members ...]   (default 200 400 800)"""
import json, subprocess, sys, time
from kit import Simulator, generate

def call(req):
    t = time.time()
    p = subprocess.run([sys.executable, 'policy.py'], input=json.dumps(req), capture_output=True, text=True, timeout=10)
    return json.loads(p.stdout), time.time() - t, len(json.dumps(req)), len(p.stdout)

def run(n, days=20):
    sim = Simulator(generate(4242, n, 'evaluation', 'development'))
    mem, worst, req_max, resp_max = {}, 0, 0, 0
    for _ in range(days):
        s = sim.observe()
        r, t, a, b = call({'phase': 'ask', 'state': s, 'memory': mem})
        worst, req_max, resp_max = max(worst, t), max(req_max, a), max(resp_max, b)
        mem = r.get('memory', mem); sim.resolve_asks(r['asks']); s = sim.observe()
        r, t, a, b = call({'phase': 'match', 'state': s, 'memory': mem})
        worst, req_max, resp_max = max(worst, t), max(req_max, a), max(resp_max, b)
        mem = r.get('memory', mem); sim.advance(r['pairs'])
    return worst, req_max, resp_max, len(json.dumps(mem))

if __name__ == '__main__':
    for n in map(int, sys.argv[1:] or [200, 400, 800]):
        w, a, b, m = run(n)
        print(f'n={n}: worst call {w:.2f}s, max request {a/1024:.0f} KiB, max response {b/1024:.1f} KiB, memory {m} B', flush=True)
        assert w < 10 and a < 2**20 and b < 2**20
