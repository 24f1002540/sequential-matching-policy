import json
from pathlib import Path
import sys
import tempfile
import unittest
from evaluate import docker_command, invoke, summarise, validate_response
from kit import Simulator, generate
from policy import decide


class RunnerTests(unittest.TestCase):
    def test_empty_request_through_real_process(self):
        state = Simulator(generate(42, 0)).observe()
        response, _ = invoke([sys.executable, 'policy.py'], {'schema_version': '1.0.0', 'phase': 'match', 'state': state, 'memory': None})
        self.assertEqual(response, {'pairs': [], 'memory': {}})

    def test_malformed_output_rejected(self):
        for value in ({'pairs': []}, {'pairs': [['one']], 'memory': None}, {'asks': [{'member_id': 'one'}], 'memory': None}):
            with self.assertRaises(ValueError):
                validate_response(value, 'ask' if 'asks' in value else 'match')

    def test_timeout_rejected(self):
        with self.assertRaises(ValueError):
            invoke([sys.executable, '-c', 'import time; time.sleep(3)'], {'phase': 'ask'}, timeout=.1)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            invoke([sys.executable, '-c', 'print(\'{"asks": [], "memory": NaN}\')'], {'phase': 'ask'})

    def test_equal_scenario_weights(self):
        base = dict(valid=True, coverage=.2, mutual_acceptances_per_100=2, ask_cost=12, inference_seconds=1)
        rows = [dict(base, variant='a', msmi_per_100_arrived_members=2), dict(base, variant='b', msmi_per_100_arrived_members=0), dict(base, variant='b', msmi_per_100_arrived_members=0)]
        self.assertEqual(summarise(rows)['primary_score'], 1)
        rows.append({'valid': False})
        self.assertFalse(summarise(rows)['eligible'])

    def test_container_has_no_host_mount(self):
        command = docker_command('policy:test')
        self.assertIn('--network=none', command)
        self.assertIn('--read-only', command)
        self.assertNotIn('-v', command)
        self.assertNotIn('--mount', command)

    def test_observed_policy_never_receives_world_fields(self):
        sim = Simulator(generate(42, 80))
        for _ in range(20):
            state = sim.observe()
            asks = decide({'phase': 'ask', 'state': state, 'memory': None})['asks']
            sim.resolve_asks(asks)
            state = sim.observe()
            self.assertNotIn('seed', state)
            for member in state['members']:
                self.assertNotIn('truth', member)
                self.assertNotIn('response_rate', member)
            sim.advance(decide({'phase': 'match', 'state': state, 'memory': None})['pairs'])

if __name__ == '__main__':
    unittest.main()
