# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-15

### Added

- Initial scaffold.
- 24 MCP tools across four areas:
  - **Auth:** `instagram_login` (with optional `verification_code` for 2FA),
    `instagram_logout`, `instagram_session_status`
  - **Profile / read:** `instagram_get_my_profile`, `instagram_get_user_profile`,
    `instagram_search_users`, `instagram_get_user_posts`, `instagram_get_post`,
    `instagram_get_post_comments`, `instagram_get_post_likers`,
    `instagram_get_followers`, `instagram_get_following`,
    `instagram_get_timeline`, `instagram_get_user_stories`
  - **Engagement:** `instagram_like_post`, `instagram_unlike_post`,
    `instagram_comment_on_post`, `instagram_follow_user`,
    `instagram_unfollow_user`, `instagram_save_post`, `instagram_unsave_post`
  - **DMs:** `instagram_list_dm_threads`, `instagram_get_dm_thread`,
    `instagram_send_dm`
- Resolves an IG URL or numeric media pk transparently for any tool that takes
  `url_or_pk`.
- Session persistence to `~/.config/instagram-personal-mcp/session.json`
  (override via `IG_SESSION_PATH`).
- Structured error responses with `code`, `type`, and a `hint` for the common
  recoverable cases (`2FA_REQUIRED`, `CHALLENGE_REQUIRED`, `LOGIN_REQUIRED`,
  `RATE_LIMITED`).
