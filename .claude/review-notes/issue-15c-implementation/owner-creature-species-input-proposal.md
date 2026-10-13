# CRD Issue 15c — proposed bounded creature species input

**Proposed, not approved or implemented.** This is separate from source-defined C8 creature-type facts and their exact native semantic acceptance. Prepare the native packet while this input authority remains held; consolidate the Owner questions when the packet is reviewable.

## Why a decision is necessary

The accepted Ghoul Claw predicate spares Undead and Elves. Validated character species identity already answers Elf status. For generic role Humanoids, the source explicitly allows varied species (`monsters.md:55`), while `CreatureState`/validation currently record template, summon and type but no species identity. Missing descriptive tags, table residence or a Humanoid type do not establish not Elf. A source-fixed type fact cannot manufacture individual species data.

Current bounded GM input approvals cover spatial relationships, recovery timing and hand/grip facts. They do not explicitly authorize individual species identification. This is a true input-policy decision, not a question about whether Ghoul is in scope. That admission is already promised; its incomplete target qualification remains a coverage gap.

## Recommended narrow approval

Permit an auditable, subject-bound selection of an exact accepted species identity from code-generated options **only when the creature's accepted source template leaves individual species open**. Code must:

- Bind the selection to the named creature instance, exact template/species authority and revision. Identify eligible templates from source authority; a name or missing tag is insufficient.
- Offer only represented species identities compatible with the source-fixed type and other relevant constraints. Refuse conflicting fixed source identity, contradictory effects/forms, absent authority, unknown or unrepresented species. Missing selection cannot default to non-Elf.
- Record the selected identity and its provenance through the owned state/audit path. Recheck bindings/revisions at delivery and invalidate affected cached facts or certifications after identity, template or relevant form changes.
- Use this identity only for the bounded target qualification. Selection grants no species traits, actions, numeric adjustments, character-build legality, arbitrary type changes or general transformation mechanics. Respect public visibility in labels/audit projections.

This allows the code to recognize both an explicitly selected Elf and an explicitly selected other admitted species without trusting a free-text taxonomy assertion. Ordinary character species and independently valid Undead exclusion remain unaffected.

## Alternatives and held work

**Approve the bounded input:** implement the minimum validated representation and positive/negative target proof within the same CRD Issue 15c PR, after exact C8 semantic acceptance wherever new facts are required.

**Keep this input unapproved:** continue refusing the specific Ghoul operations whose creature-instance Elf status cannot be established. That remains an AC2/4/7 gap and prevents full merge readiness unless the Owner explicitly reconciles the promised scope; it is not an accepted exclusion today.

No implementation or policy acceptance is inferred from this proposal, a peer message or candidate preparation. No general inventory, faction, species-trait, form or encounter engine is proposed. Merge and shared-runtime boundaries remain held.
