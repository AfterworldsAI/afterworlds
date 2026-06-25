"""Tests for BranchSelectionValidationService — CRD Issue 16 Phase D."""

from __future__ import annotations

from afterworlds.models.enums import InteractionRejectionReason
from afterworlds.models.node import PersistedBranchOption
from afterworlds.pipeline.branching.models import (
    BranchSelectionValidationVerdict,
)
from afterworlds.pipeline.branching.selection import BranchSelectionValidationService


def _opts(
    *labels: str,
) -> list[PersistedBranchOption]:
    return [
        PersistedBranchOption(option_id=f"opt_{i + 1}", action_text=label)
        for i, label in enumerate(labels)
    ]


TWO_OPTS = _opts("Take the bridge", "Wade the river")
THREE_OPTS = _opts("Take the bridge", "Wade the river", "Turn back")


class TestExplicitOptionId:
    """Exact opt_N token in the user's input resolves correctly."""

    def setup_method(self) -> None:
        self.svc = BranchSelectionValidationService()

    def test_opt_1_matches_first_option(self) -> None:
        result = self.svc.validate("opt_1", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_1"

    def test_opt_2_matches_second_option(self) -> None:
        result = self.svc.validate("I choose opt_2", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_2"

    def test_out_of_range_opt_id_rejects(self) -> None:
        result = self.svc.validate("opt_5", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.REJECT
        assert (
            result.rejection_reason
            is InteractionRejectionReason.INVALID_BRANCH_SELECTION
        )

    def test_accepted_action_text_preserved(self) -> None:
        result = self.svc.validate("opt_1", TWO_OPTS)
        assert result.selected_context is not None
        assert result.selected_context.action_text == "Take the bridge"


class TestNumericReference:
    """Numeric phrase ("option 2", "choice 3", or bare "2") resolves correctly."""

    def setup_method(self) -> None:
        self.svc = BranchSelectionValidationService()

    def test_bare_number_matches_option(self) -> None:
        result = self.svc.validate("2", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_2"

    def test_option_n_phrase_matches(self) -> None:
        result = self.svc.validate("option 1", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_1"

    def test_choice_n_phrase_matches(self) -> None:
        result = self.svc.validate("choice 2", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_2"

    def test_number_out_of_range_rejects(self) -> None:
        result = self.svc.validate("option 3", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.REJECT
        assert (
            result.rejection_reason
            is InteractionRejectionReason.INVALID_BRANCH_SELECTION
        )

    def test_three_opts_third_resolves(self) -> None:
        result = self.svc.validate("I pick 3", THREE_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_3"


class TestOrdinalReference:
    """Ordinal words ("first", "second", …) resolve to opt_N."""

    def setup_method(self) -> None:
        self.svc = BranchSelectionValidationService()

    def test_first_resolves_to_opt_1(self) -> None:
        result = self.svc.validate("Take the first option", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_1"

    def test_second_resolves_to_opt_2(self) -> None:
        result = self.svc.validate("I want the second", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_2"

    def test_third_resolves_with_three_options(self) -> None:
        result = self.svc.validate("third", THREE_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.option_id == "opt_3"

    def test_third_out_of_range_rejects(self) -> None:
        result = self.svc.validate("third", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.REJECT


class TestNoMatch:
    """Inputs that don't match any option are rejected."""

    def setup_method(self) -> None:
        self.svc = BranchSelectionValidationService()

    def test_generic_freeform_rejects(self) -> None:
        result = self.svc.validate("I do something completely different", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.REJECT
        assert (
            result.rejection_reason
            is InteractionRejectionReason.INVALID_BRANCH_SELECTION
        )

    def test_rejection_message_is_non_empty(self) -> None:
        result = self.svc.validate("random text", TWO_OPTS)
        assert result.rejection_message is not None
        assert len(result.rejection_message) > 0

    def test_empty_presented_options_rejects(self) -> None:
        result = self.svc.validate("opt_1", [])
        assert result.verdict is BranchSelectionValidationVerdict.REJECT
        assert (
            result.rejection_reason
            is InteractionRejectionReason.INVALID_BRANCH_SELECTION
        )


class TestAnnotation:
    """Trailing text after the selection token is captured as annotation."""

    def setup_method(self) -> None:
        self.svc = BranchSelectionValidationService()

    def test_trailing_text_captured_as_annotation(self) -> None:
        result = self.svc.validate("opt_1 but I stop to grab the sword first", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.annotation is not None
        assert "sword" in result.selected_context.annotation

    def test_no_trailing_text_yields_none_annotation(self) -> None:
        result = self.svc.validate("opt_1", TWO_OPTS)
        assert result.verdict is BranchSelectionValidationVerdict.ACCEPT
        assert result.selected_context is not None
        assert result.selected_context.annotation is None
