"""Prepare private worlds outside the repository and grade offline policy images."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
from evaluate import VARIANTS, docker_command, episode, summarise
from kit import generate, VERSION


def prepare(workspace):
    workspace = Path(workspace).resolve()
    repository = Path(__file__).resolve().parent
    if workspace == repository or repository in workspace.parents:
        raise ValueError('Private workspace must be outside the public repository')
    workspace.mkdir(parents=True, exist_ok=False)
    manifest = {'release': VERSION, 'private': True, 'worlds': []}
    used = set()
    for variant in VARIANTS:
        for index in range(20):
            seed = secrets.randbits(63)
            while seed in used:
                seed = secrets.randbits(63)
            used.add(seed)
            name = f'{variant}_{index:02d}.json'
            raw = (json.dumps(generate(seed, 200, 'private_pool', variant), sort_keys=True) + '\n').encode()
            (workspace / name).write_bytes(raw)
            manifest['worlds'].append({'path': name, 'variant': variant, 'sha256': hashlib.sha256(raw).hexdigest()})
    (workspace / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared 120 private worlds outside the repository. Keep this workspace private and unchanged.')


def grade(workspace, image, output):
    workspace = Path(workspace).resolve()
    manifest = json.loads((workspace / 'manifest.json').read_text())
    worlds = manifest['worlds']
    if manifest['release'] != VERSION or len(worlds) != 120:
        raise ValueError('Expected a release 1.0 manifest with 120 worlds')
    if any(sum(w['variant'] == variant for w in worlds) != 20 for variant in VARIANTS):
        raise ValueError('Expected 20 worlds in each of six families')
    image_info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
    if image_info['Size'] > 2 * 1024 ** 3:
        raise ValueError('Policy image exceeds 2 GiB')
    # Pin the built image digest; a mutable tag cannot switch code midway through grading.
    image_id = image_info['Id']
    rows = []
    for index, record in enumerate(worlds):
        raw = (workspace / record['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('Private world checksum mismatch')
        world = json.loads(raw)
        try:
            row = episode(world, docker_command(image_id))
        except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as error:
            row = {'valid': False, 'error': str(error)}
        row.update(episode_index=index, variant=record['variant'])
        rows.append(row)
        print(json.dumps({'episode': index + 1, 'total': 120, 'valid': row['valid']}), flush=True)
    result = {'release': VERSION, 'mode': 'container', 'image_id': image_id,
              'world_manifest_sha256': hashlib.sha256((workspace / 'manifest.json').read_bytes()).hexdigest(),
              'episodes': rows, 'summary': summarise(rows)}
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return 0 if result['summary']['eligible'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='action', required=True)
    init = commands.add_parser('prepare')
    init.add_argument('--workspace', required=True)
    run = commands.add_parser('grade')
    run.add_argument('--workspace', required=True)
    run.add_argument('--image', required=True)
    run.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.workspace)
    else:
        raise SystemExit(grade(args.workspace, args.image, args.output))
