"""The schema pins this suite states once — CRD Issue 5d.

Minting one representation schema used to restamp the same three facts across
nineteen files: *which contract this build declares*, *which registered
crossings a prior has to make to reach it*, and *which version string is still
unminted*. None of those three is a historical anchor — they are expectations of
the **current** contract, repeated. Repeating them is not independent
verification; every copy was transcribed from the same registry, so a mint
edited twenty transcriptions of one decision.

They are stated here instead, and every one is written out rather than read back
from the production value it is meant to check. A pin derived from
``representation_schema_hash()`` asserts nothing.

What deliberately stays outside this module, and why:

* **Historical anchors.** Every ``SCHEMA_<n>_VERSION``/``SCHEMA_<n>_HASH`` pair
  stays in ``schema_lift``, and every test naming one keeps naming it. Those
  are fixed fingerprints of contracts that are finished; nothing about a later
  mint may move them.
* **The independent canaries.** ``EXPECTED_SCHEMA_HASH`` in
  ``test_representation_schema_identity``, the declared pair in
  ``test_review_round_7_draft_exact_types``, and the patch-layer hash in
  ``tests/services/rules_authority`` stay written out where they are. Their
  whole job is to fail when the schema moves without review, so they must not
  be able to agree with this module by construction.
* **The full-chain canary.** ``test_committed_accepted_authority`` keeps the
  whole schema-3-to-current chain listed literally, so one site still states the
  succession end to end without consulting :data:`REGISTERED_CROSSINGS`.
* **Per-version semantics.** A module that subtracts, admits or refuses one
  specific version — the merged-version key sets, the sibling-refusal sets —
  names that version itself. Those are decisions about that schema, not repeats
  of which schema is current.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_VERSION,
    SCHEMA_4_VERSION,
    SCHEMA_5_VERSION,
    SCHEMA_6_VERSION,
    SCHEMA_7_VERSION,
    SCHEMA_8_VERSION,
    SCHEMA_9_VERSION,
    SCHEMA_10_VERSION,
    SCHEMA_11_VERSION,
    SCHEMA_12_VERSION,
    SCHEMA_13_HASH,
    SCHEMA_13_VERSION,
)

#: The contract this build declares. Two lines a mint edits, in place of the
#: same pair restamped across four modules. Still a pin, not a lookup: it names
#: schema 13 explicitly, so a build that changes ``REPRESENTATION_SCHEMA_VERSION``
#: without touching this line is caught by the canary in
#: ``test_schema_6_succession``.
CURRENT_SCHEMA_VERSION = SCHEMA_13_VERSION
CURRENT_SCHEMA_HASH = SCHEMA_13_HASH

#: The next version string no succession has minted. The payload-refusal probes
#: move here when a mint makes the previous probe real, rather than being
#: retired — which is the point of those tests.
UNMINTED_SCHEMA_VERSION = "5d-representation-schema-14"

#: Every registered crossing, oldest first, as ``(from_version, lift_id)``.
#: Written out rather than derived from version order: deriving
#: ``schema-{n}-to-{n+1}`` would make a missing registration inherit a name it
#: never earned, and an unreviewed inheritance is the failure this whole area
#: guards against. One line is added per mint, here.
#:
#: ``test_schema_6_succession`` asserts this list *is* the registry, so it
#: cannot drift from ``SCHEMA_LIFTS`` unnoticed.
REGISTERED_CROSSINGS: tuple[tuple[str, str], ...] = (
    (SCHEMA_3_VERSION, "5d-lift-schema-3-to-4"),
    (SCHEMA_4_VERSION, "5d-lift-schema-4-to-5"),
    (SCHEMA_5_VERSION, "5d-lift-schema-5-to-6"),
    (SCHEMA_6_VERSION, "5d-lift-schema-6-to-7"),
    (SCHEMA_7_VERSION, "5d-lift-schema-7-to-8"),
    (SCHEMA_8_VERSION, "5d-lift-schema-8-to-9"),
    (SCHEMA_9_VERSION, "5d-lift-schema-9-to-10"),
    (SCHEMA_10_VERSION, "5d-lift-schema-10-to-11"),
    (SCHEMA_11_VERSION, "5d-lift-schema-11-to-12"),
    (SCHEMA_12_VERSION, "5d-lift-schema-12-to-13"),
)


def crossings_from(from_version: str) -> list[str]:
    """Every registered crossing from *from_version* to the current contract.

    A slice of :data:`REGISTERED_CROSSINGS`, so a prior reviewed under any
    schema states its expected chain by naming its own schema and nothing else.
    Raises if *from_version* is not the source of a registered crossing, because
    a prior that cannot be lifted must not silently expect an empty chain.
    """
    sources = [source for source, _ in REGISTERED_CROSSINGS]
    return [
        lift_id for _, lift_id in REGISTERED_CROSSINGS[sources.index(from_version) :]
    ]
