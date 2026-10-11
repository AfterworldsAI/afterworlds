# CRD Issue 2b G1 — Equipment successor candidate (semantic review packet)

**Candidate only. Not accepted, recorded, committed, published or activated.**
Every approval inside the preview artifact is a labelled **simulation**
(`reviewer = "SIMULATION - not an Owner approval"`, rule `"SIMULATION ONLY - CRD
Issue 2b G1 candidate; not an Owner acceptance or authorization"`, time
`2026-10-10T00:00:00Z`). The Owner's decision is requested through the
consolidated packet `../../../../G1-OWNER-ACCEPTANCE.md` (SHA-256 `9a3c9414…`);
this README raises no separate semantic question.

## Pins

| Item | Value |
| --- | --- |
| G1 Equipment proposal identity | `8a8a737b0d1e47410de86bbeca44b66522b46511e078727d20760678943b5345` |
| Rendered proposal | `candidate/issue-2b-g1-equipment-PROPOSAL.json`, SHA-256 `d1385de0f02af5f63bd218c1fb2f6acc58857e1e7e6bb3e04a4fa28815ab4508` |
| Preview artifact (simulated receipts) | `candidate/srd-5-2-1-corpus-8781d4e0-a3b-g1-candidate.json`, SHA-256 `bfd0d371fc7ee3cecee45bb607b5b709050347ddf9766b4a442783a966076082` |
| Preview oracle identity | `3e7b27dbb291eb11ca7489719442308397b091d745beb3e48a517bf38685c05a` |
| Preview projection | `efab27a9-5d44-52ba-ad74-47940d5fd717` |
| Schema | `5d-representation-schema-18`, hash `276c3d0ca0bf4c2f98aa8e7d2db6cd321d7fb55dee6d8c60fdd4a58e51fa8701`; lift `5d-lift-schema-17-to-18` |
| Replaced Equipment proposal | `390f63672ea035abb0c8f0ae2efd4cffda81753df8089daee372931b5618d728` |
| Prior accepted oracle (unchanged) | `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json`, SHA-256 `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`; release `1299484e-c72d-509b-bd8d-d0169ee1f8d2`; projection `1f0db408-ee07-5e8d-897d-29838d614c53`; oracle identity `c4e0ac6a…e681` |
| G1 generator | `issue-2b-g1-equipment-generator.py` SHA-256 `d6463b3c…ffe4`; diff vs the recorded `issue-5d-equipment-cited-targets-generator.py`: `issue-2b-g1-equipment-generator.diff` (`53886cd3…e1e4`, +304/−10) |

Recording with real Owner approvals will change only the acceptance-evidence
fields (reviewer, time, rule) of the Equipment batch; the proposal identity,
oracle identity and projection above must stay fixed.

## Content

- **Twelve identities** as named records, each owning its own table row and read and cited like the accepted row it mirrors: `equipment.weapons.{dart, glaive, halberd, lance, maul, trident, war_pick, whip, blowgun}`, `equipment.armor.{scale_mail, ring_mail}`, `equipment.adventuring_gear.needles`. Each is a `catalogue_member` of its section.
- **Structured category and mastery for all 38 weapons**: one `weapon_category` (`simple`/`martial`, from the row's group row) and one `weapon_mastery` (the eight printed properties) fact per Weapons-table row. Each row component becomes `mixed`; the rest of the row stays governing prose under its prior retention reason. Melee/Ranged is not typed (the printed *Category* is Simple or Martial).
- Records 1,835 → 1,847; components 3,956; spans 10,493 → 10,495 (Halberd+Lance and War Pick+Whip were shared section spans, now split); references 8,047 → 8,104; relationships +12; resolutions 1,486 unchanged.
- **Authoring choice disclosed:** the Needles row owns the Ammunition table's close, because a bare close duplicates the Arcane Focuses close in the same entry and spans are keyed by (entry, text).

## How it was built (no whole-corpus re-recording)

The recorded native chain pickle is absent from this clone; recapturing it would
have meant rebuilding retired release orders and replaying every batch, so it was
not used. Instead (`scripts/`):

1. `regen_control.py`: the recorded generator plus the accepted class-eligibility edit, built against an isolated rebuild of the release (all six binding coordinates equal the oracle's), reproduces the recorded Equipment proposal identity `390f6367…` exactly.
2. `identity_control.py`: excising the Equipment batch (`excise.py`) and re-accepting that unchanged proposal natively reproduces the prior `oracle_identity` and every oracle payload key. Only evidence differs: the batch's proposal identity (re-declared at 17) and its anchor position (`reports/identity-control.json`).
3. `build_candidate.py`: the same excision, then native `accept_proposal` of the G1 proposal (records the 17→18 lift); round-trips byte-equal through `load_accepted_inputs`.

## Evidence

| Check | Result |
| --- | --- |
| `verify_candidate.py` (`reports/verify-candidate.json`) | 32/32 pass: candidate 0 native findings; persist → reconstruct → re-identify; read-only publication gate passes for the candidate with 0 failures, and each projection is refused against the other oracle; the other 23 batches, their acceptance/review-unit records and anchors, all 1,486 resolutions and their records, all non-Equipment spans, review units and representation elements byte-identical; prior SHA unchanged. Under the schema-18 build the prior is refused for its schema-17 declaration **only**. |
| `source_catalogue_check.py` (`reports/source-catalogue-check.json`) | Catalogue derived from the pinned Markdown and the official PDF (Weapons p.91, Armor p.92, Ammunition p.96, Category p.89, Mastery Properties p.90; `reports/source-locators.json` gives each row's Markdown line); both sources agree on 38 weapons, 13 armor and 5 ammunition rows. Prior: exactly the 12 missing identities and 76 missing weapon facts. Candidate: clean. No artifact count consulted. |
| `identity_census.py` (`reports/identity-census.json`) | Informational, see boundaries. |
| Existing citations naming the twelve | One: `"+1 Lance"` → `magic_items.weapon_1_2_or_3` (correct, unchanged). |
| Independent Codex review | `../../../../review-evidence/INDEPENDENT-REVIEW.md` (SHA-256 `9baa01c0…`). Review evidence, not acceptance. |

## Engineering in this workstream (`src-and-tests.diff`)

- `representation.py`, `projection.py`, `schema_lift.py`: schema 18 (two families, two vocabularies, registered lift); `verify_lift` proves the prior byte-identical under 18.
- `oracle.py`: `SUPERSEDED_ORACLE_SHA256`, **empty**. Resolution skips a listed same-release file so a recorded successor can be the one claimant while the prior stays byte-for-byte. Adding `def7caa1…` belongs to recording, not to this checkpoint.
- Tests: schema-18 exemplars and legality cases, mint pins and canaries, the bounded fixture lifted 17→18 (byte-equal to native lifted inputs), and `test_oracle_succession.py`.

## Boundaries for the Owner/recording

- **Recording is one step.** Under the schema-18 build, the committed schema-17 oracle is refused by production publication (no lift on that path). The schema change therefore cannot land without the recorded successor, its digest-supersession entry, wheel/sdist exclusion of the prior, and the README's one-file-per-release wording. Publication or activation of `efab27a9…` (replacing local active `1f0db408…`) needs separate authorization.
- **Item identity beyond G1 (not added):** Mounts (8), Tack/Harness/Drawn Vehicles (10), large vehicles (5) and focus forms (10) have no record or component identity. Spell Scroll's two rows belong to the existing `spell_scroll` record (a census false positive). This bears on 2b item instances; it is outside G1's approved twelve.
- **Cost of a later Melee/Ranged fact:** it would need a schema-19 lift and another successor.
