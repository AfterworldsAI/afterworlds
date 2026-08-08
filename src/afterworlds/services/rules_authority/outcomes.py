"""Typed runtime authority states — CRD Issue 5d, contracts 5 and 6.

#137 requires mechanical authority operations to distinguish ``ABSENT``,
``AMBIGUOUS``, ``UNRESOLVED``, ``UNREVIEWED``, ``INCOMPLETE``, ``STALE``,
``MISMATCHED_RELEASE``, ``INVALID_SELECTOR``, ``INVALID_REFERENCE``,
``INVALID_OVERRIDE``, and ``UNPUBLISHED``, and forbids collapsing any of them
into ``None``, an empty result, a generic exception, retrieval fallback, or
model inference.

Those states are owned by two stages, and this enum declares only the runtime
half. ``UNRESOLVED``, ``UNREVIEWED``, and ``INCOMPLETE`` are judgements about a
projection *candidate* — they can only be reached by the publication gate, and
they live in
:class:`afterworlds.ingestion.mechanical.publication.PublicationOutcome`.
Declaring them here as members no runtime path can return would be a menu of
states rather than a contract. ``STALE``, ``MISMATCHED_RELEASE``, and
``UNPUBLISHED`` appear in both, because both stages can genuinely reach them.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["AuthorityOutcome"]


class AuthorityOutcome(StrEnum):
    """The typed result of one runtime authority resolution."""

    #: The complete four-component effective binding was resolved.
    RESOLVED = "resolved"
    #: No such package, or no such retained override-set version.
    ABSENT = "absent"
    #: A human-facing slug resolved to more than one package.
    AMBIGUOUS = "ambiguous"
    #: The package has no active published mechanical projection.
    UNPUBLISHED = "unpublished"
    #: A recorded binding no longer matches current authority — a superseded
    #: projection or, equally, an override-set identity that no longer matches
    #: the identity recomputed from current override state.
    STALE = "stale"
    #: The recorded release is not the release the package now publishes.
    MISMATCHED_RELEASE = "mismatched_release"
    #: A malformed package reference, or a selector set that selects nothing
    #: without saying so — the accidentally-empty selector.
    INVALID_SELECTOR = "invalid_selector"
    #: An override that cannot be applied: outside the closed patch union,
    #: authored against another release, aimed at a target that does not exist,
    #: or type-incompatible with the target it names.
    INVALID_OVERRIDE = "invalid_override"
    #: A selector naming an element the bound projection does not contain.
    INVALID_REFERENCE = "invalid_reference"
