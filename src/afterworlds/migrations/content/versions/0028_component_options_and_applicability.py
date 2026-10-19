"""Component applicability and exhaustive actor-choice options.

CRD Issue 5d (#137), representation schema ``5d-representation-schema-2``.

Two structures the schema-1 component could not hold:

* ``rp_mech_components.applies_when`` — the closed applicability qualifier, or
  NULL when the component applies unconditionally. Stored as its canonical
  payload rather than as one column per field, so a later reshaping of the
  qualifier is a payload change checked by the schema hash rather than a table
  migration per field.
* ``rp_mech_component_options`` — one row per option of a component that states
  an exhaustive actor choice. A component that is a conjunction has none.
* ``rp_mech_overrides.target_option_key`` and
  ``rp_override_set_entries.target_option_key`` — the owning option of a fact
  *target*, so an override authored against an option fact survives authoring,
  retention, and replay instead of reconstructing as a direct-fact target in
  the component's own scope. Nullable, unlike ``rp_mech_facts.option_key``:
  a fact always has a scope and ``""`` names the direct one, but a record,
  component, or prose target has no option axis at all, and NULL is what says
  so. The loaders reject a non-NULL value on such a target.

Adding a content column to a retained table means
``prevent_rp_override_set_entries_reinsert`` no longer covers the whole entry,
so migration ``0024``'s trigger is dropped and recreated over the new column
set. A content column outside that guard is content a re-insert could rewrite
silently. Its ``IS NOT`` comparisons are already NULL-safe, which is what lets
the new nullable column join them unchanged.

``rp_mech_facts.option_key`` names the owning option, or ``""`` for a fact held
directly on the component. It is ``NOT NULL`` with an empty-string default
because "no option" is a real, addressable scope: making it nullable would give
the grouping key a third state meaning the same thing as ``""`` and let two
spellings of one scope diverge.

**Additive, with no backfill, deliberately.** Every existing fact row is a
direct fact, and ``""`` is exactly what a direct fact carries — so the server
default is the correct value rather than a placeholder awaiting repair. No
component can have options yet, because no projection built under schema 2
exists: ``oracles/`` holds no accepted oracle, so nothing has ever been
accepted, persisted, or published under the new contract. There is therefore no
prior state to translate and no data-shape decision hidden in this migration.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COMPONENTS = "rp_mech_components"
_FACTS = "rp_mech_facts"
_OPTIONS = "rp_mech_component_options"
_OVERRIDES = "rp_mech_overrides"
_ENTRIES = "rp_override_set_entries"

#: Every content column of a retained entry, in the order ``0024`` declared
#: them plus the one this migration adds. The append-only guard compares all of
#: them, so this list and the table definition move together.
_ENTRY_CONTENT_COLUMNS = (
    "override_id",
    "override_origin",
    "target_kind",
    "target_record_key",
    "target_component_key",
    "target_fact_key",
    "target_option_key",
    "override_operation",
    "precedence",
    "is_enabled",
    "payload",
)


def _entry_triggers(columns: tuple[str, ...]) -> list[str]:
    """Every ``rp_override_set_entries`` trigger ``0024`` installs.

    All four, not just the one this migration's column set changes. SQLite
    ``ALTER TABLE ... DROP COLUMN`` is implemented by rebuilding the table, and
    a rebuild drops every trigger attached to the old one — so a downgrade that
    restored only the re-insert guard left retained evidence updatable,
    deletable, and extendable past its seal. Both directions call this, and the
    SQL is copied from ``0024`` verbatim so the two cannot drift.

    Order matters for ``seal_``: it reads ``rp_override_set_versions``, which
    both directions leave in place, so it is safe last.
    """
    return [
        """
        CREATE TRIGGER prevent_rp_override_set_entries_update
        BEFORE UPDATE ON rp_override_set_entries
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is append-only: UPDATE is forbidden'
            );
        END
        """,
        """
        CREATE TRIGGER prevent_rp_override_set_entries_delete
        BEFORE DELETE ON rp_override_set_entries
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is append-only: DELETE is forbidden'
            );
        END
        """,
        _entries_reinsert_trigger(columns),
        """
        CREATE TRIGGER seal_rp_override_set_entries
        BEFORE INSERT ON rp_override_set_entries
        WHEN (
            SELECT COUNT(*) FROM rp_override_set_entries
            WHERE override_set_uuid = NEW.override_set_uuid
        ) >= (
            SELECT entry_count FROM rp_override_set_versions
            WHERE override_set_uuid = NEW.override_set_uuid
        )
        AND NOT EXISTS (
            SELECT 1 FROM rp_override_set_entries
            WHERE override_set_uuid = NEW.override_set_uuid
              AND apply_order = NEW.apply_order
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is sealed: version already complete'
            );
        END
        """,
    ]


_ENTRY_TRIGGER_NAMES = (
    "prevent_rp_override_set_entries_update",
    "prevent_rp_override_set_entries_delete",
    "prevent_rp_override_set_entries_reinsert",
    "seal_rp_override_set_entries",
)


def _drop_entry_triggers() -> None:
    for name in _ENTRY_TRIGGER_NAMES:
        op.execute(f"DROP TRIGGER IF EXISTS {name}")


def _entries_reinsert_trigger(columns: tuple[str, ...]) -> str:
    differs = "\n                OR ".join(f"{c} IS NOT NEW.{c}" for c in columns)
    return f"""
        CREATE TRIGGER prevent_rp_override_set_entries_reinsert
        BEFORE INSERT ON rp_override_set_entries
        WHEN EXISTS (
            SELECT 1 FROM rp_override_set_entries
            WHERE override_set_uuid = NEW.override_set_uuid
              AND apply_order = NEW.apply_order
              AND (
                   {differs}
              )
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is append-only: rewrite refused'
            );
        END
        """


def upgrade() -> None:
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.add_column(sa.Column("applies_when", sa.JSON(), nullable=True))

    with op.batch_alter_table(_FACTS) as batch:
        batch.add_column(
            sa.Column(
                "option_key",
                sa.String(255),
                nullable=False,
                server_default="",
            )
        )

    for table in (_OVERRIDES, _ENTRIES):
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column("target_option_key", sa.String(255), nullable=True)
            )

    # SQLite ADD COLUMN does not rebuild the table, so the other three guards
    # survive this direction; only the re-insert guard's column set changes.
    # The whole family is recreated regardless, so both directions leave
    # identical schema and neither has to be reasoned about separately.
    _drop_entry_triggers()
    for statement in _entry_triggers(_ENTRY_CONTENT_COLUMNS):
        op.execute(statement)

    op.create_table(
        _OPTIONS,
        sa.Column("row_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("record_key", sa.String(255), nullable=False, index=True),
        sa.Column("component_key", sa.String(255), nullable=False),
        sa.Column("semantic_key", sa.String(255), nullable=False),
        sa.Column("applies_when", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "projection_uuid",
            "record_key",
            "component_key",
            "semantic_key",
            name="uq_mech_component_option",
        ),
    )


def downgrade() -> None:
    op.drop_table(_OPTIONS)
    _drop_entry_triggers()
    for table in (_ENTRIES, _OVERRIDES):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("target_option_key")
    # The batch rebuild above dropped every trigger on the rebuilt table, not
    # only the one whose column set changed. Restoring just the re-insert guard
    # left retained evidence updatable, deletable, and extendable past its seal
    # after a rollback.
    for statement in _entry_triggers(
        tuple(c for c in _ENTRY_CONTENT_COLUMNS if c != "target_option_key")
    ):
        op.execute(statement)
    with op.batch_alter_table(_FACTS) as batch:
        batch.drop_column("option_key")
    with op.batch_alter_table(_COMPONENTS) as batch:
        batch.drop_column("applies_when")
