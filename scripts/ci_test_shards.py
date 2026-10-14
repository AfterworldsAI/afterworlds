"""Print the test files of one CI shard, so the backend suite runs in parallel.

usage: ci_test_shards.py COUNT INDEX

The files are the ones pytest itself collects under the configured discovery,
each assigned to exactly one of COUNT shards; ``WEIGHTS`` only balances them.
Exits nonzero, printing nothing, if collection fails or the shard is empty. CI
also compares every shard's collected nodes with a full collection, and combines
the shards' coverage before enforcing the configured threshold once.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Observed seconds per file, from the timestamped log of the passing 8-shard
#: CI run 38493129598 (ca85662): each file's gaps between its pytest progress
#: lines. A session or module fixture counts against the file whose test first
#: needed it, so a file's figure is what its shard pays to run it. Listed: every
#: file observed at 30 s or more (50 files, about 96% of the observed time).
#: Unlisted files count as 5, above the 3.2 s those 261 averaged. Estimates for
#: balance only: a stale weight unbalances the shards, never drops a test.
WEIGHTS: dict[str, float] = {
    "tests/ingestion/mechanical/test_accepted_release_publication.py": 3559,
    "tests/ingestion/mechanical/test_animals_proposal.py": 3141,
    "tests/ingestion/mechanical/test_magic_items_proposal.py": 2417,
    "tests/ingestion/mechanical/test_equipment_spell_references_candidate.py": 1637,
    "tests/ingestion/mechanical/test_monsters_proposal.py": 1253,
    "tests/ingestion/mechanical/test_spell_descriptions_proposal.py": 934,
    "tests/ingestion/mechanical/test_classes_proposal.py": 900,
    "tests/ingestion/mechanical/test_final_ten_references_candidate.py": 897,
    "tests/ingestion/corpus/test_gate.py": 703,
    "tests/ingestion/mechanical/test_reference_alternatives_candidate.py": 630,
    "tests/ingestion/mechanical/test_character_origins_feats_proposal.py": 624,
    "tests/ingestion/mechanical/test_finite_reference_routes_candidate.py": 564,
    "tests/ingestion/corpus/test_source_lifecycle.py": 526,
    "tests/ingestion/mechanical/test_bounded_d20_on_published_release.py": 450,
    "tests/ingestion/mechanical/test_character_origins_feats_acceptance.py": 429,
    "tests/ingestion/mechanical/test_gameplay_toolbox_proposal.py": 309,
    "tests/ingestion/mechanical/test_srd_state_on_published_release.py": 282,
    "tests/ingestion/corpus/test_source_release.py": 252,
    "tests/ingestion/corpus/test_source_completeness.py": 235,
    "tests/ingestion/corpus/test_ledger_pipeline.py": 227,
    "tests/ingestion/mechanical/test_committed_accepted_authority.py": 216,
    "tests/ingestion/mechanical/test_checks_actions_rests_proposal.py": 200,
    "tests/ingestion/mechanical/test_rules_glossary_completion_proposal.py": 195,
    "tests/ingestion/mechanical/test_equipment_proposal.py": 188,
    "tests/ingestion/mechanical/test_source_release_readiness.py": 165,
    "tests/ingestion/mechanical/test_publication.py": 162,
    "tests/ingestion/mechanical/test_oracle.py": 159,
    "tests/ingestion/mechanical/test_actions_pilot_proposal.py": 151,
    "tests/ingestion/mechanical/test_character_creation_foundations_proposal.py": 111,
    "tests/ingestion/corpus/test_findings.py": 110,
    "tests/ingestion/mechanical/test_packaging.py": 105,
    "tests/ingestion/mechanical/test_spellcasting_proposal.py": 101,
    "tests/ingestion/corpus/test_source_units.py": 98,
    "tests/persistence/test_rules_authority_migration.py": 94,
    "tests/ingestion/mechanical/test_checks_actions_rests_acceptance.py": 78,
    "tests/ingestion/source/test_community_compare.py": 78,
    "tests/ingestion/corpus/test_source_baseline_reset.py": 68,
    "tests/ingestion/source/test_community_source_structure.py": 65,
    "tests/ingestion/mechanical/test_oracle_succession.py": 64,
    "tests/ingestion/mechanical/test_srd_equipment_catalogue.py": 64,
    "tests/ingestion/mechanical/test_conditions_pilot_proposal.py": 58,
    "tests/ingestion/corpus/test_packaging.py": 57,
    "tests/services/rules_authority/test_expanded_families_overrides.py": 57,
    "tests/ingestion/mechanical/test_core_play_completion_proposal.py": 47,
    "tests/ingestion/mechanical/test_subclass_refusal_at_authority_seams.py": 45,
    "tests/ingestion/mechanical/test_equipment_cited_targets_candidate.py": 44,
    "tests/ingestion/test_ingestion.py": 42,
    "tests/ingestion/mechanical/test_core_play_dependencies_proposal.py": 41,
    "tests/services/rules_authority/test_authored_prose_overlay.py": 38,
    "tests/ingestion/mechanical/test_combat_damage_breaking_proposal.py": 34,
}


def collected_files(root: Path) -> list[str]:
    """Every file holding a test pytest collects from *root*, in order."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-cov"]
        + ["-p", "no:cacheprovider"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit(f"pytest collection failed:\n{result.stdout}{result.stderr}")
    nodes = [line for line in result.stdout.splitlines() if "::" in line]
    return list(dict.fromkeys(node.split("::", 1)[0] for node in nodes))


def shards(files: list[str], count: int) -> list[list[str]]:
    loads = [0.0] * count
    groups: list[list[str]] = [[] for _ in range(count)]
    # Heaviest first, each to the lightest shard so far.
    for name in sorted(files, key=lambda name: (-WEIGHTS.get(name, 5.0), name)):
        lightest = loads.index(min(loads))
        loads[lightest] += WEIGHTS.get(name, 5.0)
        groups[lightest].append(name)
    # Each shard keeps the serial run's module order.
    return [sorted(group, key=files.index) for group in groups]


def main(argv: list[str], root: Path = ROOT) -> str:
    count, index = int(argv[0]), int(argv[1])
    selected = shards(collected_files(root), count)[index]
    if not selected:
        raise SystemExit(f"shard {index} of {count} is empty")
    return "\n".join(selected)


if __name__ == "__main__":
    print(main(sys.argv[1:]))
