"""Intent Classifier service — CRD Issue 7.

Classifies Sojourner input into one of eight typed intent categories before
context is assembled.  Intent classification is the first processing step on
every turn by architectural design (Design doc §4, Step 1; CRD Item 9,
Issue 7).

Key constraints from the issue spec:
  - Classification happens before context assembly; this service never reads
    from the Story Bible, assembles prompts, or calls any pipeline pass.
  - The model-invocation dependency is injectable.  No real network call is
    made in tests.  Provider routing is wired in Issue 14.
  - Fail-closed: malformed model output raises IntentClassificationError.
    No silent fallback to a default intent type.
  - ClassificationHints is a typed stub; neither field affects classification
    logic in this issue.
  - confidence is advisory in v1; it is not consumed by any routing logic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from uuid import UUID

from afterworlds.models.intent_classification import (
    ClassificationHints,
    IntentClassificationError,
    IntentClassificationResult,
)

# ---------------------------------------------------------------------------
# Injectable model-caller type
# ---------------------------------------------------------------------------

#: Callable interface for the model invocation dependency.
#:
#: Argument:
#:   prompt (str): the complete classification prompt, including the player
#:     input to classify.
#:
#: Returns:
#:   str: the raw model response text (expected to be a JSON object).
ModelCallerT = Callable[[str], str]


# ---------------------------------------------------------------------------
# Classification prompt artifact
# ---------------------------------------------------------------------------

#: Versioned classification prompt.  Encodes the full eight-type taxonomy and
#: all high-collision seam policies so boundary-case classification is
#: determined by explicit instruction, not by model inference.
#:
#: The player input is appended after this string at call time.
CLASSIFICATION_PROMPT: str = """\
You are an intent classifier for an interactive storytelling platform called \
Afterworlds.

Your task: classify the player input below into exactly one of the eight intent \
types listed here, then output a JSON object. Do not output anything else.

## Intent Types

1. `in_character_action` — Player performs an action within the story world.
   Examples: "I draw my sword and charge the guard." / "She picks the lock." /\
 "I search the room for hidden doors."

2. `dialogue` — Player speaks as their character with no accompanying action.
   Examples: "\"We mean you no harm,\" I say slowly." / "\"Where is the key?\"" /\
 "I tell him I know nothing about the letter."

3. `author_instruction` — Player directs the narrative as an author (craft or\
 tone directive).
   Examples: "Make this scene darker." / "Skip ahead to the morning." /\
 "Write this more slowly and with more tension."

4. `branch_choice` — Player selects a presented branch using explicit selection\
 language.
   Examples: "I choose option 2." / "Take the second option." /\
 "I pick the southern-road option." / "Go with choice 3."

5. `beat_milestone` — Player advances or sets a story beat or chapter marker.
   Examples: "Start the next chapter." / "Mark this as the end of Act 1." /\
 "Begin the next scene."

6. `rewind` — Player requests a retry, undo, or regeneration of a prior turn.
   Examples: "Let me try that again." / "Rewind to before I opened the door." /\
 "Undo that." / "Can we go back?"

7. `lore_question` — Player asks an in-world factual question without taking\
 action.
   Examples: "What do I know about the Ember Court?" /\
 "How far is it to Veldris?" / "What does this symbol mean?"

8. `ooc` — Out-of-character input: a meta or platform-level statement not\
 directed at the story world.
   Examples: "[OOC] How does the dice system work?" /\
 "Can you write longer responses?" / "How do I save my progress?" /\
 "What commands are available?"

## Classification Policies for High-Collision Boundaries

**`in_character_action` vs. `dialogue`:**
If the input contains both an action and speech (e.g., "I step forward and say,\
 'Drop your weapon.'"), classify as `in_character_action`. Dialogue embedded in\
 an action beat is still an action beat. Pure speech with no accompanying\
 physical action classifies as `dialogue`.

**`author_instruction` vs. `beat_milestone`:**
`author_instruction` directs narrative craft or tone ("write this more slowly");\
 `beat_milestone` advances story structure ("end this chapter"). If the input\
 does both, classify as `author_instruction` — structural advancement is an\
 effect of the craft instruction, not a separate intent.

**`branch_choice` vs. `in_character_action`:**
Classify as `branch_choice` only when the input uses explicit selection language\
 ("I choose option N", "take the [named] option", "I pick option N",\
 "go with choice N"). Without explicit selection language, classify by the\
 input's surface linguistic form — do not infer branch correspondence from\
 likely content match.

**`ooc` detection:**
Classify as `ooc` if ANY of the following apply:
- The input begins with `[OOC]` (injected by the UI)
- The input is clearly directed at the platform, system, or AI rather than at\
 the story world (questions about mechanics, platform features, response\
 formatting, how things work)
- The input refers to the AI, the system, or the game as a game from outside\
 the story world
Note: absence of the `[OOC]` prefix does not mean the input is in-character.\
 Unmarked meta questions must also be classified as `ooc`.

## Ambiguity Handling

Set `ambiguous` to `true` when the input could reasonably classify as more than\
 one intent type. When ambiguous, set `secondary_intent` to the next most likely\
 intent type. When not ambiguous, set `secondary_intent` to null.
A classifier that never returns `ambiguous: true` has hidden its edge cases.

## Output Format

Return ONLY a JSON object with this exact structure — no markdown fences, no\
 prose, no commentary:

{
  "intent_type": "<one of the 8 intent type string values>",
  "confidence": <float 0.0 to 1.0>,
  "ambiguous": <true or false>,
  "secondary_intent": "<intent type string or null>"
}

## Player Input to Classify

"""


# ---------------------------------------------------------------------------
# Internal parse helper
# ---------------------------------------------------------------------------


def _parse_model_response(
    raw_response: str, raw_input: str
) -> IntentClassificationResult:
    """Parse and validate the model's JSON response.

    Args:
        raw_response: raw text from the model caller.
        raw_input: the original player input (set on the result by the service,
            not echoed from the model, to guarantee fidelity).

    Returns:
        Validated IntentClassificationResult.

    Raises:
        IntentClassificationError: if the response cannot be parsed as valid
            JSON or cannot be validated against IntentClassificationResult.
    """
    text = raw_response.strip()
    # Strip markdown code fences if the model wraps its response
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```")).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IntentClassificationError(
            f"Model returned non-JSON output: {exc!r}"
        ) from exc

    # The service owns raw_input — always override to guarantee it matches the
    # actual submitted input rather than whatever the model echoed.
    data["raw_input"] = raw_input

    try:
        return IntentClassificationResult.model_validate(data)
    except Exception as exc:
        raise IntentClassificationError(
            f"Model response failed schema validation: {exc!r}"
        ) from exc


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class IntentClassifierService:
    """Classifies Sojourner input into a typed IntentClassificationResult.

    The model-invocation callable is injected at construction time.  No
    hardwired provider or model.  Tests pass a stub callable; production wiring
    passes a real provider call (Issue 14).

    Args:
        model_caller: callable that accepts the complete classification prompt
            and returns the raw model response string.  See ModelCallerT.
    """

    def __init__(self, model_caller: ModelCallerT) -> None:
        self._model_caller = model_caller

    def classify(
        self,
        raw_input: str,
        story_id: UUID,
        hints: ClassificationHints | None = None,
    ) -> IntentClassificationResult:
        """Classify a single player input into a typed IntentClassificationResult.

        Classification uses the raw input only.  No Story Bible reads, no
        context assembly, no pipeline calls.  ``story_id`` is included in the
        contract for downstream wiring stability and future evolution; v1
        classification logic does not read story state.  ``hints`` is accepted
        but not consumed in v1; see ClassificationHints for intended future use.

        Args:
            raw_input: the raw player input string to classify.
            story_id: UUID of the story this input belongs to.  Not used by v1
                classification logic.
            hints: optional typed hints stub.  Not consumed in v1.

        Returns:
            IntentClassificationResult with a typed IntentType.

        Raises:
            IntentClassificationError: if the model returns output that cannot
                be parsed and validated as IntentClassificationResult.  No
                silent fallback.
        """
        prompt = CLASSIFICATION_PROMPT + raw_input
        raw_response = self._model_caller(prompt)
        return _parse_model_response(raw_response, raw_input)
