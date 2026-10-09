# Owner Decision - Wizard starting-equipment Spellbook reference

Recorded 6 October 2026 for CRD Issues 5c and 5d (#132, #137), inventory
reference 39. This is an accepted direction for source ownership and scope;
it is not acceptance of an exact candidate or a recorded reference resolution.

## Owner instruction

> 39: Owner Decision: This starting-equipment pointer should be resolved to the Wizard-owned spellbook description, and its current scope should be reconciled accordingly. Spellbooks are made by a wizard for his or her own use. They are not an Equipment item for sale. That doesn't mean spellbooks can never be bought. I image an adventuring group lacking a wizard would be happy to sell the evil evoker's spellbook they recovered from his tower after defeating him.

## Decision

Resolve the Spellbook pointer in Wizard starting equipment to the Wizard-owned
spellbook description. Reconcile its current Equipment scope with that class
ownership. No separate Equipment spellbook item, price, or substitution of the
ordinary Book entry is authorized or needed.

This is not a prohibition on selling a recovered spellbook. It establishes the
ownership of the starting-equipment reference; it does not define a resale
price, market, or new availability rule. Preserve the source's personal-use,
reading, contents, and copying rules.

## Verified source and existing representation

- Official SRD 5.2.1 PDF p.77: Wizard Core Traits includes Spellbook among the
  starting-equipment choices; p.78: the Spellbook subsection describes the
  unique book created during wizardly apprenticeship. Qualified source:
  [classes.md:9765](../sources/community/dnd-5e-srd-markdown/classes.md#core-wizard-traits)
  and classes.md:10152-10156. Expanding and Replacing a Spellbook is separate
  supporting source at classes.md:10190-10198.
- Accepted source citation: `classes.wizard` / `core_traits`, printed wording
  `Spellbook`, current scope `srd-5.2.1/equipment`, empty target.
- Existing destination: `classes.wizard.spellcasting`, whose `spellbook`
  component and prose bindings already describe the intended object. Existing
  Wizard-target references use the class scope `srd-5.2.1/classes`.
- The oracle remains SHA-256
  `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`:
  1,476 resolutions and ten remaining reference findings. No candidate was
  generated or applied to verify a new effective mapping for this decision.

## Implementation and acceptance boundary

Claude Code's next bounded candidate should apply this direction using the
existing destination and the smallest supported scope reconciliation. Preserve
the historical accepted citation and evidence: its source wording and original
scope are part of its current identity, and the native empty-target resolution
path currently matches that identity exactly. The candidate must make the class
scope reconciliation explicit rather than silently rewriting accepted bytes or
pretending that the spellbook is Equipment-owned. Do not pad a route with
unnecessary destinations to evade a contract limitation. Any required contract
change must be visible in the candidate and its review.

Prove that the effective pointer exposes the Wizard's spellbook description,
with correct provenance, scope, persistence, and reader behavior. The final
exact candidate still requires separate Owner acceptance before recording.
There is no commit, push, merge, publication, activation, shared-database write,
dependency repair, or acceptance of the other remaining references here.
