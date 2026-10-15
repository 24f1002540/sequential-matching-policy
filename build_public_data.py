"""Rebuild the fully synthetic public snapshot dataset in a new output folder."""
import argparse
import csv
import hashlib
from pathlib import Path
from kit import VERSION, SOFT, generate, rollout, dump_json, dump_lines

def questionnaire(m):
    f=m['fields'];q={k:f[k] for k in SOFT if f[k] is not None}
    # Only current observations appear; unknowns are omitted, never filled from truth.
    mapping={'relationship_structure':{'monogamous':'Monogamous','non_monogamous':'Ethically non-monogamous'},
             'smoking':{'no':'No','yes':'Yes','occasionally':'Occasionally'},
             'partner_smoking':{'no_smoking':'Not compatible for me','any':'Open to it'},
             'partner_children':{'no_children':'Prefer not to','any':'Open to it'},
             'wants_children':{'yes':'I would like children','no':'I do not want children','unsure':'Unsure'}}
    for k,mp in mapping.items():
        if f[k] is not None:q[k]=mp[f[k]]
    if f['has_children'] is not None:q['has_children']='Yes' if f['has_children'] else 'No'
    if f['who_to_meet'] is not None:q['who_to_meet']=', '.join({'man':'men','woman':'women','non_binary':'non-binary people'}[g] for g in f['who_to_meet'])
    if f['age_min'] is not None and f['age_max'] is not None:q['age_range']=f"{f['age_min']}-{f['age_max']}"
    if f['schedule'] is not None:q['schedule']=', '.join(f['schedule'])
    q['location']=m['zone'];q['gender']=m['gender']
    return {'member_id':m['member_id'],'synthetic':True,'age':m['age'],'gender':m['gender'],'city':m['zone'],'questionnaire_answers':q}

def conversation(m):
    f=m['fields'];msgs=[]
    prompts={'relationship_goal':'What are you hoping to find?', 'relationship_pace':'What pace feels comfortable?',
             'lifestyle':'How do you tend to spend free time?','conversations':'What kinds of conversation do you enjoy?'}
    answers={'long_term':'I would like to build a lasting relationship.','exploring':'I am still working out what I want.',
             'slow':'I prefer to get to know someone gradually.','steady':'A steady pace suits me.','quick':'I am comfortable meeting fairly soon.',
             'quiet':'I usually prefer a quiet evening.','mixed':'I like a mixture of quiet time and seeing people.','social':'I enjoy having plans with people.',
             'ideas':'I enjoy talking about ideas.','stories':'I like hearing the stories behind things.','practical':'I enjoy working through practical questions.','playful':'I like a playful conversation.'}
    for k,p in prompts.items():
        if f[k] is not None:msgs += [{'role':'assistant','content':p},{'role':'user','content':answers[f[k]]}]
    return {'member_id':m['member_id'],'synthetic':True,'style':'authored_templates_not_real_transcripts',
            'observed_day':30,'messages':msgs}


def build(output):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    pools = []
    for index in range(10):
        pool = f'public_{index + 1:02d}'
        seed = 20261000 + index
        state = rollout(generate(seed, 200, pool), 30).observe()
        target = root / 'data' / pool
        dump_json(target / 'state.json', state)
        dump_lines(target / 'members.jsonl', state['members'])
        dump_lines(target / 'introductions.jsonl', state['introductions'])
        dump_lines(target / 'feedback.jsonl', state['feedback'])
        dump_lines(target / 'questionnaires.jsonl', [questionnaire(m) for m in state['members']])
        dump_lines(target / 'conversations.jsonl', [conversation(m) for m in state['members'] if conversation(m)['messages']])
        with (target / 'members_flat.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['member_id', 'pool_id', 'age', 'gender', 'zone', 'available'] + SOFT, lineterminator='\n')
            writer.writeheader()
            writer.writerows({**{k: m[k] for k in ['member_id', 'pool_id', 'age', 'gender', 'zone', 'available']}, **{k: m['fields'][k] for k in SOFT}} for m in state['members'])
        pools.append(dict(pool_id=pool, seed=seed, members=len(state['members']), introductions=len(state['introductions']), feedback_events=len(state['feedback']), snapshot_day=30))
    dump_json(root / 'data_manifest.json', {'schema_version': VERSION, 'synthetic': True, 'status': 'participant_release', 'pools': pools,
        'splits': {'train': [p['pool_id'] for p in pools[:6]], 'validation': [p['pool_id'] for p in pools[6:8]], 'development_test': [p['pool_id'] for p in pools[8:]]}})
    checks = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root / 'data').rglob('*')) if p.is_file()}
    checks['data_manifest.json'] = hashlib.sha256((root / 'data_manifest.json').read_bytes()).hexdigest()
    dump_json(root / 'data_checksums.json', checks)
    print('Generated ten synthetic public pools. No real records or private worlds were used.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, help='New directory; existing directories are never overwritten')
    build(parser.parse_args().output)
