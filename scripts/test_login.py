"""Interactive end-to-end login test.

Reads IG_USERNAME / IG_PASSWORD from .env (or env vars), logs in, prompts for
a 2FA code if Instagram asks, then exercises a few read-only tools so we know
the session works.

Run from the project root with the venv activated:
    .venv/bin/python scripts/test_login.py
"""
from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

load_dotenv()

from instagram_personal_mcp.server import (  # noqa: E402  pylint: disable=wrong-import-position
    instagram_get_my_profile,
    instagram_login,
    instagram_session_status,
)


def show(label: str, value: object) -> None:
    print(f"\n=== {label} ===")
    try:
        print(json.dumps(value, indent=2, default=str)[:2000])
    except Exception:
        print(value)


def main() -> int:
    print("Status before login:")
    show("session_status", instagram_session_status())

    print("\nAttempting login (reads IG_USERNAME / IG_PASSWORD from env)...")
    res = instagram_login()
    show("login", res)

    if isinstance(res, dict) and res.get("error") and res.get("code") == "2FA_REQUIRED":
        try:
            code = input("\n2FA required. Enter the 6-digit code: ").strip()
        except EOFError:
            print("No TTY available for 2FA input. Re-run with a terminal attached.")
            return 2
        res = instagram_login(verification_code=code)
        show("login (with 2FA)", res)

    if not (isinstance(res, dict) and res.get("ok")):
        print("\nLogin did not succeed. See errors above.")
        return 1

    show("session_status", instagram_session_status())
    show("my_profile", instagram_get_my_profile())

    print("\nDone. Session saved to disk; future runs should skip the login step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
