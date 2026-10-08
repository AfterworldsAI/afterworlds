# Owner Decision - Cantrip and Ritual reference scope

Recorded 6 October 2026 for CRD Issues 5c and 5d (#132, #137), inventory
references 87 and 88. This settles the intended destination scope, not acceptance
of an exact candidate or recording of either resolution.

## Owner direction

The Cantrip and Ritual glossary entries concern general rules and principles.
Their generic Spells links should expose the relevant casting guidance on SRD
5.2.1 p.104. Individual spell descriptions are specific instances, and linking
these two general entries to the entire spell-description catalogue adds no
useful coverage for this purpose.

- Reference 87 should expose the general Cantrips rule: casting without a spell
  slot. The glossary entry already identifies a cantrip as a level 0 spell.
- Reference 88 should expose the general Rituals rule: the Ritual tag permits
  ritual casting, which takes ten minutes longer, expends no spell slot, and
  requires the spell to be prepared. Preserve the glossary's related restriction
  that ritual casting cannot use a higher-level slot.
- These two references do not require an inventory of individual cantrip or
  ritual spell descriptions, the full spell catalogue, or its embedded creature
  stat blocks. Preserve those accepted records and their ordinary access paths.

This direction supersedes the whole-chapter interpretation for references 87
and 88 in the historical [3 October reference disposition](../../.claude/review-notes/issue-5d-current-reference-disposition-2026-10-03.md).
That interpretation was a review assumption, not an accepted requirement. Keep
that historical evidence intact; do not impose its catalogue-coverage hurdle
on these two candidates.

## Current source and accepted destination evidence

The [official PDF](../sources/DnD5_5e_SRD_CC_v5_2_1.pdf), p.104, supplies both
passages. The qualified source contains the inciting entries at
[rules-glossary.md:379](../sources/community/dnd-5e-srd-markdown/rules-glossary.md#cantrip)
and [rules-glossary.md:1226](../sources/community/dnd-5e-srd-markdown/rules-glossary.md#ritual),
and the destination passages at spells.md:95 (Cantrips) and spells.md:97
(Rituals), under [Casting Spells](../sources/community/dnd-5e-srd-markdown/spells.md#casting-spells).

The current accepted representation already has general-rule record
`spells.casting_spells` with prose-bound components `cantrips` and `rituals`.
It also contains the general spell-level and spell-slot guidance. Existing
accepted resolution `cited-89-glossary.spell-spell` targets that record for a
related general Spells pointer. It is an available destination, not a newly
invented aggregate. The full spell-description catalogue is a separate record,
`spells.spell_descriptions`.

The next candidate may use the existing Casting Spells record as the general
rules destination for each citation. Verify that the effective reader exposes
the relevant passage. Do not invent extra destinations merely to encode a
single component through a multiple-destination contract, and do not introduce
a schema change just to narrow the landing point. Preserve each source
citation's distinct identity, empty record-owned component key, wording,
provenance, and `srd-5.2.1/spells` scope.

## Acceptance and restart boundary

The verified oracle remains SHA-256
`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`,
with 1,476 recorded resolutions. Both held citations still lack resolutions;
ten reference findings remain on disk. All ten now have source or Owner
directions, but their exact candidates remain undrafted and unaccepted.

Claude Code should prepare the bounded candidate with native validation and
reader evidence; Codex reviews it before exact Owner acceptance and recording.
Reuse unaffected accepted evidence. This decision grants no commit, push,
merge, publication, activation, shared-database write, or dependency-repair
authority. Include this decision and the updated restart opening in the normal
restart workflow when authorized.
