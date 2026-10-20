
"""Multilingual comment embedding engine."""

from functools import lru_cache

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "BAAI/bge-m3"


@lru_cache(maxsize=1)
def load_embedding_model(model_name=DEFAULT_MODEL):
    """Load the embedding model once per Python process."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    return SentenceTransformer(
        model_name,
        device=device
    )


def generate_embeddings(
    comments,
    model_name=DEFAULT_MODEL,
    batch_size=8
):
    """
    Convert comment texts into normalized embeddings.

    Parameters
    ----------
    comments : list[str]
        Comment texts in the intended analysis order.
    model_name : str
        SentenceTransformer model identifier.
    batch_size : int
        Number of comments encoded per batch.

    Returns
    -------
    numpy.ndarray
        Shape: (number_of_comments, embedding_dimension)
    """

    if not comments:
        raise ValueError("Comment list cannot be empty.")

    if batch_size < 1:
        raise ValueError("batch_size must be positive.")

    if any(
        not isinstance(text, str) or not text.strip()
        for text in comments
    ):
        raise ValueError("All comments must be non-empty strings.")

    model = load_embedding_model(model_name)

    embeddings = model.encode(
        comments,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(embeddings)

    if not np.isfinite(embeddings).all():
        raise ValueError("Non-finite values found in embeddings.")

    return embeddings
