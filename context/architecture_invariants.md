# Architecture Invariants — Test Anchors and Violation Examples

**Purpose:** This file teaches Claude Code what the Afterworlds architecture
invariants look like in practice — both correct implementations and violations.
Use it when writing tests, reviewing code for architectural correctness, or
evaluating whether a design decision drifts from spec.

**When to use:** Before writing any invariant test; when an implementation
decision touches the pipeline, Story Bible, Extractor, or caching behavior;
when writing the Architecture Notes section of a PR.

---

## Invariant 1 — Story Bible is structurally separate from prose history

**What this means:** Story Bible content (cast, world rules, locked facts,
events ledger, relationship ledger) and prose turn history (the actual
generated narrative text) must never be stored in the same table or
commingled in the same data structure.

**Correct:**
```python
# Separate tables, separate services
class Turn(Base):
    __tablename__ = "turns"
    id: int
    node_id: int
    user_input: str
    ai_response: str  # prose only

class StoryBibleEntry(Base):
    __tablename__ = "story_bible_entries"
    id: int
    story_id: int
    partition: str  # "static" | "dynamic" | "provisional"
    entry_type: str  # "locked_fact" | "character" | "event" | ...
    content: dict
```

**Violation:**
```python
# Wrong — prose and canon in the same table
class StoryContent(Base):
    __tablename__ = "story_content"
    id: int
    content_type: str  # "turn" or "bible_entry" — do not do this
    content: str
```

**CI invariant test anchor:**
Confirm Story Bible tables and Turn/Node tables share no columns and are
never joined in a single query that returns both prose and canon fields.

---

## Invariant 2 — Intent is classified before context is assembled

**What this means:** The intent classification call must complete and return
a typed result before the context builder is invoked. Context assembly must
never begin with an unclassified or raw input string.

**Correct:**
```python
async def process_turn(raw_input: str, story_id: int) -> TurnResult:
    intent = await classify_intent(raw_input)       # step 1
    context = await build_context(story_id, intent) # step 2, receives typed intent
    result = await run_pipeline(context)
    return result
```

**Violation:**
```python
async def process_turn(raw_input: str, story_id: int) -> TurnResult:
    context = await build_context(story_id, raw_input)  # wrong — raw string passed
    intent = await classify_intent(raw_input)           # classified after the fact
    ...
```

**CI invariant test anchor:**
`build_context` must accept a typed `IntentClassification` object, not a raw
string. Any call signature accepting a plain string for intent is a violation.

---

## Invariant 3 — Extractor proposes, never writes canon directly

**What this means:** The Extractor pass produces a `CanonProposal` object.
That object is then routed through the classification policy (locked /
soft / transient / unresolved). Nothing is written to the Story Bible
without passing through that classification step first.

**Correct:**
```python
async def extractor_pass(writer_output: str) -> CanonProposal:
    # Returns proposals only — does not touch the Story Bible
    return CanonProposal(items=[...])

async def apply_extractor_output(proposal: CanonProposal) -> None:
    for item in proposal.items:
        match item.classification:
            case "locked":    await stage_for_confirmation(item)
            case "soft":      await auto_commit(item, confidence="low")
            case "transient": await auto_commit(item, confidence="auto")
            case "unresolved": await queue_to_plot_tracker(item)
```

**Violation:**
```python
async def extractor_pass(writer_output: str, story_id: int) -> None:
    facts = extract_facts(writer_output)
    for fact in facts:
        await story_bible_service.write(story_id, fact)  # direct write — violation
```

**CI invariant test anchor:**
No code path from the Extractor pass may call any Story Bible write method
without first producing a `CanonProposal` and routing through classification.
Test with a mock that confirms zero direct writes.

---

## Invariant 4 — Stable prefix assembled once per turn, not per pass

**What this means:** The stable prefix (system prompt + mode contract +
Story Bible active context + rolling summary) is assembled once and cached.
All five pipeline passes receive the same prefix object. It is never
rebuilt between passes.

**Correct:**
```python
async def run_pipeline(story_id: int, intent: IntentClassification) -> PipelineResult:
    stable_prefix = await context_builder.build_stable_prefix(story_id)  # once
    volatile_suffix = await context_builder.build_volatile_suffix(story_id, intent)

    planner_result  = await planner_pass(stable_prefix, volatile_suffix)
    writer_result   = await writer_pass(stable_prefix, volatile_suffix, planner_result)
    extractor_result = await extractor_pass(stable_prefix, writer_result)
    contradiction_result = await contradiction_pass(stable_prefix, writer_result)
    safety_result   = await safety_pass(stable_prefix, writer_result)
    return PipelineResult(...)
```

**Violation:**
```python
async def writer_pass(...) -> str:
    prefix = await context_builder.build_stable_prefix(story_id)  # rebuilt per pass — violation
    ...
```

**CI invariant test anchor:**
`build_stable_prefix` must be called exactly once per turn regardless of
pipeline depth. Assert call count == 1 in pipeline orchestration tests.

---

## Invariant 5 — Output gated until contradiction checker clears

**What this means:** Nothing is returned to the user until both the Writer
pass and the Contradiction pass have completed. The contradiction checker
runs in parallel with the Writer; the gate holds until both resolve.

**Correct:**
```python
writer_task = asyncio.create_task(writer_pass(context))
contradiction_task = asyncio.create_task(contradiction_pass(context))
writer_result, contradiction_result = await asyncio.gather(
    writer_task, contradiction_task
)
if contradiction_result.has_violations:
    return handle_contradiction(contradiction_result)
return deliver_to_user(writer_result)
```

**Violation:**
```python
writer_result = await writer_pass(context)
await deliver_to_user(writer_result)          # delivered before checker runs — violation
contradiction_result = await contradiction_pass(context)
```

**CI invariant test anchor:**
Inject a deliberate contradiction (dead character acting; item never
acquired; violated locked fact) and assert that output is never delivered
when the checker returns violations. The listed examples are test anchors,
not an exhaustive definition of detectable violations.

---

## Invariant 6 — Free tier never receives full five-pass pipeline

**What this means:** Free tier sessions run: lightweight Planner + Writer +
lightweight Contradiction + Safety. The Extractor pass does not run for
free tier users. Paid tier runs all five passes.

**Correct:**
```python
def get_pipeline_for_tier(tier: Tier) -> list[PassType]:
    match tier:
        case Tier.FREE:
            return [PassType.PLANNER, PassType.WRITER,
                    PassType.CONTRADICTION, PassType.SAFETY]
        case Tier.PAID | Tier.BYOK:
            return [PassType.PLANNER, PassType.WRITER, PassType.EXTRACTOR,
                    PassType.CONTRADICTION, PassType.SAFETY]
```

**CI invariant test anchor:**
Assert that for a free tier session, `PassType.EXTRACTOR` is never in the
resolved pipeline. Assert that for paid/BYOK, all five passes are present.
Tier routing logic is tested as an architectural invariant, not left to
convention.

---

## Lessons

<!-- Claude Code appends dated one-line lessons here as they are learned -->
