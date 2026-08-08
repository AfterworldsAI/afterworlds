"""The one code-owned binding-resolution path — CRD Issue 5d, Decision 9.

Everything that needs the effective mechanical authority of a package comes
through here. There is one resolution function, and it produces the complete
four-component binding or a typed refusal — never a partially populated binding,
never ``None``, and never an empty result a caller could read as permission.

Two resolutions, layered:

* :func:`resolve_package_reference` turns a human-facing reference into a
  package UUID. It is the *only* place a slug is interpreted. ADR-005d
  Decision 9 allows a slug to resolve through one code-owned service but never
  to serve as canonical authority, so what comes back is a UUID, and the
  binding is built from that.
* :func:`resolve_effective_binding` produces the binding itself: package UUID,
  release version, the active base projection's UUID, and the override-set UUID
  derived from current override state — which it also retains as an immutable
  replayable version, because a binding whose override-set identity names
  nothing retrievable is the exact defect ADR-005d rejected.

**Runtime resolution and replay are different operations**, and the difference
lives here. Runtime recomputes the override-set identity from current state; a
recorded binding that no longer matches is ``STALE`` and fails, and is never
silently re-resolved against current overrides. Replay does not come through
this path at all — it resolves the retained version through
:func:`afterworlds.services.rules_authority.retention.load_override_set_version`
and must succeed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    resolve_active_projection,
)
from afterworlds.models.enums import PublicationStatusEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideSet,
    OverrideStateError,
    collect_current_override_state,
)
from afterworlds.services.rules_authority.retention import retain_override_set

__all__ = [
    "BindingResolution",
    "PackageResolution",
    "package_slug",
    "resolve_effective_binding",
    "resolve_package_reference",
]

_SLUG_SEPARATORS = re.compile(r"[^a-z0-9]+")


def package_slug(name: str) -> str:
    """The human-facing slug form of a package name.

    Deliberately lossy and deliberately not authority: several package names can
    slugify to the same value, which is precisely why an ambiguous slug is a
    typed ``AMBIGUOUS`` refusal rather than a first match.
    """
    return _SLUG_SEPARATORS.sub("-", name.strip().lower()).strip("-")


@dataclass(frozen=True)
class PackageResolution:
    """The typed result of resolving a human-facing package reference."""

    outcome: AuthorityOutcome
    package_uuid: UUID | None = None
    detail: str = ""
    #: Every package a slug matched. Populated on ``AMBIGUOUS`` so an operator
    #: can see what to disambiguate between rather than being told only that
    #: something was ambiguous.
    candidates: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class BindingResolution:
    """The typed result of resolving an effective binding.

    ``binding`` is populated only on ``RESOLVED``. ``current_binding`` is
    populated on ``STALE`` and ``MISMATCHED_RELEASE`` as well, so a caller that
    must report what superseded a recorded binding does not have to resolve a
    second time to find out.
    """

    outcome: AuthorityOutcome
    binding: RulesPackageBinding | None = None
    current_binding: RulesPackageBinding | None = None
    override_state: EffectiveOverrideSet | None = None
    detail: str = ""


def resolve_package_reference(session: Session, reference: str) -> PackageResolution:
    """Resolve a UUID string or human-facing slug to one package UUID.

    A reference that is neither a well-formed UUID nor a slug matching exactly
    one enabled package is a typed refusal. The previous behaviour this
    replaces — parse the reference as a UUID and, on ``ValueError``, quietly
    proceed with no rules at all — is the fail-open path #137 contract 6
    requires to have no surviving caller: a malformed reference and a package
    with genuinely no rules produced the same silence.
    """
    raw = reference.strip()
    if not raw:
        return PackageResolution(
            AuthorityOutcome.INVALID_SELECTOR, detail="package reference is blank"
        )

    try:
        return PackageResolution(AuthorityOutcome.RESOLVED, package_uuid=UUID(raw))
    except ValueError:
        pass

    slug = package_slug(raw)
    if not slug:
        return PackageResolution(
            AuthorityOutcome.INVALID_SELECTOR,
            detail=f"package reference {reference!r} is neither a UUID nor a slug",
        )

    rows = (
        session.execute(
            select(RulesPackageORM)
            .where(RulesPackageORM.is_enabled == True)  # noqa: E712
            .order_by(RulesPackageORM.rules_package_id)
        )
        .scalars()
        .all()
    )
    matches = [row for row in rows if package_slug(row.name) == slug]
    if not matches:
        return PackageResolution(
            AuthorityOutcome.ABSENT,
            detail=f"no enabled package resolves the slug {slug!r}",
        )
    if len(matches) > 1:
        return PackageResolution(
            AuthorityOutcome.AMBIGUOUS,
            detail=(
                f"slug {slug!r} resolves to {len(matches)} packages; a slug is not "
                "canonical authority"
            ),
            candidates=tuple(UUID(row.rules_package_id) for row in matches),
        )
    return PackageResolution(
        AuthorityOutcome.RESOLVED, package_uuid=UUID(matches[0].rules_package_id)
    )


def _projection_header(
    session: Session, projection_uuid: str
) -> MechanicalProjectionORM | None:
    return session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == projection_uuid
        )
    ).scalar_one_or_none()


def resolve_effective_binding(
    session: Session,
    package_uuid: UUID,
    *,
    now: str,
    expected_release: str | None = None,
    recorded: RulesPackageBinding | None = None,
    retain: bool = True,
) -> BindingResolution:
    """Resolve the complete four-component effective binding of a package.

    The order of checks is the contract, because each earlier failure would make
    a later one meaningless:

    1. the package exists and is published;
    2. it has an active, published mechanical projection — otherwise
       ``UNPUBLISHED``, which is a typed answer and not an empty one;
    3. the projection's release matches *expected_release* when one is supplied
       — otherwise ``MISMATCHED_RELEASE``;
    4. current override state parses and yields an override-set identity, which
       is retained as an immutable version; and
    5. when *recorded* is supplied, all four components must match — a
       superseded projection or a superseded override set is ``STALE``.

    *retain* exists for the one caller that must not write: a diagnostic read
    that only wants to know whether a recorded binding is current. It defaults
    to ``True`` because resolution is the point at which replay evidence has to
    exist; skipping it silently would leave a binding whose override-set UUID
    names nothing retrievable.
    """
    package = session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == str(package_uuid)
        )
    ).scalar_one_or_none()
    if package is None:
        return BindingResolution(
            AuthorityOutcome.ABSENT, detail=f"no package {package_uuid}"
        )
    if not package.is_enabled:
        return BindingResolution(
            AuthorityOutcome.ABSENT, detail=f"package {package_uuid} is disabled"
        )
    if package.publication_status != PublicationStatusEnum.PUBLISHED.value:
        return BindingResolution(
            AuthorityOutcome.UNPUBLISHED,
            detail=(
                f"package {package_uuid} is {package.publication_status}, not "
                "published"
            ),
        )

    active = resolve_active_projection(session, str(package_uuid))
    if active.outcome is PublicationOutcome.UNPUBLISHED:
        return BindingResolution(
            AuthorityOutcome.UNPUBLISHED,
            detail=f"package {package_uuid} has no active mechanical projection",
        )
    if active.outcome is not PublicationOutcome.PUBLISHED:
        # ``resolve_active_projection`` reports STALE for an activation row
        # pointing at a draft, at another package's projection, or at one whose
        # recorded evidence was cleared or edited. It is stale here too — the
        # active authority is not what the record says it is.
        return BindingResolution(
            AuthorityOutcome.STALE,
            detail=(
                f"active projection {active.projection_uuid} of package "
                f"{package_uuid} does not verify: {active.outcome.value}"
            ),
        )

    assert active.projection_uuid is not None
    header = _projection_header(session, active.projection_uuid)
    if header is None:  # pragma: no cover - resolve_active_projection proves it
        return BindingResolution(
            AuthorityOutcome.STALE,
            detail=f"active projection {active.projection_uuid} has no header",
        )
    release_version = header.release_version

    if expected_release is not None and expected_release != release_version:
        return BindingResolution(
            AuthorityOutcome.MISMATCHED_RELEASE,
            detail=(
                f"package {package_uuid} publishes release {release_version!r}, "
                f"caller expected {expected_release!r}"
            ),
        )

    try:
        state = collect_current_override_state(
            session, str(package_uuid), release_version
        )
    except OverrideStateError as exc:
        return BindingResolution(AuthorityOutcome.INVALID_OVERRIDE, detail=str(exc))

    override_set_uuid = state.override_set_uuid
    if retain:
        retain_override_set(session, state, now=now)

    current = RulesPackageBinding(
        package_uuid=package_uuid,
        release_version=release_version,
        mechanical_projection_uuid=UUID(active.projection_uuid),
        override_set_uuid=UUID(override_set_uuid),
    )

    if recorded is not None:
        if recorded.package_uuid != current.package_uuid:
            return BindingResolution(
                AuthorityOutcome.INVALID_SELECTOR,
                current_binding=current,
                override_state=state,
                detail=(
                    f"recorded binding names package {recorded.package_uuid}, "
                    f"resolution was requested for {current.package_uuid}"
                ),
            )
        if recorded.release_version != current.release_version:
            return BindingResolution(
                AuthorityOutcome.MISMATCHED_RELEASE,
                current_binding=current,
                override_state=state,
                detail=(
                    f"recorded binding names release {recorded.release_version!r}, "
                    f"the package now publishes {current.release_version!r}"
                ),
            )
        if recorded.mechanical_projection_uuid != current.mechanical_projection_uuid:
            return BindingResolution(
                AuthorityOutcome.STALE,
                current_binding=current,
                override_state=state,
                detail=(
                    "recorded binding names base projection "
                    f"{recorded.mechanical_projection_uuid}, the active projection "
                    f"is {current.mechanical_projection_uuid}"
                ),
            )
        if recorded.override_set_uuid != current.override_set_uuid:
            return BindingResolution(
                AuthorityOutcome.STALE,
                current_binding=current,
                override_state=state,
                detail=(
                    "recorded binding names override set "
                    f"{recorded.override_set_uuid}, current override state is "
                    f"{current.override_set_uuid}"
                ),
            )

    return BindingResolution(
        AuthorityOutcome.RESOLVED,
        binding=current,
        current_binding=current,
        override_state=state,
    )
