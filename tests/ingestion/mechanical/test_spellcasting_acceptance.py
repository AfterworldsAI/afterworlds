"""Spellcasting, its one resolution: the recorded chain (#132, #137).

``.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py``
recorded ``oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json``, which accepts this
batch in two native steps under the one Owner approval: ``accept_proposal``
over the thirteen-batch Equipment state, then one ``resolve_references`` action
carrying the one reviewed draft. These tests rebuild both states through the
seams and hold the fourteen-batch state to the prefix the committed file
preserves; they hold the prior's batches, 216 records, 49 resolutions and
their authorizations preserved inside it; and the resolution to the reviewed
draft under the Owner's authorization. The committed file is the superseded
release's, read by path: the production resolver refuses its binding. The
check that held the fourteen-batch state to what blocked publication judged it
against that release's corpus, which is not rebuilt; it is retired (see
``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_violations,
)
from tests.ingestion.mechanical._replacement_chain import (
    REPLACEMENT,
    animals_recorded,
    identity,
    kept_whole,
    through,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


#: The Spellcasting generator states the reviewed draft.
GENERATOR = _load("spellcasting_gen", NOTES / "issue-5d-spellcasting-generator.py")
BATCH = "spellcasting"
#: The thirteen-batch state and this batch over it, rebuilt through the seams.
PRIOR: AcceptedInputs = through("equipment")
FINAL: AcceptedInputs = through(BATCH)
#: The superseded release's committed file, read by path as historical evidence.
_resolved = load_accepted_inputs(REPLACEMENT.ACCEPTED_PATH)
#: The Animals recording, rebuilt at its recorded bytes: the last recording
#: that held this batch's Equipment state. The committed file
#: (:data:`_resolved`) keeps it outside the replaced Equipment batch.
COMMITTED: AcceptedInputs = animals_recorded()


def test_the_committed_file_preserves_both_steps_replayed_over_the_prior() -> None:
    assert (
        serialize_accepted_inputs(_resolved) == REPLACEMENT.ACCEPTED_PATH.read_bytes()
    )
    # Every item of the fourteen-batch state is kept (a loaded file holds its
    # batches in canonical order, not recorded order).
    assert not kept_whole(FINAL, COMMITTED)
    # The Animals recording records the one approval time for the Spellcasting items.
    assert {a.accepted_at for a in COMMITTED.acceptances if a.batch_id == BATCH} == {
        REPLACEMENT.ACCEPTED_AT
    }


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    assert [b.batch_id for b in FINAL.batches][-1] == BATCH
    (batch,) = [b for b in FINAL.batches if b.batch_id == BATCH]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    mine = [a for a in FINAL.acceptances if a.batch_id == BATCH]
    assert len(mine) == 72 and set(batch.resolved_scope) == {a.span_id for a in mine}
    assert {(a.reviewer, a.accepted_at) for a in mine} == {
        (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
    }
    records = len(FINAL.oracle.representation.records)
    assert records - len(PRIOR.oracle.representation.records) == 19


def test_the_thirteen_prior_batches_and_49_resolutions_are_preserved() -> None:
    prior, final = PRIOR.oracle, FINAL.oracle
    assert (len(PRIOR.batches), len(prior.representation.records)) == (13, 216)
    assert len(prior.reference_resolutions) == 49
    # Whole-payload multiset inclusion, and the first thirteen batches equal.
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(PRIOR), accepted_inputs_payload(FINAL)
    )
    assert FINAL.batches[:13] == PRIOR.batches
    assert (FINAL.lifts, FINAL.policy_transitions) == (
        PRIOR.lifts,
        PRIOR.policy_transitions,
    )
    assert final.schema_version == prior.schema_version
    assert final.binding == prior.binding
    assert (
        len(FINAL.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (14, 235, 1497, 169, 50)


def test_the_one_resolution_is_the_reviewed_draft_under_the_owner() -> None:
    assert FINAL is not None
    final = FINAL.oracle
    old = {r.resolution_id for r in PRIOR.oracle.reference_resolutions}
    new = {r for r in final.reference_resolutions if r.resolution_id not in old}
    assert len(new) == 1
    assert new == set(GENERATOR.draft_resolutions(final.binding))
    assert {(r.scope_key, r.target_record_key) for r in new} == {
        ("srd-5.2.1/spells", "spells.attack_rolls")
    }
    authorizations = [
        a for a in FINAL.reference_resolution_acceptances if a.resolution_id not in old
    ]
    assert {a.resolution_id for a in authorizations} == {r.resolution_id for r in new}
    assert {
        (a.authorized_by, a.reviewer, a.authorization_reference, a.resolved_at)
        for a in authorizations
    } == {
        (
            REPLACEMENT.OWNER,
            REPLACEMENT.OWNER,
            REPLACEMENT.AUTHORIZATION_REFERENCE,
            REPLACEMENT.ACCEPTED_AT,
        )
    }
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
