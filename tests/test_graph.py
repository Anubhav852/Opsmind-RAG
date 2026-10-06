from datetime import datetime, timedelta, timezone

from opsmind.graph.entity_resolution import canonical_service
from opsmind.graph.temporal_graph import build_graph, cluster_alerts, dependents, recovery_order, upstream
from opsmind.topology import EDGES


def test_aliases_resolve():
    assert canonical_service("Payment_Service") == "payments"
    assert canonical_service("pg-main") == "postgres-main"
    assert canonical_service("unknown-thing") == "unknown-thing"


def test_upstream_and_dependents():
    g = build_graph(EDGES)
    assert set(upstream(g, "checkout")) == {"payments", "inventory", "redis-cache", "postgres-main"}
    assert "web" in dependents(g, "payments")
    assert upstream(g, "checkout")["postgres-main"] == 2


def test_recovery_order_puts_dependencies_first():
    order = recovery_order(build_graph(EDGES))
    assert order.index("postgres-main") < order.index("payments") < order.index("checkout")


def test_alert_clustering():
    g = build_graph(EDGES)
    t = datetime(2025, 1, 1, tzinfo=timezone.utc)
    alerts = [{"service": "checkout", "ts": t}, {"service": "payments", "ts": t + timedelta(minutes=2)},
              {"service": "auth", "ts": t + timedelta(days=1)}]
    clusters = cluster_alerts(alerts, g)
    assert sorted(len(c) for c in clusters) == [1, 2]
