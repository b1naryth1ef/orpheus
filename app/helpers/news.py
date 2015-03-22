from database import Cursor
from datetime import datetime
from util.errors import APIError

from helpers.user import gache_user_info

def newspost_to_json(entry):
    user_info = {}

    if not entry.steamid:
        with Cursor() as c:
            user = c.execute(
                "SELECT steamid FROM users WHERE id=%s", (entry.created_by, )).fetchone()

            if user:
                user_info = gache_user_info(user.steamid)
    else:
        user_info = gache_user_info(entry.steamid)

    return {
            "id": entry.id,
            "title": entry.title,
            "category": entry.category,
            "content": entry.content,
            "is_public": entry.is_public,
            "created_at": entry.created_at.isoformat() if entry.created_at else "Unknown",
            "created_by": user_info.get("personaname") or "Anonymous"
    }

def create_news_post(title, category, content, meta, is_public, created_by):
    with Cursor() as c:
        return c.insert("newsposts", {
            "title": title,
            "category": category,
            "content": content,
            "meta": c.json(meta),
            "is_public": is_public,
            "created_at": datetime.utcnow(),
            "created_by": created_by
        })

def update_news_post(id, title, category, content, meta, is_public):
    with Cursor() as c:
        c.update("newsposts", id, {
            "title": title,
            "category": category,
            "content": content,
            "meta": c.json(meta),
            "is_public": is_public,
        })

