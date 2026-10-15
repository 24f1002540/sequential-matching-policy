import copy,json,unittest
from kit import *

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.w=generate(81,24);self.s=Simulator(self.w)
    def test_reproducible(self):self.assertEqual(self.w,generate(81,24))
    def test_no_latent_leak(self):
        for m in self.s.observe()['members']:
            self.assertFalse(set(m)&{'truth','bias','response_rate','second_bias','exit_day'})
    def test_no_future_members(self):
        self.assertTrue(all(m['arrived_day']<=0 for m in self.s.observe()['members']))
    def test_observation_is_copy(self):
        x=self.s.observe();x['members'][0]['age']=1
        self.assertNotEqual(self.s.observe()['members'][0]['age'],1)
    def test_ask_budget_atomic(self):
        before=self.s.observe()
        asks=[{'member_id':m['member_id'],'field':'constraints'} for m in before['members'][:5]]
        with self.assertRaises(ValueError):self.s.resolve_asks(asks)
        self.assertEqual(before,self.s.observe())
    def test_invalid_match_atomic(self):
        before=self.s.observe();i=before['members'][0]['member_id']
        with self.assertRaises(ValueError):self.s.advance([[i,i]])
        self.assertEqual(before,self.s.observe())
    def test_unknown_not_pass(self):
        a,b=copy.deepcopy(self.w['members'][:2]);a['fields']={k:None for k in a['fields']};b['fields']=a['fields'].copy()
        self.assertEqual(eligibility(a,b)['status'],'needs_clarification')
    def test_symmetric_feasibility(self):
        a,b=self.w['members'][:2]
        self.assertEqual(eligibility(a,b)['status'],eligibility(b,a)['status'])
    def test_declined_stays_declined(self):
        m=next(m for m in self.s.members.values() if m['arrived_day']==0)
        m['fields']['age_min']=None;m['field_status']['age_min']='declined'
        self.s.resolve_asks([{'member_id':m['member_id'],'field':'constraints'}])
        self.assertIsNone(m['fields']['age_min'])
    def test_temporal_integrity(self):
        s=rollout(generate(20261000,80),35)
        for e in s.receive_feedback():self.assertLessEqual(e['observed_day'],s.day)
        ids={m['member_id'] for m in s.observe()['members']}
        for x in s.introductions:self.assertTrue({x['user_a'],x['user_b']}<=ids)
        self.assertTrue(all(m['field_observed_day'][k] is None or m['field_observed_day'][k]<=s.day for m in s.observe()['members'] for k in m['fields']))
    def test_order_independent_world_randomness(self):
        # Same actions in a reversed batch yield identical feedback.
        s=rollout(generate(20261000,60),10);t=copy.deepcopy(s)
        pairs=baseline_match(s.observe());s.advance(pairs);t.advance(list(reversed(pairs)))
        self.assertEqual(s.events,t.events)
    def test_outcome_funnel(self):
        s=rollout(generate(20261001,80),40)
        for _ in range(40):s.advance([])
        m=s.metrics();self.assertLessEqual(m['mutual_second_meeting_intention'],m['dates']);self.assertLessEqual(m['dates'],m['mutual_acceptances']);self.assertLessEqual(m['mutual_acceptances'],m['assignments'])

if __name__=='__main__':unittest.main()
