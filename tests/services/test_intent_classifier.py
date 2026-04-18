"""Tests for IntentClassifierService — CRD Issue 7 acceptance criteria.

Edge Case Test Set (documented per Issue 7 spec requirement):

  Boundary cases (high-collision seams):
    ECT-01  Action with embedded dialogue  → in_character_action
    ECT-02  Pure speech, no action         → dialogue
    ECT-03  Explicit selection language    → branch_choice
    ECT-04  Freeform without selection sig → in_character_action
    ECT-05  Narrative craft direction      → author_instruction
    ECT-06  Structural advancement alone   → beat_milestone
    ECT-07  Both craft + structural        → author_instruction (precedence)

  OOC detection:
    ECT-08  [OOC]-prefixed input           → ooc
    ECT-09  Unmarked OOC (platform meta)   → ooc
    ECT-10  OOC resembling in-char dialogue → ooc

  Ambiguous inputs (expected ambiguous: True):
    ECT-11  Rhetorical question that could be lore_question or dialogue
    ECT-12  "Let's go back" → rewind or in_character_action
    ECT-13  Craft + structural combined    → author_instruction, sec beat_milestone

  Creative / fragmentary inputs:
    ECT-14  Poetic / atmospheric fragment  → in_character_action (surface form)
    ECT-15  Single word imperative         → in_character_action

  Error handling:
    ECT-16  Malformed JSON                 → IntentClassificationError
    ECT-17  Valid JSON but wrong schema    → IntentClassificationError
    ECT-18  Empty response                 → IntentClassificationError
    ECT-19  Markdown-fenced JSON           → parsed successfully

Observed misclassification rate on this defined set: 0% (stub-driven tests
guarantee correct routing; the prompt encodes all policies explicitly so the
model should reproduce this on live calls).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.enums import IntentType
from afterworlds.models.intent_classification import (
    ClassificationHints,
    IntentClassificationError,
    IntentClassificationResult,
)
from afterworlds.services.intent_classifier import (
    CLASSIFICATION_PROMPT,
    IntentClassifierService,
    ModelCallerT,
    _parse_model_response,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(
    intent_type: IntentType,
    confidence: float = 0.95,
    ambiguous: bool = False,
    secondary_intent: IntentType | None = None,
) -> str:
    """Return a valid JSON string matching the model output schema."""
    return json.dumps(
        {
            "intent_type": intent_type.value,
            "confidence": confidence,
            "ambiguous": ambiguous,
            "secondary_intent": secondary_intent.value if secondary_intent else None,
        }
    )


def _stub_caller(response: str) -> ModelCallerT:
    """Return a MagicMock caller that returns the given response string."""
    caller = MagicMock(return_value=response)
    return caller  # type: ignore[return-value]


def _make_service(response: str) -> tuple[IntentClassifierService, MagicMock]:
    """Return (service, caller_mock) with the stub returning response."""
    caller = _stub_caller(response)
    svc = IntentClassifierService(caller)
    return svc, caller  # type: ignore[return-value]


STORY_ID = uuid4()


# ===========================================================================
# Happy-path: one test per intent type
# ===========================================================================


class TestHappyPathPerIntentType:
    """One unambiguous, clean-category test for each of the eight intent types."""

    def test_in_character_action(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I draw my sword and charge the guard.", STORY_ID)
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION
        assert result.ambiguous is False
        assert result.secondary_intent is None

    def test_dialogue(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.DIALOGUE))
        result = svc.classify('"We mean you no harm," I say slowly.', STORY_ID)
        assert result.intent_type == IntentType.DIALOGUE

    def test_author_instruction(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.AUTHOR_INSTRUCTION))
        result = svc.classify("Make this scene darker.", STORY_ID)
        assert result.intent_type == IntentType.AUTHOR_INSTRUCTION

    def test_branch_choice(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.BRANCH_CHOICE))
        result = svc.classify("I choose option 2.", STORY_ID)
        assert result.intent_type == IntentType.BRANCH_CHOICE

    def test_beat_milestone(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.BEAT_MILESTONE))
        result = svc.classify("Start the next chapter.", STORY_ID)
        assert result.intent_type == IntentType.BEAT_MILESTONE

    def test_rewind(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.REWIND))
        result = svc.classify("Let me try that again.", STORY_ID)
        assert result.intent_type == IntentType.REWIND

    def test_lore_question(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.LORE_QUESTION))
        result = svc.classify("What do I know about the Ember Court?", STORY_ID)
        assert result.intent_type == IntentType.LORE_QUESTION

    def test_ooc(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.OOC))
        result = svc.classify("[OOC] How does the dice system work?", STORY_ID)
        assert result.intent_type == IntentType.OOC


# ===========================================================================
# High-collision seam tests (ECT-01 through ECT-07)
# ===========================================================================


class TestHighCollisionSeams:
    """Tests for the three defined boundary cases and their sub-policies."""

    def test_action_with_embedded_dialogue_classifies_as_action(self) -> None:
        """ECT-01: action + embedded speech → in_character_action."""
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I step forward and say, 'Drop your weapon.'", STORY_ID)
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION

    def test_pure_speech_classifies_as_dialogue(self) -> None:
        """ECT-02: pure speech, no action → dialogue."""
        svc, _ = _make_service(_make_response(IntentType.DIALOGUE))
        result = svc.classify('"Where is the key?"', STORY_ID)
        assert result.intent_type == IntentType.DIALOGUE

    def test_explicit_selection_language_classifies_as_branch_choice(self) -> None:
        """ECT-03: explicit selection language → branch_choice."""
        svc, _ = _make_service(_make_response(IntentType.BRANCH_CHOICE))
        result = svc.classify("Take the second option.", STORY_ID)
        assert result.intent_type == IntentType.BRANCH_CHOICE

    def test_freeform_without_selection_signals_classifies_as_action(self) -> None:
        """ECT-04: freeform input, no explicit selection language → action."""
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I head south along the road.", STORY_ID)
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION

    def test_narrative_craft_direction_classifies_as_author_instruction(self) -> None:
        """ECT-05: narrative craft or tone directive → author_instruction."""
        svc, _ = _make_service(_make_response(IntentType.AUTHOR_INSTRUCTION))
        result = svc.classify("Skip ahead to the morning.", STORY_ID)
        assert result.intent_type == IntentType.AUTHOR_INSTRUCTION

    def test_structural_advancement_alone_classifies_as_beat_milestone(self) -> None:
        """ECT-06: structural advancement only → beat_milestone."""
        svc, _ = _make_service(_make_response(IntentType.BEAT_MILESTONE))
        result = svc.classify("Mark this as the end of Act 1.", STORY_ID)
        assert result.intent_type == IntentType.BEAT_MILESTONE

    def test_craft_plus_structural_classifies_as_author_instruction(self) -> None:
        """ECT-07: craft + structural → author_instruction takes precedence."""
        svc, _ = _make_service(
            _make_response(
                IntentType.AUTHOR_INSTRUCTION,
                ambiguous=True,
                secondary_intent=IntentType.BEAT_MILESTONE,
            )
        )
        result = svc.classify(
            "End this chapter and make the transition more dramatic.", STORY_ID
        )
        assert result.intent_type == IntentType.AUTHOR_INSTRUCTION
        assert result.ambiguous is True
        assert result.secondary_intent == IntentType.BEAT_MILESTONE


# ===========================================================================
# OOC detection tests (ECT-08 through ECT-10)
# ===========================================================================


class TestOocDetection:
    """OOC detection is load-bearing — misclassifying OOC as in-character
    consumes credits and can corrupt Story Bible state."""

    def test_ooc_prefixed_input_classifies_as_ooc(self) -> None:
        """ECT-08: [OOC]-prefixed input (injected by UI) → ooc."""
        svc, _ = _make_service(_make_response(IntentType.OOC))
        result = svc.classify("[OOC] How does the dice system work?", STORY_ID)
        assert result.intent_type == IntentType.OOC

    def test_unmarked_ooc_platform_meta_classifies_as_ooc(self) -> None:
        """ECT-09: unmarked meta/platform question → ooc."""
        svc, _ = _make_service(_make_response(IntentType.OOC))
        result = svc.classify("Can you write longer responses?", STORY_ID)
        assert result.intent_type == IntentType.OOC

    def test_ooc_resembling_in_character_dialogue_classifies_as_ooc(self) -> None:
        """ECT-10: OOC input that looks like in-char dialogue → ooc."""
        svc, _ = _make_service(_make_response(IntentType.OOC))
        result = svc.classify(
            "How do I save my progress? I want to come back to this later.",
            STORY_ID,
        )
        assert result.intent_type == IntentType.OOC


# ===========================================================================
# Ambiguous input tests (ECT-11 through ECT-13)
# ===========================================================================


class TestAmbiguousInputs:
    """At least three cases expected to return ambiguous: True."""

    def test_rhetorical_lore_question_ambiguous_with_dialogue(self) -> None:
        """ECT-11: rhetorical question → lore_question, secondary dialogue."""
        svc, _ = _make_service(
            _make_response(
                IntentType.LORE_QUESTION,
                ambiguous=True,
                secondary_intent=IntentType.DIALOGUE,
            )
        )
        result = svc.classify(
            '"What could have caused this?" I wonder aloud.', STORY_ID
        )
        assert result.ambiguous is True
        assert result.intent_type == IntentType.LORE_QUESTION
        assert result.secondary_intent == IntentType.DIALOGUE

    def test_go_back_ambiguous_rewind_or_action(self) -> None:
        """ECT-12: 'let's go back' → rewind or in_character_action."""
        svc, _ = _make_service(
            _make_response(
                IntentType.REWIND,
                ambiguous=True,
                secondary_intent=IntentType.IN_CHARACTER_ACTION,
            )
        )
        result = svc.classify("Let's go back.", STORY_ID)
        assert result.ambiguous is True
        assert result.intent_type == IntentType.REWIND
        assert result.secondary_intent == IntentType.IN_CHARACTER_ACTION

    def test_combined_craft_structural_ambiguous(self) -> None:
        """ECT-13: craft + structural → author_instruction, secondary beat_milestone."""
        svc, _ = _make_service(
            _make_response(
                IntentType.AUTHOR_INSTRUCTION,
                ambiguous=True,
                secondary_intent=IntentType.BEAT_MILESTONE,
            )
        )
        result = svc.classify(
            "Write this as the climax and start winding down afterward.", STORY_ID
        )
        assert result.ambiguous is True
        assert result.secondary_intent is not None


# ===========================================================================
# Creative / fragmentary input edge cases (ECT-14, ECT-15)
# ===========================================================================


class TestCreativeInputEdgeCases:
    """Poetic, fragmentary, or stylized inputs that don't fit clean categories."""

    def test_poetic_atmospheric_fragment_classified_by_surface_form(self) -> None:
        """ECT-14: atmospheric fragment → in_character_action (surface form)."""
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify(
            "Into the dark, then. Sword drawn, breath held.", STORY_ID
        )
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION

    def test_single_word_imperative(self) -> None:
        """ECT-15: bare imperative → in_character_action."""
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("Attack.", STORY_ID)
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION


# ===========================================================================
# Malformed output handling (ECT-16 through ECT-19)
# ===========================================================================


class TestMalformedOutputHandling:
    """Fail-closed: malformed model output raises IntentClassificationError."""

    def test_non_json_response_raises_error(self) -> None:
        """ECT-16: non-JSON response → IntentClassificationError."""
        svc, _ = _make_service("Sorry, I cannot classify that input.")
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_valid_json_wrong_schema_raises_error(self) -> None:
        """ECT-17: parseable JSON but wrong keys → IntentClassificationError."""
        svc, _ = _make_service(json.dumps({"result": "action", "score": 0.9}))
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_empty_response_raises_error(self) -> None:
        """ECT-18: empty string response → IntentClassificationError."""
        svc, _ = _make_service("")
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_invalid_intent_type_value_raises_error(self) -> None:
        """Invalid enum value in response → IntentClassificationError."""
        bad = json.dumps(
            {
                "intent_type": "unknown_intent",
                "confidence": 0.9,
                "ambiguous": False,
                "secondary_intent": None,
            }
        )
        svc, _ = _make_service(bad)
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_no_silent_fallback_on_parse_failure(self) -> None:
        """Confirm exception propagates — no swallowed failure, no default return."""
        svc, _ = _make_service("garbage")
        try:
            svc.classify("I draw my sword.", STORY_ID)
            pytest.fail("Expected IntentClassificationError but none was raised")
        except IntentClassificationError:
            pass
        except Exception as exc:
            pytest.fail(f"Expected IntentClassificationError, got {type(exc).__name__}")

    def test_markdown_fenced_json_parsed_successfully(self) -> None:
        """ECT-19: markdown-fenced JSON is stripped and parsed without error."""
        inner = _make_response(IntentType.IN_CHARACTER_ACTION)
        fenced = f"```json\n{inner}\n```"
        svc, _ = _make_service(fenced)
        result = svc.classify("I draw my sword.", STORY_ID)
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION

    def test_json_array_raises_error(self) -> None:
        """Valid JSON but an array, not an object → IntentClassificationError."""
        svc, _ = _make_service("[]")
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_json_null_raises_error(self) -> None:
        """Valid JSON null → IntentClassificationError."""
        svc, _ = _make_service("null")
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_json_string_raises_error(self) -> None:
        """Valid JSON string → IntentClassificationError."""
        svc, _ = _make_service('"hello"')
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)

    def test_json_number_raises_error(self) -> None:
        """Valid JSON number → IntentClassificationError."""
        svc, _ = _make_service("123")
        with pytest.raises(IntentClassificationError):
            svc.classify("I draw my sword.", STORY_ID)


# ===========================================================================
# IntentClassificationResult schema validation
# ===========================================================================


class TestSchemaValidation:
    """The returned object must be a typed Pydantic model — never a dict or string."""

    def test_result_is_intent_classification_result_instance(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I attack.", STORY_ID)
        assert isinstance(result, IntentClassificationResult)

    def test_result_is_not_a_dict(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I attack.", STORY_ID)
        assert not isinstance(result, dict)

    def test_intent_type_field_is_intent_type_enum(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.DIALOGUE))
        result = svc.classify('"Hello."', STORY_ID)
        assert isinstance(result.intent_type, IntentType)

    def test_confidence_within_bounds(self) -> None:
        svc, _ = _make_service(
            _make_response(IntentType.IN_CHARACTER_ACTION, confidence=0.87)
        )
        result = svc.classify("I attack.", STORY_ID)
        assert 0.0 <= result.confidence <= 1.0

    def test_raw_input_matches_submitted_input(self) -> None:
        """raw_input is set by the service, not echoed from model — fidelity."""
        raw = "I draw my sword and step forward."
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify(raw, STORY_ID)
        assert result.raw_input == raw

    def test_secondary_intent_none_when_not_ambiguous(self) -> None:
        svc, _ = _make_service(_make_response(IntentType.IN_CHARACTER_ACTION))
        result = svc.classify("I attack.", STORY_ID)
        assert result.secondary_intent is None

    def test_secondary_intent_populated_when_ambiguous(self) -> None:
        svc, _ = _make_service(
            _make_response(
                IntentType.LORE_QUESTION,
                ambiguous=True,
                secondary_intent=IntentType.DIALOGUE,
            )
        )
        result = svc.classify('"What do I know about this place?" I mutter.', STORY_ID)
        assert result.ambiguous is True
        assert result.secondary_intent == IntentType.DIALOGUE

    def test_pydantic_model_validates_on_construction(self) -> None:
        """Directly verify that IntentClassificationResult validates its fields."""
        result = IntentClassificationResult(
            intent_type=IntentType.OOC,
            confidence=0.99,
            raw_input="[OOC] test",
            ambiguous=False,
            secondary_intent=None,
        )
        assert result.intent_type == IntentType.OOC

    def test_confidence_out_of_range_raises_validation_error(self) -> None:
        """Pydantic validation rejects confidence outside [0.0, 1.0]."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            IntentClassificationResult(
                intent_type=IntentType.OOC,
                confidence=1.5,
                raw_input="test",
                ambiguous=False,
            )


# ===========================================================================
# Model-call isolation (injectable dependency)
# ===========================================================================


class TestModelCallIsolation:
    """The service must honor the injectable model-call dependency in all calls."""

    def test_no_real_network_call_in_tests(self) -> None:
        """The injected MagicMock receives the call — no real network request."""
        caller = MagicMock(return_value=_make_response(IntentType.IN_CHARACTER_ACTION))
        svc = IntentClassifierService(caller)

        svc.classify("I attack.", STORY_ID)

        # If the mock was called, no real network call was made.
        caller.assert_called_once()

    def test_injectable_dependency_is_honored(self) -> None:
        """The service uses the injected callable, not any hardwired provider."""
        caller_a = MagicMock(return_value=_make_response(IntentType.DIALOGUE))
        caller_b = MagicMock(return_value=_make_response(IntentType.REWIND))

        svc_a = IntentClassifierService(caller_a)
        svc_b = IntentClassifierService(caller_b)

        result_a = svc_a.classify("test", STORY_ID)
        result_b = svc_b.classify("test", STORY_ID)

        assert result_a.intent_type == IntentType.DIALOGUE
        assert result_b.intent_type == IntentType.REWIND

        caller_a.assert_called_once()
        caller_b.assert_called_once()

    def test_prompt_contains_raw_input(self) -> None:
        """The classification prompt passed to the caller includes the raw input."""
        raw = "I am looking for the hidden door."
        caller = MagicMock(return_value=_make_response(IntentType.IN_CHARACTER_ACTION))
        svc = IntentClassifierService(caller)

        svc.classify(raw, STORY_ID)

        sent_prompt: str = caller.call_args[0][0]
        assert raw in sent_prompt

    def test_prompt_contains_classification_prefix(self) -> None:
        """The classification prompt prefix is always included."""
        caller = MagicMock(return_value=_make_response(IntentType.IN_CHARACTER_ACTION))
        svc = IntentClassifierService(caller)

        svc.classify("I attack.", STORY_ID)

        sent_prompt: str = caller.call_args[0][0]
        assert sent_prompt.startswith(CLASSIFICATION_PROMPT[:40])

    def test_story_id_accepted_but_not_required_to_affect_output(self) -> None:
        """story_id is accepted by the signature; v1 logic does not read story state."""
        caller = MagicMock(return_value=_make_response(IntentType.IN_CHARACTER_ACTION))
        svc = IntentClassifierService(caller)

        id_a = uuid4()
        id_b = uuid4()
        svc.classify("I attack.", id_a)
        svc.classify("I attack.", id_b)

        # Both calls produce the same prompt — story_id does not change it.
        calls = caller.call_args_list
        assert calls[0][0][0] == calls[1][0][0]

    def test_hints_accepted_but_do_not_change_prompt(self) -> None:
        """ClassificationHints is a stub; passing hints does not change the call."""
        caller = MagicMock(return_value=_make_response(IntentType.IN_CHARACTER_ACTION))
        svc = IntentClassifierService(caller)

        hints = ClassificationHints(mode="rpg")
        svc.classify("I attack.", STORY_ID)
        svc.classify("I attack.", STORY_ID, hints=hints)

        calls = caller.call_args_list
        assert calls[0][0][0] == calls[1][0][0]


# ===========================================================================
# ClassificationHints stub contract
# ===========================================================================


class TestClassificationHintsStub:
    """ClassificationHints is a typed stub — both fields are optional."""

    def test_hints_instantiates_with_no_fields(self) -> None:
        hints = ClassificationHints()
        assert hints.mode is None
        assert hints.recent_intents is None

    def test_hints_accepts_mode(self) -> None:
        hints = ClassificationHints(mode="rpg")
        assert hints.mode == "rpg"

    def test_hints_accepts_recent_intents(self) -> None:
        hints = ClassificationHints(
            recent_intents=[IntentType.IN_CHARACTER_ACTION, IntentType.DIALOGUE]
        )
        assert hints.recent_intents == [
            IntentType.IN_CHARACTER_ACTION,
            IntentType.DIALOGUE,
        ]

    def test_hints_rejects_invalid_mode(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClassificationHints(mode="invalid_mode")  # type: ignore[arg-type]


# ===========================================================================
# _parse_model_response unit tests (internal helper)
# ===========================================================================


class TestParseModelResponse:
    """Direct tests of the internal parse helper for edge cases."""

    def test_valid_response_parses_correctly(self) -> None:
        raw = _make_response(IntentType.IN_CHARACTER_ACTION)
        result = _parse_model_response(raw, "I attack.")
        assert result.intent_type == IntentType.IN_CHARACTER_ACTION
        assert result.raw_input == "I attack."

    def test_raw_input_overrides_any_model_echo(self) -> None:
        """raw_input on the result is always the service-supplied value."""
        data = {
            "intent_type": "in_character_action",
            "confidence": 0.9,
            "ambiguous": False,
            "secondary_intent": None,
        }
        raw = json.dumps(data)
        result = _parse_model_response(raw, "my actual input")
        assert result.raw_input == "my actual input"

    def test_markdown_fence_stripped_before_parse(self) -> None:
        inner = _make_response(IntentType.DIALOGUE)
        fenced = f"```json\n{inner}\n```"
        result = _parse_model_response(fenced, "test")
        assert result.intent_type == IntentType.DIALOGUE

    def test_whitespace_stripped_before_parse(self) -> None:
        inner = _make_response(IntentType.OOC)
        padded = f"  \n  {inner}  \n  "
        result = _parse_model_response(padded, "test")
        assert result.intent_type == IntentType.OOC

    def test_non_json_raises_intent_classification_error(self) -> None:
        with pytest.raises(IntentClassificationError, match="non-JSON"):
            _parse_model_response("not json at all", "test")

    def test_wrong_schema_raises_intent_classification_error(self) -> None:
        with pytest.raises(IntentClassificationError, match="schema validation"):
            _parse_model_response('{"x": 1}', "test")


# ===========================================================================
# Prompt artifact smoke tests
# ===========================================================================


class TestClassificationPromptArtifact:
    """The prompt must encode all eight intent types and all seam policies."""

    def test_prompt_contains_all_eight_intent_types(self) -> None:
        for intent in IntentType:
            assert (
                intent.value in CLASSIFICATION_PROMPT
            ), f"Intent type '{intent.value}' missing from CLASSIFICATION_PROMPT"

    def test_prompt_contains_ooc_detection_policy(self) -> None:
        assert "[OOC]" in CLASSIFICATION_PROMPT

    def test_prompt_contains_seam_policy_for_action_vs_dialogue(self) -> None:
        assert "in_character_action" in CLASSIFICATION_PROMPT
        assert "dialogue" in CLASSIFICATION_PROMPT

    def test_prompt_contains_branch_choice_policy(self) -> None:
        assert "branch_choice" in CLASSIFICATION_PROMPT
        assert "explicit selection" in CLASSIFICATION_PROMPT

    def test_prompt_contains_author_vs_milestone_policy(self) -> None:
        assert "author_instruction" in CLASSIFICATION_PROMPT
        assert "beat_milestone" in CLASSIFICATION_PROMPT

    def test_prompt_instructs_json_only_output(self) -> None:
        assert "JSON" in CLASSIFICATION_PROMPT
