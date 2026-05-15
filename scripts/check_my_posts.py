"""List the logged-in user's recent posts + commenters on the first few."""
from __future__ import annotations

import json

from dotenv import load_dotenv

load_dotenv()

from instagram_personal_mcp.client import get_client, is_logged_in  # noqa: E402
from instagram_personal_mcp.server import (  # noqa: E402
    instagram_get_post_comments,
    instagram_get_user_posts,
    instagram_session_status,
)

if not is_logged_in():
    print("Not logged in. Run scripts/test_login.py first.")
    raise SystemExit(1)

me = get_client().username
print(f"Logged in as @{me}")
print(instagram_session_status())

print("\n=== Recent posts ===")
posts = instagram_get_user_posts(me, amount=10)
if isinstance(posts, dict) and posts.get("error"):
    print(json.dumps(posts, indent=2))
    raise SystemExit(1)

for i, p in enumerate(posts, 1):
    caption = (p.get("caption_text") or "")[:80].replace("\n", " ")
    print(
        f"{i:>2}. pk={p.get('pk')} "
        f"type={p.get('media_type')}/{p.get('product_type') or '-'} "
        f"likes={p.get('like_count')} comments={p.get('comment_count')} "
        f"taken={p.get('taken_at')} "
        f"caption={caption!r}"
    )

print("\n=== Commenters on the 3 most recent posts ===")
for p in posts[:3]:
    pk = p.get("pk")
    print(f"\n--- post {pk} ---")
    comments = instagram_get_post_comments(str(pk), amount=20)
    if isinstance(comments, dict) and comments.get("error"):
        print(json.dumps(comments, indent=2))
        continue
    if not comments:
        print("(no comments)")
        continue
    for c in comments:
        user = c.get("user") or {}
        uname = user.get("username") if isinstance(user, dict) else None
        text = (c.get("text") or "")[:120].replace("\n", " ")
        print(f"  @{uname}: {text}")
