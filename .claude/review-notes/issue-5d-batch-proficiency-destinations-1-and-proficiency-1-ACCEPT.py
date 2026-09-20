"""Record the Owner's acceptance of `proficiency-destinations-1` then
`proficiency-1` into the committed accepted authority — CRD Issue 5d.

This is the shared per-batch acceptance workflow the seven accepted batches
used, applied once to a **pair**. It re-derives the exact two objects the Owner
named, calls the one native acceptance seam twice in the authorized order, and
asserts that what landed on disk is what was authorized and nothing else. The
reviewer recorded in the artifact is therefore the Owner, not the agent that ran
this file.

**Why one script and not two.** The two batches are one acceptance action with
an internal order: `proficiency-1` cites four records that do not exist until
`proficiency-destinations-1` is accepted, so a destination has to be accepted
before the batch pointing at it can be. Split into two scripts, the second one's
`--verify` would need a frozen copy of an *intermediate* eight-batch artifact
that was never committed and that nothing else has any use for. One script needs
one frozen prior — the committed seven-batch state — enforces the order in code,
and cannot be replayed half-applied.

**Both proposals are reconstructed from their committed PROPOSAL.json, in every
mode.** The other ACCEPT scripts rebuild the reviewed proposal in acceptance
mode by executing the reviewed generator. That is not available here and would
be wrong if it were: both generators read the *live* accepted artifact as their
prior and assert disjointness against it, so after this acceptance they compare
against an artifact that already holds their own spans, and they also write their
proposal and audit files, which a verification must not do. Reconstruction is not
taken on trust instead: the rebuilt proposal is round-tripped back through
`proposal_payload` and asserted equal to the committed JSON document, and its
`proposal_identity` is asserted to be the hash the Owner's authorization names.
That is strictly the evidence the generator path would produce, without the
coupling.

**The scope is stated here, not read out of the proposal.** `DEST_SCOPE` and
`PROF_SCOPE` are literal span-id tuples in the order the reviewed proposals
emitted them, and `DEST_UNITS` and `PROF_UNITS` are literal review-unit ids. The
proposals are then asserted to propose exactly those and nothing else. Neither
scope is derived from persisted candidate output, and neither is taken from the
artifact this script writes.

**What this does not do.** It does not publish, activate or merge anything. It
invokes no reference resolution: the four citations the destinations batch prints
at *Stat Block*, *Combat Encounters*, the *Combat* subsection and *Opportunity
Attack* have no reviewed destination, and this script asserts they are still
reported as unresolved afterwards. It ingests no source. It creates no second
oracle file — the resolver refuses two artifacts claiming one release, so this
acceptance *extends* the existing one.

Modes:

* default — the acceptance. Extends the live artifact. Writes once, last, after
  every assertion below has passed.
* `--probe` — meaningful only while the live artifact is still the seven-batch
  prior; once the acceptance has run it refuses at the same prior-digest check
  the default mode does. Computes the same merge in memory, writes nothing, and prints the
  three identities of the artifact the acceptance would produce. This is how the
  `MERGED_*` pins below were obtained *before* the acceptance ran, so the
  acceptance run asserted them strictly rather than being allowed to mint them.
* `--verify` — rebuilds the merge against the frozen seven-batch prior and
  asserts the committed artifact is byte-identical to it. Writes nothing.

Run from the repository root:

    python .claude/review-notes/issue-5d-batch-proficiency-destinations-1-and-proficiency-1-ACCEPT.py --verify
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
assert HERE.name == "review-notes" and HERE.parent.name == ".claude", HERE
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
)
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ReleaseBinding,
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    ProposedSpan,
    load_proposal,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    RepresentationDraft,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    relationship_and_reference_violations,
)

MODE_PROBE = "--probe" in sys.argv
MODE_VERIFY = "--verify" in sys.argv
assert not (MODE_PROBE and MODE_VERIFY), "pick one mode"
IS_ACCEPTANCE = not (MODE_PROBE or MODE_VERIFY)

DEST_PROPOSAL_FILE = HERE / "issue-5d-batch-proficiency-destinations-1-PROPOSAL.json"
PROF_PROPOSAL_FILE = HERE / "issue-5d-batch-proficiency-1-PROPOSAL.json"
ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: The frozen prior: a byte-for-byte copy of accepted authority as it stood
#: after the Owner accepted `speed-1`, which is the state both proposals were
#: authored and independently reviewed against. `--verify` merges against this
#: file rather than the live one, so a later acceptance cannot re-date this
#: evidence. It is never written by this script.
FROZEN_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1_cover_1_speed_1.json"
    )
)

for _p in (DEST_PROPOSAL_FILE, PROF_PROPOSAL_FILE, ACCEPTED_PATH, FROZEN_PRIOR_PATH):
    assert _p.exists(), _p

# ---------------------------------------------------------------------------
# The two reviewed proposals, by the identities the authorization names
# ---------------------------------------------------------------------------
DEST_BATCH_ID = "proficiency-destinations-1"
PROF_BATCH_ID = "proficiency-1"
REVIEWER = "Ravenlok (Owner)"

DEST_PROPOSAL_IDENTITY = "723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e"  # noqa: E501  # pragma: allowlist secret
DEST_PROPOSAL_SHA256 = "6a88c886f320aa05cb6c9363b9a5bd1ab5d5c0b551d21832ab2dd2daf035fe1d"  # noqa: E501  # pragma: allowlist secret
DEST_PROPOSAL_BYTES = 139405

PROF_PROPOSAL_IDENTITY = "f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a"  # noqa: E501  # pragma: allowlist secret
PROF_PROPOSAL_SHA256 = "c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d"  # noqa: E501  # pragma: allowlist secret
PROF_PROPOSAL_BYTES = 61375

SCHEMA_VERSION = "5d-representation-schema-15"
SCHEMA_HASH = "e87e0bacdc476b0bef092a04cbedd933e0b57b128651b08ef0ffbd0c94d186fd"  # noqa: E501  # pragma: allowlist secret
POLICY_VERSION = "5d-semantic-policy-2"
POLICY_HASH = "da63b8940c5b3997b44d53e02941389b68e2a2ba35250e73194d38bb1d74cde7"  # noqa: E501  # pragma: allowlist secret

#: The branch head both proposals were reviewed at.
REVIEWED_HEAD = "88d4ec6d7456c5bf3ec43ed974cf6ad2af13d7b0"  # pragma: allowlist secret

#: The Owner's authorization, verbatim, from the brief that ordered this
#: acceptance. Retained in both batch rules below so the artifact carries the
#: actual words the decision was made in rather than a paraphrase written by the
#: process that executed it. No verbatim per-batch acceptance sentence of the
#: form the earlier batches quote exists for this pair; these are the Owner's
#: words that do, and they are quoted rather than improved on.
AUTHORIZATION = (
    "Perform the already Owner-authorized formal acceptance of the two "
    "independently reviewed Proficiency batches under CRD Issue 5d. "
    "Accept these exact full proposals, destinations before Proficiency, with "
    "full explicit span scopes and review-unit scopes, not derived from "
    "persisted candidate output: "
    ".claude/review-notes/issue-5d-batch-proficiency-destinations-1-PROPOSAL.json "
    "identity 723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e, "
    "SHA256 6a88c886f320aa05cb6c9363b9a5bd1ab5d5c0b551d21832ab2dd2daf035fe1d; "
    ".claude/review-notes/issue-5d-batch-proficiency-1-PROPOSAL.json identity "
    "f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a, SHA256 "
    "c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d."
)

#: The independent review the authorization was conditional on, named by where
#: it is recorded and quoted for the sentence that released the hold. Attributed
#: as review, not as authorization: the decision is the Owner's.
CODEX_REVIEW = (
    "Independent review by Codex at branch head "
    "88d4ec6d7456c5bf3ec43ed974cf6ad2af13d7b0, recorded in "
    "pr172-independent-review.md under 'Corrected Option A verdict at "
    "88d4ec6d7456c5bf3ec43ed974cf6ad2af13d7b0', verbatim: 'Verdict: ready for "
    "the already Owner-authorized formal acceptance of the exact two reviewed "
    "proposals. This does not authorize publication, activation or merge.' That "
    "review independently rederived both proposal identities, ran the lifecycle, "
    "proposal/succession and override suites, and confirmed the four Proficiency "
    "links resolve in the merged data while the fourteen reported reference "
    "obligations remain."
)

# ---------------------------------------------------------------------------
# The prior accepted authority, by identities that survive a checkout
# ---------------------------------------------------------------------------
#: Canonical order, which is the order the loaded artifact holds the batches in.
#: Not acceptance order — that is `PRIOR_ANCHOR_ORDER`, and the two differ.
PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "cover-1",
    "hazards-1",
    "speed-1",
]
PRIOR_ANCHOR_ORDER = [
    "conditions-1",
    "hazards-1",
    "actions-1",
    "attitudes-1",
    "areas-of-effect-1",
    "cover-1",
    "speed-1",
]
PRIOR_ANCHOR_SCHEMAS = [
    "5d-representation-schema-3",
    "5d-representation-schema-5",
    "5d-representation-schema-7",
    "5d-representation-schema-8",
    "5d-representation-schema-9",
    "5d-representation-schema-10",
    "5d-representation-schema-11",
]
PRIOR_CONTENT_SHA256 = "eed7df0476445fc6e5d1d9cd6bdd67977f72372bc67b01808eaa240b69a7e619"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "4fcfab6f667923acbaa98345b56a405061287643"  # pragma: allowlist secret
PRIOR_ORACLE_IDENTITY = "d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f"  # noqa: E501  # pragma: allowlist secret
PRIOR_SCHEMA_VERSION = "5d-representation-schema-11"
PRIOR_SCHEMA_HASH = "605e8b4cfdaf0cb6d4f0b65fcf0d23f3e45c4734404c9568f41dc4261eefd037"  # noqa: E501  # pragma: allowlist secret
PRIOR_POLICY_VERSION = "5d-semantic-policy-1"
PRIOR_POLICY_HASH = "e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454"  # noqa: E501  # pragma: allowlist secret
PRIOR_LIFT_IDS = [
    "5d-lift-schema-3-to-4",
    "5d-lift-schema-4-to-5",
    "5d-lift-schema-5-to-6",
    "5d-lift-schema-6-to-7",
    "5d-lift-schema-7-to-8",
    "5d-lift-schema-8-to-9",
    "5d-lift-schema-9-to-10",
    "5d-lift-schema-10-to-11",
]
PRIOR_COUNTS = {
    "records": 48,
    "components": 145,
    "prose_bindings": 49,
    "relationships": 0,
    "references": 62,
    "provenance": 627,
}
PRIOR_SPANS = 594
PRIOR_OBLIGATIONS = 48
PRIOR_FACTS = 190

# ---------------------------------------------------------------------------
# The merged artifact of record
# ---------------------------------------------------------------------------
#: Three identities that fail for three different reasons. The oracle identity
#: covers accepted *content*; the canonical content digest and the Git blob
#: additionally cover the acceptance **evidence** — reviewer, timestamps, batch
#: rules, resolved scopes, review-unit records, anchors, lifts and the policy
#: transition — which the oracle identity deliberately excludes, because
#: re-reviewing an unchanged classification must not remint a projection.
#:
#: All three were obtained by `--probe` before the acceptance ran.
MERGED_ORACLE_IDENTITY = "3b8941ce9039a78e72fd3ddf05952d0da4bed18dc4d38fb99b8b80db137fb407"  # noqa: E501  # pragma: allowlist secret
MERGED_CONTENT_SHA256 = "995976ac1c2b0227d419fc4a7b65a966358e311c7806a1a8f0457a535b4300d7"  # noqa: E501  # pragma: allowlist secret
MERGED_BLOB = "ec645c7e89a126b6ec4778247460449f04da5deb"  # pragma: allowlist secret

#: The **observed execution times** of the two acceptance actions, truncated to
#: the second. Fixed rather than `now()`, because pinning them is what makes the
#: merged artifact reproducible: wall-clock timestamps would give the same
#: accepted content a different file digest on every run, so the pins above
#: could never be asserted. Two values, not one, because they are two acceptance
#: actions and the artifact's own gate requires one distinct timestamp per
#: batch.
DEST_ACCEPTED_AT = "2026-09-20T02:50:55Z"
PROF_ACCEPTED_AT = "2026-09-20T02:50:58Z"

#: How those times are known.
ACCEPTED_AT_BASIS = (
    "Two UTC clock reads taken in the same shell session that ran this script, "
    "both before the run, three seconds apart and in the acceptance order they "
    "are used in, each truncated - not rounded - to the second, and written "
    "into the constants above before the interpreter started. Neither is a wall "
    "clock read at replay and neither is a synthetic midnight. They are the "
    "moments the two acceptance actions were initiated rather than the moment "
    "the bytes landed; the observed write time of the accepted artifact is "
    "recorded in the acceptance checkpoint beside this script rather than "
    "passed off as either value. The session in which this acceptance was "
    "ordered is the session that ran it, whose local date is 2026-09-19 and "
    "whose local times at the two reads were 19:50:55 and 19:50:58 - the "
    "workstation runs seven hours behind UTC, and both readings are stated "
    "rather than one being reported as the other. An earlier pair of reads, "
    "2026-09-20T02:32:04Z and 02:32:07Z, recorded a first run of this script "
    "whose destination rule misstated where thirteen of the seventeen "
    "destination references resolve; that run was reverted with "
    "git checkout before anything was committed, the rule was corrected, and "
    "these later reads time the run that stands. The reverted run is recorded "
    "in the acceptance checkpoint rather than omitted."
)

for _t in (DEST_ACCEPTED_AT, PROF_ACCEPTED_AT):
    assert _t.endswith("Z") and len(_t) == 20, _t
assert DEST_ACCEPTED_AT < PROF_ACCEPTED_AT, "the destination was accepted first"

# ---------------------------------------------------------------------------
# The explicit scopes, stated before anything is loaded
# ---------------------------------------------------------------------------
#: Every span id `proficiency-destinations-1` proposes, in emission order.
DEST_SCOPE = (
    "42e3d51b-52e2-597c-a7d0-1913e05a1771",
    "9c4cab20-550a-5a32-94f3-d5c5fb00bec6",
    "09638d45-b512-5856-ba96-dce4a217596b",
    "a81c1196-e4f7-5d6e-959b-526ed88d2e41",
    "33996d8b-1253-552a-8a3e-509d0ba889e5",
    "443f088b-070b-5cab-a9bb-7308fdd06570",
    "0437f088-3ad7-57ed-9518-dcb7b208103c",
    "f1808a9f-5caf-5d43-b0be-0c0d5881cdd7",
    "4da7c0a3-4e4a-5967-8778-a43116257aa0",
    "481b5698-0671-5767-aabc-36b91bb3b6c1",
    "35659aa7-2e0c-55e7-b8af-f3262250e3cd",
    "f25e82e3-71dd-5b4a-8933-bfb0853c3bc7",
    "b6f79bd9-a4c0-52e6-8694-f1f82e6f1172",
    "579edd53-c223-55b0-a45f-8036e1949cb8",
    "0e5782a0-faba-5ff4-a983-c42715f7ba2f",
    "dc1737c9-b510-51a8-91ac-2502bb776289",
    "448be42e-d25c-5300-9cfc-3bebae549533",
    "7af94041-831d-53d2-b74f-390055a4ab26",
    "2b861ce8-8d3c-5d70-96df-46e8fe6e9b38",
    "524b2c8f-bee6-576d-a417-738b90fcd40e",
    "290b6127-890b-508a-a5ce-72a209d815b4",
    "0b8d22a5-a99a-57e5-9dcd-e0a561ca77f0",
    "2f211b14-13fe-50ee-94ec-bcbff664e0ab",
    "43ec5b29-c4e9-5883-964c-ee85cbbff2e0",
    "c9b0bd38-aa76-5614-93df-405076aadbad",
    "ab21c840-fe1f-56f3-99f8-04d062346f5e",
    "896517c4-9a16-5f73-a112-480eeaf1c1c9",
    "6d879119-c453-5d21-b75a-1b545073502d",
    "df311e0f-4ceb-58a2-9bd8-759bdae1c3c2",
    "16c08c4c-60e9-58ca-9414-9850723f9b02",
    "4dd554ad-195c-5793-a407-ab570cda1cbc",
    "a3ad8b51-4599-512e-bf50-e239c1928809",
    "1c81b8ae-e9c2-5287-bd74-c0309fad0d6c",
    "84868926-496d-5c15-9819-8a2f5acab373",
    "63e8189d-60cd-5afe-9a0a-159795644737",
    "a6529a9e-8ec8-5d9e-bd98-a215f72e2242",
    "ad7584f4-a369-5173-8513-e684d9cf76a5",
    "14744918-02c4-5222-b7a2-20ec340c831b",
    "ef152512-6826-5579-9bfd-5dbd72d20862",
    "5188727a-34d1-5351-84fa-4f3b054af937",
    "65e222a2-5f5e-5aa7-bf51-a40fd8c2890b",
    "b5d08772-e5f2-55e0-9a47-4c69d80e79ad",
    "a15bcd0e-3418-5931-80f6-19530533cd2b",
    "695de6a7-246b-55f9-8085-beb0080dd7eb",
    "5410a3ba-f1ab-535a-a93a-5fe52bad47fd",
    "09d65dac-7226-5eb0-8162-15d977e93f7f",
    "cbce6c99-3e27-5773-9a79-ffda4a60c175",
    "16b95238-9fb2-59b4-bdf1-1ecce9e83c6d",
    "14ff4a98-1be0-5d02-b880-4625f2e8e5e4",
    "79c20fea-2262-539a-9454-834853db6ade",
    "4690ee45-9cb6-5493-9740-7770278f5d3a",
    "31540f45-3a05-509d-ace8-4898332b9114",
    "4dfc320f-51e7-568e-b999-490420f1cc63",
    "718dd3d2-fb43-5f64-b663-b6ff17336fdd",
    "9e97d459-0aee-5165-9b37-21e541216ddf",
    "49821e2a-0418-5411-9c28-677ed8b70877",
    "1eea05e2-845f-5f23-80ae-78706183a374",
    "948d2e71-b4dd-5892-a908-e3eefef02159",
    "7cacf3c0-ca9a-5b53-91bd-6da7ea730938",
    "cb52d546-7aa6-5bdc-b1ec-b3f7fad6440e",
    "3da12366-4df3-55a6-817d-c244ba6f9bd4",
    "c6de6139-c8c9-5af1-9dc3-7fa8dc5bb1d4",
    "aa4536bd-a89e-51e0-a8a2-072d11627329",
    "8d5f85b0-6dca-514d-899a-ebe4be27dfdb",
    "5aef742e-1ade-5415-8e9d-d9fecc871e4b",
    "072d7ba0-9a38-52f4-9d9a-803f4f5c7963",
    "acbc8c2b-dfcb-5ce6-afbd-84c9303f01de",
    "993a5c77-75fd-5371-9310-c27f4cde137e",
    "4dd69e02-09ed-5e4c-9657-47738ea61a58",
    "e06641fe-db95-59aa-81a7-d4608e232635",
    "543f1584-23d6-5fbe-8b6e-eadc70f32b92",
    "6c0b1e8c-9837-59f4-a861-608af32e0c28",
    "deb31bdc-180f-5aa8-89cd-45808395b8f4",
    "14148e78-1f0c-582a-93ef-64e8c1461f65",
    "7211f93a-f957-5aaf-b887-4f8490775a12",
    "f983d033-37c7-5301-bebd-05608ebefbd0",
    "25aec9eb-b25c-55eb-88c6-52ec0332e31d",
    "1a6c2e6b-1283-5fb9-bf9b-8441ee1b66f6",
    "826d1dab-406b-5dce-9158-4716fc3f4343",
    "ef788616-d142-569c-9d61-1b0f8e5c99e7",
    "62ef5944-bc8b-5ff5-a1ec-158e16cc1f9e",
    "ad5368b0-d0bd-5510-9b1e-7b82beda985c",
    "b2aca997-0a57-562f-bc30-5aadc7a1010a",
    "df82fb87-5082-5cb9-8ad5-090c701c41c2",
    "87d60ebc-4286-59f1-8e82-cf9787c9ebf2",
    "0e6ffa84-2ec3-5b07-b174-84adcd156f10",
    "4b06357c-47f4-50e5-9d63-d2bb0d35b515",
    "cd6d4b08-474b-5601-98c5-737430776548",
    "4338966e-1909-564a-bf6b-173b1846f940",
    "80e3cb51-55c1-5884-8e18-3dd5a7e657f8",
    "9d74f39a-22cc-51f0-9613-a9eae55e078c",
    "93241fbe-9060-5d2c-a709-2bb80499f463",
    "b790d644-2abe-5b43-8c83-88147740c157",
    "1edb9bfd-22b8-595c-aaef-629cc9768e60",
    "3d4def3c-864b-5a00-8e1a-864d4b74f668",
    "f4aefc6a-5440-56be-bfcb-c06c8eac2ca0",
    "350e187f-061a-5255-b3b4-fb7655c0c669",
    "56ed4416-dbdc-5692-9b13-1e5b53a8d6d9",
    "f212b70b-d08f-54e1-aca6-6e8026dadf1e",
    "abbd4dc0-791b-5900-9763-5726a1267120",
    "2e0004e2-2f4d-5978-b8b4-7945c8cdc61c",
    "da2e906e-2d5c-5ae5-bf7c-ec62675e13fd",
    "1131d4dd-6100-51a7-982c-0ce93e94112d",
    "8a39ce7a-ce6f-5c9c-8f76-10f492f1927e",
    "963d7cc5-bdf8-57b4-87ef-b857ffc2a087",
    "d68f0296-35fb-5d5e-9050-9e10e745a96c",
    "28d4de27-6de6-5163-9ae4-f8c35774b439",
    "e8e149bf-4f57-5cc9-874a-3af7ecaa1961",
    "7a7caf00-5484-58e4-916e-842cf46b2e90",
    "a9974d19-485f-53f3-8d52-3b4e6f1326e1",
    "69ef93dd-6e1b-5875-9bfb-a9c3ab8ac048",
    "2ffa3561-5881-5f36-8fc1-aef88ac9432a",
    "61b8ee3e-6855-58b4-91c1-b6f6841673ce",
    "ae88f88f-cf88-5397-af89-c7ba86a1765d",
    "1e517119-2310-5e94-9398-986cf113d5be",
    "2003bc13-5eca-53e1-9fb8-d820fd9f91b9",
    "4a59025c-2a9d-50b3-9a58-91cad8ca5e73",
    "988dcfed-4547-5c48-90ac-50c17569c1ca",
    "05923c2f-909f-500f-988f-a34baf300cb2",
    "90444dcc-d94f-548b-a2ee-3918f971cd51",
)

#: Every span id `proficiency-1` proposes, in emission order.
PROF_SCOPE = (
    "120d037c-5783-5923-84a2-e62c90286ea8",
    "9394c1d2-4d5c-589a-9d82-559880829bc8",
    "23392c3b-6777-565c-bf21-9f40f37e631a",
    "ea6a68d7-f63b-54d6-901e-ebb5f7377325",
    "b2713604-2542-5cd4-b7ef-ad955d79940b",
    "8a3f9441-c376-55c3-9ca1-c28d0e8864bb",
    "f0edb0aa-365c-5fdb-99bb-8da070563aa0",
    "2c96d390-620f-5221-a312-ebdb3edab1b0",
    "e1dae7c0-1d50-586b-80b4-80efda5dd0ef",
    "e34ab75a-e48d-5ce9-aad6-ab6d24e0ceba",
    "469024e5-5c06-5093-9474-cbd7756bb526",
    "3af7d80f-ff07-529e-b16e-da22b4f9c33c",
    "57138909-f66b-5df2-b63e-87c3150bb861",
    "1425564a-aa9a-59bc-a657-53e825d8d1eb",
    "a0f678da-3d79-5b71-96dd-a170dc38f837",
    "7ef035f1-5a97-597c-866f-a3e34a00b96f",
    "6ee9426f-a46c-5077-83ed-dc68643c0796",
    "e6893e50-f7a2-5a84-9683-3ad0aa3503d0",
    "e81f89fc-c00c-581f-9579-148238af2e4a",
    "fe2b2531-5ed0-5911-b635-d4ad7e4a37f5",
    "be9dc626-eef4-5a02-91c5-8a284091ba66",
    "b611642f-464e-5a89-b66c-74142d6a0323",
    "27ea6091-6b62-5286-b6c7-c50305a694fc",
    "35ebd462-f194-56f9-a15e-a7f4233d6a6f",
    "9078592f-dd48-5d05-8a39-902262a3ef9f",
    "f085a8f8-ccdc-5c97-a241-f3258eb8b8fb",
    "35aad074-449b-52a9-be70-0789a7e7673f",
    "c96afd21-ea70-52ff-9d3b-75aa68fae08c",
    "9c9c83c5-9ef0-5220-ab11-2c73a7934c50",
    "9d4156f9-6b23-5896-8078-2393157f3faa",
    "38a95007-8038-5f16-b217-7b0af54b393d",
    "d9674944-a2de-590e-b6e3-623642864ab0",
    "5496b8d1-fb24-5ed6-80c0-89bdb039f857",
    "9bbd64a5-10e0-5feb-8580-d1eb91979369",
    "2333d94f-74da-5fdc-a336-894e1de0a6f3",
    "12044246-ef25-53b8-9ee7-75f530039ca1",
    "d6f05f07-625b-5ab0-9d38-4f1614c798e6",
    "336b19d8-e6c1-507a-8bcb-ba7195b9e738",
    "8bbd30f1-6fad-5280-89fd-314de843bda7",
    "72bc5b6c-406d-5ca3-b80a-748ed43f798c",
    "c2012286-6e57-52fe-8733-671c3a881b9f",
    "76d0fe9a-6eef-5dc7-8cc3-8740e28ab010",
    "ef8ac329-29da-5c20-98ed-8f3c3e423f1f",
    "25ecaf72-0f86-58af-b6ed-191d43ab53f3",
    "8f87a8ad-da08-5f03-bdf4-0d58c871dead",
    "f0da0e16-5a36-50ba-b53d-aba43796bbbb",
    "d9bb8dbe-dfc2-50a9-a4b9-477d8c8ec205",
)

#: The review inventory each batch accepts. `resolved_review_units` accumulates
#: across batches and a unit a prior batch recorded cannot be recorded again;
#: these five are the first review units any batch has recorded, because the
#: seven accepted batches predate the inventory and record none.
DEST_UNITS = (
    "proficiency-destinations-1-actions-section",
    "proficiency-destinations-1-challenge-rating",
    "proficiency-destinations-1-expertise",
    "proficiency-destinations-1-skills-table",
)
PROF_UNITS = ("proficiency-1-section",)

# ---------------------------------------------------------------------------
# The expected merged shape, stated before it is computed
# ---------------------------------------------------------------------------
DEST_BATCH_COUNTS = {
    "spans": 120,
    "leaves": 101,
    "records": 4,
    "components": 19,
    "prose_bindings": 70,
    "relationships": 0,
    "references": 17,
    "provenance": 138,
    "facts": 2,
    "substantive": 70,
    "supporting_authority": 50,
    "non_mechanical": 0,
}
PROF_BATCH_COUNTS = {
    "spans": 47,
    "leaves": 19,
    "records": 1,
    "components": 13,
    "prose_bindings": 23,
    "relationships": 0,
    "references": 4,
    "provenance": 63,
    "facts": 18,
    "substantive": 35,
    "supporting_authority": 11,
    "non_mechanical": 1,
}

#: After the first acceptance and before the second, so the order is checked at
#: the point it matters rather than only in the total.
AFTER_DEST_COUNTS = {
    "records": 52,
    "components": 164,
    "prose_bindings": 119,
    "relationships": 0,
    "references": 79,
    "provenance": 765,
}
AFTER_DEST_SPANS = 714

MERGED_COUNTS = {
    "records": 53,
    "components": 177,
    "prose_bindings": 142,
    "relationships": 0,
    "references": 83,
    "provenance": 828,
}
MERGED_SPANS = 761
MERGED_OBLIGATIONS = 53
MERGED_FACTS = 210
MERGED_REVIEW_UNITS = 5

MERGED_BATCH_IDS = sorted([*PRIOR_BATCH_IDS, DEST_BATCH_ID, PROF_BATCH_ID])
MERGED_ANCHOR_ORDER = [*PRIOR_ANCHOR_ORDER, DEST_BATCH_ID, PROF_BATCH_ID]

#: The registered schema successions this acceptance carries the prior across.
#: Four steps, not one: the prior is anchored at schema 11 and both proposals
#: were reviewed under schema 15. The path is asserted as an exact list so a
#: silent re-registration fails here.
EXPECTED_LIFT_IDS = [
    *PRIOR_LIFT_IDS,
    "5d-lift-schema-11-to-12",
    "5d-lift-schema-12-to-13",
    "5d-lift-schema-13-to-14",
    "5d-lift-schema-14-to-15",
]

#: The one semantic-policy succession, recorded in its own field because a
#: schema lift and a policy transition authorize different things.
EXPECTED_POLICY_TRANSITIONS = [(PRIOR_POLICY_VERSION, POLICY_VERSION)]

# ---------------------------------------------------------------------------
# References: what closes, what stays open, and what is never touched
# ---------------------------------------------------------------------------
GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"
PLAYING_SCOPE = "srd-5.2.1/playing-the-game"
TOOLBOX_SCOPE = "srd-5.2.1/gameplay-toolbox"

#: The four links this acceptance closes: `(scope, printed wording)` to the one
#: record each must resolve to. All four are authored by `proficiency-1`; the
#: destination of each is minted by `proficiency-destinations-1`. Asserted to
#: resolve to exactly one target apiece, so "resolves" cannot be satisfied by
#: an ambiguous edge.
ORIGINATING_LINKS = {
    (GLOSSARY_SCOPE, "Challenge Rating"): "glossary.challenge_rating",
    (GLOSSARY_SCOPE, "Expertise"): "glossary.expertise",
    (PLAYING_SCOPE, "Skills table"): "play.skills",
    (PLAYING_SCOPE, "Actions"): "play.actions",
}

#: The ten obligations already accepted authority carries and this acceptance
#: must leave exactly as it found them: nine `speed-1` citations plus the
#: inherited `glossary.concentration`.
PREEXISTING_OUTWARD = tuple(
    f"reference {GLOSSARY_SCOPE}:{text!r}: unknown target record {target}"
    for text, target in sorted(
        {
            "Burrow Speed": "glossary.burrow_speed",
            "Climb Speed": "glossary.climb_speed",
            "Climbing": "glossary.climbing",
            "Concentration": "glossary.concentration",
            "Crawling": "glossary.crawling",
            "Fly Speed": "glossary.fly_speed",
            "Flying": "glossary.flying",
            "Jumping": "glossary.jumping",
            "Swim Speed": "glossary.swim_speed",
            "Swimming": "glossary.swimming",
        }.items()
    )
)

#: The four obligations this acceptance opens: explicit citations the reviewed
#: destinations print at headings no batch has minted a record for. They carry
#: no target at all, so the checker reports `unresolved reference`. This
#: acceptance does not resolve them and invokes no resolution: closing one is the
#: work of whichever batch reviews *Stat Block*, *Combat Encounters*, the
#: *Combat* subsection or *Opportunity Attack*.
NEW_OUTWARD = tuple(
    f"reference {scope}:{text!r}: unresolved reference"
    for scope, text in sorted(
        {
            (GLOSSARY_SCOPE, "Stat Block"),
            (TOOLBOX_SCOPE, "Combat Encounters"),
            (PLAYING_SCOPE, "Combat"),
            (PLAYING_SCOPE, "Opportunity Attack"),
        }
    )
)
EXPECTED_OUTWARD = tuple(sorted(PREEXISTING_OUTWARD + NEW_OUTWARD))
assert len(PREEXISTING_OUTWARD) == 10
assert len(NEW_OUTWARD) == 4

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _identifiers(path: Path) -> tuple[str, str, str]:
    """Raw digest, canonical-LF digest, and Git blob id of one file.

    The canonical digest and the blob id are properties of the *content*; the
    raw digest is a property of a checkout, because `.gitattributes` declares
    `eol=lf` and a working copy predating that attribute can hold CRLF.
    """
    raw = path.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        blob,
    )


def _count_facts(payload: object) -> int:
    """Every fact in a representation payload, including nested ones.

    A fact is an object carrying a `family` discriminator. Counting the
    top-level `facts` lists alone undercounts, because a fact may carry facts.
    """
    if isinstance(payload, dict):
        here = 1 if "family" in payload else 0
        return here + sum(_count_facts(v) for v in payload.values())
    if isinstance(payload, list):
        return sum(_count_facts(v) for v in payload)
    return 0


def _counts(draft: RepresentationDraft) -> dict[str, int]:
    return {
        "records": len(draft.records),
        "components": len(draft.components),
        "prose_bindings": len(draft.prose_bindings),
        "relationships": len(draft.relationships),
        "references": len(draft.references),
        "provenance": len(draft.provenance),
    }


def _reconstruct(path: Path, document: dict[str, object]) -> MechanicalProposal:
    """The reviewed proposal, rebuilt from its committed JSON.

    Deserialization goes through the loader's own field parsers, so a field this
    script forgot to carry cannot be quietly dropped instead of rejected. The
    caller round-trips the result back through `proposal_payload` and asserts
    equality with the committed document, which is what makes "reconstructed
    from the retained proposal" a checked claim rather than an assertion about
    this function.
    """
    loaded = load_proposal(path)
    assert isinstance(loaded, MechanicalProposal), loaded
    assert isinstance(loaded.binding, ReleaseBinding), loaded.binding
    assert all(isinstance(p, ProposedSpan) for p in loaded.proposed_spans)
    assert proposal_payload(loaded) == document, (
        f"the proposal rebuilt from {path.name} does not round-trip to the "
        "committed JSON document"
    )
    return loaded


def _targets_by_citation(draft: RepresentationDraft) -> dict[tuple[str, str], set[str]]:
    """Every destination each `(scope, printed wording)` resolves to.

    A citation resolving to more than one record is the ambiguity the production
    check reports; collecting it as a set is what lets "resolves uniquely" be
    asserted rather than assumed from a passing report.
    """
    targets: dict[tuple[str, str], set[str]] = {}
    for ref in draft.references:
        targets.setdefault((ref.scope_key, ref.source_text), set()).add(
            ref.target_record_key
        )
    return targets


# ---------------------------------------------------------------------------
# 1. The prior accepted authority, asserted before anything is computed from it
# ---------------------------------------------------------------------------
PRIOR_PATH = ACCEPTED_PATH if IS_ACCEPTANCE or MODE_PROBE else FROZEN_PRIOR_PATH

_frozen_raw, _frozen_content, _frozen_blob = _identifiers(FROZEN_PRIOR_PATH)
assert _frozen_content == PRIOR_CONTENT_SHA256, _frozen_content
assert _frozen_blob == PRIOR_BLOB, _frozen_blob

_prior_raw, _prior_content, _prior_blob = _identifiers(PRIOR_PATH)
assert _prior_content == PRIOR_CONTENT_SHA256, (
    "the prior this acceptance extends is not the seven-batch state both "
    f"proposals were reviewed against: {_prior_content}"
)
assert _prior_blob == PRIOR_BLOB, _prior_blob

PRIOR = load_accepted_inputs(PRIOR_PATH)
PRIOR_PAYLOAD = accepted_inputs_payload(PRIOR)

assert sorted(b.batch_id for b in PRIOR.batches) == PRIOR_BATCH_IDS
assert [a.batch_id for a in PRIOR.schema_anchors] == PRIOR_ANCHOR_ORDER
assert [a.schema_version for a in PRIOR.schema_anchors] == PRIOR_ANCHOR_SCHEMAS
assert [lift.lift_id for lift in PRIOR.lifts] == PRIOR_LIFT_IDS
assert PRIOR.policy_transitions == (), PRIOR.policy_transitions
assert PRIOR.review_unit_acceptances == (), PRIOR.review_unit_acceptances
assert PRIOR.oracle.review_units == (), "the prior records no review inventory"
assert PRIOR.oracle.reference_resolutions == ()
assert PRIOR.oracle.schema_version == PRIOR_SCHEMA_VERSION
assert PRIOR.oracle.schema_hash == PRIOR_SCHEMA_HASH
assert PRIOR.oracle.policy_version == PRIOR_POLICY_VERSION
assert PRIOR.oracle.policy_hash == PRIOR_POLICY_HASH
assert oracle_identity(PRIOR.oracle) == PRIOR_ORACLE_IDENTITY
assert len(PRIOR.oracle.spans) == PRIOR_SPANS
assert len(PRIOR.oracle.obligations) == PRIOR_OBLIGATIONS
assert _counts(PRIOR.oracle.representation) == PRIOR_COUNTS
assert _count_facts(PRIOR_PAYLOAD["representation"]) == PRIOR_FACTS
assert not validate_acceptance(PRIOR.classification()), "the prior does not validate"

#: Every span id the prior already accepted, so the disjointness the acceptance
#: seam enforces is also stated here.
PRIOR_SPAN_IDS = {s.span_id for s in PRIOR.oracle.spans}
assert not PRIOR_SPAN_IDS & set(DEST_SCOPE), "a destination span is already accepted"
assert not PRIOR_SPAN_IDS & set(PROF_SCOPE), "a Proficiency span is already accepted"
assert not set(DEST_SCOPE) & set(PROF_SCOPE), "the two scopes overlap"

_prior_record_keys = {r.semantic_key for r in PRIOR.oracle.representation.records}
for _target in sorted(set(ORIGINATING_LINKS.values())):
    assert _target not in _prior_record_keys, (
        f"{_target} is already an accepted record; this pair would not be "
        "minting the destination it says it mints"
    )

# ---------------------------------------------------------------------------
# 2. The two reviewed proposals, by identity, before either is accepted
# ---------------------------------------------------------------------------
_DEST_DOC = json.loads(DEST_PROPOSAL_FILE.read_text(encoding="utf-8"))
_PROF_DOC = json.loads(PROF_PROPOSAL_FILE.read_text(encoding="utf-8"))

DEST_PROPOSAL = _reconstruct(DEST_PROPOSAL_FILE, _DEST_DOC)
PROF_PROPOSAL = _reconstruct(PROF_PROPOSAL_FILE, _PROF_DOC)

for _name, _file, _proposal, _identity, _sha, _size, _scope, _units, _counts_ in (
    (
        DEST_BATCH_ID,
        DEST_PROPOSAL_FILE,
        DEST_PROPOSAL,
        DEST_PROPOSAL_IDENTITY,
        DEST_PROPOSAL_SHA256,
        DEST_PROPOSAL_BYTES,
        DEST_SCOPE,
        DEST_UNITS,
        DEST_BATCH_COUNTS,
    ),
    (
        PROF_BATCH_ID,
        PROF_PROPOSAL_FILE,
        PROF_PROPOSAL,
        PROF_PROPOSAL_IDENTITY,
        PROF_PROPOSAL_SHA256,
        PROF_PROPOSAL_BYTES,
        PROF_SCOPE,
        PROF_UNITS,
        PROF_BATCH_COUNTS,
    ),
):
    # The identity the authorization names, checked two independent ways: the
    # file's own digest, and the content-derived identity of the rebuilt object.
    _raw_sha, _content_sha, _ = _identifiers(_file)
    assert _raw_sha == _sha, f"{_name}: file sha256 {_raw_sha}"
    assert _content_sha == _sha, f"{_name}: canonical sha256 {_content_sha}"
    assert _file.stat().st_size == _size, f"{_name}: {_file.stat().st_size} bytes"
    assert proposal_identity(_proposal) == _identity, proposal_identity(_proposal)

    assert _proposal.schema_version == SCHEMA_VERSION, _proposal.schema_version
    assert _proposal.schema_hash == SCHEMA_HASH
    assert _proposal.policy_version == POLICY_VERSION
    assert _proposal.policy_hash == POLICY_HASH
    assert _proposal.binding == PRIOR.oracle.binding, (
        f"{_name} is bound to a different 5c release than accepted authority"
    )

    # The scope this script states is exactly what the reviewed proposal
    # proposes — in the same order, with no repeat and nothing outside it.
    _proposed = tuple(p.span.span_id for p in _proposal.proposed_spans)
    assert _proposed == _scope, (
        f"{_name}: the scope stated in this script is not the reviewed "
        "proposal's span set in its emission order"
    )
    assert len(set(_scope)) == len(_scope), f"{_name}: the scope repeats a span"
    assert len(_scope) == _counts_["spans"], f"{_name}: {len(_scope)} spans"

    # Likewise the review-unit scope.
    _declared = tuple(sorted(u.unit_id for u in _proposal.proposed_review_units))
    assert _declared == tuple(sorted(_units)), (
        f"{_name}: the review-unit scope stated in this script is not the "
        f"inventory the reviewed proposal proposes: {_declared}"
    )

    # The shape the review packet states, asserted against the proposal.
    assert _counts(_proposal.proposed_representation) == {
        k: _counts_[k]
        for k in (
            "records",
            "components",
            "prose_bindings",
            "relationships",
            "references",
            "provenance",
        )
    }, _counts(_proposal.proposed_representation)
    assert (
        _count_facts(proposal_payload(_proposal)["proposed_representation"])
        == _counts_["facts"]
    )
    assert len({p.span.leaf_id for p in _proposal.proposed_spans}) == _counts_["leaves"]
    for _disposition in ("substantive", "supporting_authority", "non_mechanical"):
        _seen = sum(
            1
            for p in _proposal.proposed_spans
            if p.span.disposition.value == _disposition
        )
        assert _seen == _counts_[_disposition], f"{_name}: {_disposition} {_seen}"
    assert {p.span.review_state.value for p in _proposal.proposed_spans} == {
        "proposed"
    }, f"{_name}: a span is not proposed"

    # Each proposal alone reports the other's records as unknown. Stated so the
    # ordering requirement is evidence rather than an instruction in prose.
    assert relationship_and_reference_violations(
        _proposal.proposed_representation
    ), f"{_name}: reports no outstanding reference on its own, which it should"

# ---------------------------------------------------------------------------
# 3. The batch rules
# ---------------------------------------------------------------------------
DEST_RULE = (
    f"Owner authorization recorded at {DEST_ACCEPTED_AT}, verbatim: "
    f"{AUTHORIZATION!r} {CODEX_REVIEW} Applied to CRD Issue 5d batch "
    f"{DEST_BATCH_ID}, proposal identity {DEST_PROPOSAL_IDENTITY} under "
    f"representation schema {SCHEMA_VERSION} and semantic policy "
    f"{POLICY_VERSION} over 5c release "
    f"{PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 120 spans over 101 represented "
    "5c leaves and 4 records - Challenge Rating and Expertise from the Rules "
    "Glossary, and the Skills table and the Actions section from Playing the "
    "Game - with 70 substantive and 50 supporting-authority dispositions, and "
    "zero unresolved and zero non-mechanical. The accepted review inventory is "
    "four units: one entry unit apiece for Challenge Rating (7 leaves) and "
    "Expertise (4), one table unit for the Skills table (58) and one section "
    "unit for Actions (38); their leaf memberships are disjoint and their "
    "union is exactly the represented leaves of the containers they name. "
    "These are the first review units any batch has recorded, because the "
    "seven accepted batches predate the inventory and record none; they do not "
    "retroactively claim review of anything those batches accepted. Only two "
    "typed facts are carried, both ActionAllowanceFact, accepted since "
    "actions-1: this batch adds no field and no fact family. Seventy prose "
    "bindings carry the rest, five of them under an irreducibility reason code "
    "- one contextual_applicability, one gamemaster_latitude, one "
    "open_ended_effect and two subjective_judgment - and the other sixty-five "
    "under no_identified_structured_use, which states that the clause is "
    "reducible in principle and this build has no identified consumer for a "
    "typed form of it. The batch authors seventeen references, and none of them "
    "resolves to a record this batch mints. Twelve resolve backward into "
    "authority already accepted: the twelve action entries the Actions section "
    "cites - Attack, Dash, Disengage, Dodge, Help, Hide, Influence, Magic, "
    "Ready, Search, Study and Utilize - all of them records actions-1 accepted "
    "and none of them retargeted here. One resolves forward rather than "
    "backward: Expertise cites Proficiency, whose record play.proficiency "
    "proficiency-1 mints in the acceptance immediately after this one, so "
    "between the two acceptances that citation is reported as an unknown "
    "target and the destination batch alone carries fifteen reference "
    "obligations rather than fourteen. That forward link is the reciprocal of "
    "the four this batch exists to receive, and it is closed by the very next "
    "acceptance rather than left open or resolved by decision. The remaining "
    "four carry no target at all "
    "and are reported as unresolved: the citations printed at Stat Block, "
    "Combat Encounters, the Combat subsection and Opportunity Attack, none of "
    "which any batch has minted a record for. Those four are cited, not "
    "ingested - no record, component, fact or span is created for any of them, "
    "no target was invented, and no reference resolution is invoked by this "
    "acceptance. Two 5c containment facts found in review are reported and not "
    "repaired, because no 5c change is in scope: the Skills table container is "
    "nested inside the Actions subsection container because the printed Skills "
    "heading was captured as a paragraph leaf, and the running footer on the "
    "page break between printed pages 9 and 10 is excluded by 5c from the "
    "represented population, so no unit names it. The prior accepted "
    "schema-11 authority is carried forward by the four registered lifts "
    "5d-lift-schema-11-to-12, 12-to-13, 13-to-14 and 14-to-15, and the "
    "accepted reason codes by the one registered policy transition from "
    f"{PRIOR_POLICY_VERSION} to {POLICY_VERSION}; both are recorded as "
    "evidence and neither remints a projection. Accepted before proficiency-1 "
    "because a destination has to exist before the batch that points at it can "
    "be accepted. This acceptance does not publish, activate or merge anything. "
    "Recorded by an agent executing this authorization; the decision is the "
    "Owner's, the review cited above is independent of the agent, and the "
    "execution is not a review."
)

PROF_RULE = (
    f"Owner authorization recorded at {PROF_ACCEPTED_AT}, verbatim: "
    f"{AUTHORIZATION!r} {CODEX_REVIEW} Applied to CRD Issue 5d batch "
    f"{PROF_BATCH_ID}, proposal identity {PROF_PROPOSAL_IDENTITY} under "
    f"representation schema {SCHEMA_VERSION} and semantic policy "
    f"{POLICY_VERSION} over 5c release "
    f"{PRIOR.oracle.binding.package_uuid}/"
    f"{PRIOR.oracle.binding.release_version}. The scope is the complete "
    "proposed span set and nothing outside it: 47 spans over 19 represented 5c "
    "leaves and 1 record - the Proficiency section of Playing the Game - with "
    "35 substantive, 11 supporting-authority and 1 non-mechanical "
    "(flavor_setting) dispositions, and zero unresolved. The accepted review "
    "inventory is one section unit, proficiency-1-section, over 30 leaves; the "
    "section's leaves are 31 in the 5c ledger and the thirty-first, the running "
    "footer on the page break between printed pages 8 and 9, is excluded by 5c "
    "from the represented population, so naming it would claim review of source "
    "the accounting population does not contain. A section unit rather than a "
    "table unit, because 5c represents the Proficiency Bonus table's later "
    "rows - levels and CRs 17 through 30 - outside the table container as a "
    "single paragraph leaf in the subsection container: a table-scoped unit "
    "would have reviewed a progression that stops at +5 and reported no gap. "
    "The one record carries 13 components and 18 typed facts - 8 bonus bands, "
    "4 applications, 3 operation limits, 2 bonus uses and 1 advantage - with 23 "
    "prose bindings and 63 provenance claims. It authors four references, and "
    "all four resolve within this merged authority to the records "
    "proficiency-destinations-1 accepted immediately before it: Challenge "
    "Rating to glossary.challenge_rating, Expertise to glossary.expertise, the "
    "Skills table to play.skills and Actions to play.actions. Each resolves to "
    "exactly one record; none is ambiguous and none was retargeted. It opens no "
    "new obligation of its own, and it closes one: the Expertise entry's "
    "citation of Proficiency, which proficiency-destinations-1 authored against "
    "a record that did not exist yet, resolves to the record minted here. That "
    "is why the intermediate state carried fifteen reference obligations and "
    "the merged authority carries fourteen. The fourteen reference obligations "
    "the merged "
    "authority reports are therefore exactly the ten it inherited - nine "
    "speed-1 movement citations plus glossary.concentration, none of which this "
    "acceptance touches - and the four proficiency-destinations-1 opened. All "
    "fourteen remain publication blockers until the batches that define them "
    "are accepted. The prior accepted schema-11 authority was carried forward "
    "to schema 15 by the four registered lifts recorded with the destination "
    "batch, and the accepted reason codes by the one registered policy "
    f"transition from {PRIOR_POLICY_VERSION} to {POLICY_VERSION}. This "
    "acceptance does not publish, activate or merge anything, invokes no "
    "reference resolution, ingests no source, and changes no accepted "
    "classification. Recorded by an agent executing this authorization; the "
    "decision is the Owner's, the review cited above is independent of the "
    "agent, and the execution is not a review."
)

for _rule in (DEST_RULE, PROF_RULE):
    assert AUTHORIZATION in _rule, "the Owner's words did not survive into the rule"
    assert REVIEWED_HEAD in _rule, "the reviewed head is not attributed"

# ---------------------------------------------------------------------------
# 4. The two acceptance actions, in the authorized order
# ---------------------------------------------------------------------------
AFTER_DEST = accept_proposal(
    DEST_PROPOSAL,
    batch_id=DEST_BATCH_ID,
    rule=DEST_RULE,
    resolved_scope=DEST_SCOPE,
    reviewer=REVIEWER,
    accepted_at=DEST_ACCEPTED_AT,
    prior=PRIOR,
    resolved_review_units=DEST_UNITS,
)

assert len(AFTER_DEST.oracle.spans) == AFTER_DEST_SPANS
assert _counts(AFTER_DEST.oracle.representation) == AFTER_DEST_COUNTS
assert sorted(b.batch_id for b in AFTER_DEST.batches) == sorted(
    [*PRIOR_BATCH_IDS, DEST_BATCH_ID]
)
assert AFTER_DEST.oracle.schema_version == SCHEMA_VERSION
assert AFTER_DEST.oracle.policy_version == POLICY_VERSION

#: The four destinations exist now, and the four Proficiency links still do not
#: resolve, because the batch that authors them has not been accepted yet. Both
#: halves of the ordering claim, stated where the order is.
_after_dest_records = {r.semantic_key for r in AFTER_DEST.oracle.representation.records}
assert set(ORIGINATING_LINKS.values()) <= _after_dest_records
_after_dest_citations = _targets_by_citation(AFTER_DEST.oracle.representation)
for _key in ORIGINATING_LINKS:
    assert _key not in _after_dest_citations, (
        f"{_key} is cited before proficiency-1 is accepted"
    )

#: The destination batch cites Proficiency back, at the Expertise entry, and
#: that record is minted by the batch accepted next. So the intermediate state
#: carries one obligation the merged state does not, and the destination rule
#: says so rather than claiming its references resolve within its own
#: acceptance. Twelve of its seventeen resolve backward into actions-1.
AFTER_DEST_OUTWARD = tuple(
    sorted(relationship_and_reference_violations(AFTER_DEST.oracle.representation))
)
assert len(AFTER_DEST_OUTWARD) == len(EXPECTED_OUTWARD) + 1, AFTER_DEST_OUTWARD
assert (
    set(AFTER_DEST_OUTWARD) - set(EXPECTED_OUTWARD)
    == {
        f"reference {PLAYING_SCOPE}:'Proficiency': "
        "unknown target record play.proficiency"
    }
), set(AFTER_DEST_OUTWARD) - set(EXPECTED_OUTWARD)
assert set(EXPECTED_OUTWARD) <= set(AFTER_DEST_OUTWARD)

ACCEPTED = accept_proposal(
    PROF_PROPOSAL,
    batch_id=PROF_BATCH_ID,
    rule=PROF_RULE,
    resolved_scope=PROF_SCOPE,
    reviewer=REVIEWER,
    accepted_at=PROF_ACCEPTED_AT,
    prior=AFTER_DEST,
    resolved_review_units=PROF_UNITS,
)

# ---------------------------------------------------------------------------
# 5. The merged result, asserted in memory before anything is written
# ---------------------------------------------------------------------------
assert isinstance(ACCEPTED, AcceptedInputs)
assert sorted(b.batch_id for b in ACCEPTED.batches) == MERGED_BATCH_IDS
assert len(ACCEPTED.batches) == len(MERGED_BATCH_IDS), "a batch id is recorded twice"
assert [a.batch_id for a in ACCEPTED.schema_anchors] == MERGED_ANCHOR_ORDER
assert [a.schema_version for a in ACCEPTED.schema_anchors] == [
    *PRIOR_ANCHOR_SCHEMAS,
    SCHEMA_VERSION,
    SCHEMA_VERSION,
]
assert [lift.lift_id for lift in ACCEPTED.lifts] == EXPECTED_LIFT_IDS
assert [
    (t.from_version, t.to_version) for t in ACCEPTED.policy_transitions
] == EXPECTED_POLICY_TRANSITIONS
assert ACCEPTED.oracle.schema_version == SCHEMA_VERSION
assert ACCEPTED.oracle.schema_hash == SCHEMA_HASH
assert ACCEPTED.oracle.policy_version == POLICY_VERSION
assert ACCEPTED.oracle.policy_hash == POLICY_HASH
assert ACCEPTED.oracle.binding == PRIOR.oracle.binding
assert len(ACCEPTED.oracle.spans) == MERGED_SPANS
assert len(ACCEPTED.oracle.obligations) == MERGED_OBLIGATIONS
assert _counts(ACCEPTED.oracle.representation) == MERGED_COUNTS
assert len(ACCEPTED.acceptances) == MERGED_SPANS
assert oracle_identity(ACCEPTED.oracle) == MERGED_ORACLE_IDENTITY, oracle_identity(
    ACCEPTED.oracle
)

#: No reference resolution was invoked. The four unresolved citations are left
#: unresolved by this acceptance, not decided by it.
assert ACCEPTED.oracle.reference_resolutions == ()
assert ACCEPTED.reference_resolution_acceptances == ()

# --- The review inventory ---------------------------------------------------
assert len(ACCEPTED.oracle.review_units) == MERGED_REVIEW_UNITS
assert sorted(u.unit_id for u in ACCEPTED.oracle.review_units) == sorted(
    [*DEST_UNITS, *PROF_UNITS]
)
assert sorted(
    (r.unit_id, r.batch_id) for r in ACCEPTED.review_unit_acceptances
) == sorted(
    [*((u, DEST_BATCH_ID) for u in DEST_UNITS), *((u, PROF_BATCH_ID) for u in PROF_UNITS)]
)
assert {r.reviewer for r in ACCEPTED.review_unit_acceptances} == {REVIEWER}
assert {r.accepted_at for r in ACCEPTED.review_unit_acceptances} == {
    DEST_ACCEPTED_AT,
    PROF_ACCEPTED_AT,
}
assert not review_unit_violations(
    ACCEPTED.oracle.review_units,
    ACCEPTED.oracle.representation,
    ACCEPTED.oracle.policy_version,
    ACCEPTED.oracle.spans,
), "the accepted review inventory is not coverage of what it names"

# --- The two new batches ----------------------------------------------------
_by_batch = {b.batch_id: b for b in ACCEPTED.batches}
for _bid, _identity, _rule, _scope, _at, _counts_ in (
    (DEST_BATCH_ID, DEST_PROPOSAL_IDENTITY, DEST_RULE, DEST_SCOPE, DEST_ACCEPTED_AT, DEST_BATCH_COUNTS),
    (PROF_BATCH_ID, PROF_PROPOSAL_IDENTITY, PROF_RULE, PROF_SCOPE, PROF_ACCEPTED_AT, PROF_BATCH_COUNTS),
):
    _batch = _by_batch[_bid]
    assert _batch.proposal_identity == _identity
    assert _batch.rule == _rule
    assert tuple(_batch.resolved_scope) == _scope
    assert len(_batch.diff) == _counts_["spans"]
    _records = [a for a in ACCEPTED.acceptances if a.batch_id == _bid]
    assert len(_records) == _counts_["spans"]
    assert {a.reviewer for a in _records} == {REVIEWER}
    assert {a.accepted_at for a in _records} == {_at}
    assert {a.span_id for a in _records} == set(_scope)

#: One distinct timestamp per batch, which is the artifact's own gate.
assert len({a.accepted_at for a in ACCEPTED.acceptances}) == len(MERGED_BATCH_IDS)
assert {a.reviewer for a in ACCEPTED.acceptances} == {REVIEWER}
assert not validate_acceptance(ACCEPTED.classification()), validate_acceptance(
    ACCEPTED.classification()
)

# --- The seven prior batches, unchanged -------------------------------------
#
# Not a count and not a sample: the retained evidence of each prior batch is
# compared field for field against the frozen prior, and so are its per-span
# acceptance records, its schema anchor and the eight lifts it was carried
# across. A schema lift that rewrote an accepted span, or an acceptance that
# re-dated a prior reviewer, fails here.
MERGED_PAYLOAD = accepted_inputs_payload(ACCEPTED)
_prior_batches_before = {b["batch_id"]: b for b in PRIOR_PAYLOAD["acceptance"]["batches"]}
_prior_batches_after = {b["batch_id"]: b for b in MERGED_PAYLOAD["acceptance"]["batches"]}
for _bid in PRIOR_BATCH_IDS:
    assert _prior_batches_after[_bid] == _prior_batches_before[_bid], (
        f"the retained evidence of accepted batch {_bid} changed"
    )

_prior_records_before = [
    r for r in PRIOR_PAYLOAD["acceptance"]["records"] if r["batch_id"] in PRIOR_BATCH_IDS
]
_prior_records_after = [
    r
    for r in MERGED_PAYLOAD["acceptance"]["records"]
    if r["batch_id"] in PRIOR_BATCH_IDS
]
assert _prior_records_after == _prior_records_before, (
    "a prior batch's per-span acceptance records changed"
)
assert len(_prior_records_before) == PRIOR_SPANS

assert (
    MERGED_PAYLOAD["acceptance"]["schema_anchors"][: len(PRIOR_ANCHOR_ORDER)]
    == PRIOR_PAYLOAD["acceptance"]["schema_anchors"]
), "the prior schema anchors changed or were reordered"
assert (
    MERGED_PAYLOAD["acceptance"]["lifts"][: len(PRIOR_LIFT_IDS)]
    == PRIOR_PAYLOAD["acceptance"]["lifts"]
), "the prior lift records changed or were reordered"

_prior_spans_before = {s["span_id"]: s for s in PRIOR_PAYLOAD["spans"]}
_prior_spans_after = {s["span_id"]: s for s in MERGED_PAYLOAD["spans"]}
assert set(_prior_spans_before) <= set(_prior_spans_after)
for _sid, _span in _prior_spans_before.items():
    assert _prior_spans_after[_sid] == _span, f"accepted span {_sid} changed"

#: `speed-1`'s recorded scope order, specifically. The Owner's brief names it,
#: and a lift or a merge that canonically re-sorted a retained scope would pass
#: every count above.
assert (
    _prior_batches_after["speed-1"]["resolved_scope"]
    == _prior_batches_before["speed-1"]["resolved_scope"]
), "the recorded Speed scope order changed"

# --- The four links, and the residue ----------------------------------------
_citations = _targets_by_citation(ACCEPTED.oracle.representation)
for _key, _target in sorted(ORIGINATING_LINKS.items()):
    assert _citations.get(_key) == {_target}, (
        f"{_key} resolves to {_citations.get(_key)}, not uniquely to {_target}"
    )

FINDINGS = tuple(
    sorted(relationship_and_reference_violations(ACCEPTED.oracle.representation))
)
assert FINDINGS == EXPECTED_OUTWARD, (
    "the merged reference report is not the fourteen obligations this "
    f"acceptance states:\n  got:      {FINDINGS}\n  expected: {EXPECTED_OUTWARD}"
)
assert _count_facts(MERGED_PAYLOAD["representation"]) == MERGED_FACTS

# ---------------------------------------------------------------------------
# 6. The bytes
# ---------------------------------------------------------------------------
EXPECTED_BYTES = serialize_accepted_inputs(ACCEPTED)
assert b"\r" not in EXPECTED_BYTES, "the accepted artifact would carry CR bytes"
_expected_content_sha = hashlib.sha256(EXPECTED_BYTES).hexdigest()
_expected_blob = hashlib.sha1(  # noqa: S324 - Git's object id
    b"blob " + str(len(EXPECTED_BYTES)).encode() + b"\x00" + EXPECTED_BYTES
).hexdigest()

if MODE_PROBE:
    print("probe only; nothing was written.")
    print("MERGED_ORACLE_IDENTITY =", oracle_identity(ACCEPTED.oracle))
    print("MERGED_CONTENT_SHA256  =", _expected_content_sha)
    print("MERGED_BLOB            =", _expected_blob)
    print("bytes                  =", len(EXPECTED_BYTES))
    _live_raw, _live_content, _live_blob = _identifiers(ACCEPTED_PATH)
    assert _live_content == PRIOR_CONTENT_SHA256, "the probe changed the live artifact"
    sys.exit(0)

assert _expected_content_sha == MERGED_CONTENT_SHA256, _expected_content_sha
assert _expected_blob == MERGED_BLOB, _expected_blob

if IS_ACCEPTANCE:
    ACCEPTED_PATH.write_bytes(EXPECTED_BYTES)

#: The claim the reproduction rests on, deliberately total: the artifact rebuilt
#: from the two retained proposals and the frozen prior is compared **byte for
#: byte** against the committed one. It subsumes every pin above and below —
#: those stay because they name *what* differs when something does, but none of
#: them is what makes the reproduction sound. A field nobody thought to sample
#: still fails here.
_committed_bytes = ACCEPTED_PATH.read_bytes().replace(b"\r\n", b"\n")
if _committed_bytes != EXPECTED_BYTES:
    _expected_doc = json.loads(EXPECTED_BYTES.decode("utf-8"))
    _committed_doc = json.loads(_committed_bytes.decode("utf-8"))
    _differing = sorted(
        key
        for key in sorted(set(_expected_doc) | set(_committed_doc))
        if _expected_doc.get(key) != _committed_doc.get(key)
    )
    raise AssertionError(
        "the merge rebuilt from the two retained proposals and the frozen prior "
        "is not the committed artifact; top-level keys that differ: "
        f"{_differing or ['(none - byte-level difference only)']}"
    )

# ---------------------------------------------------------------------------
# 7. The committed file is the subject from here
# ---------------------------------------------------------------------------
RESULT = load_accepted_inputs(ACCEPTED_PATH)
_result_raw, _result_content, _result_blob = _identifiers(ACCEPTED_PATH)
assert _result_content == MERGED_CONTENT_SHA256, _result_content
assert _result_blob == MERGED_BLOB, _result_blob
assert oracle_identity(RESULT.oracle) == MERGED_ORACLE_IDENTITY
assert accepted_inputs_payload(RESULT) == MERGED_PAYLOAD, (
    "the committed artifact does not reload to the accepted value"
)
assert serialize_accepted_inputs(RESULT) == EXPECTED_BYTES, (
    "the committed artifact does not re-serialize to its own bytes"
)
assert sorted(b.batch_id for b in RESULT.batches) == MERGED_BATCH_IDS
assert len(RESULT.oracle.spans) == MERGED_SPANS
assert not validate_acceptance(RESULT.classification())
assert (
    tuple(sorted(relationship_and_reference_violations(RESULT.oracle.representation)))
    == EXPECTED_OUTWARD
)

#: One artifact for this release, still. The resolver refuses two files claiming
#: one release, so this acceptance had to extend rather than add.
_oracle_dir = sorted(p.name for p in ACCEPTED_PATH.parent.glob("*.json"))
assert _oracle_dir == [ACCEPTED_PATH.name], _oracle_dir

#: The frozen prior is not superseded by this acceptance: it remains the frozen
#: seven-batch state it was created to be, and both of its identities are
#: unchanged in every mode.
_after_frozen = _identifiers(FROZEN_PRIOR_PATH)
assert (_after_frozen[1], _after_frozen[2]) == (PRIOR_CONTENT_SHA256, PRIOR_BLOB)

print(
    "verified" if MODE_VERIFY else "accepted",
    f"{DEST_BATCH_ID} then {PROF_BATCH_ID}:",
    f"{len(RESULT.batches)} batches,",
    f"{len(RESULT.oracle.spans)} spans,",
    f"{len(RESULT.oracle.review_units)} review units,",
    f"oracle {MERGED_ORACLE_IDENTITY[:12]}...,",
    f"blob {MERGED_BLOB[:12]}...,",
    f"{len(FINDINGS)} reference obligations remain.",
)
