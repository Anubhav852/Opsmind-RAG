import os
import threading
import time
from collections import defaultdict, deque

import redis

from ..config import settings

_r = None
_redis_down_until = 0.0
_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def _client():
    global _r
    if _r is None:
        _r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    return _r


def _allow_redis(key: str, limit: int, window: int) -> bool:
    now = time.time()
    pipe = _client().pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}:{os.urandom(4).hex()}": now})
    pipe.zcard(key)
    pipe.expire(key, window)
    _, _, count, _ = pipe.execute()
    return count <= limit


def _allow_memory(key: str, limit: int, window: int) -> bool:
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window:
            q.popleft()
        q.append(now)
        return len(q) <= limit


def allow(key: str, limit: int, window: int) -> bool:
    """Sliding-window limiter. Uses Redis when reachable, else an in-process fallback."""
    global _redis_down_until
    if time.time() >= _redis_down_until:
        try:
            return _allow_redis(key, limit, window)
        except Exception:
            _redis_down_until = time.time() + 30  # skip Redis for 30s, then retry
    return _allow_memory(key, limit, window)