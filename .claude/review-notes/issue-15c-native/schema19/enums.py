# ---------------------------------------------------------------------------
# Schema 19 vocabularies -- CRD Issue 15c bounded d20 source contract
# ---------------------------------------------------------------------------
#
# Every member below is a value the independently reviewed raw candidate C5
# states (``.claude/review-notes/issue-15c-implementation/candidate-c5``). Where
# C5 printed a phrase rather than a token, the member is the phrase's closed
# reading and the correspondence is disclosed in the native preview's
# ``correspondence.md``; no member is a reading C5 does not state.


class TurnWhich(StrEnum):
    """Which turn a turn boundary names: *"its next turn"*, *"this turn"*."""

    NEXT = "next"
    THIS = "this"


class TurnOwner(StrEnum):
    """Whose turn a boundary or trigger belongs to, relative to the entry.

    ``source`` is the creature or effect the entry belongs to, ``target`` the
    creature it affects, ``subject`` the creature a rule is about, and
    ``caster`` the creature that cast the spell a stat block belongs to.
    """

    SOURCE = "source"
    TARGET = "target"
    SUBJECT = "subject"
    CASTER = "caster"


class EntrySection(StrEnum):
    """The stat-block section an entry is printed under."""

    TRAIT = "trait"
    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    LEGENDARY_ACTION = "legendary_action"


class EntrySubject(StrEnum):
    """Whom a standing trait applies to, relative to the creature printing it."""

    SELF = "self"
    OTHERS = "others"
    SELF_AND_ALLIES = "self_and_allies"
    RIDER = "rider"
    AMULET_WEARER = "amulet_wearer"
    CASTER = "caster"


class CreatureAttackRange(StrEnum):
    """A creature attack's printed kind: *"Melee Attack Roll"*, *"Ranged
    Attack Roll"*, *"Melee or Ranged Attack Roll"*."""

    MELEE = "melee"
    RANGED = "ranged"
    MELEE_OR_RANGED = "melee_or_ranged"


class AttackAdvantageWhen(StrEnum):
    """The printed parenthetical on an attack bonus, *"(with Advantage if
    ...)"*. "Grappled by the <creature>" always names the attacking creature
    itself, so it is one member."""

    TARGET_MISSING_HIT_POINTS = "target_missing_hit_points"
    TARGET_GRAPPLED_BY_SOURCE = "target_grappled_by_source"
    FIRST_ROUND_OF_EACH_COMBAT = "first_round_of_each_combat"


class SizeInput(StrEnum):
    """Which input chooses a size-keyed damage row."""

    RECORDED_SIZE = "recorded_size"


class FormulaInput(StrEnum):
    """A runtime value a parameterized damage term adds."""

    SPELL_LEVEL = "spell_level"
    CASTER_SPELLCASTING_ABILITY_MODIFIER = "caster_spellcasting_ability_modifier"


class FormulaSubject(StrEnum):
    """Whose values a referenced formula is computed for."""

    CASTER = "caster"


class FormulaTerm(StrEnum):
    """A named term a printed formula sums."""

    SPELLCASTING_ABILITY_MODIFIER = "spellcasting_ability_modifier"
    PROFICIENCY_BONUS = "proficiency_bonus"
    ATTACK_ABILITY_MODIFIER = "attack_ability_modifier"


class RiderSubject(StrEnum):
    """Whom a hit or failure rider affects."""

    TARGET = "target"


class DamageMode(StrEnum):
    """Whether a conditional damage term is added to, or replaces, the hit's."""

    ADDITIONAL = "additional"
    INSTEAD = "instead"


class ForcedDirection(StrEnum):
    """The printed direction of a push or pull."""

    STRAIGHT_AWAY = "straight_away"
    STRAIGHT_TOWARD_SOURCE = "straight_toward_source"


class LinkEnd(StrEnum):
    """What ends a condition linked to another effect: *"until the grapple
    ends"*."""

    GRAPPLE_ENDS = "grapple_ends"


class TargetTag(StrEnum):
    """A creature tag a save's target clause or exclusion names: a creature
    type, a species, a tag (Demon) or *"enemy"*."""

    BEAST = "beast"
    CELESTIAL = "celestial"
    DEMON = "demon"
    ELF = "elf"
    ENEMY = "enemy"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    UNDEAD = "undead"


class SaveSuccess(StrEnum):
    """A printed success line: *"Half damage."* or *"Half damage only."*"""

    HALF_DAMAGE = "half_damage"
    HALF_DAMAGE_ONLY = "half_damage_only"


class ReuseLimitKind(StrEnum):
    """*"The <creature> can't take this action again until the start of its
    next turn."*"""

    ONCE_UNTIL_START_OF_OWN_TURN = "once_until_start_of_own_turn"


class AreaShape(StrEnum):
    """The area shapes C5's save targets print."""

    CONE = "cone"
    CYLINDER = "cylinder"
    EMANATION = "emanation"
    LINE = "line"
    SPHERE = "sphere"


class TargetExclusion(StrEnum):
    """*"that isn't currently affected by this <effect>"*."""

    CURRENTLY_AFFECTED_BY_THIS_EFFECT = "currently_affected_by_this_effect"


class AreaOriginAnchor(StrEnum):
    """*"originating from the <creature>"*."""

    SOURCE = "source"


class SourceEnvironment(StrEnum):
    """The source's environment a target clause requires."""

    UNDERWATER = "underwater"


class TargetsStatedBy(StrEnum):
    """A save whose participants are stated by its framing sentence."""

    FRAME = "frame"


class MultiattackCondition(StrEnum):
    """A printed condition on one Multiattack alternative."""

    USED_HASTEN_THIS_TURN = "used_hasten_this_turn"


class CountFormula(StrEnum):
    """A Multiattack count stated by a formula, not a number."""

    HALF_SPELL_LEVEL_ROUNDED_DOWN = "half_spell_level_rounded_down"
    HALF_SUMMONER_PROFICIENCY_BONUS_ROUNDED_UP = (
        "half_summoner_proficiency_bonus_rounded_up"
    )
    PER_HEAD = "per_head"


class UsageKind(StrEnum):
    """A stat-block entry's printed usage parenthetical."""

    RECHARGE = "recharge"
    PER_DAY = "per_day"
    LEGENDARY_ACTION_USES = "legendary_action_uses"
    FORM_ONLY = "form_only"
    REQUIRES_ENTRY = "requires_entry"


class CreatureForm(StrEnum):
    """A form a *"(<Form> Form Only)"* parenthetical names."""

    BAT = "bat"
    BEAR = "bear"
    BOAR = "boar"
    CELESTIAL = "celestial"
    CENTIPEDE = "centipede"
    FEY = "fey"
    FIEND = "fiend"
    HUMANOID = "humanoid"
    HYBRID = "hybrid"
    OBJECT = "object"
    RAT = "rat"
    SPIDER = "spider"
    TIGER = "tiger"
    VAMPIRE = "vampire"
    WOLF = "wolf"


class ObserverKind(StrEnum):
    """Who makes a check another creature's entry sets, as printed."""

    ANOTHER_CREATURE = "another_creature"
    A_CREATURE_THAT_HEARS_THE_SOUNDS = "a_creature_that_hears_the_sounds"
    A_HEARER = "a_hearer"


class ObserverPurpose(StrEnum):
    """What an observer check is made for, as printed."""

    TO_DISCERN_THE_SOUNDS_ARE_IMITATIONS = "to_discern_the_sounds_are_imitations"
    TO_NOTICE_THE_SUBJECT = "to_notice_the_subject"


class ContributorStated(StrEnum):
    """A trait's applicability stated as a sentence rather than a state."""

    FORCING_EFFECT_IS_A_SPELL_OR_MAGICAL = "forcing_effect_is_a_spell_or_magical"
    SUBJECT_IN_SUNLIGHT = "subject_in_sunlight"


class ContributorPurpose(StrEnum):
    """The purpose a check about the subject must have (Inscrutable)."""

    TO_ASCERTAIN_INTENTIONS_OR_SINCERITY = "to_ascertain_intentions_or_sincerity"


class SaveOverrideChooser(StrEnum):
    """Who chooses to apply a printed save override."""

    GAMEMASTER = "gamemaster"


class SaveOverrideOutcome(StrEnum):
    """The outcome a save override may substitute."""

    SUCCESS = "success"


class SaveOverrideTrigger(StrEnum):
    """When a save override may be used."""

    FAILED_SAVING_THROW = "failed_saving_throw"


class SaveOverrideUsage(StrEnum):
    """Which usage limit governs a save override."""

    PER_ENTRY_LIMIT = "per_entry_limit"


class SaveDamageScope(StrEnum):
    """The effects a save-damage override applies to (Evasion)."""

    HALF_DAMAGE_EFFECTS = "half_damage_effects"


class SaveDamageResult(StrEnum):
    """The damage a save-damage override substitutes."""

    NO_DAMAGE = "no_damage"
    HALF_DAMAGE = "half_damage"


class SurfaceKind(StrEnum):
    """The surfaces a climb-check removal covers."""

    DIFFICULT_SURFACES_INCLUDING_CEILINGS = "difficult_surfaces_including_ceilings"
    ICY_SURFACES = "icy_surfaces"


class TerrainKind(StrEnum):
    """Terrain a trait says is not Difficult Terrain for its subject."""

    ICE = "ice"
    SNOW = "snow"


class ZeroHitPointTrigger(StrEnum):
    """*"If damage reduces the <creature> to 0 Hit Points"*."""

    DAMAGE_REDUCES_SUBJECT_TO_ZERO_HIT_POINTS = "damage_reduces_subject_to_zero_hit_points"


class DcAddend(StrEnum):
    """A runtime amount a printed DC adds: *"DC 5 plus the damage taken"*."""

    DAMAGE_TAKEN = "damage_taken"


class ClausePart(StrEnum):
    """Which part of an entry a clause was printed in."""

    HIT = "hit"
    FAILURE = "failure"
    SUCCESS = "success"
    FAILURE_OR_SUCCESS = "failure_or_success"
    TARGETS = "targets"
    FRAME = "frame"
    OUTCOMES = "outcomes"


class ClauseBranch(StrEnum):
    """The printed branch a clause piece belongs to: its part, or the
    branch label (*"_Second Failure:_"*) it follows."""

    HIT = "hit"
    FAILURE = "failure"
    SUCCESS = "success"
    FAILURE_OR_SUCCESS = "failure_or_success"
    TARGETS = "targets"
    FRAME = "frame"
    OUTCOMES = "outcomes"
    FIRST_FAILURE = "first_failure"
    SECOND_FAILURE = "second_failure"
    SUBSEQUENT_FAILURES = "subsequent_failures"
    FAILURE_BY_5_OR_MORE = "failure_by_5_or_more"
    HIT_OR_MISS = "hit_or_miss"


class EndingEventKind(StrEnum):
    """An event a clause says ends an effect early."""

    TARGET_TAKES_DAMAGE = "target_takes_damage"
    ENDS_TURN_OUT_OF_LINE_OF_SIGHT = "ends_turn_out_of_line_of_sight"
    WOKEN_BY_AN_ACTION = "woken_by_an_action"


class PredicateWhile(StrEnum):
    """A named effect a *"While <X>"* / *"Until the <X> ends"* predicate
    depends on, other than a condition."""

    CURSE = "curse"
    GRAPPLE = "grapple"
    INFERNAL_WOUND = "infernal_wound"
    SONG = "song"


class PredicateRefersTo(StrEnum):
    """*"Until **this** poison ends"*: the effect this entry inflicted."""

    THIS_POISON = "this_poison"


class RepeatSaveAt(StrEnum):
    """When a repeated save is made."""

    END_OF_EACH_OF_ITS_TURNS = "end_of_each_of_its_turns"
    END_OF_ITS_NEXT_TURN = "end_of_its_next_turn"


class SaveEndsOn(StrEnum):
    """The repeated save's result that ends the effect."""

    SUCCESS = "success"


class ImmunityScope(StrEnum):
    """*"immune to **this** <creature>'s <entry>"*."""

    THIS_SOURCE_ENTRY = "this_source_entry"


class NamedEffect(StrEnum):
    """An effect a clause names without a condition: *"is cursed"*."""

    CURSED = "cursed"


class SpanEnd(StrEnum):
    """An alternative end of an elapsed duration."""

    SOURCE_DIES = "source_dies"


class TimedSpeedChange(StrEnum):
    """A timed Speed change: decreases by N, is halved, is set to N."""

    DECREASE = "decrease"
    HALVE = "halve"
    SET_TO = "set_to"


class NextRollActor(StrEnum):
    """Whose next attack roll a next-roll modifier names."""

    TARGET = "target"
    SOURCE = "source"
    ANY = "any"


class PenaltyTarget(StrEnum):
    """What a penalty die is subtracted from."""

    D20_TEST = "d20_test"


class ReturningWeaponKind(StrEnum):
    """The weapon a *"magically returns"* clause names."""

    SPEAR = "spear"
    SWORD = "sword"


class RescueCost(StrEnum):
    """What a rescuer spends: *"As an action"*."""

    ACTION = "action"


class RescueEnds(StrEnum):
    """What a successful rescue ends."""

    GRAPPLE = "grapple"


class SourceMovementLimit(StrEnum):
    """*"then moves up to its Speed"*."""

    SPEED = "speed"


class TriggerOn(StrEnum):
    """The event a framing sentence triggers on."""

    SOURCE_DIES = "source_dies"


class ClauseZeroHitPointResult(StrEnum):
    """What a clause says a creature at 0 Hit Points becomes."""

    DEAD = "dead"
    STABLE = "stable"


class ClauseZeroHitPointCause(StrEnum):
    """*"if reduced to 0 Hit Points by this attack"*."""

    REDUCED_TO_ZERO_BY_THIS_ATTACK = "reduced_to_0_by_this_attack"


class AreaCenter(StrEnum):
    """*"centered on that point"*: the point the framing sentence chose."""

    THE_FRAME_POINT = "the_frame_point"


class AuraTargets(StrEnum):
    """*"in the aura"*."""

    THE_AURA = "the_aura"


class TargetingExclusion(StrEnum):
    """*"can't be targeted by the <creature>'s Tail"*: whom it excludes."""

    THE_CREATURE_GRAPPLED_BY_THIS_ATTACK = "the_creature_grappled_by_this_attack"


class EffectLastsScope(StrEnum):
    """*"This effect lasts ..."*: the effects stated before it."""

    SENTENCE_EFFECTS_ABOVE = "sentence_effects_above"


class EscapePurpose(StrEnum):
    """*"Ability checks made to escape this grapple"*."""

    ESCAPE_THIS_GRAPPLE = "escape_this_grapple"


class AppendageUse(StrEnum):
    """How many of a creature's appendages a grapple occupies."""

    ONE = "one"
    BOTH = "both"
    ALL = "all"


class Appendage(StrEnum):
    """The appendage a grapple is made with, as printed."""

    CLAWS = "claws"
    CHAINS = "chains"
    FRONT_CLAWS = "front_claws"
    HANDS = "hands"
    PINCERS = "pincers"
    TALONS = "talons"
    TENTACLES = "tentacles"


class RelationKind(StrEnum):
    """A printed relation to the subject: *"its <qualification> master"*."""

    MASTER_OF_THE_SUBJECT = "master_of_the_subject"


class RelationQualifier(StrEnum):
    """The qualification a related creature must have: *"vampire"*."""

    VAMPIRE = "vampire"


class ChoiceAnchor(StrEnum):
    """The printed choice a damage type is read from."""

    DRACONIC_ORIGIN = "draconic_origin"


class Chooser(StrEnum):
    """Who makes a printed choice."""

    GAMEMASTER = "gamemaster"
    CASTER = "caster"


class ChoiceSource(StrEnum):
    """The set a printed damage-type choice is made from."""

    THIS_CREATURES_RESISTANCES = "this_creatures_resistances"


class ChoiceTime(StrEnum):
    """When a printed choice is made."""

    CASTING = "casting"


class ConditionalDefenseKind(StrEnum):
    """Which defensive list a qualified entry was printed in."""

    CONDITION_IMMUNITY = "condition_immunity"
    RESISTANCE = "resistance"
    VULNERABILITY = "vulnerability"


class DefenseAttack(StrEnum):
    """*"from a weapon"*."""

    WEAPON = "weapon"


class ParameterizedHitPointsBasis(StrEnum):
    """*"Half the HP maximum of its summoner"*."""

    SUMMONER_HIT_POINT_MAXIMUM = "summoner_hit_point_maximum"


# Rules, grants and equipment (C5-A, C5-C) ----------------------------------


class GrantContext(StrEnum):
    """*"As a Level 1 Character: Gain all the traits in the Core <Class>
    Traits table."*"""

    LEVEL_1_CHARACTER = "level_1_character"


class ArmorCategory(StrEnum):
    """The printed armor categories."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class ToolCategory(StrEnum):
    """The Tools section's two groups."""

    ARTISANS_TOOLS = "artisans_tools"
    OTHER_TOOLS = "other_tools"


class ToolVariant(StrEnum):
    """A kind of Gaming Set or Musical Instrument, each its own proficiency."""

    DICE = "dice"
    DRAGONCHESS = "dragonchess"
    PLAYING_CARDS = "playing_cards"
    THREE_DRAGON_ANTE = "three_dragon_ante"
    BAGPIPES = "bagpipes"
    DRUM = "drum"
    DULCIMER = "dulcimer"
    FLUTE = "flute"
    HORN = "horn"
    LUTE = "lute"
    LYRE = "lyre"
    PAN_FLUTE = "pan_flute"
    SHAWM = "shawm"
    VIOL = "viol"

class ToolActivity(StrEnum):
    """A tool's printed activity: the reviewed C5 activity option keys, each
    the selectable identity of one *"Utilize"* activity. An identity only; its
    text stays governed prose."""

    ADD_A_DESIGN_TO_A_LEATHER_ITEM = "add_a_design_to_a_leather_item"
    APPLY_MAKEUP = "apply_makeup"
    ASSEMBLE_A_TINY_ITEM_COMPOSED_OF_SCRAP_WHICH_FALLS_APART_IN_1_MINUTE = "assemble_a_tiny_item_composed_of_scrap_which_falls_apart_in_1_minute"
    CARVE_A_PATTERN_IN_WOOD = "carve_a_pattern_in_wood"
    CHISEL_A_SYMBOL_OR_HOLE_IN_STONE = "chisel_a_symbol_or_hole_in_stone"
    DETECT_A_POISONED_OBJECT = "detect_a_poisoned_object"
    DETECT_POISONED_DRINK = "detect_poisoned_drink"
    DETECT_SPOILED_OR_POISONED_FOOD = "detect_spoiled_or_poisoned_food"
    DETERMINE_POSITION_BY_STARGAZING = "determine_position_by_stargazing"
    DISARM_A_TRAP = "disarm_a_trap"
    DISCERN_A_GEMS_VALUE = "discern_a_gems_value"
    DISCERN_WHAT_A_CERAMIC_OBJECT_HELD_IN_THE_PAST_24_HOURS = "discern_what_a_ceramic_object_held_in_the_past_24_hours"
    DISCERN_WHAT_A_GLASS_OBJECT_HELD_IN_THE_PAST_24_HOURS = "discern_what_a_glass_object_held_in_the_past_24_hours"
    DISCERN_WHETHER_SOMEONE_IS_CHEATING = "discern_whether_someone_is_cheating"
    DRAFT_A_MAP_OF_A_SMALL_AREA = "draft_a_map_of_a_small_area"
    DUPLICATE_A_WAX_SEAL = "duplicate_a_wax_seal"
    IDENTIFY_A_PLANT = "identify_a_plant"
    IDENTIFY_A_SUBSTANCE = "identify_a_substance"
    IDENTIFY_ALCOHOL = "identify_alcohol"
    IMPROVE_FOODS_FLAVOR = "improve_foods_flavor"
    IMPROVISE_A_SONG = "improvise_a_song"
    MEND_A_TEAR_IN_CLOTHING = "mend_a_tear_in_clothing"
    MIMIC_10_OR_FEWER_WORDS_OF_SOMEONE_ELSES_HANDWRITING = "mimic_10_or_fewer_words_of_someone_elses_handwriting"
    MODIFY_FOOTWEAR_TO_GIVE_ADVANTAGE_ON_THE_WEARERS_NEXT_DEXTERITY_ACROBATICS_CHECK = "modify_footwear_to_give_advantage_on_the_wearers_next_dexterity_acrobatics_check"  # noqa: E501
    PAINT_A_RECOGNIZABLE_IMAGE_OF_SOMETHING_YOUVE_SEEN = "paint_a_recognizable_image_of_something_youve_seen"
    PICK_A_LOCK = "pick_a_lock"
    PLAY_A_KNOWN_TUNE = "play_a_known_tune"
    PLOT_A_COURSE = "plot_a_course"
    PRY_OPEN_A_DOOR_OR_CONTAINER = "pry_open_a_door_or_container"
    SEAL_OR_PRY_OPEN_A_DOOR_OR_CONTAINER = "seal_or_pry_open_a_door_or_container"
    SEW_A_TINY_DESIGN = "sew_a_tiny_design"
    START_A_FIRE = "start_a_fire"
    WIN_THE_GAME = "win_the_game"
    WRITE_TEXT_WITH_IMPRESSIVE_FLOURISHES_THAT_GUARD_AGAINST_FORGERY = "write_text_with_impressive_flourishes_that_guard_against_forgery"


class FeatCategory(StrEnum):
    """A feat's printed category."""

    GENERAL = "general"
    EPIC_BOON = "epic_boon"
    ORIGIN = "origin"


class RequiredFeature(StrEnum):
    """A feature a feat prerequisite names."""

    SPELLCASTING = "spellcasting"


class FeatQualifier(StrEnum):
    """The parenthetical on a granted feat: *"Magic Initiate (Cleric)"*."""

    CLERIC = "cleric"
    WIZARD = "wizard"


class RestKind(StrEnum):
    """The two rests."""

    SHORT_REST = "short_rest"
    LONG_REST = "long_rest"


class SwapScope(StrEnum):
    """How many mastery choices a Long Rest lets the character change."""

    ONE = "one"
    ANY = "any"


class RangeClass(StrEnum):
    """Melee or ranged, as a rule distinguishes them."""

    MELEE = "melee"
    RANGED = "ranged"


class Difficulty(StrEnum):
    """The printed Typical Difficulty Classes."""

    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    NEARLY_IMPOSSIBLE = "nearly_impossible"


class NaturalOutcome(StrEnum):
    """What a natural 1 or 20 on an attack roll does."""

    HIT = "hit"
    MISS = "miss"


class CriticalDamageScope(StrEnum):
    """*"Roll all of the attack's damage dice twice"*."""

    EVERY_DAMAGE_DIE_OF_THE_ATTACK = "every_damage_die_of_the_attack"


class ModifierApplication(StrEnum):
    """*"add any relevant modifiers as normal"* -- once."""

    ADDED_ONCE = "added_once"


class ZeroHitPointSubject(StrEnum):
    """Whom a zero-HP rule is about."""

    MONSTER = "monster"
    CHARACTER = "character"
    ANY = "any"


class ZeroHitPointResult(StrEnum):
    """What a zero-HP rule says happens."""

    DIES = "dies"
    UNCONSCIOUS_AND_DYING = "unconscious_and_dying"


class GamemasterException(StrEnum):
    """The exception a GameMaster may make to a zero-HP rule."""

    TREAT_AS_CHARACTER = "treat_as_character"


class ExceptionScope(StrEnum):
    """How widely that exception is made: per individual monster."""

    INDIVIDUAL_MONSTER = "individual_monster"


class ZeroHitPointRuleTrigger(StrEnum):
    """*"If your Hit Point maximum drops to 0"*."""

    HIT_POINT_MAXIMUM_ZERO = "hit_point_maximum_zero"


class LifecycleEvent(StrEnum):
    """An event a zero-HP rule names."""

    REGAINS_HIT_POINTS = "regains_hit_points"
    BECOMES_STABLE = "becomes_stable"
    FIRST_AID_SUCCESS = "first_aid_success"


class DeathThreshold(StrEnum):
    """The amount a death determination compares damage against."""

    HIT_POINT_MAXIMUM = "hit_point_maximum"


class StabilizeAction(StrEnum):
    """The action that stabilizes a dying creature."""

    HELP = "help"


class StabilizeOutcome(StrEnum):
    """What a successful stabilization makes the creature."""

    STABLE = "stable"


class RecoveryUnless(StrEnum):
    """*"A Stable creature that isn't healed"*."""

    HEALED = "healed"


class KnockoutTrigger(StrEnum):
    """*"When you would reduce a creature to 0 Hit Points"*."""

    WOULD_REDUCE_TO_ZERO_HIT_POINTS = "would_reduce_to_0_hit_points"


class UnmetEffect(StrEnum):
    """What an unmet weapon requirement imposes."""

    ATTACK_DISADVANTAGE = "attack_disadvantage"


class LightTrigger(StrEnum):
    """*"When you take the Attack action on your turn"*."""

    ATTACK_ACTION_ON_OWN_TURN = "attack_action_on_own_turn"


class LightFirstAttack(StrEnum):
    """*"and attack with a Light weapon"*."""

    WITH_A_LIGHT_WEAPON = "with_a_light_weapon"


class LightRequirement(StrEnum):
    """*"with a different Light weapon"*."""

    DIFFERENT_LIGHT_WEAPON = "different_light_weapon"


class LightTiming(StrEnum):
    """*"later on the same turn"*."""

    LATER_ON_THE_SAME_TURN = "later_on_the_same_turn"


class ModifierDamage(StrEnum):
    """*"you don't add your ability modifier to the extra attack's damage
    unless that modifier is negative"*."""

    ONLY_IF_NEGATIVE = "only_if_negative"


class UseFrequency(StrEnum):
    """*"once per turn"*."""

    ONCE_PER_TURN = "once_per_turn"


class RangeOutcome(StrEnum):
    """What attacking beyond a range band does."""

    ATTACK_DISADVANTAGE = "attack_disadvantage"
    CANNOT_ATTACK = "cannot_attack"


class ReachScope(StrEnum):
    """What a Reach weapon's extra 5 feet applies to."""

    ATTACKS_WITH_IT = "attacks_with_it"
    OPPORTUNITY_ATTACK_REACH = "opportunity_attack_reach"


class ThrownAbility(StrEnum):
    """*"use the same ability modifier ... that you would use for a melee
    attack"*."""

    AS_MELEE_ATTACK = "as_melee_attack"


class HandsWhen(StrEnum):
    """*"requires two hands when you attack with it"*."""

    ATTACKING = "attacking"


class AmmunitionRequirement(StrEnum):
    """*"ammunition of the type specified"*."""

    AMMUNITION_OF_THE_PRINTED_TYPE = "ammunition_of_the_printed_type"


class FreeHandWhen(StrEnum):
    """*"a free hand to load a one-handed weapon"*."""

    WEAPON_IS_ONE_HANDED = "weapon_is_one_handed"


class RecoveryAfter(StrEnum):
    """*"after a fight"*."""

    FIGHT = "fight"


class RecoveryRemainder(StrEnum):
    """*"the rest is lost"*."""

    LOST = "lost"


class AmmunitionKind(StrEnum):
    """The ammunition an Ammunition weapon's row names."""

    ARROW = "arrow"
    BOLT = "bolt"
    BULLET = "bullet"
    NEEDLE = "needle"


class TwoHandedException(StrEnum):
    """The Lance's *"unless mounted"*."""

    MOUNTED = "mounted"


class MasteryTrigger(StrEnum):
    """When a mastery property applies."""

    HIT_CREATURE = "hit_creature"
    HIT_AND_DAMAGE = "hit_and_damage"
    HIT_MELEE_ATTACK_ROLL = "hit_melee_attack_roll"
    MISS_CREATURE = "miss_creature"
    LIGHT_EXTRA_ATTACK = "light_extra_attack"


class MasteryAppliesTo(StrEnum):
    """Whom a mastery effect applies to."""

    HIT_CREATURE = "hit_creature"
    WIELDER = "wielder"


class MasteryAgainst(StrEnum):
    """Vex: Advantage against *"that creature"*."""

    THE_HIT_CREATURE = "the_hit_creature"


class MasteryCost(StrEnum):
    """Nick: the extra attack is made *"as part of the Attack action"*."""

    ATTACK_ACTION = "attack_action"


class MasteryDamage(StrEnum):
    """Graze: damage equal to the ability modifier."""

    ATTACK_ABILITY_MODIFIER = "attack_ability_modifier"


class MasteryDamageType(StrEnum):
    """Graze: *"of the same type dealt by the weapon"*."""

    WEAPON = "weapon"


class MasteryIncrease(StrEnum):
    """Graze: *"can be increased only by increasing the ability modifier"*."""

    ONLY_BY_INCREASING_THE_ABILITY_MODIFIER = "only_by_increasing_the_ability_modifier"


class AttackSection(StrEnum):
    """The outcome sections a creature attack prints."""

    HIT = "hit"
    MISS = "miss"
    HIT_OR_MISS = "hit_or_miss"


class DamageNotation(StrEnum):
    """The two printed damage notations."""

    AVERAGE = "average"
    DICE = "dice"


class MultiattackAction(StrEnum):
    """The action a Multiattack is taken as."""

    ATTACK = "attack"


class MultiattackComposition(StrEnum):
    """*"each Multiattack entry states ..."*."""

    PER_ENTRY = "per_entry"


class UsageRuleKind(StrEnum):
    """The limited-usage notations Parts of a Stat Block explains."""

    PER_DAY = "per_day"
    RECHARGE = "recharge"
    RECHARGE_AFTER_REST = "recharge_after_rest"


class LegendaryTiming(StrEnum):
    """*"immediately after another creature's turn"*."""

    AFTER_ANOTHER_CREATURES_TURN = "after_another_creatures_turn"


class LegendaryRegain(StrEnum):
    """*"regains all expended uses at the start of each of its turns"*."""

    START_OF_OWN_TURN = "start_of_own_turn"


class TrainingCondition(StrEnum):
    """*"If you wear armor with which you lack training"*."""

    WEARER_LACKS_TRAINING_WITH_WORN_ARMOR_CATEGORY = (
        "wearer_lacks_training_with_worn_armor_category"
    )


class UntrainedShield(StrEnum):
    """*"you gain the Armor Class benefit of a Shield only if you have
    training"*."""

    NO_ARMOR_CLASS_BENEFIT = "no_armor_class_benefit"
