from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from mcp.server.fastmcp import FastMCP

from .client import (
    IGClientError,
    env_credentials,
    get_client,
    is_logged_in,
    require_auth,
    reset_client,
    resolve_media_pk,
    resolve_user_id,
    save_session,
    session_path,
)

mcp = FastMCP("instagram-personal-mcp")

F = TypeVar("F", bound=Callable[..., Any])


def tool(fn: F) -> F:
    """Register an MCP tool, mapping common instagrapi errors to a structured dict."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except IGClientError as e:
            return e.to_dict()
        except (ValueError, TypeError) as e:
            return {"error": True, "message": str(e), "type": type(e).__name__}
        except Exception as e:
            return _classify_instagrapi_error(e)

    return mcp.tool()(wrapper)  # type: ignore[return-value]


def _classify_instagrapi_error(e: Exception) -> dict[str, Any]:
    name = type(e).__name__
    msg = str(e) or name
    code_map = {
        "TwoFactorRequired": "2FA_REQUIRED",
        "ChallengeRequired": "CHALLENGE_REQUIRED",
        "BadPassword": "BAD_PASSWORD",
        "LoginRequired": "LOGIN_REQUIRED",
        "PleaseWaitFewMinutes": "RATE_LIMITED",
        "FeedbackRequired": "FEEDBACK_REQUIRED",
        "UserNotFound": "USER_NOT_FOUND",
        "MediaNotFound": "MEDIA_NOT_FOUND",
        "ClientNotFoundError": "NOT_FOUND",
        "ClientError": "CLIENT_ERROR",
    }
    hint = {
        "2FA_REQUIRED": "Call instagram_login again with verification_code set.",
        "CHALLENGE_REQUIRED": "Log into the account from the IG app/web once to clear the security challenge.",
        "LOGIN_REQUIRED": "Saved session is invalid; call instagram_login again.",
        "RATE_LIMITED": "Wait a few minutes before retrying.",
    }
    code = code_map.get(name, name)
    out: dict[str, Any] = {"error": True, "type": name, "code": code, "message": msg}
    if code in hint:
        out["hint"] = hint[code]
    return out


# ---------- Auth ----------

@tool
def instagram_login(
    username: str | None = None,
    password: str | None = None,
    verification_code: str | None = None,
) -> dict[str, Any]:
    """Log in to Instagram. Falls back to IG_USERNAME / IG_PASSWORD env vars.

    If 2FA is required the first call returns an error with code='2FA_REQUIRED';
    call again with verification_code set.
    """
    env_u, env_p = env_credentials()
    username = username or env_u
    password = password or env_p
    if not username or not password:
        raise IGClientError(
            "Username and password required (pass args or set IG_USERNAME / IG_PASSWORD).",
            code="MISSING_CREDENTIALS",
        )

    cl = get_client()
    cl.login(username, password, verification_code=verification_code or "")
    save_session()
    return {"ok": True, "user_id": str(cl.user_id), "username": cl.username}


@tool
def instagram_logout() -> dict[str, Any]:
    """Log out, clear in-memory client, and delete the saved session file."""
    try:
        get_client().logout()
    except Exception:
        pass
    sp = session_path()
    if sp.exists():
        sp.unlink()
    reset_client()
    return {"ok": True}


@tool
def instagram_session_status() -> dict[str, Any]:
    """Report whether a usable session is loaded."""
    if not is_logged_in():
        return {"logged_in": False, "session_file": str(session_path())}
    cl = get_client()
    return {
        "logged_in": True,
        "user_id": str(cl.user_id),
        "username": cl.username,
        "session_file": str(session_path()),
    }


# ---------- Profile / read ----------

@tool
def instagram_get_my_profile() -> dict[str, Any]:
    """Profile of the logged-in account."""
    cl = require_auth()
    info = cl.account_info()
    return info.model_dump() if hasattr(info, "model_dump") else dict(info)


@tool
def instagram_get_user_profile(username: str) -> dict[str, Any]:
    """Public profile info for another user."""
    cl = require_auth()
    info = cl.user_info_by_username(username)
    return info.model_dump() if hasattr(info, "model_dump") else dict(info)


@tool
def instagram_search_users(query: str, count: int = 20) -> list[dict[str, Any]]:
    """Search users by username/keyword."""
    cl = require_auth()
    results = cl.search_users(query, count)
    return [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in results]


@tool
def instagram_get_user_posts(username: str, amount: int = 20) -> list[dict[str, Any]]:
    """Recent posts by a user."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    medias = cl.user_medias(user_id, amount)
    return [m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in medias]


@tool
def instagram_get_post(url_or_pk: str) -> dict[str, Any]:
    """Details of a single post. Accepts an IG URL or a numeric media pk."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    info = cl.media_info(pk)
    return info.model_dump() if hasattr(info, "model_dump") else dict(info)


@tool
def instagram_get_timeline(amount: int = 20) -> list[dict[str, Any]]:
    """Home timeline (posts from accounts you follow)."""
    cl = require_auth()
    medias = cl.get_timeline_feed() if hasattr(cl, "get_timeline_feed") else []
    items = getattr(medias, "feed_items", medias) or []
    out: list[dict[str, Any]] = []
    for item in items[:amount]:
        if hasattr(item, "model_dump"):
            out.append(item.model_dump())
        elif isinstance(item, dict):
            out.append(item)
    return out


@tool
def instagram_get_user_stories(username: str) -> list[dict[str, Any]]:
    """Active stories from a user."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    stories = cl.user_stories(user_id)
    return [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in stories]


@tool
def instagram_get_post_comments(url_or_pk: str, amount: int = 20) -> list[dict[str, Any]]:
    """Comments on a post."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    comments = cl.media_comments(pk, amount)
    return [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in comments]


@tool
def instagram_get_post_likers(url_or_pk: str) -> list[dict[str, Any]]:
    """Users who liked a post."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    likers = cl.media_likers(pk)
    return [u.model_dump() if hasattr(u, "model_dump") else dict(u) for u in likers]


@tool
def instagram_get_followers(username: str, amount: int = 50) -> list[dict[str, Any]]:
    """List a user's followers (capped at `amount`; 0 = all, which is slow)."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    followers = cl.user_followers(user_id, amount=amount)
    items = followers.values() if isinstance(followers, dict) else followers
    return [u.model_dump() if hasattr(u, "model_dump") else dict(u) for u in items]


@tool
def instagram_get_following(username: str, amount: int = 50) -> list[dict[str, Any]]:
    """List who a user follows (capped at `amount`; 0 = all, which is slow)."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    following = cl.user_following(user_id, amount=amount)
    items = following.values() if isinstance(following, dict) else following
    return [u.model_dump() if hasattr(u, "model_dump") else dict(u) for u in items]


# ---------- Engagement ----------

@tool
def instagram_like_post(url_or_pk: str) -> dict[str, Any]:
    """Like a post."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    return {"ok": bool(cl.media_like(pk)), "media_pk": pk}


@tool
def instagram_unlike_post(url_or_pk: str) -> dict[str, Any]:
    """Unlike a post."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    return {"ok": bool(cl.media_unlike(pk)), "media_pk": pk}


@tool
def instagram_comment_on_post(url_or_pk: str, text: str) -> dict[str, Any]:
    """Comment on a post."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    comment = cl.media_comment(pk, text)
    return comment.model_dump() if hasattr(comment, "model_dump") else dict(comment)


@tool
def instagram_follow_user(username: str) -> dict[str, Any]:
    """Follow a user."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    return {"ok": bool(cl.user_follow(user_id)), "user_id": user_id}


@tool
def instagram_unfollow_user(username: str) -> dict[str, Any]:
    """Unfollow a user."""
    cl = require_auth()
    user_id = resolve_user_id(username)
    return {"ok": bool(cl.user_unfollow(user_id)), "user_id": user_id}


@tool
def instagram_save_post(url_or_pk: str) -> dict[str, Any]:
    """Save a post to your saved collection."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    return {"ok": bool(cl.media_save(pk)), "media_pk": pk}


@tool
def instagram_unsave_post(url_or_pk: str) -> dict[str, Any]:
    """Remove a post from your saved collection."""
    cl = require_auth()
    pk = resolve_media_pk(url_or_pk)
    return {"ok": bool(cl.media_unsave(pk)), "media_pk": pk}


# ---------- Direct messages ----------

@tool
def instagram_list_dm_threads(amount: int = 20) -> list[dict[str, Any]]:
    """List recent DM threads."""
    cl = require_auth()
    threads = cl.direct_threads(amount=amount)
    return [t.model_dump() if hasattr(t, "model_dump") else dict(t) for t in threads]


@tool
def instagram_get_dm_thread(thread_id: str, amount: int = 20) -> dict[str, Any]:
    """Fetch messages in a DM thread."""
    cl = require_auth()
    thread = cl.direct_thread(int(thread_id), amount=amount)
    return thread.model_dump() if hasattr(thread, "model_dump") else dict(thread)


@tool
def instagram_send_dm(usernames: str, text: str) -> dict[str, Any]:
    """Send a DM. `usernames` is a single username or a comma-separated list (group DM)."""
    cl = require_auth()
    names = [u.strip() for u in usernames.split(",") if u.strip()]
    if not names:
        raise IGClientError("At least one recipient username is required.", code="BAD_ARGS")
    user_ids = [resolve_user_id(n) for n in names]
    result = cl.direct_send(text, user_ids=user_ids)
    return result.model_dump() if hasattr(result, "model_dump") else dict(result)


def run() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run()
