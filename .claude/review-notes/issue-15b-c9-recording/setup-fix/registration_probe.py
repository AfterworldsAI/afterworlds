"""For each given test module that calls ``Base.metadata.create_all``: does
importing it with its conftest chain, alone in a fresh interpreter, register
``stories`` (and ``dnd5e_character_states``)? Fresh interpreter per module,
so the answer does not depend on collection order. Run from the repository
root with ``src`` and the root on ``PYTHONPATH``:

    python registration_probe.py $(git grep -l "Base.metadata.create_all" -- tests)
"""

import json
import subprocess
import sys

CHILD = """
import importlib, pathlib, sys
p = pathlib.Path(sys.argv[1])
chain = [d / "conftest.py" for d in reversed(p.parents) if (d / "conftest.py").exists()]
for f in [*chain, p]:
    importlib.import_module(".".join(f.with_suffix("").parts))
from afterworlds.persistence.orm.base import Base
t = Base.metadata.tables
print("stories" in t, "dnd5e_character_states" in t)
"""

out = {}
for module in sys.argv[1:]:
    r = subprocess.run(
        [sys.executable, "-c", CHILD, module], capture_output=True, text=True
    )
    out[module] = r.stdout.strip() or "IMPORT ERROR " + r.stderr.strip()[-300:]
print(json.dumps(out, indent=1))
