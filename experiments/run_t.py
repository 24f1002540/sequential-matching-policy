import sys, json, time
import run_eval2
from t_arm import completion_asks
from kit import baseline_match
run_eval2.ARMS['T_completion'] = (completion_asks, baseline_match)
out = sys.argv[1]; seeds = [int(s) for s in sys.argv[2].split(',')]; variants = sys.argv[3].split(',')
for s in seeds:
    for v in variants:
        t = time.time(); r = run_eval2.run('T_completion', s, v); r['secs'] = round(time.time() - t, 1)
        open(out, 'a').write(json.dumps(r) + '\n'); print(s, v, r['assignments'], r['mutual_acceptances'], r['dates'], r['mutual_second_meeting_intention'], r['ask_cost'], r['secs'], flush=True)
