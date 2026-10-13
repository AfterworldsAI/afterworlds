"""ORM for CRD Issue 2b D&D 5e character and continuing-creature state.

One authoritative state row per subject, holding the typed document
(:mod:`afterworlds.models.dnd5e_state`), an integer ``revision`` for
compare-and-swap writes, and the exact four-part Rules Package binding the
document is held under. Separate tables exist only where the database must
enforce a rule across subjects: one holder per item instance, creature
associations, binding history, adoption requests and in-flight turn leases.

References into the Rules Package are plain strings, never foreign keys
(CRD Issue 5a separation invariant).
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class Dnd5eCharacterStateORM(Base):
    """The authoritative state of one character (FK to its sheet identity)."""

    __tablename__ = "dnd5e_character_states"

    sheet_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
        primary_key=True,
    )
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    document: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    release_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    projection_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    override_set_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RpgPartyORM(Base):
    """A minimal party identity: a story-scoped name a creature can belong to.

    Membership, governance and gameplay are out of scope; a story is never
    treated as a party.
    """

    __tablename__ = "rpg_parties"

    party_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: The Rules Package whose current exact binding governs items the party
    #: holds; checked at every item operation, never cached as a binding.
    package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class Dnd5eCreatureORM(Base):
    """A continuing creature's identity and authoritative state.

    Its own record, never nested in a character: an ended or absent
    association leaves it, its hit points and its conditions intact.
    """

    __tablename__ = "dnd5e_creatures"

    creature_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    document: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    release_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    projection_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    override_set_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class Dnd5eCreatureAssociationORM(Base):
    """One relationship of a creature to a character or a party.

    Exactly one of ``character_id``/``party_id``. Several may be open at once
    (sharing); ending one sets ``ended_marker`` and changes nothing about the
    creature.
    """

    __tablename__ = "dnd5e_creature_associations"
    __table_args__ = (
        sa.CheckConstraint(
            "(character_id IS NULL) != (party_id IS NULL)",
            name="ck_dnd5e_creature_associations_one_target",
        ),
    )

    association_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    creature_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("dnd5e_creatures.creature_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    character_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
        nullable=True,
    )
    party_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_parties.party_id", ondelete="CASCADE"),
        nullable=True,
    )
    started_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    ended_at: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


class Dnd5eItemInstanceORM(Base):
    """One item instance with exactly one holder.

    Identity is an accepted record, optionally narrowed to one of its
    components. ``attuned_subject_id`` names the character or creature attuned
    to it, if any.
    """

    __tablename__ = "dnd5e_item_instances"
    __table_args__ = (
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

    item_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    component_key: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    holder_character_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"),
        nullable=True,
    )
    holder_creature_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("dnd5e_creatures.creature_id", ondelete="CASCADE"),
        nullable=True,
    )
    holder_party_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_parties.party_id", ondelete="CASCADE"),
        nullable=True,
    )
    equipped: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    attuned_subject_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    charges_remaining: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    #: An injury poison applied to this item (an accepted poison record).
    applied_poison_record_key: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class Dnd5eBindingHistoryORM(Base):
    """Append-only: every binding a subject has held, and why it changed."""

    __tablename__ = "dnd5e_binding_history"

    history_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    subject_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    subject_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    event: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    release_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    projection_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    override_set_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    state_revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    adoption_request_id: Mapped[str | None] = mapped_column(
        sa.String(36), nullable=True
    )
    recorded_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class Dnd5eAdoptionRequestORM(Base):
    """One deliberate request to adopt an exact target binding.

    ``status``: ``held`` (waiting on an affected event or the referenced
    change), ``applied``, ``refused`` (with ``reason``) or ``withdrawn``.
    ``change_id`` names the shared change whose activation produces the target,
    when there is one; it is a plain string (Rules Package separation).
    """

    __tablename__ = "dnd5e_adoption_requests"

    request_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    subject_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    subject_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    from_package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    from_release_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    from_projection_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    from_override_set_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    target_package_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    target_release_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    target_projection_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    target_override_set_uuid: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    change_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    requested_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    resolved_at: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


class RpgTurnLeaseORM(Base):
    """A durable marker that an adjudicating turn is in flight for a story.

    Written in its own committed transaction before the turn reads any
    subject binding, and deleted atomically with the turn's commit (or by its
    rollback cleanup). A shared rule change cannot activate while an affected
    story holds one.
    """

    __tablename__ = "rpg_turn_leases"

    lease_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    #: The process that owns the lease (see ``services.dnd5e_state.leases``).
    owner_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    started_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RpgTurnCoordinationORM(Base):
    """A story's actor-turn coordination (CRD Issue 15c): whose turn is active
    and the next turn instance, as a typed document with a ``revision`` for
    compare-and-swap. It holds no hit points, conditions, effects or pending
    state; those stay on each subject's own state.
    """

    __tablename__ = "rpg_turn_coordination"

    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        primary_key=True,
    )
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    document: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RpgTurnEdgeORM(Base):
    """Append-only: every actor-turn edge (``begin``/``end``) and once-per-turn
    ``use`` a delivered Turn applied, in order.

    ``sequence`` is per story; ``coordination_revision`` is the revision the
    event was applied to; ``use_key`` names a use's source. The coordination
    document is reconstructable by replaying these rows
    (:func:`afterworlds.services.dnd5e_state.coordination.replay`).
    """

    __tablename__ = "rpg_turn_edges"
    __table_args__ = (
        sa.UniqueConstraint("story_id", "sequence", name="uq_rpg_turn_edges_sequence"),
        sa.CheckConstraint(
            "kind IN ('begin', 'end', 'use')", name="ck_rpg_turn_edges_kind"
        ),
        sa.CheckConstraint(
            "(kind = 'use') = (use_key IS NOT NULL)", name="ck_rpg_turn_edges_use_key"
        ),
    )

    edge_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: The delivered Turn that applied it (plain string, like the audit rows).
    turn_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(8), nullable=False)
    subject_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    subject_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    turn_instance: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    coordination_revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    use_key: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    recorded_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
