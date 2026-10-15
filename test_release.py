"""Release regressions for pair-level scoring and the frozen arrival denominator."""
import unittest
from unittest.mock import patch
from evaluate import episode
from kit import Simulator, generate


class ReleaseTests(unittest.TestCase):
    def test_one_successful_pair_is_one_outcome(self):
        world = generate(42, 2)
        for member in world['members']:
            member['arrived_day'] = 0
        sim = Simulator(world)
        a, b = [m['member_id'] for m in world['members']]
        sim.introductions = [{'introduction_id': 'i', 'user_a': a, 'user_b': b, 'assigned_day': 0}]
        sim.events = [
            {'introduction_id': 'i', 'event': 'introduction_response', 'value': 'yes', 'observed_day': 1},
            {'introduction_id': 'i', 'event': 'introduction_response', 'value': 'yes', 'observed_day': 2},
            {'introduction_id': 'i', 'event': 'date_happened', 'value': True, 'occurred_day': 3, 'observed_day': 3},
            {'introduction_id': 'i', 'event': 'second_meeting_intention', 'value': 'yes', 'occurred_day': 5, 'observed_day': 5},
            {'introduction_id': 'i', 'event': 'second_meeting_intention', 'value': 'yes', 'occurred_day': 6, 'observed_day': 6},
        ]
        sim.day = 40
        result = sim.metrics()
        self.assertEqual(result['mutual_second_meeting_intention'], 1)
        self.assertEqual(result['msmi_per_100_arrived_members'], 50)

    def test_episode_denominator_and_distinct_coverage(self):
        # One member arrives during follow-up; one early member later leaves.
        # The metrics stub deliberately reports the follow-up population, so
        # the evaluator must use its own frozen decision-horizon denominator.
        class Fixture:
            def __init__(self, world):
                self.day = 0
                self.introductions = [
                    {'user_a': 'a', 'user_b': 'b', 'assigned_day': 0},
                    {'user_a': 'a', 'user_b': 'c', 'assigned_day': 30},
                ]

            def observe(self):
                return {'members': [
                    {'member_id': ident, 'arrived_day': day, 'available': False}
                    for ident, day in [('a', 0), ('b', 0), ('c', 1), ('d', 59), ('late', 80)]
                    if day <= self.day
                ]}

            def resolve_asks(self, asks):
                pass

            def advance(self, pairs):
                self.day += 1

            def metrics(self):
                return {'mutual_second_meeting_intention': 1, 'mutual_acceptances': 2,
                        'arrived_members': 5, 'msmi_per_100_arrived_members': 20}

        def no_actions(command, request, timeout):
            key = 'asks' if request['phase'] == 'ask' else 'pairs'
            return {key: [], 'memory': None}, 0

        with patch('evaluate.invoke', side_effect=no_actions):
            result = episode({}, [], simulator_class=Fixture)
        self.assertEqual(result['arrived_members'], 4)
        self.assertEqual(result['msmi_per_100_arrived_members'], 25)
        self.assertEqual(result['coverage'], .75)
        self.assertEqual(result['served_members'], 3)
        self.assertEqual(result['unserved_members'], 1)
        self.assertEqual(result['first_introduction_wait_days'], [0, 0, 29])

    def test_empty_population_returns_zero_metrics(self):
        def no_actions(command, request, timeout):
            key = 'asks' if request['phase'] == 'ask' else 'pairs'
            return {key: [], 'memory': None}, 0

        with patch('evaluate.invoke', side_effect=no_actions):
            result = episode(generate(42, 0), [])
        self.assertEqual(result['arrived_members'], 0)
        self.assertEqual(result['msmi_per_100_arrived_members'], 0)
        self.assertEqual(result['coverage'], 0)


if __name__ == '__main__':
    unittest.main()
