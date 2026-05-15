from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class IGClientError(RuntimeError):
    """Tool-level error that gets serialized into a structured response."""

    def __init__(self, message: str, code: str | None = None, **extra: Any):
        self.message = message
        self.code = code
        self.extra = extra
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "message": self.message,
            "code": self.code,
            **self.extra,
        }


_client: Any = None  # instagrapi.Client, imported lazily


def session_path() -> Path:
    override = os.environ.get("IG_SESSION_PATH")
    if override:
        return Path(override).expanduser()
    base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return base / "instagram-personal-mcp" / "session.json"


def get_client() -> Any:
    """Return a process-wide instagrapi Client, loading any saved session."""
    global _client
    if _client is None:
        from instagrapi import Client

        _client = Client()
        sp = session_path()
        if sp.exists():
            try:
                _client.load_settings(sp)
            except Exception:
                pass
    # Saved settings don't include username; backfill it once we know who we are.
    if getattr(_client, "user_id", None) and not getattr(_client, "username", None):
        try:
            _client.username = _client.account_info().username
        except Exception:
            pass
    return _client


def reset_client() -> None:
    global _client
    _client = None


def save_session() -> None:
    sp = session_path()
    sp.parent.mkdir(parents=True, exist_ok=True)
    get_client().dump_settings(sp)


def is_logged_in() -> bool:
    cl = get_client()
    return bool(getattr(cl, "user_id", None))


def require_auth() -> Any:
    cl = get_client()
    if not getattr(cl, "user_id", None):
        raise IGClientError(
            "Not logged in. Call instagram_login (or set IG_USERNAME / IG_PASSWORD).",
            code="NOT_LOGGED_IN",
        )
    return cl


def env_credentials() -> tuple[str | None, str | None]:
    return os.environ.get("IG_USERNAME"), os.environ.get("IG_PASSWORD")


def resolve_media_pk(url_or_pk: str) -> int:
    """Accept either a numeric media pk or an Instagram URL and return the pk."""
    cl = require_auth()
    s = url_or_pk.strip()
    if s.isdigit():
        return int(s)
    return int(cl.media_pk_from_url(s))


def resolve_user_id(username: str) -> int:
    cl = require_auth()
    return int(cl.user_id_from_username(username))
