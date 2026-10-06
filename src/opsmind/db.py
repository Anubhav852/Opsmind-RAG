from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

_pool = ConnectionPool(settings.database_url, min_size=1, max_size=10, open=False,
                       configure=lambda c: register_vector(c))


@contextmanager
def conn():
    if _pool.closed:
        _pool.open()
    with _pool.connection() as c:      # commits on clean exit, rolls back on error
        c.row_factory = dict_row
        yield c
