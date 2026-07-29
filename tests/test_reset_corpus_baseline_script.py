"""Tests for scripts/reset_corpus_baseline.py — CRD Issue 5c (#132), PR #134 R19–R22.

One destructive command, one recurring defect family across four review rounds:
*acting before proving the precondition for acting*. These tests pin each half of
what the command must establish before it deletes anything —

* R19: the operator-facing configuration name is the one the code actually reads
  (``RetrievalMemoryConfig.from_env()`` reads
  ``AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY``; the documented short name was never
  read, so the documented command could reset the default store). Corrected,
  deliberately not aliased.
* R20: the operator is told the full-store reset also deletes ``story_memory`` and
  does not restore it — before the deletion, not after.
* R21: the SQLite rebuild source is reachable, compatible, and holds published
  releases.
* R22: those releases' actual chunk payloads are fully loaded and valid.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import text as sa_text

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.corpus  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.retrieval  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.ingestion.corpus.source_completeness import EXPECTED_PAGE_COUNT
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import (
    CorpusProjectionORM,
    CorpusReleaseORM,
    LedgerLeafORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.config import DEFAULT_PERSIST_DIRECTORY
from tests.persistence.conftest import make_story

CANONICAL_ENV = "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"
MISTAKEN_ENV = "AFTERWORLDS_RETRIEVAL_PERSIST_DIR"

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "reset_corpus_baseline.py"
)


def _load_script():  # type: ignore[no-untyped-def]
    """Import scripts/reset_corpus_baseline.py as a module (scripts/ is not a
    package). Cached in sys.modules so repeated calls don't re-exec it."""
    module_name = "reset_corpus_baseline_script_under_test"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _empty_db_url(tmp_path) -> str:  # type: ignore[no-untyped-def]
    """A real, schema-created SQLite DB with no published release — reachable and
    migrated, but with nothing to rebuild the rules corpus from."""
    db_path = tmp_path / "baseline.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    return url


_PUBLISHED_PKG = "11111111-1111-4111-8111-111111111111"
_DRAFT_PKG = "22222222-2222-4222-8222-222222222222"


def _seeded_db_url(tmp_path) -> str:  # type: ignore[no-untyped-def]
    """A DB holding one published + one draft corpus release and a real story, so
    the rebuild loop's selectivity and its indifference to stories are both
    observable."""
    db_path = tmp_path / "seeded.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    now = "2026-07-28T00:00:00Z"
    with factory() as session:
        statuses = ((_PUBLISHED_PKG, "published"), (_DRAFT_PKG, "draft"))
        for pkg, status in statuses:
            session.add(
                RulesPackageORM(
                    rules_package_id=pkg,
                    name=f"pkg-{status}",
                    system="dnd5e",
                    version="1.0.0",
                    is_enabled=True,
                    publication_status=status,
                    created_at=now,
                    updated_at=now,
                )
            )
        session.flush()  # packages must exist before the FK-referencing releases
        for pkg, status in statuses:
            session.add(
                CorpusReleaseORM(
                    package_uuid=pkg,
                    release_version="1.0.0",
                    authoritative_source_hash="a" * 64,
                    transform_config_hash="b" * 64,
                    bundle_root_hash="c" * 64,
                    ledger_hash="d" * 64,
                    policy_hash="e" * 64,
                    reconciliation_hash="f" * 64,
                    transform_config={},
                    publication_status=status,
                    created_at=now,
                )
            )
        # A published corpus release is an identity; the rebuild reads a payload.
        # Only the published package gets a complete, valid one.
        _seed_payload(session, _PUBLISHED_PKG, now)
        create_story(session, make_story())
        session.commit()
    engine.dispose()
    return url


def _seed_payload(session, pkg, now, *, chunk_count=2):  # type: ignore[no-untyped-def]
    """Seed a payload that satisfies Issue 5c's persisted-state requirements:
    the single authoritative source (``source_id == package_uuid``, expected
    metadata, enabled), enabled chunks all assigned to it, a declared projection
    per chunk so runtime membership coincides, and ledger coverage of every
    authoritative page."""
    session.add(
        RuleSourceORM(
            rules_package_id=pkg,
            source_id=pkg,
            name="SRD 5.2.1",
            category="core_rulebook",
            precedence_rank=1,
            is_enabled=True,
            created_at=now,
        )
    )
    session.flush()
    for i in range(chunk_count):
        chunk_id = f"{i:08d}-0000-4000-8000-000000000000"
        session.add(
            RuleChunkORM(
                chunk_id=chunk_id,
                rules_package_id=pkg,
                source_id=pkg,
                subsystem="general",
                content=f"chunk {i}",
                source_document="SRD 5.2.1",
                source_locator_type="page",
                source_locator_value=str(i + 1),
                is_enabled=True,
                created_at=now,
            )
        )
        session.add(
            CorpusProjectionORM(
                package_uuid=pkg,
                projection_id=f"proj-{i}",
                leaf_id=f"leaf-{i}",
                chunk_id=chunk_id,
                role="primary",
                cover_start=0,
                cover_end=7,
            )
        )
    session.flush()
    session.add_all(
        LedgerLeafORM(
            package_uuid=pkg,
            leaf_id=f"leaf-page-{page}",
            printed_page=page,
            page_index=page - 1,
            leaf_type="paragraph",
            content=f"page {page}",
            char_start=0,
            char_end=6,
            occurrence_index=0,
            container_path=[],
            disposition="represented",
        )
        for page in range(1, EXPECTED_PAGE_COUNT + 1)
    )


class _Client:
    """Stand-in for the constructed Chroma client (identity is what matters)."""


def _arm(  # type: ignore[no-untyped-def]
    script, monkeypatch, tmp_path, stub_resolver=True, db_url=None
):
    """Arm main() with the *destructive* steps (client construction + store reset)
    and the rebuild recorded instead of performed, and return the trace dict.

    The resolver is real unless stubbed, so a test can prove the configured target
    genuinely validates. *db_url* defaults to a seeded (valid) DB — the rebuild
    source must be usable or the command now refuses to touch Chroma at all.
    Does not run main(); callers assert on its exit code themselves.
    """
    seen: dict[str, object] = {}
    # Ordered trace of what the operator sees vs. what is destroyed, so a test can
    # assert the warning precedes the deletion rather than merely co-occurring.
    events: list[str] = []
    seen["events"] = events
    reindexed: list[str] = []
    seen["reindexed"] = reindexed

    def recording_print(*args, **kwargs):  # type: ignore[no-untyped-def]
        events.append("print: " + " ".join(str(a) for a in args))
        print(*args, **kwargs)

    def fake_resolve(persist_directory):  # type: ignore[no-untyped-def]
        seen["resolved_from"] = persist_directory
        return Path(persist_directory)

    def fake_build_client(config):  # type: ignore[no-untyped-def]
        events.append("CLIENT")
        seen["client_config"] = config
        return _Client()

    def fake_reset(client):  # type: ignore[no-untyped-def]
        events.append("RESET")
        seen["reset_client"] = client
        return []

    class _Service:
        def __init__(self, client, config):  # type: ignore[no-untyped-def]
            pass

        def reindex_from_sql(self, session, pkg):  # type: ignore[no-untyped-def]
            reindexed.append(str(pkg))
            return 7

    # The script's module globals shadow the builtin, so this captures its prints
    # in order without suppressing them.
    monkeypatch.setattr(script, "print", recording_print, raising=False)
    if stub_resolver:
        monkeypatch.setattr(script, "resolve_reset_target", fake_resolve)
    monkeypatch.setattr(script, "build_chroma_client", fake_build_client)
    monkeypatch.setattr(script, "reset_chroma_store", fake_reset)
    monkeypatch.setattr(script, "RulesCorpusService", _Service)
    monkeypatch.setattr(
        sys,
        "argv",
        ["reset_corpus_baseline.py", "--db-url", db_url or _seeded_db_url(tmp_path)],
    )
    return seen


def _run_main(  # type: ignore[no-untyped-def]
    script, monkeypatch, tmp_path, stub_resolver=True, db_url=None
):
    """:func:`_arm` plus a successful run."""
    seen = _arm(script, monkeypatch, tmp_path, stub_resolver, db_url)
    assert script.main() == 0
    return seen


def test_canonical_env_var_selects_the_validated_and_reset_target(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The variable the script documents is the variable that steers the reset:
    the exact configured directory is what the REAL guard validates AND what the
    client the reset runs against is built from — one target, no divergence."""
    script = _load_script()
    target = tmp_path / "isolated_chroma"
    monkeypatch.setenv(CANONICAL_ENV, str(target))

    seen = _run_main(script, monkeypatch, tmp_path, stub_resolver=False)

    # The real resolve_reset_target accepted exactly this target (it would have
    # raised ResetTargetError otherwise) and reports it before anything destructive.
    assert f"Chroma target validated: {target.resolve()}" in capsys.readouterr().out
    assert seen["client_config"].persist_directory == str(target)  # type: ignore[union-attr]
    assert seen["reset_client"] is not None


def test_mistaken_short_name_is_not_an_alias(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The erroneous spelling is corrected, not supported: exporting it alone must
    not redirect the destructive reset (it is simply ignored, as it always was)."""
    script = _load_script()
    monkeypatch.delenv(CANONICAL_ENV, raising=False)
    monkeypatch.setenv(MISTAKEN_ENV, str(tmp_path / "decoy_store"))

    seen = _run_main(script, monkeypatch, tmp_path)

    # Positive, not merely "not the decoy": with the canonical variable unset the
    # script falls through to the documented default, exactly as it always did.
    assert seen["resolved_from"] == DEFAULT_PERSIST_DIRECTORY
    assert seen["client_config"].persist_directory == DEFAULT_PERSIST_DIRECTORY  # type: ignore[union-attr]


def test_usage_documents_only_the_canonical_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--help must show operators the variable that is actually read. Every
    occurrence of the short name must be a prefix of the canonical one, so the
    counts matching proves the short name never appears on its own."""
    script = _load_script()
    # Pin the width so argparse's textwrap can't split the 40-char name.
    monkeypatch.setenv("COLUMNS", "200")
    monkeypatch.setattr(sys, "argv", ["reset_corpus_baseline.py", "--help"])

    with pytest.raises(SystemExit):
        script.main()

    out = capsys.readouterr().out
    assert CANONICAL_ENV in out
    assert out.count(MISTAKEN_ENV) == out.count(CANONICAL_ENV)


# ---------------------------------------------------------------------------
# Round 20: the full-store reset also deletes the shared story_memory collection.
# Ownership was already settled — GitHub #132 Owner Decision 1 keeps story-memory
# restoration on Issue 18's existing per-story reindex path ("any desired
# story-memory backfill ... is not redesigned here"), so this command must NOT
# enumerate or reindex stories. What was missing is operator disclosure: the loss
# has to be stated BEFORE the deletion, and --help has to say it too.
# ---------------------------------------------------------------------------


def test_warns_that_story_memory_is_deleted_before_deleting_anything(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The warning is a warning, not a post-mortem: it must be printed before
    reset_chroma_store() runs, and it must name what is lost and how to get it
    back."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))

    seen = _run_main(script, monkeypatch, tmp_path)
    events = seen["events"]

    reset_at = events.index("RESET")  # type: ignore[union-attr]
    warned_at = next(
        i
        for i, e in enumerate(events)  # type: ignore[arg-type]
        if "story_memory" in e and "DESTRUCTIVE" in e
    )
    assert warned_at < reset_at

    warning = events[warned_at]  # type: ignore[index]
    assert "does NOT restore story memory" in warning
    assert "retrieval_backfill.py" in warning and "--mode reindex" in warning


def test_reset_rebuilds_only_published_rules_corpora_and_never_story_memory(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With a published corpus release AND a story present, the command rebuilds
    exactly the published rules-corpus projection and touches no story: no story
    enumeration, no story reindex. Owner Decision 1 keeps that on Issue 18's CLI."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))

    seen = _run_main(script, monkeypatch, tmp_path)

    # Exactly the published package — the draft one is not rebuilt.
    assert seen["reindexed"] == [_PUBLISHED_PKG]
    # And the operator's warning still precedes the deletion in the scenario that
    # actually has something to rebuild, not only on an empty store.
    events = seen["events"]
    assert next(
        i
        for i, e in enumerate(events)  # type: ignore[arg-type]
        if "story_memory" in e and "DESTRUCTIVE" in e
    ) < events.index(
        "RESET"
    )  # type: ignore[union-attr]
    # And no story-memory machinery is reachable from this command at all.
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "reindex_story",
        "backfill_story",
        "StoryORM",
        "RetrievalMemoryWriteService",
    ):
        assert forbidden not in source


def test_usage_states_story_memory_is_deleted_and_not_rebuilt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--help is the operator's contract for a destructive command: it must say
    story_memory is deleted, that only rules corpora are rebuilt, and name the
    separate per-story restoration command."""
    script = _load_script()
    monkeypatch.setattr(sys, "argv", ["reset_corpus_baseline.py", "--help"])

    with pytest.raises(SystemExit):
        script.main()

    # Assert on meaning, not on markdown emphasis: a reworded docstring that still
    # discloses the loss must keep passing. Markup is normalized away first.
    out = capsys.readouterr().out.replace("*", "").replace("`", "")
    assert "story_memory" in out
    assert "not restore story memory" in out
    assert "rules-corpus projections only" in out
    assert "retrieval_backfill.py --story-id <uuid> --mode reindex" in out


# ---------------------------------------------------------------------------
# Round 21: Chroma is a rebuildable projection of SQLite — but only while SQLite
# is actually reachable and holds something to rebuild from. A mistyped,
# unreachable, unmigrated, or empty --db-url discovered AFTER the full-store
# reset would leave the rules-corpus projections erased with no source to restore
# them. The reconstruction source is therefore opened, validated, and fully
# materialized BEFORE anything is deleted.
# ---------------------------------------------------------------------------


def _unmigrated_db_url(tmp_path) -> str:  # type: ignore[no-untyped-def]
    """A real SQLite file with no schema at all — reachable but incompatible."""
    db_path = tmp_path / "unmigrated.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        conn.execute(sa_text("CREATE TABLE unrelated (x INTEGER)"))
        conn.commit()
    engine.dispose()
    return f"sqlite:///{db_path}"


@pytest.mark.parametrize("kind", ["mistyped", "unreachable", "unmigrated", "empty"])
def test_unusable_rebuild_source_leaves_chroma_untouched(
    tmp_path, monkeypatch: pytest.MonkeyPatch, kind
) -> None:
    """Mistyped, unavailable, incompatible, and no-published-corpus databases all
    abort before the store is touched: non-zero exit, no client constructed, no
    reset, no rebuild — never erase projections that cannot then be rebuilt."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))
    db_url = {
        # Fails at engine construction, before any connection is attempted.
        "mistyped": "not-a-dialect:///typo.db",
        # A directory that does not exist — SQLite cannot open the file.
        "unreachable": f"sqlite:///{tmp_path / 'missing_dir' / 'nope.db'}",
        "unmigrated": _unmigrated_db_url(tmp_path),
        "empty": _empty_db_url(tmp_path),
    }[kind]

    seen = _arm(script, monkeypatch, tmp_path, db_url=db_url)

    assert script.main() == 1
    assert "CLIENT" not in seen["events"]  # type: ignore[operator]
    assert "RESET" not in seen["events"]  # type: ignore[operator]
    assert seen["reindexed"] == []
    assert "reset_client" not in seen and "client_config" not in seen
    assert any(
        "Preflight FAILED" in e and "NOT modified" in e
        for e in seen["events"]  # type: ignore[union-attr]
    )


def test_database_is_validated_and_materialized_before_the_reset(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordering, not merely outcome: preflight reports the materialized package
    count before the client is built and before the store is reset."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))

    seen = _run_main(script, monkeypatch, tmp_path)
    events = seen["events"]

    preflight_at = next(
        i
        for i, e in enumerate(events)  # type: ignore[arg-type]
        if "Preflight OK" in e and "1 published" in e
    )
    assert preflight_at < events.index("CLIENT") < events.index("RESET")  # type: ignore[union-attr]


def test_valid_database_resets_and_rebuilds_the_preflighted_packages(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The happy path is unchanged in effect: the store is reset and exactly the
    package identities proven during preflight are rebuilt afterwards."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))
    db_url = _seeded_db_url(tmp_path)

    seen = _run_main(script, monkeypatch, tmp_path, db_url=db_url)

    assert "RESET" in seen["events"]  # type: ignore[operator]
    assert seen["reindexed"] == [_PUBLISHED_PKG]
    # The rebuild set IS the preflighted set: what preflight() hands main() is
    # exactly what gets rebuilt, not a second query issued after the deletion.
    engine, _, packages = script.preflight(db_url)
    try:
        assert [str(p) for p in packages] == seen["reindexed"]
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Round 22: a published rp_corpus_releases row is an *identity*, not a payload.
# If its enabled rp_chunks were deleted, corrupted, orphaned, or left only
# partially schema-compatible, resetting first and discovering that during
# reindex leaves the prior projection gone — either raising mid-rebuild or
# producing a legitimate-looking empty collection. The payload is therefore
# fully loaded and validated before the client is built. Issue-5c-specific:
# only packages selected from rp_corpus_releases are checked, so a generic
# Rules Package (no corpus release row) keeps its broader zero-chunk contract.
# ---------------------------------------------------------------------------


def _mutate(db_url, fn):  # type: ignore[no-untyped-def]
    """Apply *fn(session)* to the seeded DB and commit."""
    engine = create_engine(db_url)
    factory = create_session_factory(engine)
    with factory() as session:
        fn(session)
        session.commit()
    engine.dispose()


def _delete_chunks(session):  # type: ignore[no-untyped-def]
    session.execute(sa_delete(RuleChunkORM))


def _disable_chunks(session):  # type: ignore[no-untyped-def]
    for row in session.execute(select(RuleChunkORM)).scalars():
        row.is_enabled = False


def _corrupt_locator_type(session):  # type: ignore[no-untyped-def]
    row = session.execute(select(RuleChunkORM)).scalars().first()
    row.source_locator_type = "not-a-locator-type"


def _blank_provenance(session):  # type: ignore[no-untyped-def]
    row = session.execute(select(RuleChunkORM)).scalars().first()
    row.source_document = ""


def _orphan_chunk(session):  # type: ignore[no-untyped-def]
    """Drop a chunk's declared projection: runtime reads would serve a chunk the
    digest/report never proved."""
    session.execute(
        sa_delete(CorpusProjectionORM).where(CorpusProjectionORM.leaf_id == "leaf-0")
    )


def _reassign_source(session):  # type: ignore[no-untyped-def]
    session.add(
        RuleSourceORM(
            rules_package_id=_PUBLISHED_PKG,
            source_id=_DRAFT_PKG,
            name="Interloper",
            category="core_rulebook",
            precedence_rank=2,
            is_enabled=True,
            created_at="2026-07-28T00:00:00Z",
        )
    )
    session.flush()
    row = session.execute(select(RuleChunkORM)).scalars().first()
    row.source_id = _DRAFT_PKG


def _drop_a_page(session):  # type: ignore[no-untyped-def]
    session.execute(sa_delete(LedgerLeafORM).where(LedgerLeafORM.printed_page == 7))


@pytest.mark.parametrize(
    "corrupt",
    [
        _delete_chunks,
        _disable_chunks,
        _corrupt_locator_type,
        _blank_provenance,
        _orphan_chunk,
        _reassign_source,
        _drop_a_page,
    ],
    ids=[
        "chunks-deleted",
        "chunks-disabled",
        "malformed-locator-type",
        "missing-provenance",
        "orphan-chunk",
        "reassigned-source",
        "incomplete-page-coverage",
    ],
)
def test_invalid_or_incomplete_corpus_payload_leaves_chroma_untouched(
    tmp_path, monkeypatch: pytest.MonkeyPatch, corrupt
) -> None:
    """Every way an Issue-5c payload can be unrebuildable — missing, disabled,
    malformed, missing provenance, orphaned, misattributed, or incomplete —
    aborts before the store is touched: exit 1, no client, no reset, no rebuild."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))
    db_url = _seeded_db_url(tmp_path)
    _mutate(db_url, corrupt)

    seen = _arm(script, monkeypatch, tmp_path, db_url=db_url)

    assert script.main() == 1
    assert "CLIENT" not in seen["events"]  # type: ignore[operator]
    assert "RESET" not in seen["events"]  # type: ignore[operator]
    assert seen["reindexed"] == []
    assert any(
        "Preflight FAILED" in e and "NOT modified" in e
        for e in seen["events"]  # type: ignore[union-attr]
    )


def test_payload_validation_completes_before_the_reset(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordering: the payload is reported validated and materialized before the
    Chroma client is constructed and before the store is reset."""
    script = _load_script()
    monkeypatch.setenv(CANONICAL_ENV, str(tmp_path / "isolated_chroma"))

    seen = _run_main(script, monkeypatch, tmp_path)
    events = seen["events"]

    validated_at = next(
        i
        for i, e in enumerate(events)  # type: ignore[arg-type]
        if "Preflight OK" in e and "validated and materialized" in e
    )
    assert validated_at < events.index("CLIENT") < events.index("RESET")  # type: ignore[union-attr]


def test_valid_payload_passes_validation_and_only_the_published_package_is_checked(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The positive control: a complete payload yields no violations, while the
    draft package — which has none — is never validated, because only published
    corpus releases are selected."""
    script = _load_script()
    db_url = _seeded_db_url(tmp_path)
    engine = create_engine(db_url)
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            assert script.validate_corpus_payload(session, _PUBLISHED_PKG) == []
            # The draft package has no payload at all — proof the corrupted-payload
            # cases above fail for the reason claimed, and that selection (not
            # validation) is what keeps it out of the rebuild.
            assert script.validate_corpus_payload(session, _DRAFT_PKG)
    finally:
        engine.dispose()
