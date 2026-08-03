"""CI invariant tests: structural separation of Story Bible and Rules Package.

Architecture invariant (CRD Issue 4):
  No ``sb_*`` table may carry a ForeignKey constraint that references any
  prose history table (nodes, turns, arcs, chapters).

  Story Bible tables reference ``stories`` (the top-level hierarchy) which
  is explicitly permitted.  Provenance references to turns are stored as
  plain strings — not FK constraints.

Architecture invariant (CRD Issue 5a):
  No ``rp_*`` table may carry a ForeignKey constraint that references any
  non-``rp_*`` table.  Cross-subsystem references (e.g. character sheet
  ``rules_package_id``) must use plain strings without FK constraints.
"""

from __future__ import annotations

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.corpus  # noqa: F401
import afterworlds.persistence.orm.mechanical  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.persistence.orm.base import Base

# Prose history tables — Story Bible tables must not depend on these.
_PROSE_HISTORY_TABLES: frozenset[str] = frozenset(
    {"nodes", "turns", "arcs", "chapters"}
)

# Table prefix constants
_SB_PREFIX = "sb_"
_RP_PREFIX = "rp_"


# ---------------------------------------------------------------------------
# Story Bible structural invariants (CRD Issue 4)
# ---------------------------------------------------------------------------


def test_story_bible_tables_exist_with_sb_prefix() -> None:
    """All nine Story Bible tables must be registered with the sb_ prefix."""
    expected = {
        "sb_settings",
        "sb_cast_entries",
        "sb_locked_facts",
        "sb_forbidden_facts",
        "sb_events",
        "sb_relationship_ledger",
        "sb_unresolved_threads",
        "sb_provisional_staging",
        "sb_dynamic_field_history",
    }
    actual = {name for name in Base.metadata.tables if name.startswith(_SB_PREFIX)}
    assert (
        expected == actual
    ), f"Expected sb_* tables: {sorted(expected)}\nFound: {sorted(actual)}"


def test_no_story_bible_table_fk_to_prose_history() -> None:
    """No sb_* table may carry a FK that references a prose history table.

    This is the structural separation invariant required by the architecture.
    Provenance references to turns must be plain strings (no FK constraint).
    """
    violations: list[str] = []

    for table_name, table in Base.metadata.tables.items():
        if not table_name.startswith(_SB_PREFIX):
            continue
        for fk in table.foreign_keys:
            target_table = fk.column.table.name
            if target_table in _PROSE_HISTORY_TABLES:
                violations.append(
                    f"  {table_name}.{fk.parent.name} → {target_table}.{fk.column.name}"
                )

    assert not violations, (
        "Story Bible tables must not carry FK constraints to prose history tables.\n"
        "Violations found:\n" + "\n".join(violations)
    )


def test_story_bible_tables_fk_to_stories_is_permitted() -> None:
    """Story Bible tables may reference stories.story_id (top-level hierarchy)."""
    sb_tables_with_story_fk = []
    for table_name, table in Base.metadata.tables.items():
        if not table_name.startswith(_SB_PREFIX):
            continue
        for fk in table.foreign_keys:
            if fk.column.table.name == "stories":
                sb_tables_with_story_fk.append(table_name)

    # Every sb_* table except sb_dynamic_field_history should reference stories
    # (history records reference cast entities, not stories directly)
    assert "sb_settings" in sb_tables_with_story_fk
    assert "sb_cast_entries" in sb_tables_with_story_fk
    assert "sb_locked_facts" in sb_tables_with_story_fk
    assert "sb_forbidden_facts" in sb_tables_with_story_fk
    assert "sb_events" in sb_tables_with_story_fk
    assert "sb_relationship_ledger" in sb_tables_with_story_fk
    assert "sb_unresolved_threads" in sb_tables_with_story_fk
    assert "sb_provisional_staging" in sb_tables_with_story_fk


def test_source_turn_id_is_not_a_fk_constraint() -> None:
    """The source_turn_id provenance column must not be a FK to turns."""
    for table_name, table in Base.metadata.tables.items():
        if not table_name.startswith(_SB_PREFIX):
            continue
        if "source_turn_id" not in table.c:
            continue
        col = table.c["source_turn_id"]
        fk_targets = {fk.column.table.name for fk in col.foreign_keys}
        assert "turns" not in fk_targets, (
            f"{table_name}.source_turn_id must not be a FK to turns; "
            "it is a plain provenance string."
        )


# ---------------------------------------------------------------------------
# Rules Package structural invariants (CRD Issue 5a)
# ---------------------------------------------------------------------------


def test_rules_package_tables_exist_with_rp_prefix() -> None:
    """All Rules Package tables must be registered with the rp_ prefix.

    Updated in issue #60: rp_manifests replaces the legacy
    rules_package_manifests name, bringing the manifest table into the
    rp_* naming family.
    """
    expected = {
        "rp_packages",
        "rp_sources",
        "rp_chunks",
        "rp_mechanical_entities",
        "rp_overrides",
        "rp_manifests",
        # CRD Issue 5c (#132) corpus-integrity release tables.
        "rp_corpus_releases",
        "rp_source_ledgers",
        "rp_ledger_containers",
        "rp_ledger_leaves",
        "rp_reconciliation_policies",
        "rp_reconciliations",
        "rp_corpus_projections",
        # CRD Issue 5d (#137) mechanical-authority projection tables.
        "rp_mech_projections",
        "rp_mech_spans",
        "rp_mech_acceptance_batches",
        "rp_mech_batch_scope",
        "rp_mech_batch_diff",
        "rp_mech_acceptances",
        "rp_mech_records",
        "rp_mech_components",
        "rp_mech_facts",
        "rp_mech_prose_bindings",
        "rp_mech_relationships",
        "rp_mech_references",
        "rp_mech_provenance",
        "rp_mech_active_projections",
    }
    actual = {name for name in Base.metadata.tables if name.startswith(_RP_PREFIX)}
    assert (
        expected == actual
    ), f"Expected rp_* tables: {sorted(expected)}\nFound: {sorted(actual)}"


def test_no_rp_table_fk_to_non_rp_tables() -> None:
    """No rp_* table may carry a FK that references a non-rp_* table.

    rp_* tables may reference other rp_* tables (intra-subsystem cohesion).
    All cross-subsystem references must be plain strings without FK
    constraints, preserving structural independence of the Rules Package.
    """
    violations: list[str] = []

    for table_name, table in Base.metadata.tables.items():
        if not table_name.startswith(_RP_PREFIX):
            continue
        for fk in table.foreign_keys:
            target_table = fk.column.table.name
            if not target_table.startswith(_RP_PREFIX):
                violations.append(
                    f"  {table_name}.{fk.parent.name} → {target_table}.{fk.column.name}"
                )

    assert not violations, (
        "rp_* tables must not carry FK constraints to non-rp_* tables.\n"
        "Violations found:\n" + "\n".join(violations)
    )
