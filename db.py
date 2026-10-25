"""Hifadhidata ya zawadi (SQLite). Kila zawadi huhifadhiwa kama safu moja yenye data yote ya JSON.

Mazingira (environment variables):
    DATABASE_PATH   njia ya faili la hifadhidata (kawaida: data/zawadi.db)
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
    last_view  INTEGER
)
"""


def _conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _run(sql, args=(), fetch=False):
    with closing(_conn()) as c:
        cur = c.execute(sql, args)
        rows = cur.fetchall() if fetch else None
        c.commit()
        return rows


def init():
    _run(SCHEMA)
    purge()


def purge():
    """Hufuta zawadi zilizozidi muda wake (faragha + nafasi)."""
    cutoff = int(time.time()) - TTL_DAYS * 86400
    _run("DELETE FROM gifts WHERE created < ?", (cutoff,))


def create_gift(style, event, to_raw, from_raw, cfg):
    """Huhifadhi zawadi, hurudisha (id, token)."""
    token = secrets.token_urlsafe(16)
    for _ in range(8):
        gid = secrets.token_urlsafe(6).replace("_", "x").replace("-", "y")
        try:
            _run("INSERT INTO gifts(id,token,style,event,to_raw,from_raw,cfg,created) VALUES(?,?,?,?,?,?,?,?)",
                 (gid, token, style, event, to_raw, from_raw, json.dumps(cfg, ensure_ascii=False), int(time.time())))
            return gid, token
        except sqlite3.IntegrityError:
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
    _run("DELETE FROM gifts WHERE id=?", (gid,))
