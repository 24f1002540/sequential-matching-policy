"""Candidate T: pair-completion clarification. Greedy marginal-credit selection: a member's credit is the sum over still-unresolved
pairs of 1/(members of that pair not yet selected), so choosing one member raises the credit of that pair's partner and finished pairs are prioritised."""
import itertools
from kit import eligibility
from smp_core import past_pairs, unresolvable
def completion_asks(state):
    budget = state['ask_budget_remaining']; ms = [m for m in state['members'] if m['available']]
    byid = {m['member_id']: m for m in ms}; past = past_pairs(state); pairs = []
    for a, b in itertools.combinations(ms, 2):
        if tuple(sorted((a['member_id'], b['member_id']))) in past: continue
        e = eligibility(a, b)
        if e['status'] != 'needs_clarification': continue
        need = {x.split(':')[0] for x in e['missing']}
        if any(i not in byid or unresolvable(byid[i]) for i in need): continue
        pairs.append(need)
    sel, asks = set(), []
    while budget >= 3:
        score = {}
        for need in pairs:
            rem = need - sel
            if not rem: continue
            for i in rem: score[i] = score.get(i, 0.0) + 1.0 / len(rem)
        if not score: break
        i = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        sel.add(i); asks.append({'member_id': i, 'field': 'constraints'}); budget -= 3
    return asks
