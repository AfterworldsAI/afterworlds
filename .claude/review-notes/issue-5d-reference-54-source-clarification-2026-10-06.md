# CRD Issue 5d - reference 54: stat-block destination clarification

Verified 6 October 2026. Source-backed direction for the next candidate, not an
exact target proposal, acceptance, recording, or publication authorization.

## Owner clarification

> 54: This one is, I think, rather straight forward. The only reason to include a local stat bloc of a monster or animal is because it does not appear in the bestiary (or the version that appears has a special ability or weakness not listed in the bestiary stat bloc). So items without a local creature and stat bloc resolve to the bestiary. Items with a local description resolve locally.

## Source rule and disposition

PDF p.209 and qualified magic-items.md:579 explicitly establish the rule:
a capitalized creature name in bold points to its stat block; the default
location is Monsters unless the text states otherwise. Follow the source's
explicit destination, including a local block when supplied. Do not route a
local replacement to a similarly named bestiary creature. The bestiary includes
the source's Animals material. No new Owner Decision or schema is demonstrated
by this destination rule; the remaining work is ordinary complete target
inventory and reader coverage.

Where an item modifies an existing bestiary creature without providing a full
local block, preserve both the referenced base statistics and the item-specific
modifications. Local prose does not automatically replace the base block. This
is source composition, not a new creature or merged canonical record.

## Representative verified cases

- Bronze Griffon (PDF p.222; magic-items.md:2098) explicitly names Griffon.
  Its bestiary stat-block destination exists as `monsters.griffon.griffon`.
- Ebony Fly (PDF p.222; magic-items.md:2100) explicitly directs to the
  accompanying Giant Fly block. Its existing destination is
  `magic_items.figurine_of_wondrous_power.giant_fly`, not a bestiary substitute.
- The Skull card (PDF p.232; magic-items.md:2937) explicitly directs to the
  accompanying Avatar of Death block. Its existing destination is
  `magic_items.mysterious_deck.avatar_of_death`.
- Onyx Dog (PDF p.222; magic-items.md:2118) uses the Mastiff stat block
  (`animals.mastiff`), with local Intelligence 8, Common speech, and Blindsight
  60 feet. The item supplies these modifications, not a complete replacement
  block. Resolving to Mastiff must not lose that local modifying prose.

The examples verify the disposition, not an exhaustive named-creature target
inventory. Bold item names, item-variant labels, and explanatory references must
not be counted as creature-stat-block references merely because they are bold.
The already-resolved sibling pointer explaining how to read stat blocks remains
distinct from reference 54's destination-location pointer.

## Next candidate and protected state

Claude Code should prepare complete source-grounded coverage of reference 54,
using existing records, preserving local ownership and explicit exceptions,
and proving the effective reader exposes the required stat blocks and relevant
item context. Do not assume recursive reference following, invent an aggregate,
or mint a creature record solely to receive this citation. Make local-block
exceptions explicit in the Monsters-scoped citation's reconciliation.

The oracle remains SHA-256
`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`:
1,476 resolutions, ten remaining reference findings. No candidate or native
reader verification was run for this clarification. Exact candidate acceptance
is still required before recording; publication, activation, commit, push,
merge, shared-database writes, and dependency repairs remain outside this work.
