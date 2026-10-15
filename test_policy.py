import json, subprocess, sys, unittest
import policy
from kit import Simulator, generate, eligibility

def empty_state(**kw):
    s = {'schema_version': '1.0.0', 'synthetic': True, 'day': 0, 'ask_budget_remaining': 12,
         'members': [], 'introductions': [], 'feedback': [], 'ask_log': []}
    s.update(kw); return s

class PolicyTests(unittest.TestCase):
    def run_cli(self, req):
        p = subprocess.run([sys.executable, 'policy.py'], input=json.dumps(req).encode(), capture_output=True, check=True)
        return json.loads(p.stdout)

    def test_empty_population_both_phases(self):
        for phase, key in (('ask', 'asks'), ('match', 'pairs')):
            out = self.run_cli({'schema_version': '1.0.0', 'phase': phase, 'state': empty_state(), 'memory': {}})
            self.assertEqual(out, {key: [], 'memory': {}})

    def test_actions_valid_over_a_full_episode(self):
        for variant in ('development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift'):
            sim = Simulator(generate(901, 200, 'evaluation', variant))
            for _ in range(60):
                s = sim.observe()
                asks = policy.decide({'phase': 'ask', 'state': s, 'memory': {}})['asks']
                self.assertLessEqual(sum(3 if a['field'] == 'constraints' else 1 for a in asks), s['ask_budget_remaining'])
                byid = {m['member_id']: m for m in s['members']}
                for a in asks:
                    self.assertTrue(byid[a['member_id']]['available'])
                    self.assertFalse(policy.unresolvable(byid[a['member_id']]))
                sim.resolve_asks(asks); s = sim.observe()
                pairs = policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs']
                used = set(); byid = {m['member_id']: m for m in s['members']}
                for a, b in pairs:
                    self.assertNotIn(a, used); self.assertNotIn(b, used); used.update((a, b))
                    self.assertEqual(eligibility(byid[a], byid[b])['status'], 'feasible')
                sim.advance(pairs)

    def test_never_asks_declined_member_and_never_matches_unknown(self):
        sim = Simulator(generate(902, 200, 'evaluation', 'development'))
        for _ in range(30):
            s = sim.observe()
            asks = policy.decide({'phase': 'ask', 'state': s, 'memory': {}})['asks']
            byid = {m['member_id']: m for m in s['members']}
            for a in asks:
                m = byid[a['member_id']]
                self.assertFalse(policy.unresolvable(m),
                                 'asked member with a declined hard field: %s' % a['member_id'])
                for k in policy.HARD:
                    self.assertNotEqual(m['field_status'][k], 'declined',
                                        'asked %s on declined hard field %s' % (a['member_id'], k))
            sim.resolve_asks(asks); s = sim.observe()
            pairs = policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs']
            byid = {m['member_id']: m for m in s['members']}
            for a, b in pairs:
                for x in (a, b):
                    for k in policy.HARD:
                        self.assertIsNotNone(byid[x]['fields'][k],
                                             'matched %s with unknown hard field %s' % (x, k))
                        self.assertNotEqual(byid[x]['field_status'][k], 'declined',
                                             'matched %s on declined hard field %s' % (x, k))
                self.assertEqual(eligibility(byid[a], byid[b])['status'], 'feasible')
            sim.advance(pairs)

    def test_unresolvable_flags_declined_hard_field(self):
        sim = Simulator(generate(904, 40, 'evaluation', 'development'))
        declined = [m for m in sim.observe()['members']
                    if any(m['field_status'][k] == 'declined' for k in policy.HARD)]
        self.assertTrue(declined, 'fixture has no declined hard field to test')
        for m in declined:
            self.assertTrue(policy.unresolvable(m))
        resolved = [m for m in sim.observe()['members']
                    if not any(m['fields'][k] is None for k in policy.HARD)]
        for m in resolved:
            self.assertFalse(policy.unresolvable(m))

    def test_targeted_asks_skip_declined_members(self):
        sim = Simulator(generate(905, 60, 'evaluation', 'development'))
        s = sim.observe()
        byid = {m['member_id']: m for m in s['members']}
        asked = {a['member_id'] for a in policy.targeted_hard_asks(s)}
        for i in asked:
            self.assertFalse(policy.unresolvable(byid[i]),
                             'targeted asks include declined member %s' % i)

    def test_guard_pairs_drops_unknown_constraint_pairs(self):
        sim = Simulator(generate(906, 60, 'evaluation', 'development'))
        s = sim.observe()
        unknown = None
        for m in s['members']:
            if m['available'] and any(m['fields'][k] is None for k in policy.HARD):
                unknown = m
                break
        self.assertIsNotNone(unknown, 'fixture has no member with unknown hard fields')
        partner = next(m for m in s['members']
                       if m['available'] and m['member_id'] != unknown['member_id'])
        self.assertNotEqual(eligibility(unknown, partner)['status'], 'feasible')
        self.assertEqual(policy.guard_pairs(s, [[unknown['member_id'], partner['member_id']]]), [])

    def test_guard_filters_bad_actions(self):
        sim = Simulator(generate(903, 200, 'evaluation', 'development')); s = sim.observe()
        ids = [m['member_id'] for m in s['members']]
        bad = [{'member_id': 'nope', 'field': 'constraints'}, {'member_id': ids[0], 'field': 'bogus'}] + [{'member_id': i, 'field': 'constraints'} for i in ids[:10]]
        out = policy.guard_asks(s, bad)
        self.assertLessEqual(len(out), 4)
        self.assertEqual(policy.guard_pairs(s, [[ids[0], ids[0]], ['x', 'y']]), [])

    def test_internal_error_returns_empty_valid_action(self):
        out = policy.decide({'phase': 'match', 'state': {'members': 'broken'}, 'memory': {}})
        self.assertEqual(out, {'pairs': [], 'memory': {}})

if __name__ == '__main__':
    unittest.main()
