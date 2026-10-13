"""Print a template's facts of given families."""
import sys

from afterworlds.pipeline.rpg.defense import facts_of
from tests.services.dnd5e_state.builders import real_index

idx = real_index()
for f in facts_of(idx, sys.argv[1]):
    if not sys.argv[2:] or type(f).__name__ in sys.argv[2:]:
        print(f)
