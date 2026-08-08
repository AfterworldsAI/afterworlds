"""Runtime mechanical authority: typed overrides and retained override sets.

CRD Issue 5d (#137), PR 3. Adds the runtime half of ADR-005d Decisions 9 and 10:

* ``rp_mech_overrides`` — the mutable authoring surface for typed
  record/component/fact overrides. Separate from ``rp_overrides``, which holds
  the distinct chunk-targeting prose override family and still carries the
  obsolete ``target_entity_id`` column the final legacy-retirement PR removes.
* ``rp_override_set_versions`` / ``rp_override_set_entries`` — the immutable,
  append-only replay evidence an ``override_set_uuid`` names. The version's
  primary key *is* the content-derived identity of the canonical ordered
  override state, so recording an identical state twice is a no-op and two
  different states can never share a version.

Additive only. Nothing existing is altered or dropped, no projection becomes
active by migrating, and the legacy ``MechanicalEntity`` path is untouched.

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rp_mech_overrides",
        sa.Column("override_id", sa.String(36), primary_key=True),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("release_version", sa.String(64), nullable=False),
        sa.Column("target_kind", sa.String(16), nullable=False),
        sa.Column("target_record_key", sa.String(255), nullable=False),
        sa.Column("target_component_key", sa.String(255), nullable=True),
        sa.Column("target_fact_key", sa.String(32), nullable=True),
        sa.Column("override_origin", sa.String(32), nullable=False),
        sa.Column("override_operation", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("precedence", sa.Integer, nullable=False),
        sa.Column(
            "is_enabled", sa.Boolean, nullable=False, server_default=sa.true()
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
    )

    # Content-addressed and package-independent. The identity is derived from
    # the ordered entries alone, so identical states across packages — including
    # every package's empty override set — resolve to one row. An owning
    # package_uuid with ON DELETE CASCADE would name whichever package retained
    # it first and would delete shared replay evidence when *that* package is
    # deleted, breaking recorded bindings of unrelated packages.
    op.create_table(
        "rp_override_set_versions",
        sa.Column("override_set_uuid", sa.String(36), primary_key=True),
        sa.Column("entry_count", sa.Integer, nullable=False),
        sa.Column("recorded_at", sa.String(64), nullable=False),
    )

    op.create_table(
        "rp_override_set_entries",
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "override_set_uuid",
            sa.String(36),
            sa.ForeignKey(
                "rp_override_set_versions.override_set_uuid", ondelete="CASCADE"
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("apply_order", sa.Integer, nullable=False),
        sa.Column("override_id", sa.String(36), nullable=False),
        sa.Column("override_origin", sa.String(32), nullable=False),
        sa.Column("target_kind", sa.String(16), nullable=False),
        sa.Column("target_record_key", sa.String(255), nullable=False),
        sa.Column("target_component_key", sa.String(255), nullable=True),
        sa.Column("target_fact_key", sa.String(32), nullable=True),
        sa.Column("override_operation", sa.String(16), nullable=False),
        sa.Column("precedence", sa.Integer, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.UniqueConstraint(
            "override_set_uuid", "apply_order", name="uq_rp_override_set_entry_order"
        ),
    )

    # Which package/release retained which shared content. An association rather
    # than a column on the version, because the version is shared by every scope
    # holding identical override state — including every package's empty set.
    # Deleting a package drops its own association here and leaves the shared
    # content, and every other package's association, untouched.
    op.create_table(
        "rp_override_set_scopes",
        sa.Column(
            "override_set_uuid",
            sa.String(36),
            sa.ForeignKey(
                "rp_override_set_versions.override_set_uuid", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("release_version", sa.String(64), primary_key=True),
        sa.Column("first_recorded_at", sa.String(64), nullable=False),
    )

    # Append-only triggers, matching the convention this repository already
    # applies to entitlement_event, provider_refusal_log, and rpg_roll_audit.
    # Reconstruction re-derives the identity on read and so can *detect* a
    # rewritten version, but detection only reports that replay is broken — it
    # cannot reconstruct the authority that was originally applied. These
    # retained rows are the evidence a recorded binding depends on, so the
    # database refuses the rewrite rather than leaving it to be noticed later.
    #
    # DELETE is guarded on the two content tables but deliberately not on
    # rp_override_set_scopes: the scope association's lifecycle is its package's,
    # and blocking DELETE there would make deleting a package impossible. A
    # removed association fails replay closed, never with false provenance.
    for table, verbs in (
        ("rp_override_set_versions", ("UPDATE", "DELETE")),
        ("rp_override_set_entries", ("UPDATE", "DELETE")),
        ("rp_override_set_scopes", ("UPDATE",)),
    ):
        for verb in verbs:
            op.execute(
                f"""
                CREATE TRIGGER prevent_{table}_{verb.lower()}
                BEFORE {verb} ON {table}
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        '{table} is append-only: {verb} is forbidden'
                    );
                END
                """
            )

    # Guarding UPDATE and DELETE is not enough on SQLite. `INSERT OR REPLACE`
    # resolves a conflict by deleting the existing row and inserting the new one,
    # and with `recursive_triggers` off — the default — that implicit delete does
    # not fire the BEFORE DELETE trigger above. A retained row could therefore be
    # rewritten wholesale without any guard firing. These BEFORE INSERT triggers
    # refuse the re-insert directly, which is the only point REPLACE cannot slip
    # past.
    op.execute(
        """
        CREATE TRIGGER prevent_rp_override_set_versions_reinsert
        BEFORE INSERT ON rp_override_set_versions
        WHEN EXISTS (
            SELECT 1 FROM rp_override_set_versions
            WHERE override_set_uuid = NEW.override_set_uuid
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_versions is append-only: replacing a retained version is forbidden'
            );
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_rp_override_set_entries_reinsert
        BEFORE INSERT ON rp_override_set_entries
        WHEN EXISTS (
            SELECT 1 FROM rp_override_set_entries
            WHERE override_set_uuid = NEW.override_set_uuid
              AND apply_order = NEW.apply_order
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is append-only: replacing a retained entry is forbidden'
            );
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_rp_override_set_scopes_reinsert
        BEFORE INSERT ON rp_override_set_scopes
        WHEN EXISTS (
            SELECT 1 FROM rp_override_set_scopes
            WHERE override_set_uuid = NEW.override_set_uuid
              AND package_uuid = NEW.package_uuid
              AND release_version = NEW.release_version
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_scopes is append-only: replacing a retained association is forbidden'
            );
        END
        """
    )

    # A version is sealed once it holds the entry count it declared. Without
    # this, a plain INSERT with the next apply_order silently extends a retained
    # version — the unique constraint only stops reusing an existing position.
    op.execute(
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
        BEGIN
            SELECT RAISE(
                ABORT,
                'rp_override_set_entries is sealed: the retained version already holds every entry it declared'
            );
        END
        """
    )


def downgrade() -> None:
    for trigger in (
        "seal_rp_override_set_entries",
        "prevent_rp_override_set_scopes_reinsert",
        "prevent_rp_override_set_entries_reinsert",
        "prevent_rp_override_set_versions_reinsert",
        "prevent_rp_override_set_scopes_update",
        "prevent_rp_override_set_entries_update",
        "prevent_rp_override_set_entries_delete",
        "prevent_rp_override_set_versions_update",
        "prevent_rp_override_set_versions_delete",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    op.drop_table("rp_override_set_scopes")
    op.drop_table("rp_override_set_entries")
    op.drop_table("rp_override_set_versions")
    op.drop_table("rp_mech_overrides")
