# Codex provisional A/C native mapping review

Read-only review of the current deterministic mapper and immutable raw C5-A/C on the selected clean checkout; no imports, generation, tests or source changes by Codex.

No concrete semantic-loss blocker found in the inspected A/C transformations. Weapon range/property/damage and optional exceptions survive; mastery effects retain trigger, selection, target, limits and actor-relative duration; grant choices retain count, level references, origin/feat prerequisites, subclass eligibility, tool selectors, class/MC context and mastery count-by-level; armor and shield penalties/requirements remain distinct. The direct pass-through families retain the reviewed payloads, and the custom mappings disclose reserved-name, closed-vocabulary, union and optional-field changes. Native fixed-point checks prove typed serialization, not full source-item coverage.

Final review remains conditional on the exact generated correspondence: tool activity options must preserve source activity selection and common tool facts across the native conjunction/choice constraint; any shared-fact replication or singleton-option collapse must be explicitly reconciled by identity, with activity text/source retained. Two relocation addresses are permitted source-address corrections within the same already affected batch: temporary-HP absorption to play.damage_and_healing/lost_first, and Shield training to the nested equipment.armor.shield/shield record/component. The latter is not same-record. No source rule changes or scope expansion are inferred from these relocations.

This is provisional native preparation review only, not semantic acceptance, execution certification or completion of CRD Issue 15c.
