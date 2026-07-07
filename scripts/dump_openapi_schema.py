#!/usr/bin/env python
"""CLI script -- dump the FastAPI app's OpenAPI schema to a JSON file.

CRD Issue 19: source for ``openapi-typescript`` TS type generation
(frontend/src/api/schema.ts). Builds the schema directly from create_app()
-- no live uvicorn server needed, and no real database/provider credentials
required (ApiSettings defaults to a throwaway sqlite file; the schema is
static regardless of runtime data).

Usage
-----
    python scripts/dump_openapi_schema.py --out frontend/openapi.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    # A plain mkdtemp, not TemporaryDirectory: ChromaDB's sqlite connection
    # (opened inside build_orchestrator(), not exposed for explicit
    # disposal) keeps a file handle open past this function returning, and
    # Windows refuses to delete a directory with an open handle. Leaving one
    # small throwaway dir in the OS temp folder is a fine trade for a
    # one-shot schema dump.
    tmp = tempfile.mkdtemp(prefix="afterworlds_openapi_gen_")
    os.environ.setdefault("AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", f"{tmp}/chroma")

    from afterworlds.api.app import create_app
    from afterworlds.api.config import ApiSettings

    settings = ApiSettings(
        database_url=f"sqlite:///{tmp}/schema_gen.db",
        frontend_dist_dir=Path(tmp) / "dist_does_not_exist",
    )
    app = create_app(settings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(app.openapi(), indent=2))

    print(f"Wrote OpenAPI schema to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
