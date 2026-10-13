# CRD Issue 15c — C7 native SIMULATED preview (review packet)

**SIMULATION ONLY.** This is not an Owner acceptance, recording, publication, activation or supersession. The preview oracle and the rendered proposals live in the git-ignored `preview/`. `build_c7_preview.py` regenerates them byte for byte. Codex cleared exactly raw C7 (`bf2a269c…`) for this step (`../issue-15c-implementation/codex-c7-raw-review.md`).

**Branch:** `codex/issue-15c-c7-preview`. Schema 20 exists only there.

**Reproduce:** from the repository root (a worktree works), using the repository venv with this checkout's `src` first on `PYTHONPATH`:

```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-c7-native/build_c7_preview.py --twice
```

It writes `reports/c7-preview.json`.

The builder reads two git-ignored inputs read-only, from this checkout or the nearest ancestor that holds them (the main checkout, for a worktree). Each is digest-pinned:
- the accepted C5 packet proposals `issue-15c-native/preview/proposals/{character-origins-feats,equipment}-PROPOSAL.json`;
- the isolated release store `g1-work/rel/afterworlds.db`, which is only ever copied privately.

## Exact identities

| Item | Identity |
| --- | --- |
| Raw candidate C7 | `bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77` (C6-r2 `699718ff…` and C6 `eb014b30…` preserved) |
| Prior: recorded successor | `srd-5-2-1-corpus-8781d4e0-a3b-15c.json`, `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69` |
| Schema | `5d-representation-schema-20` / `759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a`; lift `5d-lift-schema-19-to-20` |
| Batches touched (identified natively from the successor's acceptance records) | `character-origins-feats`, `equipment` (2 of 24) |
| `character-origins-feats` | replaces `20716b7d…` (rendered `a8928f18…`); preview proposal `1e7b63d3800154eee539297b0ae5d4f9efbfe21c1776986db133e3cc046bfd28`, rendered `587068868bbcbc05cb881f3ae4b2e68cb2c47c257192671470bdf792c17f178e` |
| `equipment` | replaces `b01f54b9…` (rendered `7f8dadcd…`); preview proposal `b8c65454cae97f82cdb96c857aad84c70ba8c78e96fa24f1e95e89360e144a76`, rendered `5eb398b632b8dc226c22136df14e0b140408f27c5754ffbb115b7ccfba52c2ab` |
| Preview oracle file | `d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d` |
| Oracle identity | `cb04163ba0374e95ce0fcdaae939b00793e71f84ed3222593c4babfc9065ef6e` |
| Projection | `8446ab6b-be75-5999-8a9b-74fa133c030a`, payload hash `cffcdbfa70a6e64351b852ff9b932aa32df81abdd45700ef6c0034aefdaeb65a` |
| Successor lifted to 20 (for cross checks) | projection `4d2acb55-22c5-51c0-89e9-eb543dae5123`, payload hash `2e17f51398461b69fcdeecbe231dcfb405d848d82fac76a503288e3b1562a602` |

**Delta:**
- **Facts:** nine facts, one per component. Each component's handling goes from `prose_bound` to `mixed`, and its prose and retention reason are kept.
- **Provenance and expected rules:** nine contextual claims, each on the single bound span holding the fact's quote, and nine ExpectedRules.

**Proofs** (all true in `reports/c7-preview.json`):
- **Pins:** before and after.
- **The 22 other batches:** their ordered batch, record, review-unit and anchor rows are byte-identical.
- **Lifts:** the lift list is the successor's plus exactly 19→20.
- **Representation:** it changed by exactly the proposal delta.
- **Obligations:** they changed only on the nine fact records.
- **Native checks:**
  - 0 `validate_candidate` findings;
  - four malformed variants are each refused by the relational rule;
  - persist → reconstruct → re-identify is clean for the preview and for the lifted successor;
  - the gate passes against the preview oracle;
  - the successor is refused against it, and the reverse.
- **Determinism:** `--twice` gives byte-identical results.

## Schema 20

`5d-representation-schema-20` adds one closed family, `ammunition_supply` (`AmmunitionSupplyFact`):
- `kind: AmmunitionKind` (the schema-19 vocabulary);
- `for_weapons: tuple[ComponentReference, ...] | None`.

It adds no vocabulary and no field to any accepted family. The registered lift `5d-lift-schema-19-to-20` moves nothing.

**Intrinsic invariant** (manifested, so it is inside the hash): `for_weapons`, when stated, is non-empty, distinct and sorted. That gives one fact key per narrowing.

**Relational rule** (`validation._validate_ammunition_supplies`, run by `validate_representation` and therefore by `validate_candidate`). It refuses:
- a reference that is not a component of the draft;
- a referenced component without the Ammunition `WeaponPropertyFact`;
- a weapon whose ammunition kind differs from the supply's;
- one weapon claimed by two narrowed rows of the same kind.

Two shape-gate fixes were needed so an optional sequence is admitted: `_admit` and `held_container_violations`. Neither changes the schema hash.

## Interpretation I2, stated narrowly

`equipment.md:1232` names "Bullets, Firearm". `character-creation.md:849` refers to "the firearms described in 'Equipment'". The Weapons table's Bullet users are:
- the Sling (`equipment.md:239-241`);
- the Musket and the Pistol (`:429-439`).

The separate "Bullets, Sling" row (`:1239`) takes the Sling. The source never literally tags the Musket or the Pistol as a firearm. This replaces the raw README's broader, unsupported wording about which weapons are firearms, as Codex asked; the raw candidate is untouched. I2 remains for exact Owner semantic acceptance.

## Not done (held)

These are not done:
- real acceptance, recording, a committed oracle or supersession;
- ammunition or Origin-category execution;
- Loading and action economy, free-hand eligibility and zero-quantity depletion. These remain separately held boundary work.
