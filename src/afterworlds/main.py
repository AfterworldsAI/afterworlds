"""Uvicorn entry point -- the single process/origin serving the product build.

Binding Decision 8: a single uvicorn worker. Multi-worker/multi-process
deployment is out of scope and must not be silently enabled here.
"""

from __future__ import annotations

import uvicorn

from afterworlds.api.app import create_app

app = create_app()


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000, workers=1)


if __name__ == "__main__":
    main()
