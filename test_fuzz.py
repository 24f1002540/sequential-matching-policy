"""Fuzz tests: schema-valid but unusual states must never raise and must give valid actions;
malformed requests whose JSON parses and whose state is present or null must return an empty, valid action
(never an exception or a non-zero exit). Input that is not a JSON object is outside the official protocol."""
import copy, json, random, subprocess, sys, unittest
from kit import HARD, SOFT, Simulator, generate, eligibility
import policy
from evaluate import validate_response

STATUS = ['observed', 'not_asked', 'declined']

def base_states():
    out = []
    for variant, days in (('development', 12), ('cold_start', 5), ('sparse', 20), ('drift', 30)):
        sim = Simulator(generate(777, 200, 'evaluation', variant))
        for _ in range(days):
            s = sim.observe()
            sim.resolve_asks(policy.decide({'phase': 'ask', 'state': s, 'memory': {}})['asks']); s = sim.observe()
            sim.advance(policy.decide({'phase': 'match', 'state': s, 'memory': {}})['pairs'])
        out.append(sim.observe())
    return out

def mutate(state, rnd):
    s = copy.deepcopy(state)
    kind = rnd.choice(['blank_fields', 'unavailable', 'all_declined', 'few_members', 'empty', 'budget', 'shuffle', 'dup_intros', 'all_known'])
    ms = s['members']
    if kind == 'blank_fields':
        for m in ms:
            for k in list(m['fields']):
                if rnd.random() < 0.4: m['fields'][k] = None; m['field_status'][k] = rnd.choice(['not_asked', 'declined'])
    elif kind == 'unavailable':
        for m in ms:
            if rnd.random() < 0.6: m['available'] = False
    elif kind == 'all_declined':
        for m in ms:
            for k in HARD: m['fields'][k] = None; m['field_status'][k] = 'declined'
    elif kind == 'few_members':
        s['members'] = rnd.sample(ms, min(len(ms), rnd.choice([0, 1, 2, 3, 5])))
    elif kind == 'empty':
        s['members'] = []; s['introductions'] = []; s['feedback'] = []
    elif kind == 'budget':
        s['ask_budget_remaining'] = rnd.choice([0, 1, 2, 3, 4, 11, 12, 100])
    elif kind == 'shuffle':
        rnd.shuffle(s['members'])
    elif kind == 'dup_intros':
        s['introductions'] = s['introductions'] + s['introductions']
    elif kind == 'all_known':
        for m in ms:
            for k in list(m['fields']):
                if m['fields'][k] is None: m['field_status'][k] = 'not_asked'
    return s, kind

def check_asks(test, state, asks):
    byid = {m['member_id']: m for m in state['members']}; seen = set(); cost = 0
    for a in asks:
        test.assertIn(a['member_id'], byid); test.assertTrue(byid[a['member_id']]['available'])
        test.assertIn(a['field'], ['constraints'] + list(SOFT)); test.assertNotIn((a['member_id'], a['field']), seen)
        seen.add((a['member_id'], a['field'])); cost += 3 if a['field'] == 'constraints' else 1
        test.assertFalse(policy.unresolvable(byid[a['member_id']]))
    test.assertLessEqual(cost, state['ask_budget_remaining'])

def check_pairs(test, state, pairs):
    byid = {m['member_id']: m for m in state['members']}; used = set(); past = policy.past_pairs(state)
    for a, b in pairs:
        test.assertNotEqual(a, b); test.assertNotIn(a, used); test.assertNotIn(b, used); used.update((a, b))
        test.assertTrue(byid[a]['available'] and byid[b]['available']); test.assertNotIn(policy.pair_key(a, b), past)
        test.assertEqual(eligibility(byid[a], byid[b])['status'], 'feasible')

class FuzzTests(unittest.TestCase):
    def test_schema_valid_unusual_states(self):
        rnd = random.Random(2026); bases = base_states(); kinds = set()
        for i in range(60):
            s, kind = mutate(rnd.choice(bases), rnd); kinds.add(kind)
            for phase in ('ask', 'match'):
                req = {'schema_version': '1.0.0', 'phase': phase, 'state': s, 'memory': rnd.choice([None, {}, {'x': [1, 2, 3]}])}
                # direct calls: a schema-valid state must not raise inside the policy at all
                if phase == 'ask': asks = policy.targeted_hard_asks(s); check_asks(self, s, policy.guard_asks(s, asks))
                else: check_pairs(self, s, policy.guard_pairs(s, policy.baseline_match(s)))
                resp = validate_response(json.loads(json.dumps(policy.decide(req))), phase)
                key = 'asks' if phase == 'ask' else 'pairs'
                (check_asks if phase == 'ask' else check_pairs)(self, s, resp[key])
        self.assertGreaterEqual(len(kinds), 7)

    def test_garbage_requests_give_empty_valid_actions(self):
        garbage = [{'phase': 'ask', 'state': None, 'memory': None}, {'phase': 'match', 'state': {}, 'memory': None},
                   {'phase': 'ask', 'state': {'members': [{'member_id': 'x'}], 'introductions': [], 'ask_budget_remaining': 12}, 'memory': {}},
                   {'phase': 'match', 'state': {'members': 'broken', 'introductions': 5}, 'memory': {}}]
        for g in garbage:
            for phase in ('ask', 'match'):
                req = dict(g, phase=phase); out = policy.decide(req) if g.get('state') is not None else None
                if out is None:
                    p = subprocess.run([sys.executable, 'policy.py'], input=json.dumps(req).encode(), capture_output=True)
                    self.assertEqual(p.returncode, 0)          # a null state is answered, not crashed on
                    validate_response(json.loads(p.stdout), phase)
                    self.assertEqual(json.loads(p.stdout)['asks' if phase == 'ask' else 'pairs'], [])
                    continue
                validate_response(json.loads(json.dumps(out)), phase)
                self.assertEqual(out['asks' if phase == 'ask' else 'pairs'], [])

if __name__ == '__main__':
    unittest.main()
