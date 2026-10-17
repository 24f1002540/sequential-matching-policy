"""Regression test: the submitted policy must reproduce the committed action digest.
Replays seed 101 (sparse family) with the same request/response loop as evaluate.episode, in process,
and compares the hash of every ask and pair chosen with results/final.json.
If this fails after an edit, the policy's behaviour changed: re-run the evaluation and update the evidence on purpose."""
import hashlib, json, unittest
from pathlib import Path
from kit import Simulator, generate, VERSION
import policy

ROOT = Path(__file__).resolve().parent

class Regression(unittest.TestCase):
    def test_committed_action_digest(self):
        committed = {(e['seed'], e['variant']): e for e in json.load(open(ROOT / 'results' / 'final.json'))['episodes']}
        want = committed[(101, 'sparse')]['action_sha256']
        sim, memory, digest = Simulator(generate(101, 200, 'evaluation', 'sparse')), None, hashlib.sha256()
        for _ in range(60):
            for phase in ('ask', 'match'):
                request = json.loads(json.dumps({'schema_version': VERSION, 'phase': phase, 'state': sim.observe(), 'memory': memory}))
                response = policy.decide(request)
                memory = response['memory']
                action = response['asks' if phase == 'ask' else 'pairs']
                digest.update(json.dumps([phase, sim.day, action], sort_keys=True).encode())
                sim.resolve_asks(action) if phase == 'ask' else sim.advance(action)
        self.assertEqual(digest.hexdigest(), want)

if __name__ == '__main__':
    unittest.main()
