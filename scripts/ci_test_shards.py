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

#: Rough relative cost per file (seconds, from local and earlier CI runs);
#: unlisted files count as 5. A stale weight only unbalances the shards.
WEIGHTS: dict[str, float] = {
    "tests/ingestion/mechanical/test_magic_items_proposal.py": 2500,
    "tests/ingestion/mechanical/test_equipment_spell_references_candidate.py": 1250,
    "tests/ingestion/mechanical/test_animals_proposal.py": 1120,
    "tests/ingestion/mechanical/test_actions_pilot_proposal.py": 950,
    "tests/ingestion/mechanical/test_monsters_proposal.py": 800,
    "tests/ingestion/mechanical/test_final_ten_references_candidate.py": 600,
    "tests/ingestion/mechanical/test_classes_proposal.py": 600,
    "tests/ingestion/mechanical/test_spell_descriptions_proposal.py": 600,
    "tests/ingestion/mechanical/test_finite_reference_routes_candidate.py": 300,
    "tests/ingestion/mechanical/test_gameplay_toolbox_proposal.py": 200,
    "tests/ingestion/mechanical/test_chunk_locality.py": 160,
    "tests/ingestion/corpus/test_source_completeness.py": 140,
    "tests/ingestion/mechanical/test_character_origins_feats_proposal.py": 140,
    "tests/ingestion/mechanical/test_fact_field_types.py": 130,
    "tests/ingestion/corpus/test_source_lifecycle.py": 120,
    "tests/ingestion/mechanical/test_equipment_proposal.py": 100,
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
