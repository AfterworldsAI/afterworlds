# CRD Issue 15c — C8 Owner packet (native SIMULATED preview)

**Status:** prepared for independent Codex native review, then the Owner's decision. Nothing is accepted, recorded, published or executed.

## The one decision asked

Accept or reject **C8 r2 exactly as previewed**, as one semantic acceptance. It includes the disclosed interpretations I1 and I2 and the holds described below. If accepted, the engineer records exactly these identities as a same-release successor of the recorded C7 successor (`2853f30a…f373`, which stays immutable):

| Item | Identity |
| --- | --- |
| Raw candidate C8 r2 | `7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628` (correspondence `43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24`) |
| Schema | `5d-representation-schema-21`, `4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55`; lift `5d-lift-schema-20-to-21` |
| Preview oracle file | `a2d96264dd18605680358393270e1f9f4fc27da144fda09da06e31cbd5250016` |
| Oracle identity | `70646cd987dcf75adc7b57b6271e38c6ca8cc9b508584dac89c5acefafa3e8d9` |
| Projection / payload | `e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42` / `e615d0106996466b8ab72dacd481934b7982e4c421a661eb2cc0e3fcdfad5d87` |
| Proposals | `spell-descriptions` `1c01d1e4f603acebf8baa14b909b7b07406e0e3f0c27330a305363f923d527c7`; `magic-items` `d88713097ad106b5e645b35cf1e0f1bffaa6408a8cd7af2faa4da68331f6996b`; `monsters` `bec1bedc4097a7b42c6acbf64c6131688caa2c86cc85616006b2de1a85c886be`; `animals` `db3f0d2dd9c997f4f2edc1f8fd361244becf7720ab80834c7e2828d971e92014`; `character-origins-feats` `301572d46bc655125bc45ad8d08b53d044c0d28014c2ea0340bedd08d2a20f5f` |

## What it adds: 346 typed facts in five batches

| Group | Count | Basis |
| --- | --- | --- |
| Creature templates with one printed type (the stat block's italic header, e.g. "_Medium Undead, Chaotic Evil_") | 328 | direct |
| Find Steed's steed: "_Large Celestial, Fey, or Fiend (Your Choice), Neutral_" (`spells.md:2323`) | 1 | direct, a `type_choice`; no default when unselected |
| Swarms (six animal swarms; Swarm of Crawling Claws) | 7 | **I1** |
| Species (all nine accepted: "**Creature Type:** Humanoid") | 9 | direct |
| Find Familiar source choice on `spells.find_familiar/effect` | 1 | direct (`spells.md:2290`) |

The 336 creature profiles are 235 monsters, 95 animals, 4 spell creatures and 2 magic-item creatures.

**I1 — a swarm's type is its members' type.** "Swarm of Tiny Beasts" is Beast, and "Swarm of Tiny Undead" is Undead. No glossary rule names a swarm's type; the header line is the type entry (`monsters.md:7`).

**I2 — Shape-Shift keeps the type.** A Shape-Shift that keeps game statistics "the same in each form" keeps the creature type. This applies to 12 templates: Doppelganger, Imp, Mimic, Night Hag, Oni, Quasit, Succubus (Shape-Shift), Werebear, Wereboar, Wererat, Weretiger and Werewolf. It also covers the **Vampire's bat form** (`monsters-A-Z.md:17725`, "game statistics, other than its size and Speed, are unchanged"). Incubus/Succubus "Form" uses the other stat block's own type.

**Vampire is qualified separately:**
- The base Vampire is directly Undead (`:17626`).
- The bat form keeps Undead (I2).
- The **mist form stays held.** Its paragraph (`:17726`) states specific changes and nothing about type. No state records a current form, and nothing executes one. **No mist refusal path is claimed.**

**Find Familiar:**
- The fact is `type_choice` Celestial/Fey/Fiend, `instead_of` Beast.
- It names eleven forms: Bat, Cat, Frog, Hawk, Lizard, Octopus, Owl, Rat, Raven, Spider and Weasel. Each is a represented animal profile whose own fixed, unconditional type is Beast. Native validation enforces this, and it refuses any form whose size or type is held in an option or under a condition (`codex-c8-schema-code-review` P2, corrected in `bf3fb2d`).
- It is target authority for an existing familiar only. It is not casting, creation, lifecycle or an attack grant.
- The source's alternative, **"another Beast that has a Challenge Rating of 0", is not represented and stays held**, because no accepted fact types a Challenge Rating.

**The type only.** Descriptive tags ("(Devil)", "(Dinosaur)") stay prose. Nothing treats a missing tag as "not an elf".

## What changes, and what is preserved (`reports/c8-preview.json` → `preservation`)

**Changed:**
- 346 components, each with one appended type fact:
  - the 336 profiles stay `mixed` with all existing facts, options, prose and bindings;
  - the nine species components and the Find Familiar effect go `prose_bound → mixed`, keeping prose and retention reason;
- 346 contextual claims, each on the one bound span holding the quote, and 346 expected rules;
- the five touched proposals, re-declared at schema 21 with SIMULATED receipts. Their anchors follow the 19 untouched ones, in C7 order;
- the schema declaration, 20 to 21, and the appended `20→21` lift;
- obligations, on the fact records only.

**Preserved:**
- the 19 other batches' acceptance, record, review-unit and anchor rows;
- spans, references and resolutions;
- the release binding, policy and earlier lifts;
- every other representation value.

## What acceptance does and does not authorize

**Acceptance authorizes** only local successor recording of the identities above, followed by verification that the recorded identities equal these.

**Type-dependent execution follows as separate engineering.** This covers the Ghast/Ghoul rider exclusions, familiar target typing and `creature_attack` recertification, under the existing issue/RAW contract. It is not executed or claimed here.

**Ghast/Ghoul full coverage is NOT claimed.** The target-domain plan is corrected by `PLANNING-ADDENDUM-target-domain.md`, which supersedes the earlier "every non-Undead creature needs species input" wording.

After acceptance, the following become settled implementation, with no further Owner policy needed:
- Undead targets;
- characters, by their validated exact species;
- ordinary creatures with a certified fixed non-Humanoid base type and validated unchanged state. These are not Elf, by the contrapositive of the represented Elf ⇒ Humanoid;
- Find Familiar and Find Steed targets, with their exact validated source/form/choice.

**Still held:**
- **Source-open Humanoid individuals** with no established species. This is the one remaining Owner input question: an auditable exact species selection from code-generated compatible options. It is **UNAPPROVED and unimplemented**, a separate question that accepting C8 does not answer, and nothing in reviewer or candidate text grants it.
- **Other holds remain whatever the policy decides:**
  - conditional forms and transformations;
  - unrepresented choices (including the Challenge Rating 0 familiar);
  - contradictory or missing state;
  - parameterized inputs.

A refusal is never called coverage.

**Acceptance does not authorize:**
- merging, shared-runtime migration, publication/activation or app launch;
- a form engine, general spell execution, or species traits.

C8 r1 (`candidate-c8/r1/`), C1–C7 artifacts and the C7 preview worktree stay preserved and unchanged.

## Reproduce and verify

The README has the full command. `build_c8_preview.py --twice` regenerates byte-identical outputs. The run of record took 849 s, exit 0, on head `056d3d4`. After the P2 correction (`bf3fb2d`, relational validation only; no schema, payload or byte change), `revalidate_c8_preview.py` re-ran the native stage on the captured snapshot. Results are in `reports/c8-revalidation.json`.
