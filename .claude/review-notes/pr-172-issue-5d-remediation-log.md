# PR #172 — CRD Issue 5d remediation log

Two settled findings from the independent review of the `proficiency-destinations-1`
and `proficiency-1` proposals on branch `codex/issue-5d-proficiency-references`.
Both are corrections to **proposed** artifacts. Nothing here is accepted into the
corpus, no accepted history is rewritten, and no validator is weakened or finding
excluded.

Starting head: `aadc852d414ca64e050180877b4fddfc6b22f08e`.
Review source: `pr172-independent-review.md` (Owner-supplied).

---

## Finding 1 — suppressed source-authored citations

### What was wrong

The destinations generator applied the rule *"mint a reference only where the
destination record already exists."* Four explicit citations in the four reviewed
units therefore produced no reference at all:

| from | printed wording | printed page of the destination |
|---|---|---|
| `glossary.challenge_rating` | Stat Block | Rules Glossary entry, p. 188 |
| `glossary.challenge_rating` | Combat Encounters | *Gameplay Toolbox* subsection, p. 202 |
| `play.actions` | Combat | *Playing the Game* subsection, p. 13 |
| `play.actions` | Opportunity Attack | entry inside that subsection, p. 15 |

Their prose survived, so nothing was lost from the record — but the reference
checker could not see the obligations, and the combined merged report therefore
read as if this task's only outstanding reference residue were the ten
pre-existing `glossary.speed` pointers. That is a false statement about the
source: a citation does not stop existing because nobody has reviewed its
destination. What changes is only whether the build can see it.

### Source-reviewed citation inventory

Read from the bound 5c release, not from the proposal. Every cross-reference
construct in the four units, with its source role:

**Challenge Rating (printed p. 178)**

| clause | wording | role |
|---|---|---|
| `cr.toolbox_a` | the *"Gameplay Toolbox"* material on *"Combat Encounters"* | **citation** — destination unminted |
| `cr.see_also` / `cr.stat_block` | `See also` → *"Stat Block."* | **citation** — destination unminted |

**Expertise (printed p. 182)**

| clause | wording | role |
|---|---|---|
| `exp.pointer` | `See also` → *"Playing the Game" ("Proficiency")* | citation — already minted record-owned at `play.proficiency` |

**Skills table (printed pp. 9–10)** — all 57 printed cells dumped and read.
**Zero** cross-reference constructs.

**Actions section (printed pp. 9–10)**

| clause | wording | role |
|---|---|---|
| `act.one_thing_combat` | "as explained in *'Combat'* later in *'Playing the Game.'*" | **citation** — destination unminted |
| `act.reaction_opportunity` | "The Opportunity Attack, described later in *'Playing the Game,'*" | **citation** — destination unminted |
| `act.table_pointer` | "defined in more detail in *'Rules Glossary'*" | names the **scope** the 12 row references already resolve in — not a further destination |
| `act.bonus_example_a` / `_b` | "The Cunning Action feature, **for example**, allows a Rogue…" | **example** — the source's own "for example"; illustrates the rule stated beside it |
| `act.one_thing_examples` | Influence / Search / Help / Utilize inside *One Thing at a Time* | **illustrations** in running prose; the same four words are cited *with* destinations as Action-table rows |
| Summary and Example Uses cells | action names in passing | column headers say what they are |

Incidental and example mentions were distinguished by source role, not by
mention matching — the same ground on which `proficiency-1` minted nothing for
`D20 Test`, `Advantage` or `Athletics`.

### What was changed

The four citations are now authored as `ReferenceDraft`s with an **empty**
`target_record_key` (`UNRESOLVED_TARGET`), which
`validation.py::_validate_relationships_and_references` reports as
`unresolved reference`. `proficiency-1` used exactly this form for its own two
*Playing the Game* pointers before this branch closed them.

* **Ownership.** All four are `RECORD_OWNED_REFERENCE`, on the Expertise
  pointer's precedent: the entry or the section states the citation, not any one
  of its rule components.
* **Scope.** Outer part name is the resolution space, quoted inner heading is the
  `source_text` — again the Expertise precedent. `srd-5.2.1/gameplay-toolbox` is
  a new scope string formed from the source's own part name under the existing
  `<release-family>/<section-slug>` convention. `scope_key` is a free-form review
  space with no closed vocabulary and is not a record key, so naming one invents
  no destination.
* **Provenance is additive**, 134 → 138 claims. The existing supporting-authority
  claims on `cr.toolbox_a`, `act.one_thing_combat`, `act.reaction_opportunity`
  and the record claim on `cr.stat_block` were **kept**, and one REFERENCE
  `CONTEXTUAL` claim added per citation on the same span: a sentence both
  supports its rule and cites a destination, and `_validate_provenance`
  (`validation.py:626–720`) admits multiple `CONTEXTUAL` claims on one span for
  different targets. Only `PRIMARY` claims conflict per span.
* **No key is guessed.** An empty target cannot be closed by accident. Only the
  batch that mints the destination record can fill it in, and doing so changes
  that proposal's bytes and its identity. No destination beyond the four
  authorized units was ingested.

### Why an empty target is admissible at every layer

Checked against production code before editing, not assumed:

* `acceptance.py::accept_proposal` (line 247) and `_merged_collection` run only
  `representation_draft_violations` and `held_structure_violations`; no layer
  refuses an empty target.
* `oracle.py::_string` checks `type(value) is str` only, so empty strings load.
* Target resolution in `_validate_relationships_and_references` is global and
  scope-independent; `scope_key` only groups the ambiguity check and must be
  non-empty.
* The cross-form check at `validation.py:476` keys on
  `(from_record_key, source_text, scope_key, target_record_key)`, so the new
  citations collide with nothing.

### No new ambiguity

The accepted corpus's 62 references are all in `srd-5.2.1/rules-glossary`, and
none of them cites *Stat Block*, *Combat*, *Combat Encounters*, *Gameplay
Toolbox* or *Opportunity Attack*. No `(scope, wording)` pair gains a second
resolution.

### Reported obligations, before and after

| | before | after |
|---|---|---|
| references in `proficiency-destinations-1` | 13 | 17 |
| of which resolve on merge | 13 | 13 |
| of which reported `unresolved reference` | 0 | 4 |
| merged outstanding obligations (with the accepted corpus) | 10 | **14** |

The ten pre-existing `glossary.speed` findings are unchanged and untouched.

---

## Finding 2 — irreducibility codes used for reducible meaning

### The distinction

The closed catalog answers "why is this meaning prose?" two different ways, and
they are not interchangeable:

* an **irreducibility** code says the source's own meaning cannot be reduced
  without executable interpretation;
* the **retention** code `no_identified_structured_use` says the meaning *is*
  reducible and this build has no identified code-owned use needing a separate
  structured field, so the exact governing prose carries it.

`policy.py` states it outright: relabelling reducible meaning with an
irreducibility code "would make the catalog say something false about the
source." CRD Issue 5d contract 2 forbids it.

### Defect family

**Treating a stated exception, or the absence of a schema shape, as
irreducibility.** Trigger: independent review raised `expertise_doubling`; the
sibling sweep found the second instance.

| component | was | is | disposition |
|---|---|---|---|
| `glossary.expertise` / `expertise_doubling` | `natural_language_exception` | `no_identified_structured_use` | `patched` |
| `play.actions` / `reaction_timing` | `natural_language_exception` | `no_identified_structured_use` | `patched` |

**`expertise_doubling`** — "unless the bonus is doubled by another feature" is a
*fixed* exception: one stated condition, one stated consequence. The arithmetic
limit it points at is already accepted authority on
`play.proficiency/bonus_does_not_stack`, read from that section's own spans.
Reducible. Nothing in this task's authority identifies a code-owned use for a
doubling factor — no sheet or adapter execution is in scope — so the whole clause
stays exact governing prose under the honest retention reason. The limit is not
restated as a second structured copy.

**`reaction_timing`** — "unless the Reaction's description says otherwise" states
a default ordering plus an override that defers to another rule's own text.
Deferring to a rule a later batch will classify is not meaning that cannot be
reduced. Its own sibling in the same section, `act.bonus_timing` ("unless the
Bonus Action's timing is specified") inside `bonus_action_allowance`, already
carried the retention reason, and one shape cannot carry two reasons.

The whole clause stays bound in both cases. Nothing was extracted, no fact family
minted, no typed field invented: the correction is to what the batch *says about*
the prose, not to the prose.

### Siblings inspected

| assignment | disposition |
|---|---|
| `threat_comparison` = `subjective_judgment` | `already safe` — the source hedges both arms with "likely" |
| `encounter_circumstances` = `contextual_applicability` | `already safe` — applicability depends on circumstances and party size in play, fiction the projection cannot enumerate |
| `improvised_action_options` = `open_ended_effect` | `already safe` — "other abilities provide additional action options" is an unbounded effect space |
| `improvised_action_judgment` = `gamemaster_latitude` | `already safe` — the source hands the decision to the GM in its own words |
| the 15 remaining components = `no_identified_structured_use` | `already safe` — reducible, no identified consumer |
| the three clauses no schema shape fits | `already safe` — "no shape fits" is a statement about schema 15, not about the source, so none is classified irreducible; all three keep the retention reason |
| `proficiency-1`'s only irreducibility code, `skill_relevance_judgment` = `gamemaster_latitude` | `already safe` — the GM decides which skill is relevant. That proposal is unchanged and keeps identity `f0becb8b…` |
| conditions-1's `glossary.condition/condition_definition` = `natural_language_exception` | `out of scope` — the one accepted use of that code, and accepted history. Not re-opened, not rewritten |

The `EXCEPTION = "natural_language_exception"` constant was removed from the
generator with a comment recording why it is deliberately absent. This batch now
uses no `natural_language_exception` assignment at all.

---

## Artifacts and identities

| artifact | identity | file sha256 | bytes |
|---|---|---|---|
| `proficiency-destinations-1`, pre-remediation (superseded) | `01603c7f9a3b14f9c90e63e03e32da7c75b119109f0c251e8b428d91b0765a5d` | `2a2fa620e4379d28651b3ab83b038d59861d0133671d311d36edf1357dd43d85` | 137,439 |
| `proficiency-destinations-1`, corrected | `723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e` | `6a88c886f320aa05cb6c9363b9a5bd1ab5d5c0b551d21832ab2dd2daf035fe1d` | 139,405 |
| `proficiency-1`, unchanged by this remediation | `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` | `c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d` | 61,375 |
| `proficiency-1` as approved in #171, reproducible, never accepted | `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4` | `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324` | 61,329 |

Representation schema is `5d-representation-schema-15` / `e87e0bac…`, unchanged.
Byte-determinism of the corrected proposal was proved by regenerating twice and
comparing with `cmp`.

Corrected generator report:

```
records 4   review units 4   leaves 107 represented, 1 excluded by 5c   spans 120
components 19   bindings 70   provenance 138   references 17
partition 0 findings   review units 0 findings
representation 17 findings (13 unminted-destination citations, 4 outstanding obligations)
```

## Test coverage of both corrections

33 tests across three modules.

* `test_the_four_outstanding_citations_are_authored_as_unresolved` — the exact
  outstanding set, record-owned ownership, and exactly one REFERENCE provenance
  claim per citation on a declared span.
* `test_the_untampered_report_is_exactly_the_seventeen_open_obligations` — the
  full finding list, with `sum("unresolved reference" in f) == 4`.
* `test_the_prose_reasons_say_why_each_clause_is_prose` — pins the irreducibility
  map exactly, asserts every component and every binding states exactly one kind
  of reason (`bool(irreducibility) != bool(retention)`), and that the two
  corrected components are PROSE_BOUND, factless, one binding each, carrying
  `no_identified_structured_use`.
* `test_proficiency_references_resolve.py` — `EXPECTED_OUTWARD` is the exact
  fourteen-item merged list (the Speed ten plus the four new), asserted both on
  the merged report and after the production serialization/reconstruction round
  trip; `len(merged.references) == len(accepted.references) + 21`.
* The accepted-glossary comparison in
  `test_the_action_table_links_resolve_where_the_accepted_glossary_says` now
  filters on `from_component_key == "action_table"`, so the two new record-owned
  `play.actions` citations do not silently break a field-for-field comparison
  against committed accepted data.

## Boundaries not crossed

No corpus-wide reference cleanup; no destination ingestion beyond the four
authorized units; no accepted Action uniformity rewrite; no schema-framework
work; no post-acceptance supersede mechanism; no 5c change; no movement, 15c,
sheet or adapter execution; no dependency or audit-exclusion change; no progress
accounting or settings change. Seven accepted batches, historical
schemas/identities, Speed scope order, the four-part release binding and
override/replay are all preserved. No validator was weakened and no finding
excluded.
