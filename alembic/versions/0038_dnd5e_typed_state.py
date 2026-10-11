"""Typed D&D 5e character and continuing-creature state — CRD Issue 2b.

Retires the untyped sheet and replaces it with one authoritative typed state
per subject, held under an exact four-part Rules Package binding:

* drops ``dnd5e_character_sheets`` (free-text class, background and equipment;
  stored skill totals) and ``dnd5e_active_conditions``;
* drops the free-text ``rpg_character_sheet_bases.rules_package_id``;
* creates ``dnd5e_character_states``, ``rpg_parties``, ``dnd5e_creatures``,
  ``dnd5e_creature_associations``, ``dnd5e_item_instances``,
  ``dnd5e_binding_history``, ``dnd5e_adoption_requests``, ``rpg_turn_leases``
  and ``rp_mech_shared_changes``.

**Empty stores only, both ways.** No character has been played (Owner: "No
one has played. There are no existing characters."), and there is no honest
conversion between a free-text sheet and typed, bound state. The upgrade
refuses while any predecessor RPG row exists; the downgrade refuses while any
2b row exists. Remove the rows deliberately, then migrate.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: str | None = None
depends_on: str | None = None

_PREDECESSOR = (
    "pending_roll_requests",
    "rpg_session_states",
    "dnd5e_active_conditions",
    "dnd5e_character_sheets",
    "rpg_character_sheet_bases",
)
_NEW = (
    "rp_mech_shared_changes",
    "rpg_turn_leases",
    "dnd5e_adoption_requests",
    "dnd5e_binding_history",
    "dnd5e_item_instances",
    "dnd5e_creature_associations",
    "dnd5e_creatures",
    "rpg_parties",
    "dnd5e_character_states",
)


def _refuse_if_populated(tables: tuple[str, ...], direction: str) -> None:
    bind = op.get_bind()
    for table in tables:
        count = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed literals
        ).scalar_one()
        if count:
            raise RuntimeError(
                f"{table} holds {count} rows. CRD Issue 2b migrates empty stores "
                f"only: there is no honest {direction} between the untyped sheet "
                "and typed, bound state. Remove the rows deliberately, then migrate."
            )


def _binding() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("package_uuid", sa.String(36), nullable=False),
        sa.Column("release_version", sa.Text, nullable=False),
        sa.Column("projection_uuid", sa.String(36), nullable=False),
        sa.Column("override_set_uuid", sa.String(36), nullable=False),
    ]


def _story(index: bool = True) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        "story_id",
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=index,
    )


def upgrade() -> None:
    _refuse_if_populated(_PREDECESSOR, "conversion")
    op.drop_table("dnd5e_active_conditions")
    op.drop_table("dnd5e_character_sheets")
    with op.batch_alter_table("rpg_character_sheet_bases") as batch:
        batch.drop_column("rules_package_id")

    op.create_table(
        "dnd5e_character_states",
        sa.Column(
            "sheet_id",
            sa.String(36),
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _story(),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("document", sa.JSON, nullable=False),
        *_binding(),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "rpg_parties",
        sa.Column("party_id", sa.String(36), primary_key=True),
        _story(),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("package_uuid", sa.String(36), nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "dnd5e_creatures",
        sa.Column("creature_id", sa.String(36), primary_key=True),
        _story(),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("document", sa.JSON, nullable=False),
        *_binding(),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "dnd5e_creature_associations",
        sa.Column("association_id", sa.String(36), primary_key=True),
        sa.Column(
            "creature_id",
            sa.String(36),
            sa.ForeignKey("dnd5e_creatures.creature_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column(
            "character_id",
            sa.String(36),
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "party_id",
            sa.String(36),
            sa.ForeignKey("rpg_parties.party_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("started_at", sa.String(64), nullable=False),
        sa.Column("ended_at", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "(character_id IS NULL) != (party_id IS NULL)",
            name="ck_dnd5e_creature_associations_one_target",
        ),
    )
    op.create_table(
        "dnd5e_item_instances",
        sa.Column("item_id", sa.String(36), primary_key=True),
        _story(),
        sa.Column("record_key", sa.Text, nullable=False),
        sa.Column("component_key", sa.Text, nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column(
            "holder_character_id",
            sa.String(36),
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "holder_creature_id",
            sa.String(36),
            sa.ForeignKey("dnd5e_creatures.creature_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "holder_party_id",
            sa.String(36),
            sa.ForeignKey("rpg_parties.party_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("equipped", sa.Boolean, nullable=False),
        sa.Column("attuned_subject_id", sa.String(36), nullable=True),
        sa.Column("charges_remaining", sa.Integer, nullable=True),
        sa.Column("applied_poison_record_key", sa.Text, nullable=True),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "(holder_character_id IS NOT NULL) + (holder_creature_id IS NOT NULL)"
            " + (holder_party_id IS NOT NULL) = 1",
            name="ck_dnd5e_item_instances_one_holder",
        ),
        sa.CheckConstraint("quantity >= 1", name="ck_dnd5e_item_instances_quantity"),
        sa.CheckConstraint(
            "charges_remaining IS NULL OR charges_remaining >= 0",
            name="ck_dnd5e_item_instances_charges",
        ),
    )
    op.create_table(
        "dnd5e_binding_history",
        sa.Column("history_id", sa.String(36), primary_key=True),
        sa.Column("subject_kind", sa.String(16), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False, index=True),
        _story(index=False),
        sa.Column("event", sa.String(16), nullable=False),
        *_binding(),
        sa.Column("state_revision", sa.Integer, nullable=False),
        sa.Column("adoption_request_id", sa.String(36), nullable=True),
        sa.Column("recorded_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "dnd5e_adoption_requests",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("subject_kind", sa.String(16), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False, index=True),
        _story(index=False),
        *[
            sa.Column(f"{prefix}_{name}", type_, nullable=False)
            for prefix in ("from", "target")
            for name, type_ in (
                ("package_uuid", sa.String(36)),
                ("release_version", sa.Text),
                ("projection_uuid", sa.String(36)),
                ("override_set_uuid", sa.String(36)),
            )
        ],
        sa.Column("change_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("requested_at", sa.String(64), nullable=False),
        sa.Column("resolved_at", sa.String(64), nullable=True),
    )
    op.create_table(
        "rpg_turn_leases",
        sa.Column("lease_id", sa.String(36), primary_key=True),
        _story(),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("started_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "rp_mech_shared_changes",
        sa.Column("change_id", sa.String(36), primary_key=True),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("release_version", sa.Text, nullable=False),
        sa.Column("entries", sa.JSON, nullable=False),
        sa.Column("base_override_set_uuid", sa.String(36), nullable=False),
        sa.Column("target_override_set_uuid", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("requested_by", sa.Text, nullable=False),
        sa.Column("requested_at", sa.String(64), nullable=False),
        sa.Column("resolved_at", sa.String(64), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
    )


def downgrade() -> None:
    _refuse_if_populated(_NEW, "reversal")
    _refuse_if_populated(_PREDECESSOR[:2] + _PREDECESSOR[4:], "reversal")
    for table in _NEW:
        op.drop_table(table)
    with op.batch_alter_table("rpg_character_sheet_bases") as batch:
        batch.add_column(
            sa.Column("rules_package_id", sa.Text, nullable=False, server_default="")
        )
    with op.batch_alter_table("rpg_character_sheet_bases") as batch:
        batch.alter_column("rules_package_id", server_default=None)
    op.create_table(
        "dnd5e_character_sheets",
        sa.Column(
            "sheet_id",
            sa.String(36),
            sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("character_class", sa.Text, nullable=False),
        sa.Column("background", sa.Text, nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("ability_scores", sa.JSON, nullable=False),
        sa.Column("skills", sa.JSON, nullable=False),
        sa.Column("equipment", sa.JSON, nullable=False),
        sa.Column("current_hp", sa.Integer, nullable=False),
        sa.Column("maximum_hp", sa.Integer, nullable=False),
        sa.Column("spell_slots", sa.JSON, nullable=False),
    )
    op.create_table(
        "dnd5e_active_conditions",
        sa.Column("condition_id", sa.String(36), primary_key=True),
        sa.Column(
            "sheet_id",
            sa.String(36),
            sa.ForeignKey("dnd5e_character_sheets.sheet_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(128), nullable=False),
        sa.Column("display_label", sa.Text, nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("duration_policy", sa.Text, nullable=True),
        sa.Column("applied_turn_id", sa.String(36), nullable=True),
        sa.Column("rules_package_ref", sa.Text, nullable=True),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_dnd5e_active_conditions_sheet_id",
        "dnd5e_active_conditions",
        ["sheet_id"],
    )
    op.create_index(
        "ix_dnd5e_active_conditions_identifier",
        "dnd5e_active_conditions",
        ["sheet_id", "identifier"],
    )
