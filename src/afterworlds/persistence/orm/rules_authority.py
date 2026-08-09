"""Runtime mechanical-authority tables — CRD Issue 5d, Decisions 9 and 10.

Four tables, and the split between them is the whole point of ADR-005d
Decision 9:

* ``rp_mech_overrides`` is the **authoring surface**. Rows here are mutable:
  an operator edits, disables, reprioritizes, retargets, or deletes them.
* ``rp_override_set_versions`` and ``rp_override_set_entries`` are the
  **retained replay evidence**. Rows here are append-only and immutable, keyed
  by the content-derived ``override_set_uuid`` of the exact canonical ordered
  override state that produced them.
* ``rp_override_set_scopes`` records **which package and release retained which
  content**. It exists at a third grain because a version is content: identical
  override state across packages is one row, so the version itself cannot say
  whose it is, and replay would otherwise have to take a binding at its word.

Recording only the identifier and re-deriving from current rows was rejected in
the PR #138 review: the identifier would name state that no longer exists the
moment an override is edited, so audit and replay could detect divergence but
could not reconstruct the authority actually applied. The retained entries are
what makes the binding *provenance-exact* — they carry the stable override
identity and origin as well as the mechanical change, so an audit can name which
authoritative record supplied each change.

Typed mechanical overrides live in their own table rather than extending
``rp_overrides``. The existing chunk-targeting prose override is a different
family with a different payload contract (#137 contract 6 keeps them distinct),
and ``rp_overrides`` still carries the ``target_entity_id`` column of the
obsolete ``MechanicalEntity`` family, which the final activation/legacy PR
removes. Sharing one table would couple this schema to that removal.

``payload`` is the one JSON column, and it is not a generic escape hatch: it
holds the validated field set of one closed typed patch family, rebuilt through
explicit per-family builders that reject an unknown or malformed shape (see
:mod:`afterworlds.services.rules_authority.patches`).
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class MechanicalOverrideORM(Base):
    """One authored typed override against a package's mechanical authority.

    Mutable by design — this is where an operator authors. Everything an audit
    needs to reconstruct a past effective view is copied into the retained
    override-set version at binding-resolution time, so editing or deleting a
    row here never rewrites history.

    ``release_version`` is the release the override was authored against. A row
    authored against a different release than the one being resolved is a
    cross-release patch and fails as ``INVALID_OVERRIDE``; it is not silently
    applied and not silently skipped.

    ``created_at``, ``created_by``, and ``note`` are audit metadata. None of
    them participates in applicability, ordering, or resolution, so none of them
    reaches the override-set identity (ADR-005d Decision 9).
    """

    __tablename__ = "rp_mech_overrides"

    override_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    release_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    # Exact typed target identity. Semantic keys, never derived projection IDs:
    # a derived ID would bind every override to one projection UUID and expire
    # the whole override set the next time the same release is reprojected.
    target_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    target_record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    target_component_key: Mapped[str | None] = mapped_column(
        sa.String(255), nullable=True
    )
    target_fact_key: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)

    override_origin: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    override_operation: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    precedence: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=True, server_default=sa.true()
    )

    # Audit metadata — deliberately outside the override-set identity.
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    created_by: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class OverrideSetVersionORM(Base):
    """One immutable, replayable override-set version.

    The primary key *is* the content-derived identity of the canonical ordered
    override state, so re-recording an identical state is an idempotent no-op
    rather than a second row, and two different states can never share a
    version.

    **A version is content, not a possession of one package.** Because the
    identity is derived from the ordered entries alone — which is what gives the
    empty override set one deterministic identity rather than one per package —
    identical states across packages resolve to the same row, and every package
    with no overrides shares it. It therefore carries no ``package_uuid`` and no
    foreign key: an owning column would name whichever package happened to
    retain it first, and cascading that package's deletion would delete replay
    evidence that recorded bindings of unrelated packages still depend on.
    Package scope belongs to the enclosing binding, which supplies it already.

    ``recorded_at`` is audit metadata — when this content was *first* observed —
    and never participates in identity.

    Append-only, enforced by database triggers (migration ``0024``) as the
    repository does for its other append-only evidence tables. Verification on
    read can only report that replay is broken; the triggers are what stop it
    from being broken by an ordinary ORM mistake.
    """

    __tablename__ = "rp_override_set_versions"

    override_set_uuid: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    entry_count: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    recorded_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class OverrideSetScopeORM(Base):
    """One package/release a retained override-set version was recorded for.

    The version row is content and is deliberately shared: identical override
    state across packages is one row, and every package with no overrides shares
    the empty set. That sharing is what makes this table necessary. Without it
    the version carries no record of *which* scopes it was ever retained for, so
    replay has to take the caller's binding at its word — and because semantic
    keys are stable across SRD-derived releases by design, an override set
    retained for one package finds live targets in another and replays with the
    wrong provenance.

    So scope is an *association*, not a column on the content: many packages may
    legitimately share one version, and each records its own row here.

    ``ON DELETE CASCADE`` on ``package_uuid`` is correct at this grain and was
    the defect at the other one. Deleting a package removes that package's
    association — its own recorded bindings die with it — while the shared
    version and every other package's association survive untouched.

    Append-only, and the ``DELETE`` guard is **conditional** rather than absent
    (migration ``0024``). It refuses a delete only while the owning package is
    still live, which is what makes the two requirements compatible: deleting a
    package remains possible, because SQLite removes the parent row before
    cascading and the guard's condition is already false by the time the child
    trigger fires, while a direct delete against a live package's association is
    rejected. An association that goes away by the contractual route fails replay
    closed with a retention defect, never with false provenance.

    Re-inserting an *identical* association is a no-op rather than an error:
    :func:`~afterworlds.services.rules_authority.retention.retain_override_set`
    writes through ``INSERT ... ON CONFLICT DO NOTHING``, so two sessions
    retaining the same content under the same scope converge instead of racing.
    The association *is* its primary key — version, package, and release
    together — so the only column a repeat could disturb is the
    ``first_recorded_at`` audit stamp, which the conflict clause leaves at the
    first observation. ``UPDATE`` is refused outright.
    """

    __tablename__ = "rp_override_set_scopes"

    override_set_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_override_set_versions.override_set_uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        primary_key=True,
    )
    release_version: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    #: When this scope first retained this content. Audit metadata only.
    first_recorded_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class OverrideSetEntryORM(Base):
    """One retained entry of an immutable override-set version.

    A complete provenance-exact copy of the override as it applied: stable
    identity, origin, exact typed target, operation, precedence, resolved apply
    order, enablement state, and the complete validated payload. Nothing here
    points back at ``rp_mech_overrides`` for its content, because the whole
    purpose of this table is to outlive that row.

    ``(override_set_uuid, apply_order)`` is unique: the retained order is the
    order that was applied, and two entries cannot claim the same position.

    Append-only, enforced by database triggers (migration ``0024``) for the same
    reason as its version header.
    """

    __tablename__ = "rp_override_set_entries"
    __table_args__ = (
        sa.UniqueConstraint(
            "override_set_uuid", "apply_order", name="uq_rp_override_set_entry_order"
        ),
    )

    row_id: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    override_set_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_override_set_versions.override_set_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    apply_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    override_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    override_origin: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    target_kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    target_record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    target_component_key: Mapped[str | None] = mapped_column(
        sa.String(255), nullable=True
    )
    target_fact_key: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    override_operation: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    precedence: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
