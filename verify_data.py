"""Verify release data checksums, synthetic provenance and observation boundaries."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def verify():
    checksums = json.loads((ROOT / 'data_checksums.json').read_text())
    for name, expected in checksums.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    manifest = json.loads((ROOT / 'data_manifest.json').read_text())
    pools = [pool for split in manifest['splits'].values() for pool in split]
    assert len(pools) == len(set(pools)) == 10
    counts = dict(members=0, introductions=0, feedback=0, conversations=0)
    forbidden = {'truth', 'bias', 'second_bias', 'response_rate', 'exit_day', 'email', 'phone', 'full_name'}
    for pool in pools:
        folder = ROOT / 'data' / pool
        state = json.loads((folder / 'state.json').read_text())
        assert state['synthetic'] is True and state['schema_version'] == '1.0.0'
        for member in state['members']:
            assert member['synthetic'] is True and member['age'] >= 18
            assert not forbidden.intersection(member)
            assert member['arrived_day'] <= state['day']
            assert all(day is None or day <= state['day'] for day in member['field_observed_day'].values())
        assert all(event['observed_day'] <= state['day'] for event in state['feedback'])
        for table in counts:
            counts[table] += sum(1 for line in (folder / (table + '.jsonl')).read_text().splitlines() if line)
    assert counts == {'members': 2000, 'introductions': 613, 'feedback': 1270, 'conversations': 1129}, counts
    print(json.dumps({'verified': True, 'counts': counts, 'files': len(checksums)}, indent=2))

if __name__ == '__main__':
    verify()
