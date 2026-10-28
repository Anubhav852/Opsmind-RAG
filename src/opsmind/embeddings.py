from functools import lru_cache

import numpy as np

from .config import settings


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=settings.embed_model)


def embed(texts: list[str], batch_size: int = 64) -> np.ndarray:
    vecs = np.array(list(_model().embed(texts, batch_size=batch_size)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.clip(norms, 1e-12, None)