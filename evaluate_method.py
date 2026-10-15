"""Run the SUBMITTED policy (no --baseline argument) through the supplied evaluator's episode runner.
Identical to evaluate.py except for the command line used to launch policy.py."""
import argparse, json, sys
from pathlib import Path
import evaluate as ev
from kit import generate, VERSION

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--policy', default='policy.py')
    p.add_argument('--seeds', default='101'); p.add_argument('--variants', default='development')
    p.add_argument('--output', default='results/final.json')
    a = p.parse_args()
    seeds = [int(s) for s in a.seeds.split(',')]
    variants = list(ev.VARIANTS) if a.variants == 'all' else a.variants.split(',')
    command = [sys.executable, a.policy]
    rows = []
    for v in variants:
        for s in seeds:
            try:
                row = ev.episode(generate(s, 200, 'evaluation', v), command)
            except (ValueError, TypeError, KeyError, OSError) as e:
                row = {'valid': False, 'error': str(e)}
            row.update(seed=s, variant=v); rows.append(row)
            print(json.dumps({'seed': s, 'variant': v, 'valid': row['valid'], 'msmi': row.get('mutual_second_meeting_intention')}), flush=True)
    summary = ev.summarise(rows)
    out = {'release': VERSION, 'mode': 'trusted_local', 'decision_days': 60, 'follow_up_days': 40, 'members_per_episode': 200,
           'episodes': rows, 'summary': summary}
    t = Path(a.output); t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n'); print(json.dumps(summary, indent=2))
    return 0 if summary['eligible'] else 2
if __name__ == '__main__':
    raise SystemExit(main())
