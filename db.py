"""Hifadhidata ya zawadi (SQLite). Kila zawadi huhifadhiwa kama safu moja yenye data yote ya JSON.

Mazingira (environment variables):
    DATABASE_URL    anwani ya Postgres (mfano kwenye Railway/Render). Ikiwekwa, Postgres inatumika.
    DATABASE_PATH   njia ya faili la SQLite (kawaida: data/zawadi.db). Hutumika DATABASE_URL isipokuwepo.
    GIFT_TTL_DAYS   zawadi hufutwa baada ya siku ngapi (kawaida: 90)
"""
import json
import os
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = os.environ.get("DATABASE_PATH", str(BASE / "data" / "zawadi.db"))
DATABASE_URL = os.environ.get("DATABASE_URL")
PG = bool(DATABASE_URL)
if PG:
    import psycopg2
    import psycopg2.extras
    IntegrityError = psycopg2.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError
TTL_DAYS = int(os.environ.get("GIFT_TTL_DAYS", "90"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS gifts (
    id         TEXT PRIMARY KEY,
    token      TEXT NOT NULL,
    style      TEXT NOT NULL,
    event      TEXT NOT NULL,
    to_raw     TEXT NOT NULL,
    from_raw   TEXT NOT NULL,
    cfg        TEXT NOT NULL,
    created    INTEGER NOT NULL,
    views      INTEGER NOT NULL DEFAULT 0,
    first_view INTEGER,
    last_view  INTEGER,
    open_at    INTEGER
)
"""
REPLIES = """
CREATE TABLE IF NOT EXISTS replies (
    id      TEXT PRIMARY KEY,
    gid     TEXT NOT NULL,
    msg     TEXT NOT NULL,
    emoji   TEXT NOT NULL,
    created INTEGER NOT NULL
)
"""
REPLY_MAX = 10   # majibu ya juu kwa kila zawadi


def _conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _run(sql, args=(), fetch=False):
    if PG:
        return _run_pg(sql, args, fetch)
    with closing(_conn()) as c:
        cur = c.execute(sql, args)
        rows = cur.fetchall() if fetch else None
        c.commit()
        return rows


def _run_pg(sql, args, fetch):
    """Postgres: '?' hubadilishwa kuwa '%s', na INTEGER ya muda kuwa BIGINT."""
    sql = sql.replace("?", "%s")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, args)
                return cur.fetchall() if fetch else None
    finally:
        conn.close()


def init():
    fix = (lambda q: q.replace("INTEGER", "BIGINT")) if PG else (lambda q: q)
    _run(fix(SCHEMA))
    _run(fix(REPLIES))
    _migrate()
    purge()


def _migrate():
    """Huongeza safu mpya kwenye hifadhidata ya zamani (salama kuendesha mara nyingi)."""
    if PG:
        _run("ALTER TABLE gifts ADD COLUMN IF NOT EXISTS open_at BIGINT")
        return
    cols = [r["name"] for r in _run("PRAGMA table_info(gifts)", fetch=True)]
    if "open_at" not in cols:
        _run("ALTER TABLE gifts ADD COLUMN open_at INTEGER")


def purge():
    """Hufuta zawadi zilizozidi muda wake (faragha + nafasi)."""
    cutoff = int(time.time()) - TTL_DAYS * 86400
    _run("DELETE FROM replies WHERE gid IN (SELECT id FROM gifts WHERE created < ?)", (cutoff,))
    _run("DELETE FROM gifts WHERE created < ?", (cutoff,))


def create_gift(style, event, to_raw, from_raw, cfg, open_at=None):
    """Huhifadhi zawadi, hurudisha (id, token)."""
    token = secrets.token_urlsafe(16)
    for _ in range(8):
        gid = secrets.token_urlsafe(6).replace("_", "x").replace("-", "y")
        try:
            _run("INSERT INTO gifts(id,token,style,event,to_raw,from_raw,cfg,created,open_at) VALUES(?,?,?,?,?,?,?,?,?)",
                 (gid, token, style, event, to_raw, from_raw, json.dumps(cfg, ensure_ascii=False), int(time.time()), open_at))
            return gid, token
        except IntegrityError:
            continue
    raise RuntimeError("Imeshindwa kutengeneza kitambulisho cha zawadi")


def get_gift(gid):
    """Hurudisha zawadi kama dict, au None kama haipo/imeisha muda."""
    rows = _run("SELECT * FROM gifts WHERE id=?", (gid,), fetch=True)
    if not rows:
        return None
    g = dict(rows[0])
    if g["created"] < int(time.time()) - TTL_DAYS * 86400:
        return None
    g["cfg"] = json.loads(g["cfg"])
    return g


def record_view(gid):
    now = int(time.time())
    _run("UPDATE gifts SET views=views+1, first_view=COALESCE(first_view,?), last_view=? WHERE id=?",
         (now, now, gid))


def delete_gift(gid):
    _run("DELETE FROM replies WHERE gid=?", (gid,))
    _run("DELETE FROM gifts WHERE id=?", (gid,))


def add_reply(gid, msg, emoji):
    """Huhifadhi jibu la mpokeaji. Hurudisha False kama majibu yamefika kikomo."""
    n = _run("SELECT COUNT(*) AS n FROM replies WHERE gid=?", (gid,), fetch=True)[0]["n"]
    if n >= REPLY_MAX:
        return False
    _run("INSERT INTO replies(id,gid,msg,emoji,created) VALUES(?,?,?,?,?)",
         (secrets.token_urlsafe(8), gid, msg, emoji, int(time.time())))
    return True


def list_replies(gid):
    rows = _run("SELECT msg,emoji,created FROM replies WHERE gid=? ORDER BY created", (gid,), fetch=True)
    return [dict(r) for r in rows]
