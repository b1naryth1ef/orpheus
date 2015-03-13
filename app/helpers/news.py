from database import Cursor
from datetime import datetime
from util.errors import APIError

from helpers.user import gache_user_info

NEWS_POST_ENTRY_FIELDS = { "title", "category", "content" }
NEWS_POSTS_FIELDS = "newsposts.id, newsposts.title, newsposts.category, newsposts.content, newsposts.is_public, newsposts.created_at, users.steamid"

GET_NEWS_POST_QUERY = """
    SELECT {0}
    FROM newsposts
    JOIN users ON (users.id = newsposts.created_by)
    WHERE newsposts.id=%s
"""

GET_NEWS_POSTS_QUERY = """
    SELECT {0}
    FROM newsposts
    JOIN users ON (newsposts.created_by = users.id)
    WHERE newsposts.is_public=true OR {1}
    ORDER BY newsposts.created_at
"""

UPDATE_NEWS_POST_QUERY = """
    UPDATE newsposts
    SET (title, category, content, meta, is_public) = (%s, %s, %s, %s, %s)
    WHERE id=%s
"""

def create_news_post(title, category, content, meta, is_public, created_by):
    with Cursor() as c:
        c.execute("SELECT COUNT (title) FROM newsposts WHERE title={0}".format(title))
        
        if c.fetchone().count > 0:
            raise APIError("There is already a news post with the same title. Title: {0}".format(title))
        
        c.insert("newsposts", {
            "title": title,
            "category": category,
            "content": content,
            "meta": c.json(meta),
            "is_public": is_public,
            "created_at": datetime.utcnow(),
            "created_by": created_by
        })
    return

def get_news_post(id, as_admin = False):
    record = None
    
    with Cursor() as c:
        c.execute(GET_NEWS_POST_QUERY.format(NEWS_POSTS_FIELDS), [id])
        
        record = c.fetchone()
    
    if not record:
        return None
    
    if not as_admin and not record.is_public:
        return None
    
    result = record_to_news_post(record)

    return result

def get_news_posts(active_only = True, as_admin = False):
    records = None
    
    with Cursor() as c:
        c.execute(GET_NEWS_POSTS_QUERY.format(NEWS_POSTS_FIELDS, not active_only))
        
        records = c.fetchall(as_list = True)
    
    if not records:
        return {}
    
    result = {}
    
    for record in records:
        if not as_admin and not record.is_public:
            continue
        
        result[record.id] = record_to_news_post(record)
    
    return result

def parse_json_news_post(data):
    empty_fields = [i for i in NEWS_POST_ENTRY_FIELDS if not data.get(i)]
    
    if len(empty_fields):
        raise APIError("Missing Fields: %s" % ', '.join(empty_fields))
    
    return data['id'], data['title'], data['category'], data['content'], data.get("is_pubic", False)

def record_to_news_post(record):
    user_info = gache_user_info(record.steamid)
    
    result = {
            "id": record.id,
            "title": record.title,
            "category": record.category,
            "content": record.content,
            "is_public": record.is_public,
            "created_at": int(record.created_at.strftime("%s")) if record.created_at else "Unknown",
            "created_by": user_info.get("personaname")
        }
    
    return result;

def update_news_post(id, title, category, content, meta, is_public):
    with Cursor() as c:        
        c.execute(UPDATE_NEWS_POST_QUERY, [title, category, content, meta, is_public, id])
    
    return

