#!/usr/bin/env python
"""CLI script — backfill or reindex Retrieval Memory for one story.

CRD Issue 18 / ADR-018 D7: recovery for a Chroma write failure is a re-run;
this script is the idempotent manual backfill/reindex path.

Usage
-----
    python scripts/retrieval_backfill.py --story-id <uuid> --mode backfill \\
        --chroma-path .chroma_data --db-url sqlite:///afterworlds.db

    python scripts/retrieval_backfill.py --story-id <uuid> --mode reindex \\
        --chroma-path .chroma_data --db-url sqlite:///afterworlds.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

# Ensure project src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Import all ORM models so Base.metadata is complete
import afterworlds.persistence.orm.character_sheet  # noqa: E402, F401
import afterworlds.persistence.orm.node  # noqa: E402, F401
import afterworlds.persistence.orm.retrieval  # noqa: E402, F401
import afterworlds.persistence.orm.rules_package  # noqa: E402, F401
import afterworlds.persistence.orm.session_state  # noqa: E402, F401
import afterworlds.persistence.orm.state  # noqa: E402, F401
import afterworlds.persistence.orm.story  # noqa: E402, F401
import afterworlds.persistence.orm.story_bible  # noqa: E402, F401
from afterworlds.persistence.crud.story import get_story  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.pipeline.retrieval.backfill import (  # noqa: E402
    backfill_story,
    reindex_story,
)
from afterworlds.pipeline.retrieval.client import build_chroma_client  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.pipeline.retrieval.write_service import (  # noqa: E402
    RetrievalMemoryWriteService,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill or reindex Retrieval Memory for one story."
    )
    parser.add_argument("--story-id", required=True, help="Story UUID")
    parser.add_argument(
        "--mode",
        choices=["backfill", "reindex", "delete"],
        default="backfill",
        help="backfill: ingest missing eligible turns. "
        "reindex: wipe and rebuild from SQLite ground truth. "
        "delete: remove all chunks for the story (no rebuild).",
    )
    parser.add_argument("--chroma-path", default=".chroma_data")
    parser.add_argument("--db-url", default="sqlite:///afterworlds.db")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    story_id = UUID(args.story_id)

    engine = create_engine(args.db_url)
    session_factory = create_session_factory(engine)
    config = RetrievalMemoryConfig(persist_directory=args.chroma_path)
    client = build_chroma_client(config)
    write_service = RetrievalMemoryWriteService(client, config)

    session = session_factory()
    try:
        story = get_story(session, story_id)
        if story is None:
            print(f"story {story_id} not found", file=sys.stderr)
            raise SystemExit(1)
        story_mode = story.mode
        if args.mode == "delete":
            remaining = write_service.delete_story(story_id)
            print(f"deleted story chunks; remaining={remaining}")
            if remaining != 0:
                raise SystemExit(2)
            return
        if args.mode == "reindex":
            report = reindex_story(session, write_service, story_id, story_mode)
        else:
            report = backfill_story(session, write_service, story_id, story_mode)
    finally:
        session.close()

    print(
        f"scanned={report.turns_scanned} ingested={report.turns_ingested} "
        f"skipped={report.turns_skipped_ineligible} "
        f"data_integrity_errors={list(report.data_integrity_errors)}"
    )
    if report.data_integrity_errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
