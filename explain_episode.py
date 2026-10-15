"""Replay one public-simulator episode in-process with the submitted policy and write a decision log.
python explain_episode.py --seed 101 --variant development --days 60 --out results/explain_101
Writes decisions.jsonl (machine readable) and decisions.txt (readable) and prints the outcome."""
import argparse, json, os
from kit import Simulator, generate
from explain import explain_request

def main():
    p = argparse.ArgumentParser(); p.add_argument('--seed', type=int, default=101); p.add_argument('--variant', default='development')
    p.add_argument('--days', type=int, default=60); p.add_argument('--out', default='results/explain_101')
    a = p.parse_args(); os.makedirs(a.out, exist_ok=True)
    sim = Simulator(generate(a.seed, 200, 'evaluation', a.variant)); memory = {}
    jl = open(os.path.join(a.out, 'decisions.jsonl'), 'w'); tx = open(os.path.join(a.out, 'decisions.txt'), 'w')
    for _ in range(a.days):
        for phase in ('ask', 'match'):
            state = sim.observe()
            resp, trace = explain_request({'schema_version': '1.0.0', 'phase': phase, 'state': state, 'memory': memory})
            jl.write(json.dumps(trace) + '\n')
            s = trace['summary']
            if phase == 'ask':
                tx.write('DAY %d  ASK   budget %d, askable members %d, asked %d%s\n' % (trace['day'], s['budget_remaining_before'], s['askable_members'], s['asked'], ' (budget binding)' if s['budget_binding'] else ''))
                for d in trace['decisions']: tx.write('   ask %s the hard-constraint bundle (cost %d): %s\n' % (d['member_id'][-6:], d['cost'], d['reason']))
                sim.resolve_asks(resp['asks'])
            else:
                tx.write('DAY %d  MATCH %d feasible pair(s) available among %d members; introduced %d, left for later %d\n' % (trace['day'], s['feasible_pairs_available'], s['members_with_an_option'], s['introduced'], s['left_for_later']))
                for d in trace['decisions']: tx.write('   introduce %s + %s: %s\n' % (d['pair'][0][-6:], d['pair'][1][-6:], d['reason']))
                sim.advance(resp['pairs'])
    for _ in range(40): sim.advance([])
    m = sim.metrics(); tx.write('\nOUTCOME after follow-up: %s\n' % json.dumps({k: m[k] for k in ('assignments', 'mutual_acceptances', 'dates', 'mutual_second_meeting_intention', 'ask_cost')}))
    print(json.dumps({k: m[k] for k in ('assignments', 'mutual_acceptances', 'dates', 'mutual_second_meeting_intention', 'ask_cost')}))

if __name__ == '__main__':
    main()
