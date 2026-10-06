ALIASES = {
    "payments": ["payments-svc", "payment_service", "payment-service"],
    "checkout": ["checkout-svc", "checkout_service"],
    "inventory": ["inventory-svc"],
    "auth": ["auth-service"],
    "postgres-main": ["postgres", "pg-main"],
    "redis-cache": ["redis"],
    "notifications": ["notify-svc"],
    "web": ["web-frontend"],
    "analytics": ["analytics-svc"],
}


class UnionFind:
    """Disjoint sets with path compression. Near O(alpha(n)) per op."""

    def __init__(self):
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra          # `a` side stays the canonical root


_uf = UnionFind()
for canon, alts in ALIASES.items():
    for alt in alts:
        _uf.union(canon, alt)


def canonical_service(name: str) -> str:
    n = name.strip().lower()
    return _uf.find(n) if n in _uf.parent else n
