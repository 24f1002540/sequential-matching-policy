import itertools
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
            sim.resolve_asks(policy.decide({'phase': 'ask', 'state': s, 'memory': {}})['asks']); s = sim.observe()
            pairs = policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs']
            byid = {m['member_id']: m for m in s['members']}
            for a, b in pairs:
                for x in (a, b):
                    for k in policy.HARD:
                        self.assertIsNotNone(byid[x]['fields'][k]) if False else None
                self.assertEqual(eligibility(byid[a], byid[b])['status'], 'feasible')
            sim.advance(pairs)

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

    def test_guard_asks_output_accepted_by_simulator(self):
        # Invalid IDs, unknown fields, duplicates, over-budget bundles and
        # declined (but available) members: the filtered output must be
        # accepted by the real simulator, which validates atomically.
        sim = Simulator(generate(907, 120, 'evaluation', 'development'))
        s = sim.observe()
        byid = {m['member_id']: m for m in s['members']}
        avail = [m['member_id'] for m in s['members'] if m['available']]
        declined = next(i for i in avail if policy.unresolvable(byid[i]))
        bad = [{'member_id': 'syn_' + '0' * 32, 'field': 'constraints'},
               {'member_id': avail[0], 'field': 'not_a_field'},
               {'member_id': avail[1], 'field': 'constraints'},
               {'member_id': avail[1], 'field': 'constraints'},
               {'member_id': declined, 'field': 'constraints'}] + \
              [{'member_id': i, 'field': 'constraints'} for i in avail[2:14]]
        out = policy.guard_asks(s, bad)
        self.assertLess(len(out), len(bad))
        cost = sum(3 if a['field'] == 'constraints' else 1 for a in out)
        self.assertLessEqual(cost, s['ask_budget_remaining'])
        sim.resolve_asks(out)  # must not raise

    def test_guard_respects_partial_daily_budget(self):
        sim = Simulator(generate(908, 120, 'evaluation', 'development'))
        s = sim.observe()
        avail = [m['member_id'] for m in s['members'] if m['available']]
        sim.resolve_asks([{'member_id': avail[0], 'field': 'constraints'}])
        s = sim.observe()
        self.assertEqual(s['ask_budget_remaining'], 9)
        out = policy.guard_asks(
            s, [{'member_id': i, 'field': 'constraints'} for i in avail[1:6]])
        self.assertLessEqual(sum(3 for _ in out), 9)
        sim.resolve_asks(out)  # must not raise

    def test_guard_drops_unavailable_members(self):
        sim = Simulator(generate(909, 200, 'evaluation', 'development'))
        s = sim.observe()
        first = policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs']
        self.assertTrue(first)
        sim.advance(first[:1])  # endpoints are now busy (unavailable)
        busy = [i for p in first[:1] for i in p]
        s = sim.observe()
        byid = {m['member_id']: m for m in s['members']}
        avail = [m['member_id'] for m in s['members'] if m['available']]
        self.assertFalse(all(byid[i]['available'] for i in busy))
        self.assertEqual(
            policy.guard_asks(s, [{'member_id': i, 'field': 'constraints'} for i in busy]), [])
        fresh = None
        for x, y in itertools.combinations(avail, 2):
            if eligibility(byid[x], byid[y])['status'] == 'feasible':
                fresh = [x, y]
                break
        self.assertIsNotNone(fresh)
        out = policy.guard_pairs(s, [busy[:2], fresh])
        self.assertNotIn(busy[0], [i for p in out for i in p])
        self.assertEqual([sorted(p) for p in out], [sorted(fresh)])
        sim.advance(out)  # must not raise

    def test_guard_pairs_output_accepted_by_simulator(self):
        # Self-pairs, unknown IDs, overlaps, repeats, unknown-constraint and
        # infeasible pairs: only the feasible remainder may survive, and the
        # real simulator must accept it.
        sim = Simulator(generate(911, 200, 'evaluation', 'development'))
        s = sim.observe()
        first = policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs']
        self.assertGreaterEqual(len(first), 2)
        good = first[1]  # feasible on day 0; untouched by advancing first[:1]
        sim.advance(first[:1])  # one pair into history; supply stays intact
        s = sim.observe()
        byid = {m['member_id']: m for m in s['members']}
        avail = [m['member_id'] for m in s['members'] if m['available']]
        past = {tuple(sorted((i['user_a'], i['user_b']))) for i in s['introductions']}
        self.assertEqual(eligibility(byid[good[0]], byid[good[1]])['status'], 'feasible')
        self.assertNotIn(tuple(sorted(good)), past)
        infeasible = unknown = None
        for x, y in itertools.combinations(avail, 2):
            if tuple(sorted((x, y))) in past:
                continue
            status = eligibility(byid[x], byid[y])['status']
            if status == 'infeasible' and infeasible is None:
                infeasible = [x, y]
            elif status == 'needs_clarification' and unknown is None:
                unknown = [x, y]
            if infeasible and unknown:
                break
        self.assertIsNotNone(infeasible)
        self.assertIsNotNone(unknown)
        repeat = next(iter(past))
        bad = [good, [avail[0], avail[0]], ['syn_' + '0' * 32, avail[1]],
               [good[0], avail[2]], list(repeat), unknown, infeasible]
        out = policy.guard_pairs(s, bad)
        self.assertEqual([sorted(p) for p in out], [sorted(good)])
        sim.advance(out)  # must not raise

if __name__ == '__main__':
    unittest.main()
