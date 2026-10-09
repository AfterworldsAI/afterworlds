# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the **spellcasting** proposal: the general spellcasting rules of the
*Spells* part, and the Rules Glossary entries they point at, one dependency
group.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, records no reference resolution,
and imports no earlier batch's content, identity or authority: every leaf is
read afresh from the release.

Scope, 104 leaves, 19 records, one review unit each:

* the eleven ``##`` sections of *Spells* that come before *Spell
  Descriptions* (pp104-107 of the official PDF), each whole, in printed order
  -- *Gaining Spells*, *Casting Spells*, *Casting Time*, *Range*,
  *Components*, *Duration*, *Effects*, *Targets*, *Saving Throws*, *Attack
  Rolls* and *Combining Spell Effects* (78 leaves). The part title
  ``# Spells`` states no rule and belongs to no section, as ``# Equipment``
  belongs to none. *Spell Descriptions* -- every spell -- is not authored.
* the eight Rules Glossary entries these rules, or an entry authored here,
  point at and no accepted record defines (26 leaves): *Area of Effect*, its
  six shapes, and *Cover*. An entry is authored here only when the scoped
  text prints an explicit pointer to it ("defined in "Rules Glossary"", a
  shape named as an area of effect, "Total Cover", a *See also*). Terms the
  rules only use -- Bonus Action, Reaction, Proficiency Bonus, saving throw,
  target -- are defined in *Playing the Game* and are not re-authored; the
  entries that point back at these rules (Cantrip, Ritual, Spell, Spell
  Attack, Spellcasting Focus) are their consumers, not their dependencies.

Record grain: one record per section and per glossary entry, each reading its
whole unit in printed order. No record is named inside a section: no accepted
citation names a rule narrower than a section, and the one resolution draft
below names the *Attack Rolls* section.

Kinds: the sections are ``general_rule``; the glossary entries
``glossary_rule``.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the thirteen accepted batches):

* Every component is prose-bound. ``SpellDescriptorFact`` types a spell's own
  descriptor line, which these rules only explain; ``SpellSlotProgressionFact``
  is indexed by class level, and the *Classes* part is not authored;
  ``ProficiencyBonusUseFact`` is typed once, from ``play.proficiency``; slot
  recovery on a Long Rest could be a ``ResourceRecoveryFact`` but no consumer
  reads it, and no family states a derived score such as the spell save DC or
  spell attack modifier (as the character-creation batch left its own
  formulas). They are the lift path, not this batch.
* A table keeps every header and data row, in printed order, with the prose
  that introduces it. The *Area of Effect* entry's uncaptioned, headless
  table is written as the release prints it.
* Examples stay inside the clause they illustrate (as *Equipment*); a
  glossary *See also* is a supporting span of its record (as the
  core-play-dependencies batch).
* ``gamemaster_latitude`` is kept where the rule leaves the outcome to the GM
  (a monster's prepared spells; outcomes beyond a spell's stated effects);
  ``contextual_applicability`` where applying it turns on fiction the
  projection cannot enumerate (whether a spell's effect is perceptible);
  everything else is ``no_identified_structured_use``.
* References:

  - every explicit pointer: "defined in "Rules Glossary"" and each shape to
    its entry; "Total Cover" and a *See also* "Cover" to *Cover*; "Combat" in
    "Playing the Game" to ``play.combat``; "each of which is detailed below"
    to the three sections it names. A Component Pouch "(see "Equipment")" and
    a Spellcasting Focus's "see "Equipment" for descriptions" name items, and
    a named item is cited by its own record, never by the whole section that
    prices it. No accepted record is the Component Pouch, and the foci are
    three (Arcane Focus, Druidic Focus, Holy Symbol), none of them *the*
    Spellcasting Focus, so both stay unresolved under the Equipment scope.
  - each accepted Rules Glossary term a rule here depends on, by its printed
    name (``GLOSSARY_TERMS``), once per component, read from prose and never
    from a table. The *Area of Effect* entry's table is its explicit list of
    the six shapes it says are "defined elsewhere in this glossary", so each
    shape is cited from it.
  - examples (a *Spell Scroll*, *Magic Missile*, *Cure Wounds*,
    *Thunderwave*, *Bless*, "a level 3 Wizard", "two Clerics") illustrate and
    are not references; class names in the Spell Preparation by Class table
    are data. No reference names the *Classes* part.

Twenty-six accepted citations name "Spells" or a spell under scope
``srd-5.2.1/spells`` and stay unresolved. This batch makes one resolvable --
the Attack Roll Abilities table's "as explained in Spells" -- and drafts it
below for the same Owner packet. Nothing here records or applies it. The rest
stay unresolved: "Spells" for spells' damage dice points at *Spell
Descriptions*, and twenty-four name individual spells.

Run: ``python issue-5d-spellcasting-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    RecordReference,
    Target,
    build_entry_batch,
    emit,
    html_table,
    scoped,
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReleaseBinding,
)
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-spellcasting-generator.py"
PROPOSAL_FILE = "issue-5d-spellcasting-REGEN-574662e9-PROPOSAL.json"
#: The glossary entries are read under the Rules Glossary's definitions.
PARENT = ("Rules Glossary", "Rules Definitions")
#: The parts this batch's records and pointers name, formed from the release's
#: own part names under the ``<release-family>/<section-slug>`` convention.
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
PLAY = "srd-5.2.1/playing-the-game"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""

PART = "Spells"

G = RecordKind.GENERAL_RULE
GL = RecordKind.GLOSSARY_RULE

#: The *Spells* sections authored here, in printed order.
SECTIONS: tuple[tuple[str, str], ...] = (
    ("gaining_spells", "Gaining Spells"),
    ("casting_spells", "Casting Spells"),
    ("casting_time", "Casting Time"),
    ("range", "Range"),
    ("components", "Components"),
    ("duration", "Duration"),
    ("effects", "Effects"),
    ("targets", "Targets"),
    ("saving_throws", "Saving Throws"),
    ("attack_rolls", "Attack Rolls"),
    ("combining_spell_effects", "Combining Spell Effects"),
)

#: (record slug, printed label, record kind), in printed order: the *Spells*
#: sections, then the Rules Glossary entries, which the book prints later.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    *((s, label, G) for s, label in SECTIONS),
    ("area_of_effect", "Area of Effect", GL),
    ("cone", "Cone [Area of Effect]", GL),
    ("cover", "Cover", GL),
    ("cube", "Cube [Area of Effect]", GL),
    ("cylinder", "Cylinder [Area of Effect]", GL),
    ("emanation", "Emanation [Area of Effect]", GL),
    ("line", "Line [Area of Effect]", GL),
    ("sphere", "Sphere [Area of Effect]", GL),
)

#: Each section's key, container and heading; the glossary entries take the
#: default placement under ``PARENT``.
PLACEMENTS: dict[str, Placement] = {
    s: Placement(f"spells.{s}", (PART, label), f"## {label}") for s, label in SECTIONS
}

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
PROSE = None

# ---------------------------------------------------------------------------
# Table leaves, written as their rows
# ---------------------------------------------------------------------------
SPELL_PREPARATION_TABLE = html_table(
    "Spell Preparation by Class",
    ("Class", "Change When You…", "Number of Spells"),
    [
        ("Bard", "Gain a level", "One"),
        ("Cleric", "Finish a Long Rest", "Any"),
        ("Druid", "Finish a Long Rest", "Any"),
        ("Paladin", "Finish a Long Rest", "One"),
        ("Ranger", "Finish a Long Rest", "One"),
        ("Sorcerer", "Gain a level", "One"),
        ("Warlock", "Gain a level", "One"),
        ("Wizard", "Finish a Long Rest", "Any"),
    ],
)

SCHOOLS_OF_MAGIC_TABLE = html_table(
    "Schools of Magic",
    ("School", "Typical Effects"),
    [
        ("Abjuration", "Prevents or reverses harmful effects"),
        ("Conjuration", "Transports creatures or objects"),
        ("Divination", "Reveals information"),
        ("Enchantment", "Influences minds"),
        ("Evocation", "Channels energy to create effects that are often destructive"),
        ("Illusion", "Deceives the mind or senses"),
        ("Necromancy", "Manipulates life and death"),
        ("Transmutation", "Transforms creatures or objects"),
    ],
)

#: The *Area of Effect* entry's six shapes: no caption, no header row, two
#: rows of three cells, as the release prints them.
AREA_SHAPES_TABLE = (
    "<table>\n  <tbody>\n"
    "    <tr>\n      <td>Cone</td>\n      <td>Cylinder</td>\n      <td>Line</td>\n    </tr>\n"
    "    <tr>\n      <td>Cube</td>\n      <td>Emanation</td>\n      <td>Sphere</td>\n    </tr>\n"
    "  </tbody>\n</table>"
)

Clause = tuple[str, str, tuple[str | None, ...], tuple[str, ...]]


def cl(entry: str, key: str, *texts: str) -> Clause:
    """One clause row whose meaning is carried by governing prose."""
    return (entry, key, (PROSE,), texts)


#: Every covered leaf, in printed order, one row per rule.
CLAUSES: tuple[Clause, ...] = (
    # == Gaining Spells ======================================================
    cl(
        "gaining_spells",
        "gaining_spells",
        "Before you can cast a spell, you must have the spell prepared in your mind or have access to the spell from a magic item, such as a _Spell Scroll_. Your features specify which spells you have access to, if any; whether you always have certain spells prepared; and whether you can change the list of spells you have prepared.",
    ),
    cl(
        "gaining_spells",
        "preparing_spells",
        "If you have a list of level 1+ spells you prepare, your spellcasting feature specifies when you can change the list and the number of spells you can change, as summarized in the Spell Preparation by Class table.",
        SPELL_PREPARATION_TABLE,
    ),
    cl(
        "gaining_spells",
        "monster_prepared_spells",
        "Most spellcasting monsters don't change their lists of prepared spells, but the GM is free to alter them.",
    ),
    cl(
        "gaining_spells",
        "always_prepared_spells",
        "Certain features might give you a spell that you always have prepared. If you also have a list of prepared spells that you can change, a spell that you always have prepared doesn't count against the number of spells on that list.",
    ),
    # == Casting Spells ======================================================
    cl(
        "casting_spells",
        "casting_in_armor",
        "> **Casting in Armor**\n>\n> You must have training with any armor you are wearing to cast spells while wearing it. You are otherwise too hampered by the armor for spellcasting.",
    ),
    cl(
        "casting_spells",
        "spell_level",
        "Every spell has a level from 0 to 9, which is indicated in a spell's description. A spell's level is an indicator of how powerful it is. Cantrips—simple spells that can be cast almost by rote—are level 0. The rules for each spellcasting class say when its members gain access to spells of certain levels.",
    ),
    cl(
        "casting_spells",
        "spell_slots",
        "Spellcasting is taxing, so a spellcaster can cast only a limited number of level 1+ spells before resting. Spell slots are the main way a spellcaster's magical potential is represented. Each spellcasting class gives its members a limited number of spell slots of certain spell levels. For example, a level 3 Wizard has four level 1 spell slots and two level 2 slots.",
        "When you cast a spell, you expend a slot of that spell's level or higher, effectively \"filling\" a slot with the spell. Imagine a spell slot is a groove of a certain size—small for a level 1 slot and larger for a higher-level spell. A level 1 spell fits into a slot of any size, but a level 2 spell fits only into a slot that's at least level 2. So when a level 3 Wizard casts _Magic Missile_, a level 1 spell, that Wizard spends one of four level 1 slots and has three remaining.",
    ),
    cl(
        "casting_spells",
        "slot_recovery",
        "Finishing a Long Rest restores any expended spell slots.",
    ),
    # The subsection's heading is excluded; this is the rule it names, and the
    # four ways below are its instances.
    cl(
        "casting_spells",
        "casting_without_slots",
        "There are several ways to cast a spell without expending a spell slot:",
    ),
    cl(
        "casting_spells",
        "cantrips",
        "**Cantrips.** A cantrip is cast without a spell slot.",
    ),
    cl(
        "casting_spells",
        "rituals",
        "**Rituals.** Certain spells have the Ritual tag in the Casting Time entry. Such a spell can be cast following the normal rules for spellcasting, or it can be cast as a Ritual. The Ritual version of a spell takes 10 minutes longer to cast than normal, but it doesn't expend a spell slot. To cast a spell as a Ritual, a spellcaster must have it prepared.",
    ),
    cl(
        "casting_spells",
        "special_abilities",
        "**Special Abilities.** Some characters and monsters have special abilities that allow them to cast specific spells without a spell slot. This casting is usually limited in another way, such as being able to cast the spell a limited number of times per day.",
    ),
    cl(
        "casting_spells",
        "magic_items",
        "**Magic Items.** _Spell Scrolls_ and some other magic items contain spells that can be cast without a spell slot. The description of such an item specifies how many times a spell can be cast from it.",
    ),
    cl(
        "casting_spells",
        "higher_level_slot",
        "When a spellcaster casts a spell using a slot that is of a higher level than the spell, the spell takes on the higher level for that casting. For instance, if a Wizard casts _Magic Missile_ using a level 2 slot, that _Magic Missile_ is level 2. Effectively, the spell expands to fill the slot it is put into.\nSome spells, such as _Magic Missile_ and _Cure Wounds_, have more powerful effects when cast at a higher level, as detailed in a spell's description.",
    ),
    cl(
        "casting_spells",
        "school_of_magic",
        "Each spell belongs to a school of magic. The schools are listed in the Schools of Magic table. These categories help describe spells but have no rules of their own, although some other rules refer to them.",
        SCHOOLS_OF_MAGIC_TABLE,
    ),
    cl(
        "casting_spells",
        "class_spell_lists",
        "If a spell is on a class's spell list, the class's name appears in parentheses after the spell's school of magic. Some features add a spell to a character's spell list even if the character isn't a member of a class in the parentheses.",
    ),
    # == Casting Time ========================================================
    cl(
        "casting_time",
        "casting_time",
        "Most spells require the Magic action to cast, but some spells require a Bonus Action, a Reaction, or 1 minute or more. A spell's Casting Time entry specifies which of those is required.",
    ),
    cl(
        "casting_time",
        "one_slot_per_turn",
        "On a turn, you can expend only one spell slot to cast a spell. This rule means you can't, for example, cast a spell with a spell slot using the Magic action and another one using a Bonus Action on the same turn.",
    ),
    cl(
        "casting_time",
        "triggers",
        "A spell that has a casting time of a Reaction is cast in response to a trigger that is defined in the spell's Casting Time entry. Some spells that have a casting time of a Bonus Action are also cast in response to a trigger defined in the spell.",
    ),
    cl(
        "casting_time",
        "longer_casting_times",
        'Certain spells—including a spell cast as a Ritual—require more time to cast: minutes or even hours. While you cast a spell with a casting time of 1 minute or more, you must take the Magic action on each of your turns, and you must maintain Concentration (see "Rules Glossary") while you do so. If your Concentration is broken, the spell fails, but you don\'t expend a spell slot. To cast the spell again, you must start over.',
    ),
    # == Range ===============================================================
    cl(
        "range",
        "range",
        "A spell's range indicates how far from the spellcaster the spell's effect can originate, and the spell's description specifies which part of the effect is limited by the range.",
        # "usually": the forms below are not every range a spell may state.
        "A range usually takes one of the following forms:",
    ),
    cl("range", "distance", "**Distance**. The range is expressed in feet."),
    cl(
        "range",
        "touch",
        "**Touch**. The spell's effect originates on something, as defined by the spell, that the spellcaster must touch within their reach.",
    ),
    cl(
        "range",
        "self",
        "**Self**. The spell is cast on the spellcaster or emanates from them, as specified in the spell.",
    ),
    cl(
        "range",
        "movable_effects",
        "If a spell has movable effects, they aren't restricted by its range unless the spell's description says otherwise.",
    ),
    # == Components ==========================================================
    cl(
        "components",
        "components",
        "A spell's components are physical requirements the spellcaster must meet to cast the spell. Each spell's description indicates whether it requires Verbal (V), Somatic (S), or Material (M) components. If the spellcaster can't provide one or more of a spell's components, the spellcaster can't cast the spell.",
    ),
    cl(
        "components",
        "verbal",
        "A Verbal component is the chanting of esoteric words that sound like nonsense to the uninitiated. The words must be uttered in a normal speaking voice. The words themselves aren't the source of the spell's power; rather, the particular combination of sounds, with specific pitch and resonance, sets the threads of magic in motion. Thus, a creature who is gagged or in an area of magical silence can't cast a spell with a Verbal component.",
    ),
    cl(
        "components",
        "somatic",
        "A Somatic component is a forceful gesticulation or an intricate set of gestures. A spellcaster must use at least one of their hands to perform these movements.",
    ),
    cl(
        "components",
        "material",
        "A Material component is a particular material used in a spell's casting, as specified in parentheses in the Components entry. These materials aren't consumed by the spell unless the spell's description states otherwise. The spellcaster must have a hand free to access them, but it can be the same hand used to perform Somatic components, if any.",
    ),
    cl(
        "components",
        "component_pouch_and_focus",
        'If a spell doesn\'t consume its materials and doesn\'t specify a cost for them, a spellcaster can use a Component Pouch (see "Equipment") instead of providing the materials specified in the spell, or the\nspellcaster can substitute a Spellcasting Focus if the caster has a feature that allows that substitution. To use a Component Pouch, you must have a hand free to reach into it, and to use a Spellcasting Focus, you must hold it unless its description says otherwise (see "Equipment" for descriptions).',
    ),
    # == Duration ============================================================
    cl(
        "duration",
        "duration",
        "A spell's duration is the length of time the spell persists after it is cast. A duration typically takes one of the following forms:",
    ),
    cl(
        "duration",
        "concentration",
        '**Concentration.** A duration that requires Concentration follows the Concentration rules (see "Rules Glossary").',
    ),
    cl(
        "duration",
        "instantaneous",
        "**Instantaneous.** An instantaneous duration means the spell's magic appears only for a moment and then disappears.",
    ),
    cl(
        "duration",
        "time_span",
        '**Time Span.** A duration that provides a time span specifies how long the spell lasts in rounds, minutes, hours, or the like. For example, a Duration entry might say "1 minute," meaning the spell ends after 1 minute has passed. While a time-span spell that you cast is ongoing, you can dismiss it (no action required) if you don\'t have the Incapacitated condition.',
    ),
    # == Effects =============================================================
    cl(
        "effects",
        "effects",
        "The effects of a spell are detailed after its duration entry. Those details present exactly what the spell does, which ignores mundane physical laws; any outcomes beyond those effects are under the GM's purview. Whatever the effects, they typically deal with targets, saving throws, attack rolls, or all three, each of which is detailed below.",
    ),
    # == Targets =============================================================
    cl(
        "targets",
        "targets",
        "A typical spell requires the caster to pick one or more targets to be affected by the spell's magic. A spell's description says whether the spell targets creatures, objects, or something else.",
    ),
    cl(
        "targets",
        "clear_path",
        "_A Clear Path to the Target._ To target something with a spell, a caster must have a clear path to it, so it can't be behind Total Cover.",
    ),
    cl(
        "targets",
        "targeting_yourself",
        "_Targeting Yourself._ If a spell targets a creature of your choice, you can choose yourself unless the creature must be Hostile or specifically a creature other than you.",
    ),
    cl(
        "targets",
        "areas_of_effect",
        '_Areas of Effect._ Some spells, such as _Thunderwave_, cover an area called an area of effect, which is defined in "Rules Glossary." The area determines what the spell targets. The description of a spell specifies whether it has an area of effect, which is typically one of these shapes: Cone, Cube, Cylinder, Emanation, Line, or Sphere.',
    ),
    cl(
        "targets",
        "awareness_of_being_targeted",
        "_Awareness of Being Targeted._ Unless a spell has a perceptible effect, a creature doesn't know it was targeted by the spell. An effect like lightning is obvious, but a more subtle effect, such as an attempt to read thoughts, goes unnoticed unless a spell's description says otherwise.",
    ),
    cl(
        "targets",
        "invalid_targets",
        "_Invalid Targets._ If you cast a spell on someone or something that can't be affected by it, nothing happens to that target, but if you used a spell slot to cast the spell, the slot is still expended.",
        "If the spell normally has no effect on a target that succeeds on a saving throw, the invalid target appears to have succeeded on its saving throw, even though it didn't attempt one (giving no hint that the creature is an invalid target). Otherwise, you perceive that the spell did nothing to the target.",
    ),
    # == Saving Throws =======================================================
    cl(
        "saving_throws",
        "spell_save_dc",
        "Many spells specify that a target makes a saving throw to avoid some or all of a spell's effects. The spell specifies the ability that the target uses for the save and what happens on a success or failure. Here's how to calculate the DC for your spells:",
        "**Spell save DC** = 8 + your spellcasting ability modifier + your Proficiency Bonus",
    ),
    # == Attack Rolls ========================================================
    cl(
        "attack_rolls",
        "spell_attack_modifier",
        "Some spells require the caster to make an attack roll to determine whether the spell hits a target. Here's how to calculate the attack modifier for your spells:",
        "**Spell attack modifier** = your spellcasting ability modifier + your Proficiency Bonus",
    ),
    # == Combining Spell Effects =============================================
    cl(
        "combining_spell_effects",
        "combining_spell_effects",
        "The effects of different spells add together while their durations overlap. In contrast, the effects of the same spell cast multiple times don't combine. Instead, the most potent effect—such as the highest bonus—from those castings applies while their durations overlap. The most recent effect applies if the castings are equally potent and their durations overlap. For example, if two Clerics cast _Bless_ on the same target, that target gains the spell's benefit only once; the target doesn't receive two bonus dice. But if the durations of the spells overlap, the effect continues until the duration of the second _Bless_ ends.",
    ),
    cl(
        "combining_spell_effects",
        "identifying_an_ongoing_spell",
        "> **IDENTIFYING AN ONGOING SPELL**\n>\n> You can try to identify a non-instantaneous spell by its observable effects if its duration is ongoing. To identify it, you must take the Study action and succeed on a DC 15 Intelligence (Arcana) check.",
    ),
    # == Area of Effect (glossary) ===========================================
    cl(
        "area_of_effect",
        "area_of_effect",
        "The descriptions of many spells and other features specify that they have an area of effect, which typically has one of six shapes. These shapes are defined elsewhere in this glossary:",
        AREA_SHAPES_TABLE,
    ),
    cl(
        "area_of_effect",
        "point_of_origin",
        "An area of effect has a point of origin, a location from which the effect's energy erupts. The rules for each shape specify how to position its point of origin. If all straight lines extending from the point of origin to a location in the area of effect are blocked, that location isn't included in the area of effect. To block a line, an obstruction must provide Total Cover.",
    ),
    cl(
        "area_of_effect",
        "unseen_point",
        "If the creator of an area of effect places it at an unseen point and an obstruction—such as a wall—is between the creator and that point, the point of origin comes into being on the near side of the obstruction.",
    ),
    # == Cone [Area of Effect] ===============================================
    cl(
        "cone",
        "cone",
        "A Cone is an area of effect that extends in straight lines from a point of origin in a direction its creator chooses. A Cone's width at any point along its length is equal to that point's distance from the point of origin. For example, a Cone is 15 feet wide at a point along its length that is 15 feet from the point of origin. The effect that creates a Cone specifies its maximum length.",
        "A Cone's point of origin isn't included in the area of effect unless its creator decides otherwise.",
    ),
    # == Cover ===============================================================
    cl(
        "cover",
        "cover",
        "Cover provides a degree of protection to a target behind it. There are three degrees of cover, each of which provides a different benefit to a target: Half Cover (+2 bonus to AC and Dexterity saving throws), Three-Quarters Cover (+5 bonus to AC and Dexterity saving throws), and Total Cover (can't be targeted directly). If behind more than one degree of cover, a target benefits only from the most protective degree.",
    ),
    # == Cube [Area of Effect] ===============================================
    cl(
        "cube",
        "cube",
        "A Cube is an area of effect that extends in straight lines from a point of origin located anywhere on a face of the Cube. The effect that creates a Cube specifies its size, which is the length of each side.",
        "A Cube's point of origin isn't included in the area of effect unless its creator decides otherwise.",
    ),
    # == Cylinder [Area of Effect] ===========================================
    cl(
        "cylinder",
        "cylinder",
        "A Cylinder is an area of effect that extends in straight lines from a point of origin located at the center of the circular top or bottom of the Cylinder. The effect that creates a Cylinder specifies the radius of the Cylinder's base and the Cylinder's height.",
        "A Cylinder's point of origin is included in the area of effect.",
    ),
    # == Emanation [Area of Effect] ==========================================
    cl(
        "emanation",
        "emanation",
        "An Emanation is an area of effect that extends in straight lines from a creature or an object in all directions. The effect that creates an Emanation specifies the distance it extends.",
        "An Emanation moves with the creature or object that is its origin unless it is an instantaneous or a stationary effect.",
        "An Emanation's origin (creature or object) isn't included in the area of effect unless its creator decides otherwise.",
    ),
    # == Line [Area of Effect] ===============================================
    cl(
        "line",
        "line",
        "A Line is an area of effect that extends from a point of origin in a straight path along its length and covers an area defined by its width. The effect that creates a Line specifies its length and width.",
        "A Line's point of origin isn't included in the area of effect unless its creator decides otherwise.",
    ),
    # == Sphere [Area of Effect] =============================================
    cl(
        "sphere",
        "sphere",
        "A Sphere is an area of effect that extends in straight lines from a point of origin outward in all directions. The effect that creates a Sphere specifies the distance it extends as the radius of the Sphere.",
        "A Sphere's point of origin is included in the Sphere's area of effect.",
    ),
)


#: (entry, leaf prefix): whole leaves that introduce the rules after them and
#: state none of their own. An introduction that qualifies what follows ("a
#: range *usually* takes…", "ways to cast… *without expending a spell slot*")
#: is a rule and is read, not framed.
FRAMING: tuple[tuple[str, str], ...] = (
    ("casting_spells", "Each spell description has a series of entries"),
)

SUBSECTION_HEADING = "subsection heading: names a subsection and states no rule"

#: (entry, exact leaf contents, reason): whole leaves that only name a
#: subsection.
EXCLUDED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "gaining_spells",
        ("### Preparing Spells", "### Always-Prepared Spells"),
        SUBSECTION_HEADING,
    ),
    (
        "casting_spells",
        (
            "### Spell Level",
            "#### Spell Slots",
            "#### Casting without Slots",
            "#### Using a Higher-Level Spell Slot",
            "### School of Magic",
            "### Class Spell Lists",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "casting_time",
        (
            "### One Spell with a Spell Slot per Turn",
            "### Reaction and Bonus Action Triggers",
            "### Longer Casting Times",
        ),
        SUBSECTION_HEADING,
    ),
    (
        "components",
        ("### Verbal (V)", "### Somatic (S)", "### Material (M)"),
        SUBSECTION_HEADING,
    ),
)

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent


def sp(slug: str) -> Target:
    """A section record of this batch."""
    return (SPELLS, PLACEMENTS[slug].record_key)


#: A named Equipment item no accepted record is: cited, and left unresolved.
EQUIPMENT_ITEM: Target = (EQUIPMENT, UNRESOLVED_TARGET)
PLAY_COMBAT: Target = (PLAY, "play.combat")

#: Accepted Rules Glossary entries a rule here depends on, by printed name. A
#: component references each entry once, at its first printed name, and only
#: from prose: a table's cells are data, not dependencies. "reach" is also a
#: verb ("reach into it") and is cited explicitly where it means Reach.
GLOSSARY_TERMS: tuple[tuple[str, str], ...] = (
    ("Magic action", "magic"),
    ("Study action", "study"),
    ("Long Rest", "long_rest"),
    ("Concentration", "concentration"),
    ("Hostile", "hostile"),
    ("Incapacitated", "incapacitated"),
    ("attack rolls?", "attack_roll"),
)


def glossary_refs(texts: tuple[str, ...]) -> tuple[tuple[str, Target], ...]:
    """Each accepted glossary entry *texts*' prose prints, once, at its first name."""
    found: list[tuple[int, int, str, str]] = []
    for n, text in enumerate(texts):
        if "<t" in text or "</t" in text:
            continue
        for pattern, slug in GLOSSARY_TERMS:
            for m in re.finditer(rf"\b{pattern}\b", text):
                found.append((n, m.start(), m.group(), slug))
    refs: dict[str, str] = {}
    for _, _, printed, slug in sorted(found):
        refs.setdefault(slug, printed)
    return tuple((printed, slug) for slug, printed in refs.items())


#: The six shapes, as the rules print them, and their entries.
SHAPES: tuple[tuple[str, str], ...] = (
    ("Cone", "cone"),
    ("Cube", "cube"),
    ("Cylinder", "cylinder"),
    ("Emanation", "emanation"),
    ("Line", "line"),
    ("Sphere", "sphere"),
)
#: A shape's entry names the entry it is a shape of by the words it defines.
OF_AREA: tuple[tuple[str, Target], ...] = (("area of effect", "area_of_effect"),)

#: Explicit pointers, by component; accepted glossary terms are added from
#: each component's prose by :func:`glossary_refs`, unless the component
#: already cites the same printed words as a pointer of its own.
EXPLICIT_REFS: dict[tuple[str, str], tuple[tuple[str, Target], ...]] = {
    ("range", "touch"): (("reach", "reach"),),
    ("components", "component_pouch_and_focus"): (
        ("Component Pouch", EQUIPMENT_ITEM),
        ("Equipment", EQUIPMENT_ITEM),
    ),
    # "each of which is detailed below": the three sections that follow.
    ("effects", "effects"): (
        ("targets", sp("targets")),
        ("saving throws", sp("saving_throws")),
        ("attack rolls", sp("attack_rolls")),
    ),
    ("targets", "clear_path"): (("Total Cover", "cover"),),
    ("targets", "areas_of_effect"): (("area of effect", "area_of_effect"), *SHAPES),
    # The table is the entry's list of the shapes "defined elsewhere".
    ("area_of_effect", "area_of_effect"): SHAPES,
    ("area_of_effect", "point_of_origin"): (("Total Cover", "cover"),),
    **{(s, s): OF_AREA for _, s in SHAPES},
}

#: Components whose outcome the rule leaves to the GM.
GM_LATITUDE: frozenset[tuple[str, str]] = frozenset(
    {
        ("gaining_spells", "monster_prepared_spells"),
        ("effects", "effects"),
    }
)
#: Rules whose applicability turns on fiction the projection cannot enumerate.
CONTEXTUAL: frozenset[tuple[str, str]] = frozenset(
    {("targets", "awareness_of_being_targeted")}
)


def _components() -> tuple[EntryComponent, ...]:
    out = []
    for entry, key, _, texts in CLAUSES:
        explicit = EXPLICIT_REFS.get((entry, key), ())
        printed = {text for text, _ in explicit}
        refs = explicit + tuple(
            (text, slug)
            for text, slug in glossary_refs(texts)
            if text not in printed
            and scoped(slug) not in {scoped(t) for _, t in explicit}
        )
        reason = (
            GM
            if (entry, key) in GM_LATITUDE
            else CTX if (entry, key) in CONTEXTUAL else NO_USE
        )
        out.append(C(entry, key, P, reason, refs=refs))
    return tuple(out)


COMPONENTS: tuple[EntryComponent, ...] = _components()

AREA_SEE_ALSO = '_See also_ "Cover."'
COVER_SEE_ALSO = '_See also_ "Playing the Game" ("Combat").'

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). *See also* pointers identify.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("area_of_effect", AREA_SEE_ALSO, None),
    ("cover", COVER_SEE_ALSO, None),
)
#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("area_of_effect", "Cover", "cover", (AREA_SEE_ALSO,)),
    ("cover", "Combat", PLAY_COMBAT, (COVER_SEE_ALSO,)),
)

#: Targets outside this batch that no accepted record defines: none.
NEW_TARGETS: tuple[Target, ...] = ()
#: The accepted records outside the Rules Glossary this batch cites.
ACCEPTED_OUTSIDE: tuple[Target, ...] = (PLAY_COMBAT,)
IN_BATCH: frozenset[str] = frozenset(s for s, _, _ in ENTRIES)


def accepted_context_targets() -> tuple[Target, ...]:
    """The accepted records this batch's references cite."""
    glossary = sorted(
        {
            t
            for c in COMPONENTS
            for _, t in c.refs
            if isinstance(t, str) and t not in IN_BATCH and t not in NEW_TARGETS
        }
    )
    return (*glossary, *ACCEPTED_OUTSIDE)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=f"{ORIGIN} (CRD Issue 5d spellcasting batch; unaccepted)",
        unit_prefix="spellcasting",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=104,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
        placements=PLACEMENTS,
        excluded=EXCLUDED,
    )


def build(session: Session) -> Built:
    """Derive the spellcasting proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def unresolved() -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text)."""
    return sorted(
        (scope, text)
        for c in COMPONENTS
        for text, t in c.refs
        for scope, key in (scoped(t),)
        if key == UNRESOLVED_TARGET
    )


def expected_representation_findings() -> list[str]:
    """Every out-of-batch target: the accepted ones stay unknown to the batch alone."""
    return sorted(
        [
            *unknown_target_findings(
                RECORD_REFERENCES,
                COMPONENTS,
                (*NEW_TARGETS, *accepted_context_targets()),
            ),
            *(f"reference {s}:{t!r}: unresolved reference" for s, t in unresolved()),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
#: Twenty-six accepted citations print "Spells", or a spell, under scope
#: ``srd-5.2.1/spells`` and stay unresolved. One is resolvable: the Attack
#: Roll Abilities table's spell attack row ("the ability used is determined by
#: the spellcaster's spellcasting feature, as explained in Spells") names the
#: *Attack Rolls* section, which states the spell attack modifier from "your
#: spellcasting ability modifier". The draft cites the accepted citation's own
#: provenance span, becomes applicable only once its target is accepted, and
#: then only by its own authorized ``resolve_references`` action.
#:
#: (from record, component, printed text, target record, provenance spans).
DRAFTS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "play.d20_tests",
        "attack_ability_modifier",
        "Spells",
        PLACEMENTS["attack_rolls"].record_key,
        ("0d31cd96-42b9-59de-93ea-2dbecf273a13",),
    ),
)

#: The accepted citation of "Spells" that stays unresolved: spells' damage
#: dice are printed in *Spell Descriptions*, which this batch does not author.
#: The twenty-four citations naming a spell stay unresolved with it.
UNRESOLVED_CITATIONS: tuple[tuple[str, str, str], ...] = (
    ("play.damage_and_healing", "", "Spells"),
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_resolutions(binding: ReleaseBinding) -> tuple[ReferenceResolution, ...]:
    """The one pending resolution, drafted for review against *binding*."""
    return tuple(
        ReferenceResolution(
            resolution_id=(
                f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-spellcasting-1"
            ),
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=SPELLS,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in DRAFTS
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
