import csv
import io
import json
from datetime import datetime, timezone

from db import get_connection
from url_utils import extract_words_from_url, extract_words_from_title
from search_utils import parse_query, get_variants


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --- Tag helpers ---

def _get_or_create_tag(conn, name):
    name = name.lower().strip()
    if not name:
        return None
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    return cur.lastrowid


def _set_tags_for_link(conn, link_id, tag_names):
    conn.execute("DELETE FROM link_tags WHERE link_id = ?", (link_id,))
    for name in tag_names:
        tag_id = _get_or_create_tag(conn, name)
        if tag_id:
            conn.execute(
                "INSERT OR IGNORE INTO link_tags (link_id, tag_id) VALUES (?, ?)",
                (link_id, tag_id),
            )


def _get_tags_for_link(conn, link_id):
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN link_tags lt ON t.id = lt.tag_id "
        "WHERE lt.link_id = ? ORDER BY t.name",
        (link_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _link_row_to_dict(conn, row):
    d = dict(row)
    d["tags"] = _get_tags_for_link(conn, d["id"])
    return d


# --- CRUD ---

def create_link(url, title="", description="", tags=None):
    conn = get_connection()
    try:
        auto_tags = extract_words_from_url(url)
        all_tags = list(set(auto_tags + (tags or [])))

        cur = conn.execute(
            "INSERT INTO links (url, title, description, date_added) VALUES (?, ?, ?, ?)",
            (url, title, description[:256], _today()),
        )
        link_id = cur.lastrowid
        _set_tags_for_link(conn, link_id, all_tags)
        conn.commit()
        return _link_row_to_dict(conn, conn.execute(
            "SELECT * FROM links WHERE id = ?", (link_id,)
        ).fetchone())
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_link(link_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
        if not row:
            return None
        return _link_row_to_dict(conn, row)
    finally:
        conn.close()


def list_links(sort_by="url", order="asc"):
    allowed_sort = {"url": "url", "title": "title"}
    col = allowed_sort.get(sort_by, "url")
    direction = "DESC" if order.lower() == "desc" else "ASC"

    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT * FROM links ORDER BY {col} {direction}"
        ).fetchall()
        return [_link_row_to_dict(conn, r) for r in rows]
    finally:
        conn.close()


def update_link(link_id, url=None, title=None, description=None, tags=None):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
        if not row:
            return None

        new_url = url if url is not None else row["url"]
        new_title = title if title is not None else row["title"]
        new_description = description[:256] if description is not None else row["description"]

        conn.execute(
            "UPDATE links SET url = ?, title = ?, description = ? WHERE id = ?",
            (new_url, new_title, new_description, link_id),
        )
        if tags is not None:
            _set_tags_for_link(conn, link_id, tags)
        conn.commit()
        return _link_row_to_dict(conn, conn.execute(
            "SELECT * FROM links WHERE id = ?", (link_id,)
        ).fetchone())
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_link(link_id):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM links WHERE id = ?", (link_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --- Search ---

def search_links(query_string, mode="and"):
    terms = parse_query(query_string)
    if not terms:
        return []

    conn = get_connection()
    try:
        if mode == "or":
            return _search_or(conn, terms)
        return _search_and(conn, terms)
    finally:
        conn.close()


def _search_and(conn, terms):
    """AND mode: link must match ALL positive terms, excluding negated terms."""
    positive = [t for t in terms if not t.get("negate")]
    negative = [t for t in terms if t.get("negate")]

    params = []

    if positive:
        subqueries = []
        for term in positive:
            variants = get_variants(term)
            placeholders = ",".join("?" for _ in variants)
            subqueries.append(
                f"SELECT lt.link_id FROM link_tags lt "
                f"JOIN tags t ON t.id = lt.tag_id "
                f"WHERE t.name IN ({placeholders})"
            )
            params.extend(variants)
        combined = " INTERSECT ".join(subqueries)
        sql = f"SELECT l.* FROM links l WHERE l.id IN ({combined})"
    else:
        sql = "SELECT l.* FROM links l WHERE 1=1"

    for term in negative:
        variants = get_variants(term)
        placeholders = ",".join("?" for _ in variants)
        sql += (
            f" AND l.id NOT IN ("
            f"SELECT lt.link_id FROM link_tags lt "
            f"JOIN tags t ON t.id = lt.tag_id "
            f"WHERE t.name IN ({placeholders}))"
        )
        params.extend(variants)

    sql += " ORDER BY l.date_added DESC"
    rows = conn.execute(sql, params).fetchall()
    return [_link_row_to_dict(conn, r) for r in rows]


def _search_or(conn, terms):
    """OR mode: link must match ANY positive term, excluding negated terms."""
    positive = [t for t in terms if not t.get("negate")]
    negative = [t for t in terms if t.get("negate")]

    params = []

    if positive:
        all_variants = []
        for term in positive:
            all_variants.extend(get_variants(term))
        placeholders = ",".join("?" for _ in all_variants)
        sql = (
            f"SELECT DISTINCT l.* FROM links l "
            f"JOIN link_tags lt ON l.id = lt.link_id "
            f"JOIN tags t ON t.id = lt.tag_id "
            f"WHERE t.name IN ({placeholders})"
        )
        params.extend(all_variants)
    else:
        sql = "SELECT DISTINCT l.* FROM links l WHERE 1=1"

    for term in negative:
        variants = get_variants(term)
        placeholders = ",".join("?" for _ in variants)
        sql += (
            f" AND l.id NOT IN ("
            f"SELECT lt.link_id FROM link_tags lt "
            f"JOIN tags t ON t.id = lt.tag_id "
            f"WHERE t.name IN ({placeholders}))"
        )
        params.extend(variants)

    sql += " ORDER BY l.date_added DESC"
    rows = conn.execute(sql, params).fetchall()
    return [_link_row_to_dict(conn, r) for r in rows]


# --- Click tracking ---

def record_click(link_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM links WHERE id = ?", (link_id,)).fetchone()
        if not row:
            return False
        now = _now_iso()
        conn.execute(
            "INSERT INTO click_history (link_id, clicked_at) VALUES (?, ?)",
            (link_id, now),
        )
        conn.execute(
            "UPDATE links SET last_clicked = ? WHERE id = ?",
            (now, link_id),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_recent_clicks(limit=5):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT l.* FROM links l "
            "JOIN ("
            "  SELECT link_id, MAX(clicked_at) as last_click "
            "  FROM click_history GROUP BY link_id "
            "  ORDER BY last_click DESC LIMIT ?"
            ") ch ON l.id = ch.link_id "
            "ORDER BY ch.last_click DESC",
            (limit,),
        ).fetchall()
        return [_link_row_to_dict(conn, r) for r in rows]
    finally:
        conn.close()


# --- Clear database ---

def clear_all():
    """Delete all links, tags, and click history."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM click_history")
        conn.execute("DELETE FROM link_tags")
        conn.execute("DELETE FROM links")
        conn.execute("DELETE FROM tags")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Import / Export ---

def bulk_import(bookmarks):
    """Import a list of {url, title, tags?} dicts. Skip duplicates."""
    conn = get_connection()
    imported = 0
    try:
        for bm in bookmarks:
            url = bm.get("url", "").strip()
            title = bm.get("title", "").strip()
            tags = bm.get("tags", [])
            if not url:
                continue

            existing = conn.execute(
                "SELECT id FROM links WHERE url = ?", (url,)
            ).fetchone()
            if existing:
                continue

            url_tags = extract_words_from_url(url)
            title_tags = extract_words_from_title(title) if title else []
            all_tags = list(set(url_tags + title_tags + tags))

            description = bm.get("description", "").strip()[:256]
            cur = conn.execute(
                "INSERT INTO links (url, title, description, date_added) VALUES (?, ?, ?, ?)",
                (url, title, description, _today()),
            )
            _set_tags_for_link(conn, cur.lastrowid, all_tags)
            imported += 1

        conn.commit()
        return imported
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def export_json():
    links = list_links()
    return json.dumps(links, indent=2)


def export_csv():
    links = list_links()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "title", "description", "tags", "date_added", "last_clicked"])
    for link in links:
        writer.writerow([
            link["id"],
            link["url"],
            link["title"],
            link["description"],
            ",".join(link["tags"]),
            link["date_added"],
            link["last_clicked"] or "",
        ])
    return output.getvalue()
