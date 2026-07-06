"""ChromaDB client construction — CRD Issue 18 / ADR-018.

Single choke point for constructing a Chroma client. Always an embedded
client (``PersistentClient``/``EphemeralClient``) — never ``HttpClient`` /
a standalone ``chromadb run`` server process. This is the safe-deployment-
path resolution for chromadb CVE-2026-45829 (PYSEC-2026-311): that
vulnerability is a pre-auth code-injection path in chromadb's HTTP server
component (``/api/v2/.../collections`` with an attacker-controlled model
repository and ``trust_remote_code=True``). Afterworlds never runs that
server component and never sets ``trust_remote_code=True`` anywhere, so the
vulnerable code path is never reached. See this PR's Architecture Notes and
the CI pip-audit step for the full re-justification.
"""

from __future__ import annotations

from chromadb import EphemeralClient, PersistentClient
from chromadb.api import ClientAPI

from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig


def build_chroma_client(config: RetrievalMemoryConfig) -> ClientAPI:
    """Return an embedded ChromaDB client per *config*.

    Always ``PersistentClient`` — durable, local, on-disk. Never
    ``HttpClient``. Use :func:`build_ephemeral_chroma_client` for tests that
    need a throwaway in-memory client.
    """
    return PersistentClient(path=config.persist_directory)


def build_ephemeral_chroma_client() -> ClientAPI:
    """Return an in-memory ChromaDB client for tests.

    ChromaDB's ephemeral backend shares process-level state across separate
    ``EphemeralClient()`` instances when no explicit path is given (verified
    empirically against the pinned chromadb version) — two calls in the same
    test process can observe each other's collections. Tests that need
    isolation between runs (e.g. differing embedding-vector dimensions
    against the same collection name) must use
    :func:`build_isolated_test_chroma_client` instead.
    """
    return EphemeralClient()


def build_isolated_test_chroma_client(path: str) -> ClientAPI:
    """Return a fully isolated on-disk client rooted at *path* for tests.

    Use with pytest's ``tmp_path`` fixture (a fresh directory per test) to
    guarantee no shared state between tests, unlike
    :func:`build_ephemeral_chroma_client`.
    """
    return PersistentClient(path=path)
