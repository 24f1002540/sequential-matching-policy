"""Round 2 submission policy. JSON stdin/stdout (docs/POLICY_INTERFACE.md).

Design (see REPORT.md): reciprocal feasibility from the supplied `eligibility`, the supplied hard-constraint
clarification rule, supplied similarity-greedy allocation, and an independent output guard. No learned asset,
no network, no hidden-state access. The only inputs are the observable JSON request.
Any error raised while deciding returns an empty (always valid) action. (Input that is not a JSON object is
not something the official harness sends and ends the process with an error.)
"""
import argparse
import itertools
import json
import sys
import traceback

from kit import HARD, SOFT, baseline_asks, baseline_match, eligibility

ASK_COST = {'constraints': 3}


def pair_key(a, b):
    return tuple(sorted((a, b)))


def past_pairs(state):
    return {pair_key(i['user_a'], i['user_b']) for i in state['introductions']}


def unresolvable(member):
    """A member who declined a hard field can never be fully resolved: never ask again, never match."""
    return any(member['field_status'][k] == 'declined' and member['fields'][k] is None for k in HARD)


def targeted_hard_asks(state):
    """Value-of-information rule: each pair that still needs clarification gives credit 1/(members who must answer)
    to those members; ask the highest-credit available members the 3-unit hard bundle within today's budget."""
    budget = state['ask_budget_remaining']
    members = [m for m in state['members'] if m['available']]
    byid = {m['member_id']: m for m in members}
    past = past_pairs(state)
    score = {}
    for a, b in itertools.combinations(members, 2):
        if pair_key(a['member_id'], b['member_id']) in past:
            continue
        e = eligibility(a, b)
        if e['status'] != 'needs_clarification':
            continue
        need = {x.split(':')[0] for x in e['missing']}
        if any(i not in byid or unresolvable(byid[i]) for i in need):
            continue
        for i in need:
            score[i] = score.get(i, 0.0) + 1.0 / len(need)
    asks = []
    for i, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0])):
        if budget < 3:
            break
        asks.append({'member_id': i, 'field': 'constraints'})
        budget -= 3
    return asks


def guard_asks(state, asks):
    byid = {m['member_id']: m for m in state['members']}
    seen, cost, out = set(), 0, []
    for a in asks:
        i, f = a['member_id'], a['field']
        if i not in byid or not byid[i]['available'] or f not in ['constraints'] + list(SOFT) or (i, f) in seen:
            continue
        c = 3 if f == 'constraints' else 1
        if cost + c > state['ask_budget_remaining']:
            continue
        seen.add((i, f)); cost += c
        out.append({'member_id': i, 'field': f})
    return out


def guard_pairs(state, pairs):
    byid = {m['member_id']: m for m in state['members']}
    past, used, out = past_pairs(state), set(), []
    for a, b in pairs:
        if a == b or a in used or b in used or a not in byid or b not in byid:
            continue
        if not (byid[a]['available'] and byid[b]['available']):
            continue
        if pair_key(a, b) in past or eligibility(byid[a], byid[b])['status'] != 'feasible':
            continue
        used.update((a, b)); out.append([a, b])
    return out


def decide(request, mode='submission'):
    state = request['state']
    memory = request.get('memory') or {}
    phase = request['phase']
    key = 'asks' if phase == 'ask' else 'pairs'
    try:
        if mode == 'no_asks':
            asks = []
        elif mode == 'targeted':
            # Round 1/2 candidate (arm C in REPORT.md): kept for the record, not used by the submission.
            # On 40 fresh seeds it scored below the supplied asking rule (REPORT.md section 5.7).
            asks = targeted_hard_asks(state)
        else:
            # 'submission' and 'greedy': the supplied clarification rule (arm A), behind the guard below.
            asks = baseline_asks(state)
        if phase == 'ask':
            return {'asks': guard_asks(state, asks), 'memory': memory}
        return {'pairs': guard_pairs(state, baseline_match(state)), 'memory': memory}
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return {key: [], 'memory': memory}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', choices=['greedy', 'no_asks', 'random'], default=None)
    args = parser.parse_args()
    request = json.load(sys.stdin)
    if args.baseline == 'random':
        from official_baselines import decide as official_decide
        out = official_decide(request, 'random')
    elif args.baseline:
        out = decide(request, args.baseline)
    else:
        out = decide(request)
    print(json.dumps(out, allow_nan=False))
