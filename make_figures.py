"""Draws the three report figures from numbers printed in REPORT.md (sections 5.2, 5.3, 6)."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

import json, sys
SCORES = [0.367, 0.367, 0.267, 0.183]  # replaced below from results/final.json and baselines when present
try:
    _s = lambda f: json.load(open(f))['summary']['primary_score']
    SCORES = [round(_s('results/final.json'), 3), round(_s('results/baseline_greedy.json'), 3), round(_s('results/baseline_random.json'), 3), round(_s('results/baseline_no_asks.json'), 3)]
except Exception:
    pass
# 1. Funnel (supplied greedy rule A, Round 1 confirmatory seeds): per episode of 200 members
steps = ['Introductions', 'Mutual acceptances', 'Dates', 'MSMI events']
vals = [73.5, 10.5, 8.3, 113 / 120]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.barh(steps[::-1], vals[::-1], color=['#c0504d', '#4f81bd', '#4f81bd', '#4f81bd'])
for i, v in enumerate(vals[::-1]): ax.text(v + 1, i, f'{v:.1f}', va='center')
ax.set_xlabel('Average per 200-member episode'); ax.set_title('Where introductions are lost (supplied greedy rule)')
plt.tight_layout(); plt.savefig('figures/funnel.png', dpi=200); plt.close()

# 2. Forest plot of paired contrasts on the primary score (section 5.2)
rows = [('C − A  targeted vs baseline asks', -0.054, -0.208, 0.100),
        ('Fg − C  learned values vs incumbent', 0.062, -0.058, 0.196),
        ('F − Fg  global vs greedy', -0.004, -0.104, 0.096),
        ('G − F  adaptive vs frozen', -0.029, -0.113, 0.046),
        ('S − C  scarcity matching vs incumbent', -0.075, -0.192, 0.046),
        ('O − C  oracle ranking vs incumbent', 0.017, -0.083, 0.121)]
fig, ax = plt.subplots(figsize=(6.8, 3.2))
for i, (n, m, lo, hi) in enumerate(rows[::-1]):
    ax.plot([lo, hi], [i, i], color='#4f81bd', lw=2); ax.plot(m, i, 'o', color='#1f3d6b')
ax.axvline(0, color='k', lw=0.8, ls='--'); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]])
ax.set_xlabel('Difference in primary score (MSMI per 100), 95% interval over 20 seeds')
ax.set_title('Every interval contains zero: no candidate beats another'); plt.tight_layout(); plt.savefig('figures/forest.png', dpi=200); plt.close()

# 3. Left: official evaluator scores (Table A). Right: targeted minus supplied asks, every fresh paired block (Table 4)
names = ['Submitted', 'Greedy', 'Random', 'No asks']; sc = SCORES
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.4), gridspec_kw={'width_ratios': [0.8, 1.4]})
axs[0].bar(names, sc, color=['#1f3d6b', '#8aa6c9', '#8aa6c9', '#8aa6c9']); axs[0].set_title('Official evaluator, seeds 101-105', fontsize=10)
axs[0].set_ylabel('Primary score (MSMI/100)'); axs[0].tick_params(axis='x', rotation=30)
blocks = [('106-125', -0.054, -0.208, 0.092), ('5001-5040', -0.098, -0.171, -0.025), ('401-440', -0.044, -0.123, 0.035),
          ('601-640', 0.052, None, None), ('801-840', 0.000, None, None), ('1101-1140', -0.140, None, None),
          ('1301-1340', -0.058, None, None), ('3201-3240', -0.035, -0.113, 0.048), ('Pooled (300 seeds)', -0.047, -0.078, -0.015)]
for i, (n, m_, lo, hi) in enumerate(blocks[::-1]):
    bold = n.startswith('Pooled')
    if lo is not None: axs[1].plot([lo, hi], [i, i], color='#c0504d' if bold else '#4f81bd', lw=2)
    axs[1].plot(m_, i, 'D' if bold else 'o', color='#8b1a1a' if bold else '#1f3d6b')
axs[1].axvline(0, color='k', lw=0.8, ls='--'); axs[1].set_yticks(range(len(blocks))); axs[1].set_yticklabels([b[0] for b in blocks[::-1]], fontsize=8)
axs[1].set_title('Targeted minus supplied asks (Table 4)', fontsize=10); axs[1].set_xlabel('Difference in primary score')
plt.tight_layout(); plt.savefig('figures/official.png', dpi=200); plt.close()
