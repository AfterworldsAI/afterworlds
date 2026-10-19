"""Provision shared Rules authority into a remote deployment (#205, ADR-021 D7).

A fresh remote deployment starts without Rules Package data; this is the
supported, coordinated way to give it the qualified shared Rules authority::

    python -m afterworlds.remote.rules_provisioning

It runs only the existing production publication owners, unchanged and in
their documented order -- the same sequence the backend product proofs and
the RPG E2E store use:

1. :func:`~afterworlds.ingestion.corpus.persistence.finalize_source_release`
   for the source corpus built from the pinned, qualified source -- the source
   checkout's, or an installation's operator-supplied `--source-root` (it
   proves source completeness and refuses a stale or swapped candidate; the
   candidate must match a committed accepted oracle before anything publishes);
2. the committed accepted oracle for that release, persisted as a draft and
   published through
   :func:`~afterworlds.ingestion.mechanical.publication.publish_from_committed_oracle`
   (the only supported publication entry; no caller-chosen oracle).

Coordination: it holds both store locks and requires the content, control and
vector stores to belong to this deployment (``maintenance_locks``), refuses
while a restore is pending, and writes only shared Rules authority: the Rules
SQL tables and the Rules corpus collection of the bound vector store. It never
touches Story memory, accounts or Story data, imports nothing local, and
creates no new Rules authority. Re-running is an idempotent no-op (the owners'
verified-reuse and already-published paths). Running it against a real
deployment is an Owner-controlled activation step, not part of #205.
"""

from __future__ import annotations

import argparse
import gc
import sys
from dataclasses import dataclass
from pathlib import Path

from chromadb.api import ClientAPI
from chromadb.api.shared_system_client import SharedSystemClient
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.config import load_settings
from afterworlds.ingestion.corpus.pdf_source import PDF_REPO_PATH
from afterworlds.ingestion.corpus.persistence import finalize_source_release
from afterworlds.ingestion.corpus.pipeline import build_source_candidate
from afterworlds.ingestion.corpus.source_ledger import SourceInputError
from afterworlds.ingestion.mechanical.oracle import (
    candidate_from_accepted_inputs,
    committed_inputs_for,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    publish_from_committed_oracle,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import RetrievalEmbeddingFunction
from afterworlds.remote.control_store import (
    ControlStoreUnavailable,
    connect_control_store,
    iso,
    utc_now,
)
from afterworlds.remote.storage import (
    StoreRefused,
    maintenance_locks,
    pending_restores,
    refuse_store_aliasing,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def default_source_root() -> Path | None:
    """The source checkout holding the qualified Rules inputs, when this
    module runs from one; an installed distribution has none (pass
    ``--source-root``)."""
    if (REPO_ROOT / "pyproject.toml").is_file() and (
        REPO_ROOT / PDF_REPO_PATH
    ).is_file():
        return REPO_ROOT
    return None


_OK = frozenset({PublicationOutcome.PUBLISHED, PublicationOutcome.ALREADY_PUBLISHED})


@dataclass(frozen=True)
class ProvisionResult:
    package_uuid: str
    release_version: str
    corpus_reused: bool
    authority_outcome: PublicationOutcome


def _embedding_function() -> RetrievalEmbeddingFunction | None:
    """The production embedding (``None`` = the configured default)."""
    return None


def provision_shared_rules(
    content: sessionmaker[Session],
    chroma_client: ClientAPI,
    *,
    retrieval_config: RetrievalMemoryConfig,
    now: str,
    embedding_function: RetrievalEmbeddingFunction | None = None,
    source_root: Path | None = None,
) -> ProvisionResult:
    """Run the publication owners for the qualified shared release. The caller
    holds the deployment's maintenance locks.

    *source_root* supplies the qualified inputs (official PDF, pinned
    snapshot); it cannot choose the authority: the candidate built from it
    must match a committed accepted oracle shipped with this release, checked
    before anything is published."""
    root = source_root or default_source_root()
    if root is None:
        raise StoreRefused(
            "no qualified Rules inputs are installed; pass --source-root"
        )
    try:
        candidate = build_source_candidate(root, retrieval_config=retrieval_config)
    except (SourceInputError, OSError):
        raise StoreRefused(
            "the Rules inputs are missing or not the qualified ones"
        ) from None
    inputs = committed_inputs_for(candidate.package_uuid, candidate.release_version)
    if inputs is None:
        raise StoreRefused("no committed accepted oracle exists for this release")
    with content() as session:
        finalized = finalize_source_release(
            session,
            candidate,
            now=now,
            chroma_client=chroma_client,
            retrieval_config=retrieval_config,
            embedding_function=embedding_function,
        )
    if not finalized.published:
        raise StoreRefused(f"the source release was not published: {finalized.gate}")
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    with content() as session:
        if session.get(MechanicalProjectionORM, identified.projection_uuid) is None:
            persist_draft(session, identified, now=now)
            record_persisted_state_digest(session, identified.projection_uuid)
            session.commit()
        published = publish_from_committed_oracle(
            session, identified.projection_uuid, now=now
        )
        session.commit()
    if published.outcome not in _OK:
        raise StoreRefused(f"the accepted authority was not published: {published}")
    return ProvisionResult(
        package_uuid=candidate.package_uuid,
        release_version=candidate.release_version,
        corpus_reused=finalized.reused,
        authority_outcome=published.outcome,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Directory holding the qualified Rules inputs (official PDF and "
        "pinned snapshot) when the installation has none.",
    )
    args = parser.parse_args(argv)
    settings = load_settings()
    if settings.deployment != "remote" or settings.control_database_url is None:
        parser.error("requires AFTERWORLDS_DEPLOYMENT=remote and a control store")
    try:
        refuse_store_aliasing(settings.database_url, settings.control_database_url)
    except StoreRefused as exc:
        print(f"provisioning refused: {exc}", file=sys.stderr)
        return 1
    try:
        control = connect_control_store(settings.control_database_url)  # no DDL
    except ControlStoreUnavailable as exc:
        print(f"provisioning refused: {exc}", file=sys.stderr)
        return 1
    config = RetrievalMemoryConfig.from_env()
    try:
        with maintenance_locks(
            settings.database_url, Path(config.persist_directory), control
        ):
            if pending_restores(control):
                raise StoreRefused("a restore is pending")
            engine = create_engine(settings.database_url)
            try:
                result = provision_shared_rules(
                    create_session_factory(engine),
                    build_chroma_client(config),
                    retrieval_config=config,
                    now=iso(utc_now()),
                    embedding_function=_embedding_function(),
                    source_root=args.source_root,
                )
            finally:
                engine.dispose()
                SharedSystemClient.clear_system_cache()
                gc.collect()
    except StoreRefused as exc:
        print(f"provisioning refused: {exc}", file=sys.stderr)
        return 1
    print(
        f"rules {result.package_uuid} release {result.release_version}: "
        f"corpus {'reused' if result.corpus_reused else 'published'}, "
        f"authority {result.authority_outcome.value}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
