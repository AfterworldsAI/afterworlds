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
* **No key is guessed.** An empty target cannot be closed by accident. Filling
  one in while it is still a proposal changes that proposal's bytes and its
  identity; once accepted, no later batch can close it at all — a reference's key
  includes its target, so authoring the destination leaves the accepted empty edge
  beside the new one, reported both unresolved and ambiguous. That is the edge
  Option A closes, through an explicit reviewed reference resolution under Owner
  Decision 2026-09-19. No destination beyond the four authorized units was
  ingested, and none of these four is resolved.

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

## Finding 3 — an accepted empty target no supported action could close

Owner authorization, 2026-09-19: *"Option A is clearly the best choice. You are
authorized to implement A."* Recorded as an amendment to ADR-005d Decision 7.

### The verified edge

`representation.reference_target_key` includes `target_record_key`, and
`accept_proposal`'s merge is a keyed union. So a later batch that authors the
destination for an accepted empty citation states a **different** key: the union
retains both, and `relationship_and_reference_violations` then reports the one
citation twice — `unresolved reference` for the accepted empty edge and
`ambiguous` for the pair. The four citations Finding 1 restored are therefore
obligations that, once accepted, nothing in the repository could discharge.
Finding 1's own artifacts said the opposite ("only the batch that mints the
destination can close it"); every instance of that claim is corrected in this
change.

### What was built

* `models.ReferenceResolution` — the identity-bearing decision: the citation it
  resolves (source record, owning component, printed wording, committed scope),
  the reviewed destination, the release it was reviewed against, and the
  provenance spans review read the citation from. `citation_key()` is the
  four-part citation.
* `models.ReferenceResolutionAcceptance` — the evidence beside it: who authorized
  it, under which reference, which reviewer, and when. Not identity-bearing, for
  the reason `ReviewUnitAcceptance` is not.
* `reference_resolution.effective_representation` — the accepted representation
  as its resolutions state it. The empty-target reference is replaced **in
  place**, never appended beside (appending is the defect), and the matching
  `REFERENCE` provenance claims move with it because their `target_key` includes
  the target and `REFERENCE` is in `PROVENANCE_REQUIRED_KINDS`. Returns the
  argument itself when there is nothing to remap, and never applies a resolution
  to an already-targeted reference — a view that did would make the retarget
  refusal unenforceable.
* `reference_resolution.reference_resolution_violations` — reported, not raised,
  on the terms `schema_binding_violations` and `review_unit_violations` use, so
  the acceptance seam and the loader enforce one rule set. The reviewed
  destination is checked directly against the records the accepted authority
  states; everything else is a **multiset delta** against the accepted view
  rather than a restatement of the reference rules, so a resolution applies only
  where the resolved view reports more than the accepted view already reports.
  Ambiguity stays defined once, in `validation`. See Finding 4 — the delta was
  originally a set difference and the destination was inferred from it.
* `acceptance.resolve_references` — the only other acceptance action the module
  states, and an append exactly like `accept_proposal`. Refuses before building
  anything, so a caught `AcceptanceError` leaves the artifact untouched. A
  repeated `resolution_id` is **refused, not absorbed** — replay is deterministic
  and changes nothing — on the same terms as a `batch_id` already held. One
  action carries one or more resolutions, applied whole or not at all (Finding
  4); it was singular when first written.
* `acceptance._refuse_reference_retargeting` — runs on every acceptance with a
  `prior`. Two refusals in their own words: authoring a destination for a citation
  accepted with none (and it names `resolve_references`), and retargeting a
  citation already resolved (unauthorized). Carried resolutions are re-checked
  against the *merged* representation, so an extension that would leave one
  describing something else is refused before an artifact exists, and are carried
  forward rather than re-derived, so an extension cannot silently reopen a
  citation the Owner closed.
* `oracle` — `AcceptedOracle.reference_resolutions`,
  `AcceptedInputs.reference_resolution_acceptances`, strict payload parsing (all
  nine keys required, unexpected keys refused), both halves of the
  stated-versus-authorized cross-check, and omit-when-empty emission.
* `validation._validate_relationships_and_references` promoted to public
  `relationship_and_reference_violations` — one definition, two seams.

### No schema bump

`reference_resolutions` lives on `AcceptedOracle`, not on `RepresentationDraft`,
so `schema_binding_violations` never sees it and no representation schema states a
new form. With omit-when-empty emission, all seven accepted batches stay
byte-identical and the accepted oracle identity is unchanged
(`d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f`), asserted by
test against the committed artifact.

### Sibling audit — every consumer of the stored representation

**Defect family:** a production path reading `oracle.representation` where it
should read the effective view would report a resolved citation as still
unresolved, which is history mistaken for a second active citation.
**Trigger:** this change introduces a second view of one artifact. Every hit of
`oracle\.representation` / `.representation.references` in `src/afterworlds`,
dispositioned:

| site | reads | disposition |
|---|---|---|
| `oracle.py:1831` `candidate_from_accepted_inputs` | effective | **patched** — the build/persistence/query seam |
| `gate.py:438`, `gate.py:757` `_accepted_identity` | effective | **patched** — both the identity and the element comparison |
| `publication.py:627` → `_publish_projection` → `run_publication_gate` | effective, via `gate` | **already safe** — no direct read |
| `oracle.py:438` `oracle_payload` | stored + resolutions | **already safe** — identity is stored content plus the decisions about it |
| `oracle.py:1628` `schema_binding_violations`, `1641` `policy_meaning_violations`, `1657` `review_unit_violations` | stored | **already safe** — they judge what was accepted |
| `oracle.py:1698` `reference_resolution_violations` | stored | **patched** — new; applicability is a question about the accepted view |
| `acceptance.py:447`, `506`, `591`, `595`, `814` | stored | **already safe** — merge, succession evidence, retarget guard |
| `schema_lift.py:1227`, `1237` | stored | **already safe** — a lift proves stored content crossed unchanged |
| `oracle.py:350` `derive_obligations` | stored | **already safe** — reads records and components only; references are not obligation-bearing, so a resolution cannot move an obligation and the loader's exact-equality check stays valid |

Nothing outside `ingestion/mechanical` reads either view. `rules_authority`'s
override path is reference-free in this sense — `patches.py:476` `reference=` is a
`ParticipantRole` — so ADR-015's sibling surface is **already safe**.

### Governing documentation reconciled in the same change

* `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` — Decision 7
  gains **Amended by Owner Decision 2026-09-19**: the authorization quoted once,
  the edge it closes, what a resolution must state, that the decision bears
  identity and its authorization evidence does not, that Decision 7 is otherwise
  unchanged (unresolved still blocks publication), replay, the later-batch rules,
  and the verbatim list of what is **not** authorized.
* `docs/architecture/known_unknowns.md` — the two kinds of outstanding reference
  distinguished: *named-but-unminted* (the ten; each closes when some batch mints
  the key it already names) versus *empty target* (none accepted; four arrive with
  the destinations batch; closes only by an explicit reviewed resolution).
* Finding 1's artifacts — the generator, the review packet, the proposal test and
  this log — corrected wherever they said a minting batch could close an empty
  target.

### Demonstrated on isolated evidence, not on the corpus

`tests/ingestion/mechanical/test_reference_resolution.py` — 44 tests, 100 % of
`reference_resolution.py` — exercises the workflow on the bounded fixture:
acceptance of an unresolved citation that stays detectably unresolved, explicit
resolution to one effective destination, provenance moving with it, history
unrewritten, obligations unmoved, authorization evidence not reminting the
projection, gate/build identity lockstep **and** the publication gate passing the
resolved projection while refusing the stored view's, persistence round trip,
committed round trip, the pre-decision committed state still loading as
unresolved, omit-when-empty, a real 14→15 succession carrying the decision, an
unsupported succession refusing, deterministic replay refusal, and negative
controls for unattributed, idless, conflicting, release-mismatched,
provenance-mismatched, citationless, destinationless, retargeting,
unknown-destination, ambiguity-introducing and sibling-duplicating inputs — plus
seven loader refusals over mutated committed JSON and five later-batch boundary
cases.

The four real citations are deliberately **not** resolved: resolving one would
mean inventing a destination. `test_proficiency_references_resolve.py` continues
to run the real `accept_proposal(prior=<committed corpus>)` for both real
proposals in memory, so the new guards are exercised against the artifacts the
Owner has authorized accepting next, and the committed corpus is asserted
byte-identical afterwards.

## Finding 4 — overlapping citations of one wording

Codex's independent review of the Option A implementation at `90faa38`. Two
verified P1 defects, one root cause, corrected together.

### The root cause

`validation.relationship_and_reference_violations` tags a reference finding
`reference {scope}:{source_text!r}` — **no owning record or component**. That is
deliberate: two *components* of one record may legitimately cite the same
wording, each its own claim with its own provenance. The consequence is that
sibling citations of one phrase produce byte-identical finding strings, and the
resolution seam was built on top of that in two places that both assumed a
citation's wording identified it.

### Defect 1 — an invalid destination hid behind a sibling's finding

`reference_resolution_violations` ended in `set(effective) - set(accepted)`, and
the reviewed destination's existence was **inferred** from that delta rather than
checked. Codex's reproduction: give the `test_reference_resolution` fixture a
sibling reference from `OPEN_ENDED_KEY` with the same wording and scope and
`target_record_key='glossary.invented'`, accept it, then resolve the original
citation to `'glossary.invented'`. The accepted view already reports
`unknown target record glossary.invented` once; the resolved view reports it
twice; the two strings are identical, so the set difference is empty. The
resolution was **admitted**, and the artifact serialized and loaded while its
effective view reported an unknown destination twice with nothing accounting for
it.

Corrected in two independent ways, because absence of newly worded diagnostics is
not evidence a destination exists:

* the destination is now bound directly — `target_record_key` must be a record
  the accepted representation states, refused in its own words before the delta
  runs. This is what refuses the reproduction;
* the delta subtracts `collections.Counter` multisets, so a second occurrence of
  an existing finding is reported rather than absorbed. This removes the masking
  *mechanism*, so a finding the validator words by scope and wording in future
  cannot reopen the family.

### Defect 2 — a valid joint end state no single action could reach

With the same sibling but `target_record_key=''`, both citations are legitimate
and both are empty. Their destination, though, is shared: `validation` keys
ambiguity on `(scope_key, source_text)`, so resolving either one alone makes that
key resolve to `['', DESTINATION]` and the resolution is refused for an ambiguity
it introduced. `resolve_reference` took exactly one `ReferenceResolution`, so the
valid, consistent, jointly resolved end state was unreachable through any
supported path.

`acceptance.resolve_references` now records one reviewed action over one **or
more** resolutions: validated together against the accepted authority, applied
whole or not at all. Each resolution keeps its exact citation, its own reviewed
provenance spans and its own `ReferenceResolutionAcceptance`; what they share is
the single authorization the action names. Nothing about a single resolution
changed — it is `resolutions=(one,)` — and the singular/plural paths reach the
same accepted authority and the same oracle identity, asserted by test, because
how a decision was recorded is evidence and not part of the result.

True ambiguity is not weakened: two citations of one wording sent to different
records are refused whether stated in one action or several, and resolving one of
two consistent citations alone is still refused. Any already-recorded
`resolution_id` refuses the whole action, so a partial replay records no part of
itself, and an action stating no resolution at all is refused.

### Sibling audit — set-subtracted diagnostics

Family: *a diagnostic delta computed over strings that are not unique per
element*. Trigger: two review rounds on the reference-resolution seam. Searched
every set subtraction in `src/afterworlds/ingestion/`. Dispositions:

| site | disposition |
|---|---|
| `reference_resolution.reference_resolution_violations` | **patched** — multiset delta, plus a direct destination check |
| `oracle._require_keys` / `representation._require_keys` (`supplied - set(keys)`) | **already safe** — over payload key names, unique by construction |
| `corpus.source_completeness`, `corpus.table_inventory`, `corpus.vector_publication` | **already safe** — over ids and printed-name keys, and the multiplicity question does not arise |

No other diagnostic delta in the repository subtracts sets of finding strings.

### The three call sites inherit the fix

`reference_resolution_violations` has exactly three callers, and all three are
corrected by the one change: `acceptance.resolve_references` (the writer),
`accept_proposal`'s carried-decision re-check over the merged representation, and
`oracle.load_accepted_inputs` over committed bytes. An artifact that loads is
still one the seam would have produced.

### Coverage

Thirteen new tests in `test_reference_resolution.py` cover this family (57 in
the module, up from 44), including Codex's exact reproduction, the joint production
path with serialization and reconstruction, joint-versus-stepwise identity,
carried joint decisions across a later batch, effective consumer behaviour
through `candidate_from_accepted_inputs`, and the negative controls: mixed
valid/invalid leaves the prior artifact byte-identical, replay and partial replay
refuse whole, one citation stated twice in one action conflicts, differing
destinations stay ambiguous, and half a joint decision in committed bytes does not
load. `reference_resolution.py` is at 100% statement coverage; the acceptance
module's new branches are covered.

Both defects were verified reproducible before the fix: with the correction
reverted, the reproduction test reports `DID NOT RAISE`.

## Artifacts and identities

| artifact | identity | file sha256 | bytes |
|---|---|---|---|
| `proficiency-destinations-1`, pre-remediation (superseded) | `01603c7f9a3b14f9c90e63e03e32da7c75b119109f0c251e8b428d91b0765a5d` | `2a2fa620e4379d28651b3ab83b038d59861d0133671d311d36edf1357dd43d85` | 137,439 |
| `proficiency-destinations-1`, corrected | `723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e` | `6a88c886f320aa05cb6c9363b9a5bd1ab5d5c0b551d21832ab2dd2daf035fe1d` | 139,405 |
| `proficiency-1`, unchanged by this remediation | `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` | `c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d` | 61,375 |
| `proficiency-1` as approved in #171, reproducible, never accepted | `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4` | `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324` | 61,329 |

Neither proposal is accepted, and neither carries a reference resolution.
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

## Test coverage of the first two corrections

33 tests across three modules. Finding 3's own coverage is above.

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
work; no generic post-acceptance supersede mechanism and no parallel acceptance
system, `resolve_references` being bounded to empty-target resolution and
refusing every retarget; no 5c change; no movement, 15c,
sheet or adapter execution; no dependency or audit-exclusion change; no progress
accounting or settings change. Seven accepted batches, historical
schemas/identities, Speed scope order, the four-part release binding and
override/replay are all preserved. No validator was weakened and no finding
excluded.
