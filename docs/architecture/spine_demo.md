# Afterworlds — Minimal End-to-End Spine Demo

*Defines the proof-of-life sequence that confirms the Sojourn pipeline is working end-to-end.*
*All three modes must extend from this spine before v1 is considered release-capable.*
*Last updated: March 2026*

---

## Purpose

The spine demo is not a unit test. It is a full end-to-end integration verification — a human-executable walkthrough that confirms the entire system is connected and behaving correctly as a narrative product, not just as a collection of passing unit tests.

The spine demo must be executable by the project owner without developer intervention. If running it requires consulting code, reading logs, or interpreting ambiguous output, it is not complete.

**Issue 21** is the formal gate: all three mode slices of the spine demo must pass before v1 is declared release-capable.

---

## Primary Spine Demo — Branching Mode

Branching mode is the primary spine. It exercises the full pipeline with the fewest mode-specific dependencies (no Rules Package, no persona system). If Branching mode works end-to-end, the machine lives.

**Prerequisites:**
- Issues 1–20 complete and merged
- All CI gates passing
- A clean local environment with no leftover story state from previous test runs

**Steps:**

1. Create a new Story with a minimal Story Bible: one setting description, one protagonist, one dramatic hook. Example: *"A rain-soaked city. A detective who doesn't believe in coincidences. A locked-room murder with no body."*

2. Select Branching mode with default configuration (Balanced branch frequency, no length preference override).

3. Submit a first turn. Observe:
   - Intent is classified correctly (branch choice / story start)
   - Stable prefix assembles correctly — Story Bible, empty rolling summary, system prompt all present
   - Pacing stage initializes to Setup
   - Writer generates a narrative beat
   - Contradiction checker evaluates Writer output and clears (no violations on Turn 1)
   - Prose is delivered to the UI
   - 3–5 branch options are presented alongside a freeform text field with equal visual prominence
   - Turn is saved to SQLite; Node is created with pacing stage metadata

4. Verify Story Bible and rolling summary update path ran: Extractor proposed updates; no locked facts requiring confirmation on first turn; any soft/transient facts auto-committed correctly.

5. Select one of the branch options. Submit as Turn 2. Observe:
   - Correct prior state loads (Story Bible, Turn 1 summary or verbatim, pacing stage)
   - Pacing stage advances naturally or holds correctly
   - Response is coherent with Turn 1 and advances the narrative
   - Branch options again presented for Turn 3

6. Submit Turn 3 as freeform text input — something that doesn't match any of the offered branches but is coherent and dramatically plausible. Observe:
   - Freeform input is honored
   - Story adapts visibly — does not force input onto a preset rail
   - Response is coherent with prior turns

**Pass criteria:** All six steps complete without error. Output is coherent narrative prose. Freeform input on Turn 3 is honored. Turn history, Node, and Story Bible state are all correctly persisted in SQLite.

---

## RPG Mode Follow-On Slice

RPG mode extends the spine but has an additional hard dependency: a curated d20 Rules Package must be ingested, published, and queryable before this slice can run. This is delivered by Issue 5b.

**Prerequisites (in addition to primary spine prerequisites):**
- One curated d20 Rules Package ingested and queryable through the Context Builder
- Issue 15 (RPG mode integration) complete and merged

**Steps:**

1. Create a new Story. Select RPG mode.

2. Complete the pre-play sequence in order:
   - World setup: describe setting in free text; GM confirms and asks clarifying questions; confirm before proceeding
   - Character creation: work through creation conversationally with the GM, or paste a completed sheet; play does not begin until the sheet is complete enough to adjudicate against

3. Submit Turn 1 as an in-character action that requires a dice roll (e.g., attempting to pick a lock, attack an enemy, persuade an NPC).

4. **If `dice_handling = Player rolls`:** Observe that the GM announces the check type and all applicable modifiers and stops — waiting for the player to report a roll result. Do not narrate outcome before the roll is reported. Report a roll result. Observe that the GM adjudicates and narrates consequence from the reported result.

5. **If `dice_handling = AI rolls`:** Observe that the GM rolls, shows the result to the player, and narrates consequence.

6. Observe that the relevant d20 Rules Package slices were retrieved and used in adjudication — the GM did not invent rules wholesale.

7. Trigger a hidden roll scenario: submit an action where an NPC or enemy check would occur without the player's in-world knowledge. Observe that the roll is resolved privately and the outcome narrated without showing the roll result to the player.

**Pass criteria:** Pre-play sequence enforced in correct order. Dice mode behaves correctly. Rules Package slices retrieved correctly. Hidden roll resolved privately. Character sheet state updated correctly after mechanical consequences.

---

## Writing Mode Follow-On Slice

Writing mode extends the spine with the persona system. No Rules Package dependency.

**Prerequisites (in addition to primary spine prerequisites):**
- Issue 17 (Writing mode integration) complete and merged

**Steps:**

1. Create a new Story. Select Writing mode.

2. Select a Mentor persona — use Chiron as the reference case.

3. Complete the setup form: describe the project, the immediate writing goal, and any relevant context.

4. Observe the setup turn: Chiron reads the form, opens with a brief confirmation, and asks any clarifying questions needed to begin well — not a fixed number, only what is genuinely needed. Work does not begin until the working relationship and immediate goal are clear.

5. Submit Turn 1 as a short piece of original prose written toward the stated craft goal.

6. Observe: Chiron returns targeted feedback aimed at the specific craft goal — not generic praise, not manuscript repair. Feedback is oriented toward teaching through making.

7. Confirm that Chiron does not begin the session by receiving existing prose for correction — the diagnostic path (bringing existing prose to a Mentor) is a separate flow, not the default opening.

8. Submit Turn 2 as a follow-up. Observe: Chiron does not re-ask setup questions or re-establish context. The session continues from where Turn 1 left off.

**Pass criteria:** Setup turn gate fires once only. Mentor feedback is craft-goal-specific. Session continues correctly on Turn 2 without re-onboarding. Story Bible and session state persist correctly across turns.

---

## What the Spine Demo Is Not

- It is not a substitute for the unit test suite. Passing the spine demo with failing unit tests is not a passing state.
- It is not a performance benchmark. Response time is not evaluated here.
- It is not a content quality evaluation. The spine demo confirms the machine is connected and behaving architecturally correctly — not that the prose is good.
- It is not a one-time gate. The spine demo should be re-runnable at any point during construction to confirm no regression.

---

## Failure Modes to Watch For

These are the most likely failure modes at the integration level — unit tests may pass while these fail:

- **Context assembly failure:** Story Bible, rolling summary, or mode contract missing or malformed in the stable prefix
- **Extractor not running:** Story Bible not updating after Turn 1; soft/transient facts not committing
- **Checker not evaluating Writer output:** Contradictions introduced by generation passing through unchallenged
- **Freeform input ignored or forced onto a branch:** Branching mode treating freeform as invalid
- **Pre-play sequence not enforced:** RPG mode allowing Turn 1 before character sheet is complete
- **Persona re-onboarding:** Writing mode asking setup questions on Turn 2 or later
- **State not persisting:** Correct prior state not loading on Turn 2 in any mode

---

*This document is a canonical architecture artifact. Updates require a PR with an Architecture Notes section.*
