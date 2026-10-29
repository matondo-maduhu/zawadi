"""Zawadi Kiganjani - seva ya Flask.

Kuendesha kwenye kompyuta:
    pip install -r requirements.txt
    python app.py          # kisha fungua http://localhost:5000

Njia kuu:
    /                         ukurasa wa mwanzo
    /create                   ukurasa wa kutengeneza zawadi
    /g/<id>                   zawadi yenyewe (link ya kutuma)
    /m/<id>?t=<token>         ukurasa wa mmiliki (kuona kama amefungua, kufuta)
    POST /api/generate        hutengeneza faili la HTML (onyesho/kupakua)
    POST /api/gifts           huhifadhi zawadi na kurudisha link
    POST /api/gifts/<id>/delete   hufuta zawadi (inahitaji token)
"""
import hashlib
import html
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import db
from pwa import bp as pwa_bp

BASE = Path(__file__).parent
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # nyuma ya Render/Nginx
app.register_blueprint(pwa_bp)                      # manifest + ikoni (angalia pwa.py)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # ukubwa wa juu wa ombi (12 MB)

IMG_RE = re.compile(r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+")
AUD_RE = re.compile(r"data:audio/[\w.+-]+(;codecs=[\w.,+-]+)?;base64,[A-Za-z0-9+/=]+")
MAX_IMG = 1_200_000     # herufi kwa kila picha
MAX_AUDIO = 3_000_000   # herufi kwa sauti
MAX_PHOTOS = 3
BOTS = ("whatsapp", "facebookexternalhit", "twitterbot", "telegrambot", "slackbot",
        "googlebot", "bingbot", "linkedinbot", "discordbot", "crawler", "preview", "bot/")
EAT = timezone(timedelta(hours=3))
EMOJIS = ["❤️", "😍", "🥹", "😂", "🙏", "🎉", "💙", "🤗"]
CONTACT = os.environ.get("CONTACT_EMAIL", "")
RATE_LIMIT, RATE_WINDOW = 15, 3600   # zawadi 15 kwa saa kwa kila IP
_hits = {}

def _asset_version():
    """Kitambulisho cha toleo: hubadilika mafaili ya kurasa yakibadilika, ili simu zipakue toleo jipya."""
    h = hashlib.md5()
    for name in ("templates/index.html", "templates/create.html", "templates/offline.html",
                 "templates/sw.js", "pwa.py"):
        h.update((BASE / name).read_bytes())
    return h.hexdigest()[:10]


ASSET_VERSION = _asset_version()

db.init()


# ---------------------------------------------------------------- msaada
def load_events():
    import json
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((BASE / "events").glob("*.json"))]


def load_styles():
    import json
    return json.loads((BASE / "styles.json").read_text(encoding="utf-8"))


def public_event(e):
    return {k: e[k] for k in ("id", "e", "n", "f")}


def clean(text, limit):
    """Hukata urefu na kuzuia msimbo hatari (HTML) kwenye maandishi ya mtumiaji."""
    return html.escape(str(text or "").strip()[:limit], quote=True)


def rate_ok(ip):
    now = time.time()
    hits = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    if len(hits) >= RATE_LIMIT:
        _hits[ip] = hits
        return False
    hits.append(now)
    _hits[ip] = hits
    return True


def parse_open(value):
    """Hubadilisha 'YYYY-MM-DDTHH:MM' (saa za EAT) kuwa sekunde. Hurudisha (ts, kosa)."""
    if not value:
        return None, None
    try:
        ts = int(datetime.fromisoformat(str(value)[:16]).replace(tzinfo=EAT).timestamp())
    except ValueError:
        return None, "Tarehe si sahihi."
    now = int(time.time())
    if ts <= now + 60:
        return None, "Chagua tarehe iliyo mbele."
    if ts > now + (db.TTL_DAYS - 1) * 86400:
        return None, "Tarehe ni mbali mno. Kikomo ni siku %d kuanzia leo." % (db.TTL_DAYS - 1)
    return ts, None


def build_cfg(data):
    """Huthibitisha data ya mtumiaji. Hurudisha (kila kitu, kosa)."""
    events = {e["id"]: e for e in load_events()}
    styles = {s["id"]: s for s in load_styles()}
    ev = events.get(data.get("event"))
    style = styles.get(data.get("style"))
    if not ev:
        return None, "Tukio halijachaguliwa."
    if not style:
        return None, "Mtindo haujachaguliwa."
    to_raw = str(data.get("to") or "").strip()[:40]
    from_raw = str(data.get("from") or "").strip()[:40]
    if not to_raw:
        return None, "Andika jina la mpokeaji."

    photos = [p for p in (data.get("ph") or [])[:MAX_PHOTOS]
              if isinstance(p, str) and len(p) <= MAX_IMG and IMG_RE.fullmatch(p)]
    audio = data.get("au")
    if not (isinstance(audio, str) and len(audio) <= MAX_AUDIO and AUD_RE.fullmatch(audio)):
        audio = None
    memories = (data.get("m") or [])[:3]
    memories = [clean(m, 300) for m in memories] + [""] * (3 - len(memories))

    cfg = {
        "to": clean(to_raw, 40), "from": clean(from_raw, 40), "m": memories,
        "ph": photos, "au": audio,
        "ev": {"e": ev["e"], "th": ev["th"], "dodge": ev.get("dodge", 0)},
        "P": ev["P"], "C": ev["C"], "Q": ev["Q"],
    }
    return {"cfg": cfg, "style": style["id"], "event": ev["id"], "to_raw": to_raw, "from_raw": from_raw}, None


def og_title(to_raw, from_raw):
    who = from_raw or "Mtu fulani"
    return "🎁 %s amekutumia zawadi, %s" % (who, to_raw)


def render_gift(style, cfg, to_raw, from_raw):
    return render_template("gifts/%s.html" % style, cfg=cfg, to_raw=to_raw,
                           og_title=og_title(to_raw, from_raw))


def eat(ts):
    """Muda wa Afrika Mashariki (UTC+3)."""
    if not ts:
        return "-"
    return (datetime.fromtimestamp(ts, timezone.utc) + timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")


def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------- kurasa
@app.route("/")
def index():
    return render_template("index.html", events=load_events(), styles=load_styles())


@app.route("/create")
def create():
    return render_template("create.html",
                           events=[public_event(e) for e in load_events()],
                           styles=load_styles(), ttl=db.TTL_DAYS)


@app.route("/g/<gid>")
def view_gift(gid):
    g = db.get_gift(gid)
    if not g:
        abort(404)
    now = int(time.time())
    if g.get("open_at") and now < g["open_at"]:        # bado imefungwa: onyesha kuhesabu muda
        page = render_template("waiting.html", to=g["to_raw"], frm=g["from_raw"], open_at=g["open_at"],
                               now=now, og_title=og_title(g["to_raw"], g["from_raw"]))
        resp = app.response_class(page, mimetype="text/html")
        resp.headers["X-Robots-Tag"] = "noindex"
        return no_cache(resp)
    ua = (request.headers.get("User-Agent") or "").lower()
    if not any(b in ua for b in BOTS):          # usihesabu roboti za onyesho la link
        db.record_view(gid)
    cfg = dict(g["cfg"], gid=gid)
    resp = app.response_class(render_gift(g["style"], cfg, g["to_raw"], g["from_raw"]), mimetype="text/html")
    resp.headers["X-Robots-Tag"] = "noindex"
    return no_cache(resp)


@app.route("/m/<gid>")
def manage(gid):
    g = db.get_gift(gid)
    token = request.args.get("t", "")
    if not g or not secrets.compare_digest(token, g["token"]):
        abort(404)
    events = {e["id"]: e for e in load_events()}
    ev = events.get(g["event"], {})
    return no_cache(app.response_class(render_template(
        "manage.html", gid=gid, token=token, g=g, ev=ev,
        url=url_for("view_gift", gid=gid, _external=True),
        created=eat(g["created"]), first=eat(g["first_view"]), last=eat(g["last_view"]),
        opens=eat(g["open_at"]) if g.get("open_at") else None,
        replies=[dict(r, time=eat(r["created"])) for r in db.list_replies(gid)],
        ttl=db.TTL_DAYS), mimetype="text/html"))


# ---------------------------------------------------------------- PWA
@app.route("/sw.js")
def service_worker():
    resp = app.response_class(render_template("sw.js", version=ASSET_VERSION), mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"            # simu zisikae na service worker ya zamani
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


@app.route("/pwa-check")
def pwa_check():
    """Ukurasa wa kuchunguza kwa nini app haisakinishwi."""
    return render_template("pwa_check.html")


@app.route("/offline")
def offline():
    return render_template("offline.html")


@app.route("/terms")
def terms():
    return render_template("legal.html", page="terms", contact=CONTACT, ttl=db.TTL_DAYS)


@app.route("/privacy")
def privacy():
    return render_template("legal.html", page="privacy", contact=CONTACT, ttl=db.TTL_DAYS)


@app.route("/robots.txt")
def robots():
    return app.response_class("User-agent: *\nDisallow: /g/\nDisallow: /m/\nDisallow: /api/\n", mimetype="text/plain")


# ---------------------------------------------------------------- API
@app.post("/api/generate")
def generate():
    """Hutengeneza faili la zawadi (kwa onyesho na kupakua). Haihifadhi chochote."""
    built, err = build_cfg(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    page = render_gift(built["style"], built["cfg"], built["to_raw"], built["from_raw"])
    return no_cache(app.response_class(page, mimetype="text/html"))


@app.post("/api/gifts")
def create_gift():
    """Huhifadhi zawadi na kurudisha link ya kutuma."""
    if not rate_ok(request.remote_addr or "?"):
        return jsonify(error="Umetengeneza zawadi nyingi kwa muda mfupi. Jaribu tena baadaye."), 429
    built, err = build_cfg(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    open_at, err = parse_open((request.get_json(silent=True) or {}).get("open"))
    if err:
        return jsonify(error=err), 400
    db.purge()
    gid, token = db.create_gift(built["style"], built["event"], built["to_raw"], built["from_raw"],
                                built["cfg"], open_at)
    return jsonify(
        id=gid, open_at=open_at,
        url=url_for("view_gift", gid=gid, _external=True),
        manage_url=url_for("manage", gid=gid, t=token, _external=True),
        days=db.TTL_DAYS), 201


@app.post("/api/gifts/<gid>/delete")
def delete_gift(gid):
    g = db.get_gift(gid)
    token = str((request.get_json(silent=True) or {}).get("t", ""))
    if not g or not secrets.compare_digest(token, g["token"]):
        return jsonify(error="Haikupatikana."), 404
    db.delete_gift(gid)
    return jsonify(ok=True)


@app.post("/api/gifts/<gid>/reply")
def reply(gid):
    """Mpokeaji hutuma jibu (emoji na/au ujumbe) kwa mtumaji."""
    g = db.get_gift(gid)
    if not g or (g.get("open_at") and time.time() < g["open_at"]):
        return jsonify(error="Haikupatikana."), 404
    if not rate_ok("reply:" + (request.remote_addr or "?")):
        return jsonify(error="Umetuma majibu mengi. Jaribu tena baadaye."), 429
    data = request.get_json(silent=True) or {}
    msg = clean(data.get("m"), 300)
    emoji = data.get("e") if data.get("e") in EMOJIS else ""
    if not msg and not emoji:
        return jsonify(error="Chagua emoji au andika ujumbe."), 400
    if not db.add_reply(gid, msg, emoji):
        return jsonify(error="Umeshatuma majibu mengi kwa zawadi hii."), 429
    return jsonify(ok=True), 201


# ---------------------------------------------------------------- makosa
@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="Faili ni kubwa mno. Tumia picha ndogo au sauti fupi."), 413


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
