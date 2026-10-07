from functools import lru_cache

import numpy as np

from .config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embed_model)


def embed(texts: list[str], batch_size: int = 64) -> np.ndarray:
    return _model().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                           convert_to_numpy=True).astype(np.float32)
