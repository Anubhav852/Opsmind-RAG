from collections import deque
from datetime import datetime

import networkx as nx

from ..db import conn
from .entity_resolution import UnionFind


def build_graph(edges: list[tuple[str, str]]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_edges_from(edges)
    return g


def load_graph(at: datetime) -> nx.DiGraph:
    """The dependency graph as it was at time `at` (edges carry valid_from / valid_to)."""
    with conn() as c:
        rows = c.execute(
            "SELECT src, dst FROM edges WHERE rel='DEPENDS_ON' AND valid_from <= %s "
            "AND (valid_to IS NULL OR valid_to > %s)", (at, at)).fetchall()
    return build_graph([(r["src"], r["dst"]) for r in rows])


def bfs_distances(g: nx.DiGraph, start: str, reverse: bool = False) -> dict[str, int]:
    """O(V+E). reverse=False follows 'depends on'; reverse=True follows 'is depended on by'."""
    nxt = g.predecessors if reverse else g.successors
    if start not in g:
        return {start: 0}
    dist, q = {start: 0}, deque([start])
    while q:
        u = q.popleft()
        for v in nxt(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def upstream(g: nx.DiGraph, svc: str) -> dict[str, int]:
    d = bfs_distances(g, svc)
    d.pop(svc, None)
    return d


def dependents(g: nx.DiGraph, svc: str) -> dict[str, int]:
    d = bfs_distances(g, svc, reverse=True)
    d.pop(svc, None)
    return d


def recovery_order(g: nx.DiGraph) -> list[str]:
    """Restart dependencies first: reverse topological order."""
    return list(reversed(list(nx.topological_sort(g))))


def cluster_alerts(alerts: list[dict], g: nx.DiGraph, window_s: int = 600) -> list[list[dict]]:
    """Group alerts that are close in time AND on related services (one is reachable from the other).
    O(n^2) pairwise + Union-Find; fine for per-incident volumes."""
    alerts = sorted(alerts, key=lambda a: a["ts"])
    uf = UnionFind()
    for i in range(len(alerts)):
        uf.find(str(i))
        for j in range(i + 1, len(alerts)):
            if (alerts[j]["ts"] - alerts[i]["ts"]).total_seconds() > window_s:
                break
            a, b = alerts[i]["service"], alerts[j]["service"]
            related = a == b or (a in g and b in g and (nx.has_path(g, a, b) or nx.has_path(g, b, a)))
            if related:
                uf.union(str(i), str(j))
    groups: dict[str, list[dict]] = {}
    for i, a in enumerate(alerts):
        groups.setdefault(uf.find(str(i)), []).append(a)
    return list(groups.values())
