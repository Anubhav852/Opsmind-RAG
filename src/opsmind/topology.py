SERVICES = ["web", "checkout", "payments", "inventory", "auth", "postgres-main",
            "redis-cache", "notifications", "analytics"]
# (src, dst) means src DEPENDS_ON dst
EDGES = [("web", "checkout"), ("web", "auth"), ("checkout", "payments"), ("checkout", "inventory"),
         ("checkout", "redis-cache"), ("payments", "postgres-main"), ("inventory", "postgres-main"),
         ("notifications", "payments"), ("analytics", "postgres-main")]
ROOT_CANDIDATES = ["payments", "inventory", "postgres-main", "auth", "redis-cache"]
