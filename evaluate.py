"""Public evaluation harness. Local subprocess mode is for trusted code only."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from kit import Simulator, generate, VERSION

VARIANTS = ('development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift')
LIMIT = 1024 * 1024


def strict_json(text):
    def reject(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(text, parse_constant=reject)


def validate_response(response, phase):
    key = 'asks' if phase == 'ask' else 'pairs'
    if not isinstance(response, dict) or set(response) != {key, 'memory'}:
        raise ValueError('Response must contain exactly ' + key + ' and memory')
    if not isinstance(response[key], list):
        raise ValueError(key + ' must be an array')
    if len(json.dumps(response['memory'], allow_nan=False).encode()) > LIMIT:
        raise ValueError('Memory exceeds 1 MiB')
    if key == 'asks':
        for ask in response[key]:
            if not isinstance(ask, dict) or set(ask) != {'member_id', 'field'} or not all(isinstance(v, str) for v in ask.values()):
                raise ValueError('Invalid ask shape')
    else:
        for pair in response[key]:
            if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(i, str) for i in pair):
                raise ValueError('Each pair must be an array of two strings')
    return response


def invoke(command, request, timeout=10):
    raw = json.dumps(request, allow_nan=False).encode()
    if len(raw) > LIMIT:
        raise ValueError('Request exceeds 1 MiB')
    started = time.perf_counter()
    # File-backed output avoids loading unlimited child output into host memory.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err)
        try:
            proc.communicate(raw, timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            if command[:2] == ['docker', 'run'] and '--name' in command:
                name = command[command.index('--name') + 1]
                subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            raise ValueError('Policy exceeded 10-second invocation limit')
        if proc.returncode:
            err.seek(0)
            raise ValueError('Policy exited unsuccessfully: ' + err.read(2048).decode(errors='replace'))
        if out.tell() > LIMIT or err.tell() > LIMIT:
            raise ValueError('Policy output exceeds 1 MiB')
        out.seek(0)
        response = strict_json(out.read().decode('utf-8'))
    return validate_response(response, request['phase']), time.perf_counter() - started


def docker_command(image):
    # No host directories, including organiser worlds, are mounted into the policy.
    return ['docker', 'run', '--rm', '-i', '--name', 'sequential-' + uuid.uuid4().hex, '--network=none', '--cpus=2',
            '--memory=1g', '--memory-swap=1g', '--pids-limit=64', '--read-only',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=65534:65534',
            '--tmpfs=/tmp:rw,noexec,nosuid,size=64m', image]


def episode(world, command, timeout=10, simulator_class=Simulator):
    sim = simulator_class(world)
    memory = None
    inference_seconds = 0
    digest = hashlib.sha256()
    for _ in range(60):
        for phase in ('ask', 'match'):
            request = {'schema_version': VERSION, 'phase': phase,
                       'state': sim.observe(), 'memory': memory}
            response, elapsed = invoke(command, request, timeout)
            inference_seconds += elapsed
            memory = response['memory']
            action = response['asks' if phase == 'ask' else 'pairs']
            digest.update(json.dumps([phase, sim.day, action], sort_keys=True).encode())
            if phase == 'ask':
                sim.resolve_asks(action)
            else:
                sim.advance(action)
    arrived = {m['member_id']: m['arrived_day'] for m in sim.observe()['members']
               if m['arrived_day'] <= 59}
    for _ in range(40):
        sim.advance([])
    result = sim.metrics()
    first = {}
    for intro in sim.introductions:
        for member in (intro['user_a'], intro['user_b']):
            first.setdefault(member, intro['assigned_day'])
    waits = sorted(first[i] - arrived[i] for i in first)
    result.update(valid=True, arrived_members=len(arrived),
                  msmi_per_100_arrived_members=100 * result['mutual_second_meeting_intention'] / max(1, len(arrived)),
                  served_members=len(first), unserved_members=len(arrived) - len(first),
                  coverage=len(first) / max(1, len(arrived)),
                  mutual_acceptances_per_100=100 * result['mutual_acceptances'] / max(1, len(arrived)),
                  first_introduction_wait_days=waits,
                  inference_seconds=inference_seconds, action_sha256=digest.hexdigest())
    return result


def summarise(rows):
    if not rows or any(not r.get('valid') for r in rows):
        return {'eligible': False, 'primary_score': None, 'reason': 'At least one episode is invalid'}
    families = collections.defaultdict(list)
    for row in rows:
        families[row['variant']].append(row)
    keys = ('msmi_per_100_arrived_members', 'coverage', 'mutual_acceptances_per_100', 'ask_cost', 'inference_seconds')
    family_means = {name: {key: statistics.mean(r[key] for r in rs) for key in keys}
                    for name, rs in sorted(families.items())}
    overall = {key: statistics.mean(f[key] for f in family_means.values()) for key in keys}
    return {'eligible': True, 'primary_score': overall['msmi_per_100_arrived_members'],
            'scenario_means': family_means, 'overall': overall,
            'ranking_key_descending': [overall['msmi_per_100_arrived_members'], overall['coverage'],
                                       overall['mutual_acceptances_per_100'], -overall['ask_cost'], -overall['inference_seconds']]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--policy', default='policy.py')
    p.add_argument('--baseline', choices=['greedy', 'no_asks', 'random'], default='greedy')
    p.add_argument('--image', help='Use isolated offline Docker execution instead of trusted local subprocesses')
    p.add_argument('--seeds', default='101', help='Comma-separated public experiment seeds')
    p.add_argument('--variants', default='development', help='Comma-separated variants, or all')
    p.add_argument('--output', default='results/evaluation.json')
    args = p.parse_args()
    seeds = [int(s) for s in args.seeds.split(',')]
    variants = list(VARIANTS) if args.variants == 'all' else args.variants.split(',')
    if not seeds or not variants or any(v not in VARIANTS for v in variants):
        p.error('Choose at least one seed and recognised variant')
    command = docker_command(args.image) if args.image else [sys.executable, args.policy, '--baseline', args.baseline]
    rows = []
    for variant in variants:
        for seed in seeds:
            try:
                row = episode(generate(seed, 200, 'evaluation', variant), command)
            except (ValueError, TypeError, KeyError, OSError) as error:
                row = {'valid': False, 'error': str(error)}
            row.update(seed=seed, variant=variant)
            rows.append(row)
            print(json.dumps({'seed': seed, 'variant': variant, 'valid': row['valid'],
                              'msmi': row.get('mutual_second_meeting_intention')}), flush=True)
    summary = summarise(rows)
    output = {'release': VERSION, 'mode': 'container' if args.image else 'trusted_local',
              'decision_days': 60, 'follow_up_days': 40, 'members_per_episode': 200,
              'episodes': rows, 'summary': summary}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2))
    return 0 if summary['eligible'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
