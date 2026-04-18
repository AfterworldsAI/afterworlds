"""Context models for the Context Builder — CRD Issue 8.

These models form the typed payload the Context Builder assembles and the
pipeline (Issue 12) consumes.  Three structural partitions are kept strictly
separate:

  stable_prefix  — assembled once per turn; shared across all pipeline passes.
                   Contains system prompt, Story Bible active context, rolling
                   summary.  Never rebuilt per pass — architectural invariant
                   (CRD Item 12, CRD Item 2 Principle 6).
  rule_slice     — optional ActiveRuleSlice (RPG mode only); stored separately
                   from stable_prefix so query-dependent slice changes between
                   turns do not bust the stable-prefix cache window.
  volatile_suffix — assembled per turn; contains recent turns verbatim and the
                   current player input + classified intent.
  pass_forward_ledger — mutable ledger of content injected by each pipeline
                   pass for forwarding to subsequent passes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.rules_package import ActiveRuleSlice
from afterworlds.models.story_bible import (
    CastEntry,
    StoryBibleContext,
)
from afterworlds.models.turn import Turn

# ---------------------------------------------------------------------------
# Story Bible rendering helper
# ---------------------------------------------------------------------------


def _render_story_bible_context(ctx: StoryBibleContext) -> str:
    """Render StoryBibleContext to plain-text for stable prefix inclusion.

    Output is deterministic: each collection is sorted by a stable key so
    the same input always produces the same text (required for cache hits).
    Empty sections are omitted entirely to reduce token footprint.
    """
    sections: list[str] = ["## Story Bible"]

    if ctx.setting is not None:
        s = ctx.setting
        setting_lines: list[str] = [f"### Setting\n{s.summary}"]
        if s.world_rules:
            rules_text = "\n".join(f"- {r}" for r in s.world_rules)
            setting_lines.append(f"World Rules:\n{rules_text}")
        if s.geography is not None:
            setting_lines.append(f"Geography: {s.geography}")
        if s.time_period is not None:
            setting_lines.append(f"Time Period: {s.time_period}")
        sections.append("\n".join(setting_lines))

    if ctx.cast:
        cast_lines: list[str] = ["### Cast"]
        for entry in sorted(ctx.cast, key=lambda c: c.name):
            cast_lines.append(_render_cast_entry(entry))
        sections.append("\n".join(cast_lines))

    if ctx.locked_facts:
        facts = "\n".join(
            f"- {f.fact_text}"
            for f in sorted(ctx.locked_facts, key=lambda x: str(x.locked_fact_id))
        )
        sections.append(f"### Locked Facts\n{facts}")

    if ctx.forbidden_facts:
        facts = "\n".join(
            f"- {f.fact_text}"
            for f in sorted(ctx.forbidden_facts, key=lambda x: str(x.forbidden_fact_id))
        )
        sections.append(f"### Forbidden Facts\n{facts}")

    if ctx.events:
        ev = "\n".join(
            f"- [{e.significance.value}] {e.description}"
            for e in sorted(ctx.events, key=lambda x: (x.created_at, str(x.event_id)))
        )
        sections.append(f"### Events\n{ev}")

    if ctx.active_plot_threads:
        threads = "\n".join(
            f"- {t.description}"
            for t in sorted(
                ctx.active_plot_threads,
                key=lambda x: (x.created_at, str(x.thread_id)),
            )
        )
        sections.append(f"### Active Plot Threads\n{threads}")

    if ctx.relationship_ledger:
        cast_names = {str(e.cast_id): e.name for e in ctx.cast}
        rel_lines: list[str] = ["### Relationships"]
        for r in sorted(ctx.relationship_ledger, key=lambda x: str(x.relationship_id)):
            subj = cast_names.get(str(r.subject_cast_id), str(r.subject_cast_id))
            obj_ = cast_names.get(str(r.object_cast_id), str(r.object_cast_id))
            desc = (
                f" — {r.current_status_description}"
                if r.current_status_description
                else ""
            )
            rel_lines.append(f"  {subj} → {obj_}: {r.relationship_type.value}{desc}")
        sections.append("\n".join(rel_lines))

    return "\n\n".join(sections)


def _render_cast_entry(entry: CastEntry) -> str:
    lines: list[str] = []
    status = "" if entry.is_alive else " [deceased]"
    lines.append(f"\n**{entry.name}** ({entry.role.value}){status}")
    if entry.background:
        lines.append(f"  Background: {entry.background}")
    if entry.current_location:
        lines.append(f"  Location: {entry.current_location}")
    if entry.current_status:
        lines.append(f"  Status: {entry.current_status}")
    if entry.traits:
        lines.append(f"  Traits: {', '.join(entry.traits)}")
    if entry.goals:
        lines.append(f"  Goals: {', '.join(entry.goals)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rule slice rendering helper
# ---------------------------------------------------------------------------


def _render_rule_slice(rule_slice: ActiveRuleSlice) -> str:
    """Render ActiveRuleSlice to plain-text for prompt inclusion."""
    parts: list[str] = [f"## Rules (Package {rule_slice.package_id})"]

    enabled_chunks = [c for c in rule_slice.chunks if not c.is_disabled]
    if enabled_chunks:
        chunk_blocks = "\n\n".join(
            f"### {c.chunk.subsystem.value}\n{c.applied_content}"
            for c in enabled_chunks
        )
        parts.append(chunk_blocks)

    if rule_slice.entities:
        entity_blocks = "\n\n".join(
            f"**{e.entity.entity_type.value}: {e.entity.name}**"
            for e in rule_slice.entities
        )
        parts.append(entity_blocks)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Pass-forward ledger
# ---------------------------------------------------------------------------


class PassForwardEntry(BaseModel):
    """One pipeline pass's injected context forwarded to subsequent passes."""

    pass_name: str
    content: str


class PassForwardLedger(BaseModel):
    """Mutable ledger of pass-injected content for the current turn.

    The pipeline (Issue 12) calls ``add()`` after each pass completes to
    record the content that subsequent passes must see.  The ledger is
    initialised empty by the Context Builder and mutated by the pipeline.
    """

    entries: list[PassForwardEntry] = Field(default_factory=list)

    def add(self, pass_name: str, content: str) -> None:
        """Record content injected by a pipeline pass."""
        self.entries.append(PassForwardEntry(pass_name=pass_name, content=content))

    def render(self) -> str:
        """Render all ledger entries as text for inclusion in a pass prompt."""
        if not self.entries:
            return ""
        return "\n\n".join(
            f"[{e.pass_name.upper()} OUTPUT]\n{e.content}" for e in self.entries
        )


# ---------------------------------------------------------------------------
# Stable prefix
# ---------------------------------------------------------------------------


class StablePrefix(BaseModel):
    """Stable prompt prefix — assembled once per turn, shared across all passes.

    Partition contents (in render order):
      1. system_prompt — includes mode contract; provided by the caller
      2. story_bible_context — ratified canon, rendered from StoryBibleContext
      3. rolling_summary_text — compressed narrative history, or None

    The raw StoryBibleContext is preserved alongside the rendered text so
    tests and downstream consumers can inspect the structured data without
    re-parsing.

    The rule slice is intentionally NOT part of StablePrefix — it is stored
    separately on AssembledContext.  Subsystem queries can change between
    turns (combat turn vs. lore turn), and including the slice here would
    bust the stable-prefix cache window.  See ADR-0010.
    """

    system_prompt: str
    story_bible_context: StoryBibleContext
    rolling_summary_text: str | None = None

    def render(self) -> str:
        """Return the assembled stable prefix text in canonical order."""
        parts: list[str] = [
            self.system_prompt,
            _render_story_bible_context(self.story_bible_context),
        ]
        if self.rolling_summary_text is not None:
            parts.append(self.rolling_summary_text)
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Volatile suffix
# ---------------------------------------------------------------------------


class VolatileSuffix(BaseModel):
    """Volatile prompt suffix — assembled per turn from recent history.

    Partition contents (in render order):
      1. recent_turns — verbatim turn pairs, oldest-first; set by provider
      2. current_input — the raw player input for this turn
      3. classified_intent — typed classification result from Issue 7

    recent_turns is always oldest-first in this model.  The provider is
    responsible for returning turns in that order (see context_builder.py).
    """

    recent_turns: list[Turn]
    current_input: str
    classified_intent: IntentClassificationResult

    def render(self) -> str:
        """Return the assembled volatile suffix text."""
        parts: list[str] = []
        for turn in self.recent_turns:
            parts.append(
                f"Player: {turn.user_input}\nNarrator: {turn.assistant_output}"
            )
        parts.append(
            f"Player: {self.current_input}\n"
            f"[Intent: {self.classified_intent.intent_type.value}]"
        )
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Assembled context
# ---------------------------------------------------------------------------


class AssembledContext(BaseModel):
    """Complete context payload for one pipeline turn.

    Structural partitions:
      stable_prefix      — assembled once; shared across all passes.
      rule_slice         — optional; separate from stable_prefix for cache.
      volatile_suffix    — recent turns + current input.
      pass_forward_ledger — mutable; pipeline passes add to it as they run.

    The pipeline (Issue 12) calls render_for_pass() to construct the full
    prompt for each pass, splicing in the current ledger state.
    """

    stable_prefix: StablePrefix
    rule_slice: ActiveRuleSlice | None = None
    volatile_suffix: VolatileSuffix
    pass_forward_ledger: PassForwardLedger = Field(default_factory=PassForwardLedger)

    def render_for_pass(self) -> str:
        """Render the full prompt for one pipeline pass.

        Canonical order:
          1. stable prefix (system + Story Bible + rolling summary)
          2. rule slice (RPG mode only)
          3. pass-forward ledger entries from prior passes (may be empty)
          4. volatile suffix (recent turns + current input + intent)
        """
        parts: list[str] = [self.stable_prefix.render()]
        if self.rule_slice is not None:
            parts.append(_render_rule_slice(self.rule_slice))
        ledger_text = self.pass_forward_ledger.render()
        if ledger_text:
            parts.append(ledger_text)
        parts.append(self.volatile_suffix.render())
        return "\n\n".join(parts)
