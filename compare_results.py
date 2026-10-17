"""Compare freshly generated results against the committed ones, episode by episode.
Usage: python compare_results.py results/repro      (compares final.json and baseline_*.json)
Every episode present in both must have an identical action_sha256 (the policy is deterministic)."""
import json, sys
from pathlib import Path

fresh_dir = Path(sys.argv[1] if len(sys.argv) > 1 else 'results/repro')
bad = checked = 0
for name in ('final.json', 'baseline_greedy.json', 'baseline_no_asks.json', 'baseline_random.json'):
    f, c = fresh_dir / name, Path('results') / name
    if not f.exists():
        continue
    new = {(e['seed'], e['variant']): e for e in json.load(open(f))['episodes']}
    old = {(e['seed'], e['variant']): e for e in json.load(open(c))['episodes']}
    for key in sorted(new.keys() & old.keys()):
        checked += 1
        if new[key]['action_sha256'] != old[key]['action_sha256']:
            bad += 1; print('DIFFERENT', name, key)
print(f'{checked} episodes compared, {bad} different')
sys.exit(1 if bad or not checked else 0)
