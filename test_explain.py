import unittest
from kit import Simulator, generate
import policy
from explain import explain_request

class ExplainTests(unittest.TestCase):
    def test_trace_never_changes_a_decision(self):
        for variant in ('development', 'sparse', 'cold_start'):
            sim = Simulator(generate(905, 200, 'evaluation', variant))
            for _ in range(20):
                s = sim.observe()
                req = {'schema_version': '1.0.0', 'phase': 'ask', 'state': s, 'memory': {}}
                resp, trace = explain_request(req)
                self.assertEqual(resp, policy.decide(req)); self.assertEqual(len(trace['decisions']), len(resp['asks']))
                sim.resolve_asks(resp['asks']); s = sim.observe()
                req = {'schema_version': '1.0.0', 'phase': 'match', 'state': s, 'memory': {}}
                resp, trace = explain_request(req)
                self.assertEqual(resp, policy.decide(req)); self.assertEqual(len(trace['decisions']), len(resp['pairs']))
                for d in trace['decisions']: self.assertEqual(d['status'], 'feasible')
                sim.advance(resp['pairs'])
if __name__ == '__main__':
    unittest.main()
