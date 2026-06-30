"""Tests for Writing mode pipeline.

Covers registry, DTOs, context renderer, visible state, OOC extractor, and canon seam.

Covers:
- Persona Registry: load, orientation, list_active, hidden/deprecated, invalid ID
- WritingTurnRequest: cross-field validator, effective_canon_eligibility default
- WritingVersionPointer: label validation
- WritingContextRenderer: appendix content, empty when no persona
- WritingVisibleStateService: build, render_context_appendix
- Canon-eligibility enforcement: skip_story_bible_routing default behavior
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import (
    CritiqueIntensity,
    StyleDensity,
    WritingCanonEligibility,
    WritingForm,
    WritingPlayStatus,
    WritingVersionPointerKind,
    WritingWorkProductKind,
)
from afterworlds.models.session import WritingSessionState
from afterworlds.modes.personas.registry import (
    JsonPersonaRegistry,
    PersonaOrientation,
    SupportedMode,
    get_default_registry,
)
from afterworlds.pipeline.writing.context import render_writing_system_prompt_appendix
from afterworlds.pipeline.writing.models import (
    AuthoringControlsSnapshot,
    WritingConfigUpdate,
    WritingOocConfigExtractorResult,
    WritingTurnRequest,
    WritingVersionPointer,
)
from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService

# ---------------------------------------------------------------------------
# Persona Registry
# ---------------------------------------------------------------------------


class TestPersonaRegistry:
    def setup_method(self) -> None:
        self.registry: JsonPersonaRegistry = get_default_registry()

    def test_loads_six_active_personas(self) -> None:
        profiles = self.registry.list_active(SupportedMode.WRITING)
        assert len(profiles) == 6

    def test_mentor_personas_present(self) -> None:
        profiles = self.registry.list_active(SupportedMode.WRITING)
        mentors = [p for p in profiles if p.orientation is PersonaOrientation.MENTOR]
        slugs = {p.persona_id for p in mentors}
        assert {"chiron", "merlin", "vidura"} == slugs

    def test_peer_personas_present(self) -> None:
        profiles = self.registry.list_active(SupportedMode.WRITING)
        peers = [p for p in profiles if p.orientation is PersonaOrientation.PEER]
        slugs = {p.persona_id for p in peers}
        assert {"athena", "odin", "thoth"} == slugs

    def test_get_profile_chiron(self) -> None:
        profile = self.registry.get_profile("chiron", SupportedMode.WRITING)
        assert profile.persona_id == "chiron"
        assert profile.orientation is PersonaOrientation.MENTOR
        assert profile.display_name
        assert profile.prompt_fragment
        assert profile.negative_constraints

    def test_get_profile_athena(self) -> None:
        profile = self.registry.get_profile("athena", SupportedMode.WRITING)
        assert profile.persona_id == "athena"
        assert profile.orientation is PersonaOrientation.PEER

    def test_get_profile_invalid_id_raises(self) -> None:
        with pytest.raises((KeyError, ValueError)):
            self.registry.get_profile("unknown_persona", SupportedMode.WRITING)

    def test_list_active_excludes_hidden_and_deprecated(self) -> None:
        profiles = self.registry.list_active(SupportedMode.WRITING)
        statuses = {p.availability.value for p in profiles}
        assert "hidden" not in statuses
        assert "deprecated" not in statuses

    def test_all_profiles_have_required_ui_fields(self) -> None:
        for profile in self.registry.list_active(SupportedMode.WRITING):
            assert profile.ui_short_description
            assert profile.ui_long_description
            assert profile.signature_move
            assert profile.demeanor_tags

    def test_registry_version_is_positive(self) -> None:
        assert self.registry.registry_version >= 1

    def test_profile_version_is_positive(self) -> None:
        for profile in self.registry.list_active(SupportedMode.WRITING):
            assert profile.profile_version >= 1


# ---------------------------------------------------------------------------
# WritingTurnRequest
# ---------------------------------------------------------------------------


class TestWritingTurnRequest:
    def test_defaults_to_non_canon(self) -> None:
        req = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.PROSE_CONTINUATION
        )
        assert (
            req.effective_canon_eligibility is WritingCanonEligibility.NON_CANON_SUPPORT
        )  # noqa: E501

    def test_no_override_is_non_canon(self) -> None:
        for kind in WritingWorkProductKind:
            if kind in (
                WritingWorkProductKind.PROSE_CONTINUATION,
                WritingWorkProductKind.DRAFT_PROSE,
                WritingWorkProductKind.REVISION,
            ):
                req = WritingTurnRequest(work_product_kind=kind)
                assert (
                    req.effective_canon_eligibility
                    is WritingCanonEligibility.NON_CANON_SUPPORT
                )

    def test_prose_continuation_can_be_extractor_eligible(self) -> None:
        req = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.PROSE_CONTINUATION,
            canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
        )
        assert (
            req.effective_canon_eligibility
            is WritingCanonEligibility.EXTRACTOR_ELIGIBLE
        )  # noqa: E501

    def test_draft_prose_can_be_extractor_eligible(self) -> None:
        req = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.DRAFT_PROSE,
            canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
        )
        assert (
            req.effective_canon_eligibility
            is WritingCanonEligibility.EXTRACTOR_ELIGIBLE
        )  # noqa: E501

    def test_revision_can_be_extractor_eligible(self) -> None:
        req = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.REVISION,
            canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
        )
        assert (
            req.effective_canon_eligibility
            is WritingCanonEligibility.EXTRACTOR_ELIGIBLE
        )  # noqa: E501

    def test_critique_cannot_be_extractor_eligible(self) -> None:
        with pytest.raises(ValidationError, match="EXTRACTOR_ELIGIBLE is not valid"):
            WritingTurnRequest(
                work_product_kind=WritingWorkProductKind.CRITIQUE,
                canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
            )

    def test_brainstorm_cannot_be_extractor_eligible(self) -> None:
        with pytest.raises(ValidationError):
            WritingTurnRequest(
                work_product_kind=WritingWorkProductKind.BRAINSTORM,
                canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
            )

    def test_beat_plan_cannot_be_extractor_eligible(self) -> None:
        with pytest.raises(ValidationError):
            WritingTurnRequest(
                work_product_kind=WritingWorkProductKind.BEAT_PLAN,
                canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
            )

    def test_setup_confirmation_cannot_be_extractor_eligible(self) -> None:
        with pytest.raises(ValidationError):
            WritingTurnRequest(
                work_product_kind=WritingWorkProductKind.SETUP_CONFIRMATION,
                canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
            )

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WritingTurnRequest(
                work_product_kind=WritingWorkProductKind.PROSE_CONTINUATION,
                unknown_field="x",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# WritingVersionPointer
# ---------------------------------------------------------------------------


class TestWritingVersionPointer:
    def test_valid_with_label_and_turn(self) -> None:
        ptr = WritingVersionPointer(
            kind=WritingVersionPointerKind.TURN,
            label="Chapter 1 draft",
            source_turn_id=uuid4(),
            created_at=datetime.now(UTC),
        )
        assert ptr.label == "Chapter 1 draft"

    def test_empty_label_rejected(self) -> None:
        with pytest.raises(ValidationError, match="label must be non-empty"):
            WritingVersionPointer(
                kind=WritingVersionPointerKind.DRAFT_LABEL,
                label="   ",
                created_at=datetime.now(UTC),
            )

    def test_pointer_id_auto_generated(self) -> None:
        p1 = WritingVersionPointer(
            kind=WritingVersionPointerKind.NODE,
            label="v1",
            created_at=datetime.now(UTC),
        )
        p2 = WritingVersionPointer(
            kind=WritingVersionPointerKind.NODE,
            label="v2",
            created_at=datetime.now(UTC),
        )
        assert p1.pointer_id != p2.pointer_id


# ---------------------------------------------------------------------------
# AuthoringControlsSnapshot
# ---------------------------------------------------------------------------


class TestAuthoringControlsSnapshot:
    def test_valid_minimal(self) -> None:
        snap = AuthoringControlsSnapshot(
            critique_intensity=CritiqueIntensity.BALANCED,
            form=WritingForm.SHORT_STORY,
            style_density=StyleDensity.BALANCED,
        )
        assert snap.critique_intensity is CritiqueIntensity.BALANCED

    def test_dialogue_ratio_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AuthoringControlsSnapshot(
                critique_intensity=CritiqueIntensity.GENTLE,
                form=WritingForm.NOVEL,
                style_density=StyleDensity.LUSH,
                dialogue_narration_ratio=101,
            )

    def test_dialogue_ratio_zero_valid(self) -> None:
        snap = AuthoringControlsSnapshot(
            critique_intensity=CritiqueIntensity.BLUNT,
            form=WritingForm.NOVEL,
            style_density=StyleDensity.LITERARY,
            dialogue_narration_ratio=0,
        )
        assert snap.dialogue_narration_ratio == 0


# ---------------------------------------------------------------------------
# WritingContextRenderer
# ---------------------------------------------------------------------------


class TestWritingContextRenderer:
    def setup_method(self) -> None:
        self.registry = get_default_registry()

    def test_empty_when_no_persona(self) -> None:
        session_state = WritingSessionState(story_id=uuid4())
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert result == ""

    def test_contains_persona_name(self) -> None:
        session_state = WritingSessionState(story_id=uuid4(), persona_id="chiron")
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert "Chiron" in result

    def test_contains_orientation(self) -> None:
        session_state = WritingSessionState(story_id=uuid4(), persona_id="athena")
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert "peer" in result.lower()

    def test_contains_prompt_fragment(self) -> None:
        session_state = WritingSessionState(story_id=uuid4(), persona_id="odin")
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert len(result) > 100

    def test_contains_authoring_controls(self) -> None:
        session_state = WritingSessionState(
            story_id=uuid4(),
            persona_id="merlin",
            critique_intensity=CritiqueIntensity.RUTHLESS,
            specific_goals="Write a dark fantasy opening.",
        )
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert "ruthless" in result.lower()
        assert "dark fantasy" in result

    def test_invalid_persona_returns_empty(self) -> None:
        session_state = WritingSessionState(
            story_id=uuid4(), persona_id="no_such_persona"
        )
        result = render_writing_system_prompt_appendix(session_state, self.registry)
        assert result == ""

    def test_all_six_personas_produce_output(self) -> None:
        for persona_id in ("chiron", "merlin", "vidura", "athena", "odin", "thoth"):
            session_state = WritingSessionState(story_id=uuid4(), persona_id=persona_id)
            result = render_writing_system_prompt_appendix(session_state, self.registry)
            assert result, f"Empty appendix for {persona_id}"


# ---------------------------------------------------------------------------
# WritingVisibleStateService
# ---------------------------------------------------------------------------


class TestWritingVisibleStateService:
    def setup_method(self) -> None:
        registry = get_default_registry()
        self.service = WritingVisibleStateService(registry)

    def _base_state(self, persona_id: str = "chiron") -> WritingSessionState:
        return WritingSessionState(
            story_id=uuid4(),
            persona_id=persona_id,
            persona_registry_version=1,
            persona_profile_version=1,
            play_status=WritingPlayStatus.IN_PLAY,
            critique_intensity=CritiqueIntensity.BALANCED,
            style_density=StyleDensity.BALANCED,
            form=WritingForm.SHORT_STORY,
            specific_goals="Write something compelling.",
        )

    def test_build_resolves_ui_metadata(self) -> None:
        state = self._base_state("chiron")
        vs = self.service.build(state)
        assert vs.persona_id == "chiron"
        assert vs.relationship_orientation is PersonaOrientation.MENTOR
        assert vs.ui_short_description
        assert vs.signature_move
        assert vs.demeanor_tags

    def test_build_peer_orientation(self) -> None:
        state = self._base_state("odin")
        vs = self.service.build(state)
        assert vs.relationship_orientation is PersonaOrientation.PEER

    def test_build_raises_without_persona(self) -> None:
        state = WritingSessionState(story_id=uuid4())
        with pytest.raises(ValueError, match="persona_id=None"):
            self.service.build(state)

    def test_build_raises_on_bad_persona_id(self) -> None:
        state = WritingSessionState(story_id=uuid4(), persona_id="not_real")
        with pytest.raises(ValueError, match="not found in registry"):
            self.service.build(state)

    def test_build_populates_session_fields(self) -> None:
        state = self._base_state("vidura")
        state = state.model_copy(
            update={
                "specific_goals": "Epic fantasy",
                "tense": "past",
                "pov": "third limited",
                "beat_constraints": ["no deus ex machina"],
            }
        )
        vs = self.service.build(state)
        assert vs.specific_goals == "Epic fantasy"
        assert vs.tense == "past"
        assert vs.pov == "third limited"
        assert "no deus ex machina" in vs.beat_constraints

    def test_build_form_defaults_to_other_when_none(self) -> None:
        state = WritingSessionState(story_id=uuid4(), persona_id="thoth")
        vs = self.service.build(state)
        assert vs.form is WritingForm.OTHER

    def test_render_context_appendix_delegates(self) -> None:
        state = self._base_state("merlin")
        result = self.service.render_context_appendix(state)
        assert "Merlin" in result

    def test_render_context_appendix_empty_without_persona(self) -> None:
        state = WritingSessionState(story_id=uuid4())
        result = self.service.render_context_appendix(state)
        assert result == ""

    def test_registry_property_accessible(self) -> None:
        assert self.service.registry is not None


# ---------------------------------------------------------------------------
# WritingConfigUpdate
# ---------------------------------------------------------------------------


class TestWritingConfigUpdate:
    def test_all_none_is_valid(self) -> None:
        update = WritingConfigUpdate()
        assert update.persona_id is None
        assert update.critique_intensity is None

    def test_ratio_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WritingConfigUpdate(dialogue_narration_ratio=150)

    def test_valid_partial_update(self) -> None:
        update = WritingConfigUpdate(
            persona_id="chiron",
            critique_intensity=CritiqueIntensity.BLUNT,
            tense="present",
        )
        assert update.persona_id == "chiron"
        assert update.tense == "present"


# ---------------------------------------------------------------------------
# WritingOocConfigExtractorResult
# ---------------------------------------------------------------------------


class TestWritingOocConfigExtractorResult:
    def test_defaults(self) -> None:
        result = WritingOocConfigExtractorResult(config_update=WritingConfigUpdate())
        assert result.input_token_count is None
        assert result.latency_ms == 0

    def test_with_metrics(self) -> None:
        result = WritingOocConfigExtractorResult(
            config_update=WritingConfigUpdate(persona_id="odin"),
            provider="anthropic",
            model_identifier="claude-haiku",
            model_tier="haiku",
            input_token_count=100,
            output_token_count=50,
        )
        assert result.config_update.persona_id == "odin"
        assert result.input_token_count == 100


# ---------------------------------------------------------------------------
# WritingOocConfigExtractorService
# ---------------------------------------------------------------------------


def _make_ooc_assembled() -> object:
    """Return an AssembledContext for WritingOocConfigExtractorService tests."""
    from tests.pipeline.orchestrator.conftest import make_assembled

    return make_assembled(uuid4())


def _make_ooc_provider(
    tool_name: str = "extract_writing_config_update",
    tool_input: dict | None = None,
    raise_exc: Exception | None = None,
) -> MagicMock:
    """Return a fake ProviderAdapter for OOC config extractor tests."""
    from afterworlds.entitlement.enums import PipelinePassId
    from afterworlds.pipeline.provider._models import (
        ModelTier,
        ProviderCallResult,
        ProviderToolCallPart,
    )

    fake_provider = MagicMock()
    if raise_exc is not None:
        fake_provider.call.side_effect = raise_exc
    else:
        fake_provider.call.return_value = ProviderCallResult(
            pass_id=PipelinePassId.WRITING_OOC_CONFIG_EXTRACTOR,
            content_parts=[
                ProviderToolCallPart(
                    tool_name=tool_name,
                    tool_input=(
                        tool_input
                        if tool_input is not None
                        else {
                            "persona_id": None,
                            "play_status": None,
                            "critique_intensity": None,
                            "form": None,
                            "form_other": None,
                            "tense": None,
                            "pov": None,
                            "style_density": None,
                            "dialogue_narration_ratio": None,
                            "genre_conventions": None,
                            "specific_goals": None,
                            "acceptable_content": None,
                        }
                    ),
                )
            ],
            provider_name="fake",
            model_identifier="fake-haiku",
            model_tier=ModelTier.HAIKU,
            latency_ms=5,
            input_token_count=50,
            output_token_count=20,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
        )
    return fake_provider


class TestWritingOocConfigExtractorService:
    """Unit tests for WritingOocConfigExtractorService.extract()."""

    def setup_method(self) -> None:
        from afterworlds.pipeline.writing.ooc_config_extractor import (
            WritingOocConfigExtractorService,
        )

        self.service = WritingOocConfigExtractorService()

    def test_successful_extraction_all_none(self) -> None:
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider()
        result = self.service.extract(ctx, provider)  # type: ignore[arg-type]
        assert result.config_update.persona_id is None
        assert result.config_update.tense is None
        assert result.input_token_count == 50
        assert result.output_token_count == 20

    def test_successful_extraction_with_persona_change(self) -> None:
        tool_input = {
            "persona_id": "athena",
            "play_status": "in_play",
            "critique_intensity": "blunt",
            "form": None,
            "form_other": None,
            "tense": None,
            "pov": None,
            "style_density": None,
            "dialogue_narration_ratio": None,
            "genre_conventions": None,
            "specific_goals": None,
            "acceptable_content": None,
        }
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_input=tool_input)
        result = self.service.extract(ctx, provider)  # type: ignore[arg-type]
        assert result.config_update.persona_id == "athena"
        assert result.config_update.play_status is not None

    def test_missing_tool_block_raises_usage_error(self) -> None:
        from afterworlds.entitlement.enums import PipelinePassId
        from afterworlds.pipeline.provider._models import (
            ModelTier,
            ProviderCallResult,
            ProviderTextPart,
        )
        from afterworlds.pipeline.writing.models import WritingOocExtractionUsageError

        fake_provider = MagicMock()
        fake_provider.call.return_value = ProviderCallResult(
            pass_id=PipelinePassId.WRITING_OOC_CONFIG_EXTRACTOR,
            content_parts=[ProviderTextPart(text="No tool block here.")],
            provider_name="fake",
            model_identifier="fake-haiku",
            model_tier=ModelTier.HAIKU,
            latency_ms=5,
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
        )
        ctx = _make_ooc_assembled()
        with pytest.raises(WritingOocExtractionUsageError) as exc_info:
            self.service.extract(ctx, fake_provider)  # type: ignore[arg-type]
        # Usage result is preserved even on failure
        assert exc_info.value.usage_result.input_token_count == 10

    def test_wrong_tool_name_raises_usage_error(self) -> None:
        from afterworlds.pipeline.writing.models import WritingOocExtractionUsageError

        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_name="wrong_tool")
        with pytest.raises(WritingOocExtractionUsageError):
            self.service.extract(ctx, provider)  # type: ignore[arg-type]

    def test_schema_validation_failure_raises_usage_error(self) -> None:
        from afterworlds.pipeline.writing.models import WritingOocExtractionUsageError

        bad_input = {
            "persona_id": None,
            "play_status": None,
            "critique_intensity": "invalid_intensity_value",  # bad enum
            "form": None,
            "form_other": None,
            "tense": None,
            "pov": None,
            "style_density": None,
            "dialogue_narration_ratio": None,
            "genre_conventions": None,
            "specific_goals": None,
            "acceptable_content": None,
        }
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_input=bad_input)
        with pytest.raises(WritingOocExtractionUsageError):
            self.service.extract(ctx, provider)  # type: ignore[arg-type]

    def test_provider_exception_raises_pass_error(self) -> None:
        from afterworlds.pipeline.writing.models import WritingPassError

        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(raise_exc=RuntimeError("provider down"))
        with pytest.raises(WritingPassError, match="provider call failed"):
            self.service.extract(ctx, provider)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Canon eligibility orchestration seam
# ---------------------------------------------------------------------------


def _make_extractor_assembled() -> object:
    """Return an AssembledContext suitable for ExtractorService tests."""
    from tests.pipeline.orchestrator.conftest import make_assembled

    return make_assembled(uuid4())


def _make_fake_extractor_provider() -> MagicMock:
    """Return a fake ProviderAdapter that returns an empty proposal set tool call."""
    from afterworlds.entitlement.enums import PipelinePassId
    from afterworlds.pipeline.extractor.caller import EXTRACT_TOOL_NAME
    from afterworlds.pipeline.provider._models import (
        ModelTier,
        ProviderCallResult,
        ProviderToolCallPart,
    )

    fake_provider = MagicMock()
    fake_provider.call.return_value = ProviderCallResult(
        pass_id=PipelinePassId.EXTRACTOR,
        content_parts=[
            ProviderToolCallPart(
                tool_name=EXTRACT_TOOL_NAME,
                tool_input={"proposals": []},
            )
        ],
        provider_name="fake",
        model_identifier="fake-haiku",
        model_tier=ModelTier.HAIKU,
        latency_ms=0,
        input_token_count=10,
        output_token_count=5,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
    )
    return fake_provider


class TestCanonEligibilitySeam:
    """Verify skip_story_bible_routing logic in the extractor service seam."""

    def test_no_request_defaults_to_skip(self) -> None:
        """Writing turn with no WritingTurnRequest → skip routing (NON_CANON_SUPPORT default)."""  # noqa: E501
        from afterworlds.models.enums import StoryMode, WritingCanonEligibility

        story_mode = StoryMode.WRITING
        writing_turn_request = None

        skip = story_mode is StoryMode.WRITING and (
            writing_turn_request is None
            or writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )
        assert skip is True

    def test_non_canon_request_skips_routing(self) -> None:
        from afterworlds.models.enums import StoryMode, WritingCanonEligibility

        story_mode = StoryMode.WRITING
        writing_turn_request = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.CRITIQUE,
        )
        assert (
            writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )

        skip = story_mode is StoryMode.WRITING and (
            writing_turn_request is None
            or writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )
        assert skip is True

    def test_extractor_eligible_request_does_not_skip(self) -> None:
        from afterworlds.models.enums import StoryMode, WritingCanonEligibility

        story_mode = StoryMode.WRITING
        writing_turn_request = WritingTurnRequest(
            work_product_kind=WritingWorkProductKind.PROSE_CONTINUATION,
            canon_eligibility_override=WritingCanonEligibility.EXTRACTOR_ELIGIBLE,
        )
        assert (
            writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.EXTRACTOR_ELIGIBLE
        )

        skip = story_mode is StoryMode.WRITING and (
            writing_turn_request is None
            or writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )
        assert skip is False

    def test_non_writing_mode_does_not_skip(self) -> None:
        from afterworlds.models.enums import StoryMode, WritingCanonEligibility

        story_mode = StoryMode.BRANCHING
        writing_turn_request = None

        skip = story_mode is StoryMode.WRITING and (
            writing_turn_request is None
            or writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )
        assert skip is False

    def test_extractor_service_skip_routing_produces_empty_summary(self) -> None:
        """ExtractorService.extract(skip=True) discards proposals before Story Bible."""
        from afterworlds.pipeline.extractor.service import ExtractorService

        mock_sbs = MagicMock()
        svc = ExtractorService(session=MagicMock(), story_bible_service=mock_sbs)
        assembled = _make_extractor_assembled()
        fake_provider = _make_fake_extractor_provider()

        result = svc.extract(
            assembled,  # type: ignore[arg-type]
            "Some writer output",
            assembled.stable_prefix.story_bible_context.story_id,  # type: ignore[union-attr]
            uuid4(),
            provider=fake_provider,
            session=None,
            skip_story_bible_routing=True,
        )

        mock_sbs.route_extractor_proposals.assert_not_called()
        assert result.routed.locked_fact_staged_ids == []
        assert result.routed.event_ids == []

    def test_extractor_service_routes_when_not_skipped(self) -> None:
        """ExtractorService.extract(skip=False) calls route_extractor_proposals."""
        from afterworlds.models.extractor import ExtractorRoutingSummary
        from afterworlds.pipeline.extractor.service import ExtractorService

        mock_sbs = MagicMock()
        mock_sbs.route_extractor_proposals.return_value = ExtractorRoutingSummary(
            locked_fact_staged_ids=[],
            soft_fact_staged_ids=[],
            transient_state_staged_ids=[],
            unresolved_thread_staged_ids=[],
            event_ids=[],
        )
        svc = ExtractorService(session=MagicMock(), story_bible_service=mock_sbs)
        assembled = _make_extractor_assembled()
        fake_provider = _make_fake_extractor_provider()

        svc.extract(
            assembled,  # type: ignore[arg-type]
            "Writer output",
            assembled.stable_prefix.story_bible_context.story_id,  # type: ignore[union-attr]
            uuid4(),
            provider=fake_provider,
            session=None,
            skip_story_bible_routing=False,
        )

        mock_sbs.route_extractor_proposals.assert_called_once()


# ---------------------------------------------------------------------------
# WritingConfigUpdate — new field validators (Decision 10 expansion)
# ---------------------------------------------------------------------------


class TestWritingConfigUpdateNewFields:
    def test_beat_constraints_empty_string_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="beat_constraints"):
            WritingConfigUpdate(beat_constraints=["valid constraint", ""])

    def test_beat_constraints_whitespace_only_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="beat_constraints"):
            WritingConfigUpdate(beat_constraints=["   "])

    def test_beat_constraints_valid_list_accepted(self) -> None:
        update = WritingConfigUpdate(
            beat_constraints=["no deus ex machina", "protagonist earns every victory"]
        )
        assert update.beat_constraints == [
            "no deus ex machina",
            "protagonist earns every victory",
        ]

    def test_beat_constraints_none_is_valid(self) -> None:
        update = WritingConfigUpdate(beat_constraints=None)
        assert update.beat_constraints is None

    def test_version_pointers_parsed_from_dicts(self) -> None:
        update = WritingConfigUpdate(
            version_pointers=[
                WritingVersionPointer(
                    kind=WritingVersionPointerKind.DRAFT_LABEL,
                    label="Chapter 1 v2",
                )
            ]
        )
        assert update.version_pointers is not None
        assert len(update.version_pointers) == 1
        assert update.version_pointers[0].label == "Chapter 1 v2"

    def test_version_pointers_none_is_valid(self) -> None:
        update = WritingConfigUpdate(version_pointers=None)
        assert update.version_pointers is None


# ---------------------------------------------------------------------------
# WritingOocConfigExtractorService — schema accepts beat_constraints / version_pointers
# ---------------------------------------------------------------------------


class TestOocExtractorSchemaNewFields:
    """OOC extractor handles beat_constraints and version_pointers in tool output."""

    def setup_method(self) -> None:
        from afterworlds.pipeline.writing.ooc_config_extractor import (
            WritingOocConfigExtractorService,
        )

        self.service = WritingOocConfigExtractorService()

    def test_extraction_with_beat_constraints(self) -> None:
        """Tool output with beat_constraints list → parsed into WritingConfigUpdate."""
        tool_input = {
            "persona_id": None,
            "play_status": None,
            "critique_intensity": None,
            "form": None,
            "form_other": None,
            "tense": None,
            "pov": None,
            "style_density": None,
            "dialogue_narration_ratio": None,
            "genre_conventions": None,
            "specific_goals": None,
            "acceptable_content": None,
            "beat_constraints": ["no deus ex machina", "protagonist earns every win"],
            "version_pointers": None,
        }
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_input=tool_input)
        result = self.service.extract(ctx, provider)  # type: ignore[arg-type]
        assert result.config_update.beat_constraints == [
            "no deus ex machina",
            "protagonist earns every win",
        ]

    def test_extraction_with_version_pointers(self) -> None:
        """Tool output with version_pointers → parsed into WritingConfigUpdate."""
        tool_input = {
            "persona_id": None,
            "play_status": None,
            "critique_intensity": None,
            "form": None,
            "form_other": None,
            "tense": None,
            "pov": None,
            "style_density": None,
            "dialogue_narration_ratio": None,
            "genre_conventions": None,
            "specific_goals": None,
            "acceptable_content": None,
            "beat_constraints": None,
            "version_pointers": [{"kind": "draft_label", "label": "Chapter 1 v2"}],
        }
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_input=tool_input)
        result = self.service.extract(ctx, provider)  # type: ignore[arg-type]
        assert result.config_update.version_pointers is not None
        assert len(result.config_update.version_pointers) == 1
        assert result.config_update.version_pointers[0].label == "Chapter 1 v2"
        # pointer_id auto-generated (not in tool input — default_factory fills it)
        assert result.config_update.version_pointers[0].pointer_id is not None

    def test_extraction_beat_constraints_null_is_none(self) -> None:
        """Null beat_constraints from LLM → None in WritingConfigUpdate."""
        tool_input = {
            "persona_id": None,
            "play_status": None,
            "critique_intensity": None,
            "form": None,
            "form_other": None,
            "tense": None,
            "pov": None,
            "style_density": None,
            "dialogue_narration_ratio": None,
            "genre_conventions": None,
            "specific_goals": None,
            "acceptable_content": None,
            "beat_constraints": None,
            "version_pointers": None,
        }
        ctx = _make_ooc_assembled()
        provider = _make_ooc_provider(tool_input=tool_input)
        result = self.service.extract(ctx, provider)  # type: ignore[arg-type]
        assert result.config_update.beat_constraints is None
        assert result.config_update.version_pointers is None
