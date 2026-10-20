"""Controlled Owner-administrator bootstrap (prerequisite #205 §1, ADR-021 D3).

The only way to grant staff authority. Run on the server by an operator with
control-store access, after the Owner has enrolled and verified an ordinary
account::

    python -m afterworlds.remote.bootstrap --contact-address owner@example.com

The Owner's password is read from the terminal (or, for automation, one line
on stdin with ``--password-stdin``), never from argv. Re-running for the same
principal is a recorded no-op; any other principal is refused.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from alembic.util.exc import CommandError
from sqlalchemy.exc import SQLAlchemyError

from afterworlds.remote.control_store import (
    ControlStoreUnavailable,
    connect_control_store,
)
from afterworlds.remote.identity import IdentityError, IdentityService


class _NoNotices:
    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        raise AssertionError("bootstrap sends no notices")

    def purge(self, contact_address: str) -> int:
        raise AssertionError("bootstrap erases no account")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contact-address", required=True)
    parser.add_argument(
        "--control-db",
        default=os.environ.get("AFTERWORLDS_CONTROL_DATABASE_URL"),
        help="Control-store URL (default: AFTERWORLDS_CONTROL_DATABASE_URL).",
    )
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args(argv)
    if not args.control_db:
        parser.error("--control-db or AFTERWORLDS_CONTROL_DATABASE_URL is required")
    password = (
        sys.stdin.readline().rstrip("\r\n")
        if args.password_stdin
        else getpass.getpass("Owner password: ")
    )
    try:
        # Never migrates: bootstrap may run beside the serving app.
        identity = IdentityService(connect_control_store(args.control_db), _NoNotices())
        outcome = identity.bootstrap_owner_administrator(args.contact_address, password)
    except IdentityError as exc:
        print(f"bootstrap refused: {exc}", file=sys.stderr)
        return 1
    except (SQLAlchemyError, CommandError, ControlStoreUnavailable):
        # Opening, migrating or writing the control store failed. Fail closed
        # without the driver's text (it can carry the address or path): the
        # attempt was neither recorded nor granted.
        print(
            "bootstrap failed: the control store is unavailable or could not "
            "record the attempt; nothing was provisioned",
            file=sys.stderr,
        )
        return 2
    print(f"owner administrator: {outcome.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
