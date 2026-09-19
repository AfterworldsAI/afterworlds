# `proficiency-destinations-1` review packet — CRD Issue 5d

**Status: PROPOSED. Not accepted. Nothing in this branch accepts it.**

This packet is the human-readable half of an unaccepted proposal over the four
destinations `proficiency-1` cites: the Rules Glossary entries **Challenge
Rating** and **Expertise**, the **Skills table**, and the **Actions** section of
Playing the Game. It exists so a reviewer can check the proposal against the
printed source without reading 134 KB of JSON, and so the Owner's semantic
acceptance decision is made on the reviewed artifact rather than on a summary.

`proficiency-1` was reviewed and approved under PR #171 with two of its four
pointers deliberately unresolved and two naming glossary keys nothing had
minted. This batch is the source review that gives all four somewhere to land.
The revised `proficiency-1` in this branch differs from the approved artifact in
**exactly two strings** — §7 states which, and a test reconstructs the approved
identity from these bytes to prove it.

## 1. The artifact

| | |
|---|---|
| proposal | `.claude/review-notes/issue-5d-batch-proficiency-destinations-1-PROPOSAL.json` |
| generator | `.claude/review-notes/issue-5d-batch-proficiency-destinations-1-generator.py` |
| bytes | 137,439 |
| `proposal_identity` | `01603c7f9a3b14f9c90e63e03e32da7c75b119109f0c251e8b428d91b0765a5d` |
| file sha256 | `2a2fa620e4379d28651b3ab83b038d59861d0133671d311d36edf1357dd43d85` |
| proposal schema | `5d-proposal-2` |
| representation schema | `5d-representation-schema-15` |
| schema hash | `e87e0bacdc476b0bef092a04cbedd933e0b57b128651b08ef0ffbd0c94d186fd` |
| semantic policy | `5d-semantic-policy-2` |
| source | `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, printed pages 9–10, 178, 182 |
| binding | `5.2.1-corpus.36b786d8-fa2` / `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |

No schema change. Schema 15 is the accepted schema `proficiency-1` already
declares, and this batch adds no field and no fact family: the two typed facts
it carries are `ActionAllowanceFact`, accepted since `actions-1`. Five of the
six parts of the release binding are re-derived from the PDF and asserted
against the accepted oracle's binding; the sixth, `persisted_corpus_digest`, is
taken from that binding and not restated, because it is a digest over persisted
corpus state this batch neither reads nor touches.

## 2. Scope: four review units, one batch

| unit | kind | leaves | expected rules | record |
|---|---|---|---|---|
| `proficiency-destinations-1-challenge-rating` | `entry` | 7 | 3 | `glossary.challenge_rating` |
| `proficiency-destinations-1-expertise` | `entry` | 4 | 3 | `glossary.expertise` |
| `proficiency-destinations-1-skills-table` | `table` | 58 | 18 | `play.skills` |
| `proficiency-destinations-1-actions-section` | `section` | 38 | 26 | `play.actions` |

**Why one batch and not four.** The four destinations are what one Proficiency
reference set needs. Splitting them would have produced four acceptance actions
over one semantic boundary, and three of the four would have been accepted with
the Proficiency links still open — a partial state nothing needs to exist. The
units are separate because the *source shapes* are separate: two glossary
entries, a table, and a prose section.

**Why the Skills table is its own `TABLE` unit and not part of the Actions
section.** 5c nests the Skills table container inside the **Actions**
subsection container. The evidence is the container path, which the generator
asserts rather than trusting: the Actions heading, the `action_default`
paragraph and the improvised-action paragraph are direct children of
`06eb5a68`, and so is the Skills table container `d818241d`. The reason is
visible in the same place: the printed **Skills** heading was captured as a
*paragraph* leaf (`707fa349`, text `"Skills"`), so no Skills subsection
container was ever opened and its table landed in the container that was.
This is a 5c containment fact. It is **reported here and not repaired** — no 5c
change is in this task's scope — and the representation is built so the
placement cannot mislead a reviewer: the table's 58 leaves are reviewed by the
`TABLE` unit, the Actions section's 38 by the `SECTION` unit, the two
memberships are disjoint, and the generator asserts that their union is exactly
the represented leaves of the container.

**What is excluded, and by whom.** The running footer `fb25f796` on the page
break between printed pages 9 and 10 is excluded by *5c* from the represented
population, so neither unit names it. Four section and entry headings are
excluded by the *units*, in an excluded group stating the reason: each names the
rules stated below it and states none itself. Every other leaf a unit names is
reached by an expected rule or a supporting group, which `review_unit_violations`
checks.

**No accepted content is touched.** The generator asserts disjointness against
the committed accepted authority in both directions: no span id of this proposal
appears in the accepted oracle's spans, and none of the four record keys appears
among its 48 records.

## 3. Coverage at a glance

| | count |
|---|---|
| leaves in the four units | 107 |
| leaves excluded by 5c (running footer) | 1 |
| proposed spans | 120 |
| — substantive | 70 |
| — supporting authority | 50 |
| — non-mechanical | 0 |
| records | 4 |
| components | 19 |
| prose bindings | 70 |
| typed facts | 2 |
| relationships | 0 |
| references | 13 |
| provenance claims | 134 |
| expected rules | 50 |

Irreducibility reason codes, and how many bindings carry each:

| code | bindings |
|---|---|
| `contextual_applicability` | 1 |
| `gamemaster_latitude` | 1 |
| `natural_language_exception` | 2 |
| `open_ended_effect` | 1 |
| `subjective_judgment` | 2 |

Every other substantive binding carries `no_identified_structured_use`: the
clause is reducible in principle, and this build has no identified consumer for
a typed form of it. Inventing a field for one would have added a schema a
governing authority does not ask for.

## 4. Source versus disposition

Every leaf each unit names, in printed order, with the exact source text and
what the proposal does with it. `sub` is a substantive span, `sup` a supporting-
authority span, `—` a leaf the unit accounts for without a span.

### Challenge Rating — `proficiency-destinations-1-challenge-rating`

| page | leaf | 5c kind | disposition | component | source text |
|---|---|---|---|---|---|
| 178 | `5468f170` | paragraph | sub | `challenge_rating_meaning` | Challenge Rating (CR) summarizes the threat a monster poses to a group of four player characters. |
| 178 | `5468f170` | paragraph | sub | `threat_comparison` | Compare a monster’s CR to the characters’ level. If the CR is higher, the monster is likely a danger. If the |
| 178 | `571a52eb` | heading | — | — | Challenge Rating |
| 178 | `6111b141` | paragraph | sup | — | See also |
| 178 | `a5c8fb2b` | paragraph | sup | — | “Stat Block.” |
| 178 | `abdc1b9d` | paragraph | sub | `encounter_circumstances` | But circumstances and the number of player characters can significantly alter how threatening a monster is in actual play. |
| 178 | `abdc1b9d` | paragraph | sup | — | “Gameplay Toolbox” (“Combat Encounters”) provides guidance to the GM on using |
| 178 | `b28983f8` | stat_field | sub | `threat_comparison` | CR is lower, the monster likely poses little threat. |
| 178 | `b6e98c19` | stat_field | sup | — | CR while planning potential combat encounters. |

### Expertise — `proficiency-destinations-1-expertise`

| page | leaf | 5c kind | disposition | component | source text |
|---|---|---|---|---|---|
| 182 | `8f6717a9` | paragraph | sup | — | See also |
| 182 | `b77603de` | heading | — | — | Expertise |
| 182 | `f17fb7e0` | paragraph | sub | `expertise_definition` | Expertise is a feature that enhances your use of a skill proficiency. |
| 182 | `f17fb7e0` | paragraph | sub | `expertise_doubling` | When you make an ability check with a skill proficiency in which you have Expertise, your Proficiency Bonus is doubled for that check unless the bonus is doubled by another feature. |
| 182 | `f17fb7e0` | paragraph | sub | `expertise_grant` | If you gain Expertise, you gain it in one skill in which you have proficiency. |
| 182 | `f17fb7e0` | paragraph | sub | `expertise_grant` | You can’t have Expertise in the same skill proficiency more than once. |
| 182 | `f3d54e2e` | paragraph | sup | — | “Playing the Game” (“Proficiency”). |

### Skills table — `proficiency-destinations-1-skills-table`

| page | leaf | 5c kind | disposition | component | source text |
|---|---|---|---|---|---|
| 9 | `707fa349` | paragraph | sup | — | Skills |
| 9 | `c4be7de2` | table_cell | sup | — | Skill |
| 9 | `016f297b` | table_cell | sup | — | Ability |
| 9 | `ff623921` | table_cell | sup | — | Example Uses |
| 9 | `8f8b5351` | table_cell | sub | `skills_table` | Acrobatics |
| 9 | `0ed5a3c4` | table_cell | sub | `skills_table` | Dexterity |
| 9 | `f29fec23` | table_cell | sup | — | Stay on your feet in a tricky situation, or perform an acrobatic stunt. |
| 9 | `78b36880` | table_cell | sub | `skills_table` | Animal Handling |
| 9 | `2fce8f7b` | table_cell | sub | `skills_table` | Wisdom |
| 9 | `e238a28d` | table_cell | sup | — | Calm or train an animal, or get an animal to behave in a certain way. |
| 9 | `a7c659e7` | table_cell | sub | `skills_table` | Arcana |
| 9 | `5d0d1230` | table_cell | sub | `skills_table` | Intelligence |
| 9 | `7eed297d` | table_cell | sup | — | Recall lore about spells, magic items, and the planes of existence. |
| 9 | `64df74b4` | table_cell | sub | `skills_table` | Athletics |
| 9 | `e1fa3508` | table_cell | sub | `skills_table` | Strength |
| 9 | `518e7851` | table_cell | sup | — | Jump farther than normal, stay afloat in rough water, or break something. |
| 9 | `412c976c` | table_cell | sub | `skills_table` | Deception |
| 9 | `f7ba24a5` | table_cell | sub | `skills_table` | Charisma |
| 9 | `8a1174c6` | table_cell | sup | — | Tell a convincing lie, or wear a disguise convincingly. |
| 9 | `9751e128` | table_cell | sub | `skills_table` | History |
| 9 | `fc19a7e5` | table_cell | sub | `skills_table` | Intelligence |
| 9 | `a35b66d7` | table_cell | sup | — | Recall lore about historical events, people, nations, and cultures. |
| 9 | `03269e2b` | table_cell | sub | `skills_table` | Insight |
| 9 | `4e0b7e87` | table_cell | sub | `skills_table` | Wisdom |
| 9 | `d66684f4` | table_cell | sup | — | Discern a person’s mood and intentions. |
| 9 | `155735a7` | table_cell | sub | `skills_table` | Intimidation |
| 9 | `4743c9fe` | table_cell | sub | `skills_table` | Charisma |
| 9 | `dba47af8` | table_cell | sup | — | Awe or threaten someone into doing what you want. |
| 9 | `92b15884` | table_cell | sub | `skills_table` | Investigation |
| 9 | `0dea9a22` | table_cell | sub | `skills_table` | Intelligence |
| 9 | `7c6f7fc5` | table_cell | sup | — | Find obscure information in books, or deduce how something works. |
| 9 | `991fe5da` | table_cell | sub | `skills_table` | Medicine |
| 9 | `1b28c292` | table_cell | sub | `skills_table` | Wisdom |
| 9 | `e51a87fb` | table_cell | sup | — | Diagnose an illness, or determine what killed the recently slain. |
| 9 | `52334082` | table_cell | sub | `skills_table` | Nature |
| 9 | `aa1d0e7b` | table_cell | sub | `skills_table` | Intelligence |
| 9 | `865b91e9` | table_cell | sup | — | Recall lore about terrain, plants, animals, and weather. |
| 9 | `1f211206` | table_cell | sub | `skills_table` | Perception |
| 9 | `f3bce0a5` | table_cell | sub | `skills_table` | Wisdom |
| 9 | `4b8a9871` | table_cell | sup | — | Using a combination of senses, notice something that’s easy to miss. |
| 9 | `deb9b28e` | table_cell | sub | `skills_table` | Performance |
| 9 | `84572b8c` | table_cell | sub | `skills_table` | Charisma |
| 9 | `16223e50` | table_cell | sup | — | Act, tell a story, perform music, or dance. |
| 9 | `8b2d0245` | table_cell | sub | `skills_table` | Persuasion |
| 9 | `c4df93ea` | table_cell | sub | `skills_table` | Charisma |
| 9 | `ed70a005` | table_cell | sup | — | Honestly and graciously convince someone of something. |
| 9 | `f233de8b` | table_cell | sub | `skills_table` | Religion |
| 9 | `5820836e` | table_cell | sub | `skills_table` | Intelligence |
| 9 | `295552e5` | table_cell | sup | — | Recall lore about gods, religious rituals, and holy symbols. |
| 9 | `8e76d1bd` | table_cell | sub | `skills_table` | Sleight of Hand |
| 9 | `a36b5ba2` | table_cell | sub | `skills_table` | Dexterity |
| 9 | `2500ca2f` | table_cell | sup | — | Pick a pocket, conceal a handheld object, or perform legerdemain. |
| 9 | `4998d20b` | table_cell | sub | `skills_table` | Stealth |
| 9 | `5f10f84a` | table_cell | sub | `skills_table` | Dexterity |
| 9 | `38fa8fb1` | table_cell | sup | — | Escape notice by moving quietly and hiding behind things. |
| 9 | `4f23fc63` | table_cell | sub | `skills_table` | Survival |
| 9 | `73d9c0ba` | table_cell | sub | `skills_table` | Wisdom |
| 9 | `a350eaf8` | table_cell | sup | — | Follow tracks, forage, find a trail, or avoid natural hazards. |

### Actions — `proficiency-destinations-1-actions-section`

| page | leaf | 5c kind | disposition | component | source text |
|---|---|---|---|---|---|
| 9 | `a417357c` | paragraph | sub | `action_default` | When you do something other than moving or communicating, you typically take an action. |
| 9 | `a417357c` | paragraph | sub | `action_table` | The Action table lists the game’s main actions, which are defined in more detail in “Rules Glossary.” |
| 9 | `a417357c` | paragraph | sup | — | Actions |
| 9 | `abee3b23` | heading | — | — | Actions |
| 9 | `b4462ac0` | table_cell | sup | — | Action |
| 9 | `2779f91f` | table_cell | sup | — | Summary |
| 9 | `f0452450` | table_cell | sub | `action_table` | Attack |
| 9 | `bf349e19` | table_cell | sup | — | Attack with a weapon or an Unarmed Strike. |
| 9 | `37ac01d8` | table_cell | sub | `action_table` | Dash |
| 9 | `997c3986` | table_cell | sup | — | For the rest of the turn, give yourself extra movement equal to your Speed. |
| 10 | `16344390` | heading | — | — | Reactions |
| 10 | `2b508d04` | paragraph | sup | — | example, allows a Rogue to take a Bonus Action. |
| 10 | `2b508d04` | paragraph | sub | `bonus_action_availability` | You can take a Bonus Action only when a special ability, a spell, or another feature of the game states that you can do something as a Bonus Action. You otherwise don’t have a Bonus Action to take. |
| 10 | `2b508d04` | paragraph | sub | `bonus_action_allowance` | You can take only one Bonus Action on your turn, so you must choose which Bonus Action to use if you have more than one available. |
| 10 | `2b508d04` | paragraph | sub | `bonus_action_allowance` | You choose when to take a Bonus Action during your turn unless the Bonus Action’s timing is specified. |
| 10 | `2b508d04` | paragraph | sub | `bonus_action_deprivation` | Anything that deprives you of your ability to take actions also prevents you from taking a Bonus Action. |
| 10 | `41963047` | heading | — | — | Bonus Actions |
| 10 | `680dedb4` | paragraph | sub | `reaction_definition` | Certain special abilities, spells, and situations allow you to take a special action called a Reaction. A Reaction is an instant response to a trigger of some kind, which can occur on your turn or on someone else’s. |
| 10 | `680dedb4` | paragraph | sup | — | The Opportunity Attack, described later in “Playing the Game,” is the most common type of Reaction. |
| 10 | `680dedb4` | paragraph | sub | `reaction_allowance` | When you take a Reaction, you can’t take another one until the start of your next turn. |
| 10 | `680dedb4` | paragraph | sub | `reaction_interruption` | If the reaction interrupts another creature’s turn, that creature can continue its turn right after the Reaction. |
| 10 | `680dedb4` | paragraph | sub | `reaction_timing` | In terms of timing, a Reaction takes place immediately after its trigger unless the Reaction’s description says otherwise. |
| 10 | `7de88c77` | paragraph | sub | `one_action_at_a_time` | The game uses actions to govern how much you can do at one time. You can take only one action at a time. |
| 10 | `7de88c77` | paragraph | sup | — | This principle is most important in combat, as explained in “Combat” later in “Playing the Game.” |
| 10 | `7de88c77` | paragraph | sup | — | Actions can come up in other situations, too: in a social interaction, you can try to Influence a creature or use the Search action to read the creature’s body language, but you can’t do both at the same time. And when you’re exploring a dungeon, you can’t simultaneously use the Search action to look for traps and use the Help action to aid another character who’s trying to open a stuck door (with the Utilize action). |
| 10 | `b837da82` | paragraph | sub | `bonus_action_availability` | Various class features, spells, and other abilities let you take an additional action on your turn called a Bonus Action. |
| 10 | `b837da82` | paragraph | sup | — | The Cunning Action feature, for |
| 10 | `c05db2e7` | paragraph | sub | `improvised_action_options` | Player characters and monsters can also do things not covered by these actions. Many class features and other abilities provide additional action options, and you can improvise other actions. |
| 10 | `c05db2e7` | paragraph | sub | `improvised_action_judgment` | When you describe an action not detailed elsewhere in the rules, the Game Master tells you whether that action is possible and what kind of D20 Test you need to make, if any. |
| 10 | `c3d0f853` | heading | — | — | One Thing at a Time |
| 10 | `eb7692db` | table_cell | sup | — | Action |
| 10 | `95dcd286` | table_cell | sup | — | Summary |
| 10 | `7e0ea8ff` | table_cell | sub | `action_table` | Disengage |
| 10 | `9cf50cae` | table_cell | sup | — | Your movement doesn’t provoke Opportunity Attacks for the rest of the turn. |
| 10 | `ee579a3f` | table_cell | sub | `action_table` | Dodge |
| 10 | `b70c4e1a` | table_cell | sup | — | Until the start of your next turn, attack rolls against you have Disadvantage, and you make Dexterity saving throws with Advantage. You lose this benefit if you have the Incapacitated condition or if your Speed is 0. |
| 10 | `b2ace586` | table_cell | sub | `action_table` | Help |
| 10 | `d3380484` | table_cell | sup | — | Help another creature’s ability check or attack roll, or administer first aid. |
| 10 | `d4b47fe3` | table_cell | sub | `action_table` | Hide |
| 10 | `b5f5f483` | table_cell | sup | — | Make a Dexterity (Stealth) check. |
| 10 | `c8605be9` | table_cell | sub | `action_table` | Influence |
| 10 | `661c8629` | table_cell | sup | — | Make a Charisma (Deception, Intimidation, Performance, or Persuasion) or Wisdom (Animal Handling) check to alter a creature’s attitude. |
| 10 | `c71c7205` | table_cell | sub | `action_table` | Magic |
| 10 | `b5de13a2` | table_cell | sup | — | Cast a spell, use a magic item, or use a magical feature. |
| 10 | `c2a58596` | table_cell | sub | `action_table` | Ready |
| 10 | `c5320ca0` | table_cell | sup | — | Prepare to take an action in response to a trigger you define. |
| 10 | `bd10fc1c` | table_cell | sub | `action_table` | Search |
| 10 | `b4ac1177` | table_cell | sup | — | Make a Wisdom (Insight, Medicine, Perception, or Survival) check. |
| 10 | `f82cb55c` | table_cell | sub | `action_table` | Study |
| 10 | `5ab98f2c` | table_cell | sup | — | Make an Intelligence (Arcana, History, Investigation, Nature, or Religion) check. |
| 10 | `ab85acb0` | table_cell | sub | `action_table` | Utilize |
| 10 | `a38b56a2` | table_cell | sup | — | Use a nonmagical object. |

## 5. Every clause, its home, and the exceptions that stay prose

Each substantive clause is bound to a component as **exact governing prose** and
expected by its unit under `ExpectedRule(fact_family=None)`. That is the
first-class home for a rule this build carries as prose: the expectation names
the passages the rule is stated across, and the production check requires the
component to bind *every* named passage, so dropping one exception is reported
rather than certified on the surviving clause's evidence.

| record / component | reason code | clause |
|---|---|---|
| `glossary.challenge_rating` / `challenge_rating_meaning` | `no_identified_structured_use` | Challenge Rating (CR) summarizes the threat a monster poses to a group of four player characters. |
| `glossary.challenge_rating` / `encounter_circumstances` | `contextual_applicability` | But circumstances and the number of player characters can significantly alter how threatening a monster is in actual play. |
| `glossary.challenge_rating` / `threat_comparison` | `subjective_judgment` | CR is lower, the monster likely poses little threat. |
| `glossary.challenge_rating` / `threat_comparison` | `subjective_judgment` | Compare a monster’s CR to the characters’ level. If the CR is higher, the monster is likely a danger. If the |
| `glossary.expertise` / `expertise_definition` | `no_identified_structured_use` | Expertise is a feature that enhances your use of a skill proficiency. |
| `glossary.expertise` / `expertise_doubling` | `natural_language_exception` | When you make an ability check with a skill proficiency in which you have Expertise, your Proficiency Bonus is doubled for that check unless the bonus is doubled by another feature. |
| `glossary.expertise` / `expertise_grant` | `no_identified_structured_use` | If you gain Expertise, you gain it in one skill in which you have proficiency. |
| `glossary.expertise` / `expertise_grant` | `no_identified_structured_use` | You can’t have Expertise in the same skill proficiency more than once. |
| `play.actions` / `action_default` | `no_identified_structured_use` | When you do something other than moving or communicating, you typically take an action. |
| `play.actions` / `bonus_action_allowance` | `no_identified_structured_use` | You can take only one Bonus Action on your turn, so you must choose which Bonus Action to use if you have more than one available. |
| `play.actions` / `bonus_action_allowance` | `no_identified_structured_use` | You choose when to take a Bonus Action during your turn unless the Bonus Action’s timing is specified. |
| `play.actions` / `bonus_action_availability` | `no_identified_structured_use` | Various class features, spells, and other abilities let you take an additional action on your turn called a Bonus Action. |
| `play.actions` / `bonus_action_availability` | `no_identified_structured_use` | You can take a Bonus Action only when a special ability, a spell, or another feature of the game states that you can do something as a Bonus Action. You otherwise don’t have a Bonus Action to take. |
| `play.actions` / `bonus_action_deprivation` | `no_identified_structured_use` | Anything that deprives you of your ability to take actions also prevents you from taking a Bonus Action. |
| `play.actions` / `improvised_action_judgment` | `gamemaster_latitude` | When you describe an action not detailed elsewhere in the rules, the Game Master tells you whether that action is possible and what kind of D20 Test you need to make, if any. |
| `play.actions` / `improvised_action_options` | `open_ended_effect` | Player characters and monsters can also do things not covered by these actions. Many class features and other abilities provide additional action options, and you can improvise other actions. |
| `play.actions` / `one_action_at_a_time` | `no_identified_structured_use` | The game uses actions to govern how much you can do at one time. You can take only one action at a time. |
| `play.actions` / `reaction_allowance` | `no_identified_structured_use` | When you take a Reaction, you can’t take another one until the start of your next turn. |
| `play.actions` / `reaction_definition` | `no_identified_structured_use` | Certain special abilities, spells, and situations allow you to take a special action called a Reaction. A Reaction is an instant response to a trigger of some kind, which can occur on your turn or on someone else’s. |
| `play.actions` / `reaction_interruption` | `no_identified_structured_use` | If the reaction interrupts another creature’s turn, that creature can continue its turn right after the Reaction. |
| `play.actions` / `reaction_timing` | `natural_language_exception` | In terms of timing, a Reaction takes place immediately after its trigger unless the Reaction’s description says otherwise. |

## 6. Why only two typed facts

Two clauses state a countable allowance and are typed as
`ActionAllowanceFact(count=1, per=TURN, cost=…)`: one Bonus Action per turn,
and one Reaction until the start of your next turn. Both keep their prose as
well — the components are `MIXED` — because the typed form states the count and
the prose states the rest of what the sentence says.

Three clauses in the same section look typable and are deliberately not typed.
Naming them is the point of this section: each would have required asserting
something the source does not say.

* **"You can take only one action at a time."** `AllowanceScope` has no member
  for simultaneity. `per=TURN` would state a different rule — the section's own
  Bonus Action text shows a turn can carry more than one action-like thing — so
  typing it would have replaced a rule about *concurrency* with a rule about
  *budget*.
* **"You otherwise don't have a Bonus Action to take."** The available shape is
  `ActionRestrictionFact`, which asserts an unconditional prohibition. This
  clause is the negative arm of a conditional permission: it prohibits only in
  the absence of a feature that grants. Typing it would have stated that no
  Bonus Action is ever available.
* **Reaction timing** — "immediately after its trigger unless the Reaction's
  description says otherwise." `TriggeredResolutionFact.optional` carries no
  negative arm for a stated override, so the exception would have been dropped
  while the rule read as absolute. It is carried as prose under
  `natural_language_exception`.

The *Example Uses* column of the Skills table and the *Summary* column of the
Action table are illustrative rather than governing, so both are accounted for
as **supporting authority** — 22 leaves for the Skills table, 16 for the Action
table — not as rules. The Skills table's governing content is the 18
skill-to-ability pairs, one expected rule per printed row, each naming the two
cells it is read from. The generator cross-checks every pair against the
accepted `SKILL_ABILITY` mapping rather than restating 18 pairs by hand, so a
misread row fails the build.

## 7. The links: thirteen authored here, four closed in `proficiency-1`

### The thirteen this batch authors

| from | printed wording | resolution scope | destination |
|---|---|---|---|
| `glossary.expertise` *(record-owned)* | Proficiency | `srd-5.2.1/playing-the-game` | `play.proficiency` |
| `play.actions` / `action_table` | Attack | `srd-5.2.1/rules-glossary` | `action.attack` |
| `play.actions` / `action_table` | Dash | `srd-5.2.1/rules-glossary` | `action.dash` |
| `play.actions` / `action_table` | Disengage | `srd-5.2.1/rules-glossary` | `action.disengage` |
| `play.actions` / `action_table` | Dodge | `srd-5.2.1/rules-glossary` | `action.dodge` |
| `play.actions` / `action_table` | Help | `srd-5.2.1/rules-glossary` | `action.help` |
| `play.actions` / `action_table` | Hide | `srd-5.2.1/rules-glossary` | `action.hide` |
| `play.actions` / `action_table` | Influence | `srd-5.2.1/rules-glossary` | `action.influence` |
| `play.actions` / `action_table` | Magic | `srd-5.2.1/rules-glossary` | `action.magic` |
| `play.actions` / `action_table` | Ready | `srd-5.2.1/rules-glossary` | `action.ready` |
| `play.actions` / `action_table` | Search | `srd-5.2.1/rules-glossary` | `action.search` |
| `play.actions` / `action_table` | Study | `srd-5.2.1/rules-glossary` | `action.study` |
| `play.actions` / `action_table` | Utilize | `srd-5.2.1/rules-glossary` | `action.utilize` |

The twelve Action-table links are **not new keys**. The accepted Rules Glossary
`Action` entry already cites the same twelve words in the same scope at
`action.attack` … `action.utilize`, and the generator asserts its twelve targets
are a subset of the accepted records; a test compares them field for field
against the committed artifact. Repeating a citation is legitimate — several
records may point at one rule — and because both point at the *same* record, the
merged data has no `(scope, wording)` resolving two ways.

### The four `proficiency-1` closes, and the two strings that close them

| printed wording | resolution scope | destination | minted by |
|---|---|---|---|
| Challenge Rating | `srd-5.2.1/rules-glossary` | `glossary.challenge_rating` | this batch |
| Expertise | `srd-5.2.1/rules-glossary` | `glossary.expertise` | this batch |
| Skills table | `srd-5.2.1/playing-the-game` | `play.skills` | this batch |
| Actions | `srd-5.2.1/playing-the-game` | `play.actions` | this batch |

The first two already named those keys in the approved artifact; they resolve
now because the records exist. The last two were authored with an **empty**
`target_record_key`, and closing them is an edit to `proficiency-1`'s own
content: two strings, `""` → `play.skills` and `""` → `play.actions`, plus the
two provenance keys those two fields derive. Nothing else in that proposal
changes — no rule, span, component, fact, binding or expectation — and the claim
is checked, not asserted: blanking exactly those two fields and their two
derived keys and re-deriving the identity through the production payload path
returns the approved identity
`c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4`.

| `proficiency-1` | identity | sha256 | bytes |
|---|---|---|---|
| approved under PR #171 | `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4` | `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324` | 61,329 |
| revised in this branch | `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` | `c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d` | 61,375 |

### The pointers deliberately left as prose

A reference is minted only where the destination exists in accepted or in-flight
data. Minting one at a key nothing has reviewed would author an obligation this
build cannot discharge and would let a later batch close it by accident, simply
by choosing a matching key. These pointers are therefore carried as exact source
prose with no reference:

* the Challenge Rating entry's `See also` → `"Stat Block."`, and its mention of
  the Gameplay Toolbox's Combat Encounters material;
* the Expertise entry's `See also` → Playing the Game (Proficiency), which is
  the *record-owned* reference in the table above and is the one of these that
  does have a destination;
* the Actions section's mentions of Combat, Opportunity Attack and Cunning
  Action; and
* the illustrative Influence / Search / Help / Utilize mentions inside Summary
  and Example Uses cells, which name actions in passing rather than citing them.

Each is visible in §4 as source text with a supporting-authority disposition, so
a reviewer can see what was read and not linked.

## 8. Omissions, residue, and boundaries

* **The Skills table's 5c container placement** (§2) is reported, not repaired.
  A 5c change is outside this task; the representation is built so the placement
  cannot silently truncate either unit.
* **The schema's own citations of the Skills table** — `Skill`
  (`representation.py:415`) and `SKILL_ABILITY` (`:449`) both name the printed
  Skills table as their authority, and until this batch no record represented
  it; `AbilityCheckFact.skill` (`:2661`) cites the same table for its pairing
  rule. That wording predates this task, so it is reported rather than edited —
  editing accepted schema prose for no stated use is out of scope. What this
  batch changes is that the citation becomes checkable: the generator reads the
  eighteen printed rows and cross-checks them against `SKILL_ABILITY` (§6), so a
  misread row fails the build instead of resting on the docstring's word.
* **Ten outward pointers of the accepted `glossary.speed` entry** —
  `Climbing`, `Swimming`, `Burrow Speed` and the rest — still resolve at records
  no batch has reviewed. They are *reported* by the production check, which is
  the honest state, and the movement entries they name are a later batch's work.
  A test pins that list exactly, so this task cannot silence one and a later
  movement batch has to change the list to close them.
* **Nothing here is accepted.** The four records are proposed. Publication or
  activation of a partial Rules Package is not authorized and is not attempted.

## 9. How to verify this packet

```bash
# regenerate the proposal (deterministic; overwrites with identical bytes)
python .claude/review-notes/issue-5d-batch-proficiency-destinations-1-generator.py

# this batch: identity, unit shape, the thirteen links, the two typed facts
pytest tests/ingestion/mechanical/test_proficiency_destinations_1_proposal.py -q

# the revised proficiency-1, and the two-string reconstruction of PR #171's bytes
pytest tests/ingestion/mechanical/test_proficiency_1_proposal.py -q

# the four links resolving uniquely in the merged data, and the failures
pytest tests/ingestion/mechanical/test_proficiency_references_resolve.py -q
```
