import time
import uuid

import redis

from ..config import settings

_r = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def allow(key: str, limit: int, window_s: int = 60) -> bool:
    now = time.time()
    pipe = _r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_s)
    pipe.zadd(key, {f"{now}-{uuid.uuid4()}": now})
    pipe.zcard(key)
    pipe.expire(key, window_s)
    _, _, count, _ = pipe.execute()
    return count <= limit
