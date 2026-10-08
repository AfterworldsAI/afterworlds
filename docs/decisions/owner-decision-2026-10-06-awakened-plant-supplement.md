# Owner Decision - Awakened Plant supplemental template

Recorded 6 October 2026 for CRD Issues 5c and 5d (#132, #137), inventory
reference 57. This records the Owner's source/supplement direction and supplied
content, not an exact candidate acceptance or runtime activation.

## Owner direction

> Let's add a third category of awakened plant called, "Awakened Plant," to the list of 'Awakened Shrub' and 'Awakened Tree.' The DM will match the player choice to the best of those three options to provide a requisite creature stat bloc.

The Owner expressly distinguished the proposed creature from official SRD
content and proposed an Afterworlds supplemental house rule. The supplied
non-combatant block is preserved in [Awakened Plant](../house-rules/awakened-plant.md).
The Owner subsequently selected **3 (1d6) - keep the d6 Hit Die** in response
to the original HP 2 (1d6) average mismatch. No other supplied statistic has
been changed.

## Source rule and reference direction

Official SRD PDF pp.111-112 and qualified spells.md:685-689 leave the GM to
choose statistics appropriate for a natural plant awakened into a creature;
Awakened Shrub and Awakened Tree are explicitly examples. Preserve that open
adjudication. Neither example constitutes an exhaustive eligibility rule.

For the SRD's reference 57, the candidate should expose its existing example
stat blocks and preserve the governing Awaken paragraph's GM-choice wording:
`monsters.awakened_plants.awakened_shrub` and
`monsters.awakened_plants.awakened_tree`. Both individual named references were
already resolved; the held general Monsters pointer remains a distinct citation.
Do not rewrite their accepted identities or declare that every Plant stat block
is automatically appropriate. Exact destination composition and reader coverage
remain for the next bounded candidate.

Offer the Owner's third template as supplemental house-rule content, with clear
Afterworlds provenance. It is not a new SRD monster and cannot be inserted into
the accepted SRD oracle as though the PDF states it. The spell's changes to an
existing Beast or Plant creature remain distinct from choosing new statistics
for a natural plant that was not already a creature.

## Verified implementation boundary

The current house-rule origin is `house_rule`
(`src/afterworlds/models/enums.py`, OverrideOriginEnum). The existing
`ProseAdditionPatch` adds authored text after a component's effective prose
while retaining that existing prose (`services/rules_authority/patches.py`).
This supplies an ordinary way to present the template alongside Awaken without
claiming SRD source provenance or minting a new base creature record.

The closed mechanical override families replace or disable existing targets or
append components, facts, options, and prose within supported targets; they do
not add standalone creature records. A typed, independently queryable supplemental
creature would therefore require a separate content-integration design and
verification. That is a scope boundary, not authority to broaden the restart
into a new supplement engine. No override, shared store, or active Rules Package
was changed for this decision. The prose integration has not been exercised.

## Status and next work

Reference 57's SRD direction is settled as source examples with open GM
adjudication preserved. The supplemental template is a complete Owner-directed
draft, separately identifiable from SRD authority. Its implementation remains
pending through an authorized house-rule path. The next exact SRD candidate
must prove the source pointer's provenance, example destinations, persistence,
and effective reader behavior; the supplemental draft does not itself close
the accepted empty citation.

The oracle remains SHA-256
`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`,
with 1,476 resolutions and ten reference findings. Exact candidate acceptance,
publication block, release-order pass, and existing restart gates remain.
No publication, activation, commit, push, merge, shared-database write,
dependency repair, or unrelated new creature authoring is authorized here.
