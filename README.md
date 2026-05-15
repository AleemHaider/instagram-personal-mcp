# instagram-personal-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that wraps
[`instagrapi`](https://github.com/subzeroid/instagrapi) so Claude (or any MCP
client) can read, engage, and DM from a **personal** Instagram account — no
Business/Creator switch, no Meta app review.

> **⚠️ Unofficial private API.** This server uses Instagram's reverse-engineered
> mobile API (via `instagrapi`). It is not affiliated with or endorsed by Meta.
> Accounts driving private-API traffic can be rate-limited, challenged, or
> permanently disabled. Use a **burner account** until you trust your setup,
> keep activity natural, and don't connect over VPNs / datacenter IPs.

24 tools across auth, profile/read, engagement, and DMs.

## Quick start

```bash
git clone https://github.com/AleemHaider/instagram-personal-mcp
cd instagram-personal-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Drop your creds in a `.env`:

```bash
cp .env.example .env
# edit: IG_USERNAME, IG_PASSWORD
```

Then run it:

```bash
instagram-personal-mcp
```

The first call (e.g. `instagram_session_status` or `instagram_login`) will
authenticate and save a session file to
`~/.config/instagram-personal-mcp/session.json`. Subsequent runs reuse it.

## Connect to Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json` (Linux) /
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "instagram-personal": {
      "command": "instagram-personal-mcp",
      "env": {
        "IG_USERNAME": "your_username",
        "IG_PASSWORD": "your_password"
      }
    }
  }
}
```

Restart Claude Desktop.

## Tools

### Auth

| Tool | What it does |
|---|---|
| `instagram_login` | Log in. Pass `verification_code` if 2FA is on. |
| `instagram_logout` | Log out and delete the saved session. |
| `instagram_session_status` | Report whether a usable session is loaded. |

### Profile & read

| Tool | What it does |
|---|---|
| `instagram_get_my_profile` | Profile of the logged-in account. |
| `instagram_get_user_profile` | Public profile of another user. |
| `instagram_search_users` | Search users by keyword. |
| `instagram_get_user_posts` | Recent posts by a user. |
| `instagram_get_post` | Details of a single post (URL or media pk). |
| `instagram_get_post_comments` | Comments on a post. |
| `instagram_get_post_likers` | Users who liked a post. |
| `instagram_get_followers` | List a user's followers. |
| `instagram_get_following` | List who a user follows. |
| `instagram_get_timeline` | Home feed. |
| `instagram_get_user_stories` | Active stories from a user. |

### Engagement

| Tool | What it does |
|---|---|
| `instagram_like_post` | Like a post. |
| `instagram_unlike_post` | Unlike a post. |
| `instagram_comment_on_post` | Comment on a post. |
| `instagram_follow_user` | Follow a user. |
| `instagram_unfollow_user` | Unfollow a user. |
| `instagram_save_post` | Save a post to your collection. |
| `instagram_unsave_post` | Remove a post from your saved collection. |

### Direct messages

| Tool | What it does |
|---|---|
| `instagram_list_dm_threads` | List DM threads. |
| `instagram_get_dm_thread` | Messages in a thread. |
| `instagram_send_dm` | Send a DM (comma-separated usernames for group). |

## 2FA flow

1. Call `instagram_login` (no code) — if 2FA is required you'll get
   `{"error": true, "code": "2FA_REQUIRED", ...}`.
2. Get the code from your authenticator / SMS.
3. Call `instagram_login` again with `verification_code="123456"`.

## Errors

Tools return structured errors instead of raising. Look for `error: true` and a
machine-readable `code`:

- `NOT_LOGGED_IN` — call `instagram_login` first.
- `LOGIN_REQUIRED` — saved session was rejected; log in again.
- `2FA_REQUIRED` — call `instagram_login` again with `verification_code`.
- `CHALLENGE_REQUIRED` — Instagram wants a security challenge solved; log in
  from the IG app / web once to clear it.
- `RATE_LIMITED` — `PleaseWaitFewMinutes` from upstream; back off.
- `USER_NOT_FOUND` / `MEDIA_NOT_FOUND` — bad input or removed content.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Why a separate project from `instagram-mcp`?

The sibling [`instagram-mcp`](https://github.com/AleemHaider/instagram-mcp)
wraps the **official Instagram Graph API** — Business/Creator accounts only,
requires a Meta app and tokens, fully ToS-compliant. This project wraps the
**unofficial private API** for personal accounts and carries the risks above.
They're kept separate so the official one stays clean and reviewable.

## License

MIT — see [LICENSE](LICENSE).
