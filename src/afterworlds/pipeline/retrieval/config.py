"""Retrieval Memory configuration — CRD Issue 18 / ADR-018.

Configuration is read from environment variables at call time via
``RetrievalMemoryConfig.from_env()``, matching the per-pass config convention
(see ``pipeline/writer/config.py``). No global singleton — callers construct
a config object and pass it into the write/query services.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

#: Chroma distance metric used for the story_memory collection. Fixed and
#: documented once here (ADR-018 D5 requires naming the metric once in the
#: collection-config code, not per query). "cosine" produces a distance in
#: [0, 2]; normalization to a [0, 1] similarity happens in the query path,
#: never by comparing this raw distance directly against the threshold.
STORY_MEMORY_DISTANCE_METRIC: str = "cosine"

#: Character ceiling for one story-memory chunk before paragraph-boundary
#: splitting (ADR-018 D3). Starting value per the ADR.
DEFAULT_CHUNK_CHAR_CEILING: int = 4000

#: Default number of results returned by a story-memory query (ADR-018 D5).
DEFAULT_TOP_K: int = 4

#: Default minimum normalized-similarity threshold (ADR-018 D5). Inclusive:
#: a result is retained when normalized_similarity >= this value.
DEFAULT_MINIMUM_SIMILARITY_THRESHOLD: float = 0.6

#: ChromaDB embedding model identifier for the local deterministic ONNX
#: MiniLM path (ADR-018 D4). Recorded per chunk and on the collection so a
#: model change is detectable and forces a full reindex.
DEFAULT_EMBEDDING_MODEL_ID: str = "chroma-onnx-minilm-l6-v2"

#: Default on-disk path for the embedded ChromaDB PersistentClient. ADR-018's
#: chromadb CVE-2026-45829 resolution requires embedded-client-only usage —
#: never chromadb.HttpClient / a standalone chromadb server process (see
#: RetrievalMemoryConfig docstring and pip-audit CI comment).
DEFAULT_PERSIST_DIRECTORY: str = ".chroma_data"


@dataclass
class RetrievalMemoryConfig:
    """Configuration for Retrieval Memory ingestion, query, and reindex.

    Attributes:
        top_k: number of story-memory results requested per query.
        minimum_similarity_threshold: inclusive (>=) cutoff applied to the
            normalized similarity, after mandatory story_id/eligibility
            metadata filters and before rendering into StablePrefix.
        chunk_char_ceiling: character ceiling for one story-memory chunk
            before paragraph-boundary splitting.
        embedding_model_id: identifier recorded per chunk and on the
            collection metadata. Changing this forces a full reindex.
        persist_directory: on-disk path for the embedded ChromaDB
            PersistentClient. Never used to construct an HttpClient.
        distance_metric: Chroma collection distance metric, fixed to
            ``STORY_MEMORY_DISTANCE_METRIC``.

    Security note (chromadb CVE-2026-45829 / PYSEC-2026-311): this config
    intentionally exposes no server-mode / trust_remote_code knobs. The
    vulnerability is a pre-auth code-injection path in chromadb's HTTP
    server component (``/api/v2/.../collections`` with an attacker-supplied
    model repository and ``trust_remote_code=True``). Afterworlds never runs
    a chromadb server process and never sets ``trust_remote_code=True`` on
    any embedding function — the embedded ``PersistentClient`` with the
    default local ONNX MiniLM embedding function never reaches that code
    path. See the CI pip-audit step and this PR's Architecture Notes for the
    full re-justification of the retained ``--ignore-vuln``.
    """

    top_k: int = DEFAULT_TOP_K
    minimum_similarity_threshold: float = DEFAULT_MINIMUM_SIMILARITY_THRESHOLD
    chunk_char_ceiling: int = DEFAULT_CHUNK_CHAR_CEILING
    embedding_model_id: str = DEFAULT_EMBEDDING_MODEL_ID
    persist_directory: str = DEFAULT_PERSIST_DIRECTORY
    distance_metric: str = STORY_MEMORY_DISTANCE_METRIC

    @classmethod
    def from_env(cls) -> RetrievalMemoryConfig:
        """Build a RetrievalMemoryConfig from environment variables.

        Environment variables:
            AFTERWORLDS_RETRIEVAL_TOP_K
            AFTERWORLDS_RETRIEVAL_MIN_SIMILARITY
            AFTERWORLDS_RETRIEVAL_CHUNK_CHAR_CEILING
            AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID
            AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY
        """
        return cls(
            top_k=int(
                os.environ.get("AFTERWORLDS_RETRIEVAL_TOP_K", str(DEFAULT_TOP_K))
            ),
            minimum_similarity_threshold=float(
                os.environ.get(
                    "AFTERWORLDS_RETRIEVAL_MIN_SIMILARITY",
                    str(DEFAULT_MINIMUM_SIMILARITY_THRESHOLD),
                )
            ),
            chunk_char_ceiling=int(
                os.environ.get(
                    "AFTERWORLDS_RETRIEVAL_CHUNK_CHAR_CEILING",
                    str(DEFAULT_CHUNK_CHAR_CEILING),
                )
            ),
            embedding_model_id=os.environ.get(
                "AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID",
                DEFAULT_EMBEDDING_MODEL_ID,
            ),
            persist_directory=os.environ.get(
                "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY",
                DEFAULT_PERSIST_DIRECTORY,
            ),
        )
