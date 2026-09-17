# CRD Issue 5d — regular-section pilot: identification only

**Identification only.** No draft, proposal, acceptance, lift, publication or schema change is produced here, and no candidate record key is proposed. Selecting a pilot is not accepting one; new corpus acceptance still requires the ordinary explicit semantic decision.

## The section

**`Playing the Game > Proficiency`** — container `1fb4fa49-571f-5c36-8540-595aba2d643f`, release `5.2.1-corpus.36b786d8-fa2`, bundle root `03353dfb…`.

| | |
|---|---|
| represented leaves | **30** |
| reading-order span | 31 leaves |
| interlopers | **1, and it is a `running_header_footer`** — policy-excluded, so the represented leaves are contiguous in reading order |
| pages | 7–8 |
| owned table containers | 1 — `Level or CR \| Bonus`, **10 `table_cell` leaves = one header row plus four data rows** (`Up to 4`/`+2`, `5–8`/`+3`, `9–12`/`+4`, `13–16`/`+5`). The table's remaining four data rows are not cells — see the membership boundaries below. |
| overlap with any accepted batch | **0 leaves** |
| first / last leaf | `e00cea37-87da-5103-9b72-724563a15fd7` / `e9d9f35f-226b-5c61-b7cd-bb05ffeb1c67` |

Sub-entries, all inside the container: *The Bonus Doesn't Stack*, *Skill Proficiencies*, *Skill List*, *Determining Skills*, *Saving Throw Proficiencies*, *Equipment Proficiencies*.

## Why this one

* **It is a regular section, not a glossary entry.** All seven accepted batches are Rules Glossary definitions or entry-shaped populations. Proficiency is the first pilot that tests a review unit against ordinary running rules prose with headed sub-entries — which is what the amendment's "coherent section" is for.
* **Smaller than `actions-1`.** 30 leaves against actions-1's 92, and its prose is ~4,000 characters. Large enough to be a real section, small enough that a reviewer reads all of it.
* **It owns exactly one table**, and that table is the section's own subject, so table membership is a real decision rather than a formality.
* **Its exceptions are named in the prose**, with their own heading in one case — an expected-rule set that omits one is visibly wrong rather than arguably incomplete.
* **It has honest membership boundaries** (below), which is the property under test. A section with no outbound dependency would not exercise exact membership at all.

## The exceptions a source-reviewed expectation must catch

1. **The bonus does not stack** (its own heading). The Proficiency Bonus cannot be added to a die roll or another number more than once — proficiency in *both* Deception and Persuasion still adds it once.
2. **Multiplied only once, divided only once.** A qualification on (1) that a naive "Expertise doubles it" reading drops. An expectation that names (1) but not this is exactly the omission the amendment requires coverage to catch.
3. **Lacking proficiency does not forbid the check.** Without the skill a creature still makes the ability check; it just adds no Proficiency Bonus. The prohibition is on the bonus, not on the attempt.
4. **Tool plus skill gives Advantage, not a second bonus.** Proficiency with a tool *and* with the skill used on the same check yields Advantage on that check. This is a deliberate counterexample to (1): a second benefit that is not a second addition.
5. **The GM has the ultimate say on whether a skill is relevant.** Judgment-required prose, so it falls on the **irreducibility** side of the schema-12 distinction — an `IRREDUCIBILITY_REASONS` code (`policy.py:133`; `gamemaster_latitude` is the obvious fit, but the reviewer states the code at acceptance, not here), *not* the new `prose_retention_reason_code` / `no_identified_structured_use`, which asserts only that nothing needs the meaning reduced today. Naming this one structurally would be the "inferred trusted mechanical value" the invariant forbids.
6. **Starting proficiencies are determined elsewhere.** Character creation for characters, the stat block for monsters. A deferral, and the reason the section does not own a skill list of its own.

## Membership boundaries for the reviewer to adjudicate — not decided here

* **The Skills table is not in this container.** *Skill List* says the skills "are shown on the Skills table," which lives at `Playing the Game > Actions > Skill | Ability | Example Uses` — inside `actions-1`'s accepted territory. Whether the pilot's review unit cites it, includes it, or states it as an outbound reference is a membership decision for the acceptance, not an engineering one.
* **The Expertise feature** is referenced into `Rules Glossary`, outside the section.
* **Leaf `f848a0fb` is a 5c extraction artifact, and it is not a duplicate.** Verified against the ledger: the `Level or CR | Bonus` container holds exactly ten `table_cell` leaves — the header pair and four data rows ending at `13–16`/`+5`. A second column group — the `Level or CR Bonus` header repeated, plus rows `17–20`/`+6`, `21–24`/`+7`, `25–28`/`+8`, `29–30`/`+9` — arrives as one `paragraph` leaf, `f848a0fb`, outside the table container. Half the Proficiency Bonus progression is therefore reachable only through a prose leaf. A review unit of kind `table` scoped to the container would omit levels 17–30 and a source-reviewed expectation would have to catch that; a unit scoped to the section can include the paragraph but then owns a row set that is half cells and half prose. Which of those the pilot does is a membership decision for the acceptance, not an engineering one. It is the same class of retained-evidence property as speed-1's three cross-leaf sentences.

## Runners-up, and why not

| Candidate | Why not |
|---|---|
| `Playing the Game > The Six Abilities` | 62 leaves, only 5 prose — nearly all table cells. It tests tables, not sections. |
| `Playing the Game > Exploration` | 70 leaves / 40 prose / 7,700 chars — larger than the pilot should be, and it defers heavily to the glossary. |
| `Equipment > Mounts and Vehicles` | 84 leaves and two tables, but its rules are mostly deferrals into other sections. |
| `Rules Glossary > Glossary Conventions` | A glossary entry again, and it is *about* the corpus rather than a rule of play. |
| `Gameplay Toolbox > Fear and Mental Stress` | 40 prose leaves and optional-rule framing; optionality is a separate question and should not ride in on the pilot. |
