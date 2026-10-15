"""Draws the three report figures from numbers printed in REPORT.md (sections 5.2, 5.3, 6)."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

# 1. Funnel (policy C, Round 1 confirmatory seeds): per episode of 200 members
steps = ['Introductions', 'Mutual acceptances', 'Dates', 'MSMI events']
vals = [74.3, 10.9, 8.2, 100 / 120]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.barh(steps[::-1], vals[::-1], color=['#c0504d', '#4f81bd', '#4f81bd', '#4f81bd'])
for i, v in enumerate(vals[::-1]): ax.text(v + 1, i, f'{v:.1f}', va='center')
ax.set_xlabel('Average per 200-member episode'); ax.set_title('Where introductions are lost (submitted policy)')
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

# 3. Official evaluator, seeds 101-105 (section 6)
names = ['Submitted', 'Greedy', 'Random', 'No asks']; sc = [0.517, 0.367, 0.267, 0.183]; cov = [0.352, 0.353, 0.356, 0.137]
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.8))
axs[0].bar(names, sc, color=['#1f3d6b', '#8aa6c9', '#8aa6c9', '#8aa6c9']); axs[0].set_title('Primary score (MSMI/100)')
axs[1].bar(names, cov, color=['#1f3d6b', '#8aa6c9', '#8aa6c9', '#8aa6c9']); axs[1].set_title('Coverage')
for a in axs: a.tick_params(axis='x', rotation=25)
plt.tight_layout(); plt.savefig('figures/official.png', dpi=200); plt.close()
