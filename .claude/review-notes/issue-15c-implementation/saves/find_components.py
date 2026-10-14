"""List records/components whose key matches any argument, with fact families."""
import sys

from tests.services.dnd5e_state.builders import real_index

idx = real_index()
for key, rec in sorted(idx.records.items()):
    for c in rec.components:
        if any(a in c.semantic_key or a == key for a in sys.argv[1:]):
            fams = [type(f.fact).__name__ for f in c.facts]
            print(f"{key}/{c.semantic_key} {c.handling.value} {fams}")
