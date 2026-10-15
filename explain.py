"""Decision trace for the submitted policy: WHY each member was asked and WHY each pair was introduced.

explain.py never changes a decision. `explain_request` calls policy.decide for the action and recomputes the reasons separately
from the same observable state; test_explain.py checks that the two always agree.
Usage as a script: see explain_episode.py (replays a public-simulator episode and writes decisions.jsonl and decisions.txt).
"""
import itertools

from kit import HARD, SOFT, eligibility
import policy


def _needs(state):
    """For each pair still needing clarification and not blocked by a declined field: the members who must answer."""
    members = [m for m in state['members'] if m['available']]
    byid = {m['member_id']: m for m in members}
    past = policy.past_pairs(state)
    out = []
    for a, b in itertools.combinations(members, 2):
        if policy.pair_key(a['member_id'], b['member_id']) in past:
            continue
        e = eligibility(a, b)
        if e['status'] != 'needs_clarification':
            continue
        need = sorted({x.split(':')[0] for x in e['missing']})
        if any(i not in byid or policy.unresolvable(byid[i]) for i in need):
            continue
        out.append((a['member_id'], b['member_id'], need, e['missing']))
    return out


def explain_asks(state, asks):
    needs = _needs(state)
    credit, unlocks = {}, {}
    for a, b, need, _ in needs:
        for i in need:
            credit[i] = credit.get(i, 0.0) + 1.0 / len(need)
            unlocks.setdefault(i, []).append(b if i == a else a)
    rows = []
    for ask in asks:
        i = ask['member_id']
        rows.append({'member_id': i, 'field': ask['field'], 'cost': 3 if ask['field'] == 'constraints' else 1,
                     'credit': round(credit.get(i, 0.0), 3), 'pairs_it_can_unlock': len(unlocks.get(i, [])),
                     'reason': 'its answer is still missing for %d pair(s) that are otherwise not excluded (credit %.2f); '
                               'asked the hard-constraint bundle in descending credit order' % (len(unlocks.get(i, [])), credit.get(i, 0.0))})
    return rows, {'askable_members': len(credit), 'budget_remaining_before': state['ask_budget_remaining'],
                  'asked': len(asks), 'budget_binding': len(credit) > len(asks),
                  'unresolvable_members': sum(policy.unresolvable(m) for m in state['members'] if m['available'])}


def explain_pairs(state, pairs):
    byid = {m['member_id']: m for m in state['members']}
    past = policy.past_pairs(state)
    members = [m for m in state['members'] if m['available']]
    degree, edges = {}, 0
    for a, b in itertools.combinations(members, 2):
        if policy.pair_key(a['member_id'], b['member_id']) in past or eligibility(a, b)['status'] != 'feasible':
            continue
        edges += 1
        degree[a['member_id']] = degree.get(a['member_id'], 0) + 1
        degree[b['member_id']] = degree.get(b['member_id'], 0) + 1
    rows = []
    for a, b in pairs:
        ma, mb = byid[a], byid[b]
        agree = [k for k in SOFT if ma['fields'].get(k) is not None and ma['fields'].get(k) == mb['fields'].get(k)]
        rows.append({'pair': [a, b], 'status': eligibility(ma, mb)['status'], 'agreeing_soft_fields': agree, 'similarity_score': len(agree),
                     'feasible_partners_a': degree.get(a, 0), 'feasible_partners_b': degree.get(b, 0),
                     'reason': 'feasible in both directions on every hard constraint; chosen by the supplied greedy rule '
                               '(highest count of agreeing known soft fields among pairs whose members were still unused); '
                               'score %d, %d alternative partner(s) for the first member and %d for the second' % (len(agree), degree.get(a, 0) - 1, degree.get(b, 0) - 1)})
    return rows, {'feasible_pairs_available': edges, 'members_with_an_option': len(degree), 'introduced': len(pairs),
                  'left_for_later': edges - len(pairs)}


def explain_request(request):
    """Returns (response, trace). The response is exactly what policy.decide returns."""
    response = policy.decide(request)
    if request['phase'] == 'ask':
        rows, summary = explain_asks(request['state'], response['asks'])
    else:
        rows, summary = explain_pairs(request['state'], response['pairs'])
    return response, {'phase': request['phase'], 'day': request['state']['day'], 'decisions': rows, 'summary': summary}
