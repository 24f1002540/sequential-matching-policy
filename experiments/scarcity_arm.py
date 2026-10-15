import networkx as nx
from collections import Counter
from smp_core import feasible_edges
from pilot_policy import sim_score
def scarcity_match(state):
    edges = feasible_edges(state); deg = Counter()
    for a, b, _ in edges: deg[a['member_id']] += 1; deg[b['member_id']] += 1
    G = nx.Graph()
    for a, b, _ in edges:
        G.add_edge(a['member_id'], b['member_id'], weight=1.0 / deg[a['member_id']] + 1.0 / deg[b['member_id']] + 0.01 * sim_score(a, b))
    return sorted(sorted(p) for p in nx.max_weight_matching(G, maxcardinality=True))
