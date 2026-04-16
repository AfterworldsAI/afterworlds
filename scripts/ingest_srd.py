#!/usr/bin/env python
"""CLI script — ingest a structured SRD JSON file into the Afterworlds database.

Usage
-----
    python scripts/ingest_srd.py \\
        --data-path data/srd/srd_5_2_1_structured.json \\
        --chroma-path .chroma \\
        --db-url sqlite:///afterworlds.db

Defaults
--------
    --data-path  data/srd/srd_5_2_1_structured.json
    --chroma-path .chroma
    --db-url     sqlite:///afterworlds.db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chromadb

# Ensure project src is on path when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from afterworlds.ingestion.ingestion_service import IngestionService  # noqa: E402
from afterworlds.models.rules_package import IngestionConfig  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm import base as _base  # noqa: E402, F401

# Import all ORM models so Base.metadata is complete before create_all
import afterworlds.persistence.orm.rules_package  # noqa: E402, F401
import afterworlds.persistence.orm.story  # noqa: E402, F401
import afterworlds.persistence.orm.story_bible  # noqa: E402, F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a structured SRD JSON file into Afterworlds."
    )
    parser.add_argument(
        "--data-path",
        default="data/srd/srd_5_2_1_structured.json",
        help="Path to the structured SRD JSON file.",
    )
    parser.add_argument(
        "--chroma-path",
        default=".chroma",
        help="Path to ChromaDB persistent storage directory.",
    )
    parser.add_argument(
        "--db-url",
        default="sqlite:///afterworlds.db",
        help="SQLAlchemy database URL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_path = Path(args.data_path)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        return 1

    print(f"Loading SRD data from {data_path} ...")
    with data_path.open("r", encoding="utf-8") as fh:
        srd_data = json.load(fh)

    section_count = len(srd_data.get("sections", []))
    entity_count = len(srd_data.get("entities", []))
    print(f"  Found {section_count} sections, {entity_count} entities.")

    print(f"Connecting to database: {args.db_url}")
    engine = create_engine(args.db_url)
    from afterworlds.persistence.orm.base import Base

    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    print(f"Connecting to ChromaDB at: {args.chroma_path}")
    chroma_client = chromadb.PersistentClient(path=args.chroma_path)

    config = IngestionConfig(
        package_name="D&D SRD 5.2.1",
        package_version="5.2.1",
    )
    service = IngestionService(config)

    print("Running ingestion pipeline ...")
    with session_factory() as session:
        result = service.ingest(
            session=session,
            srd_data=srd_data,
            source_file_name=data_path.name,
            chroma_client=chroma_client,
        )

    print()
    print("=== Ingestion complete ===")
    print(f"  Package ID : {result.package_id}")
    print(f"  Source  ID : {result.source_id}")
    print(f"  Chunks written  : {result.chunks_written}")
    print(f"  Chunks skipped  : {result.chunks_skipped}")
    print(f"  Entities written: {result.entities_written}")
    print(f"  Entities skipped: {result.entities_skipped}")
    print(f"  Vector docs written: {result.vector_chunks_written}")
    if result.errors:
        print(f"  Errors ({len(result.errors)}):")
        for err in result.errors:
            print(f"    - {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
