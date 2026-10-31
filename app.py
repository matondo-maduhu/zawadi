"""Zawadi Kiganjani - seva ya Flask.

Kuendesha kwenye kompyuta:
    pip install -r requirements.txt
    python app.py          # kisha fungua http://localhost:5000

Njia kuu:
    /                         ukurasa wa mwanzo (na kitufe cha kusakinisha app)
    /create                   kutengeneza zawadi: tukio x mtindo (kitabu, kadi, simu), sauti, tarehe maalum
    /templates                orodha ya templates 40 (kuchuja na kutafuta)
    /t/<template>             kujaza taarifa za template moja
    /g/<id>                   zawadi yenyewe (link ya kutuma); kabla ya tarehe maalum huonyesha ukurasa wa kusubiri
    /m/<id>?t=<token>         ukurasa wa mmiliki (alifungua lini, majibu, kufuta)
    /terms  /privacy          masharti na faragha
    /offline  /sw.js          PWA (huduma ya nje ya mtandao)  |  /pwa-check  ukaguzi wa PWA
    /manifest.webmanifest  /icons/<jina>   PWA (kutoka pwa.py, hakuna folda ya static inayohitajika)
    POST /api/generate        hutengeneza faili la HTML (onyesho/kupakua)
    POST /api/gifts           huhifadhi zawadi (inahitaji makubaliano) na kurudisha link
    POST /api/t/<id>/generate hutengeneza HTML ya template (onyesho/kupakua)
    POST /api/t/<id>/gifts    huhifadhi zawadi ya template na kurudisha link
    POST /api/gifts/<id>/reply    jibu la mpokeaji (emoji + ujumbe mfupi)
    POST /api/gifts/<id>/delete   hufuta zawadi (inahitaji token)
"""
import hashlib
import html
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, make_response, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import catalog
import db
import pwa

BASE = Path(__file__).parent
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # nyuma ya Render/Nginx
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # ukubwa wa juu wa ombi (12 MB)
app.register_blueprint(pwa.bp)                        # /manifest.webmanifest na /icons/<jina>

IMG_RE = re.compile(r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+")
AUD_RE = re.compile(r"data:audio/[\w.+-]+(;codecs=[\w.,+-]+)?;base64,[A-Za-z0-9+/=]+")
CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_IMG = 1_200_000     # herufi kwa kila picha
MAX_AUDIO = 3_000_000   # herufi kwa sauti
MAX_PHOTOS = 3
REPLY_EMOJI = ("❤️", "😍", "🥹", "😂", "🙏", "🎉", "💙", "🤗")
BOTS = ("whatsapp", "facebookexternalhit", "twitterbot", "telegrambot", "slackbot",
        "googlebot", "bingbot", "linkedinbot", "discordbot", "crawler", "preview", "bot/")
RATE_LIMIT, RATE_WINDOW = 15, 3600   # zawadi 15 kwa saa kwa kila IP
REPLY_LIMIT = 12                      # majibu 12 kwa saa kwa kila IP
CONTACT = os.environ.get("CONTACT_EMAIL", "")   # barua pepe ya mawasiliano kwenye ukurasa wa masharti
_hits, _rhits = {}, {}

db.init()


# ---------------------------------------------------------------- msaada
def load_events():
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((BASE / "events").glob("*.json"))]


def load_styles():
    return json.loads((BASE / "styles.json").read_text(encoding="utf-8"))


def public_event(e):
    return {k: e[k] for k in ("id", "e", "n", "f")}


def clean(text, limit):
    """Hukata urefu na kuzuia msimbo hatari (HTML) kwenye maandishi ya mtumiaji."""
    return html.escape(str(text or "").strip()[:limit], quote=True)


def _limit_ok(store, key, limit):
    now = time.time()
    hits = [t for t in store.get(key, []) if now - t < RATE_WINDOW]
    if len(hits) >= limit:
        store[key] = hits
        return False
    hits.append(now)
    store[key] = hits
    return True


def rate_ok(ip):
    return _limit_ok(_hits, ip, RATE_LIMIT)


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


def parse_open(value):
    """Tarehe maalum ya kufunguka ("YYYY-MM-DDTHH:MM", saa za Afrika Mashariki). Hurudisha (epoch|None, kosa)."""
    value = str(value or "").strip()
    if not value:
        return None, None
    try:
        dt = datetime.strptime(value[:16], "%Y-%m-%dT%H:%M")
    except ValueError:
        return None, "Tarehe ya kufunguka si sahihi."
    ts = int(dt.replace(tzinfo=timezone(timedelta(hours=3))).timestamp())
    now = int(time.time())
    if ts < now + 60:
        return None, "Tarehe ya kufunguka lazima iwe baadaye."
    if ts > now + (db.TTL_DAYS - 1) * 86400:
        return None, "Tarehe ya kufunguka ni mbali mno. Zawadi huhifadhiwa siku %d, chagua tarehe ndani ya siku %d." % (
            db.TTL_DAYS, db.TTL_DAYS - 1)
    return ts, None


def check_save(data):
    """Makubaliano + tarehe maalum kwa kuhifadhi link. Hurudisha (open_at, kosa)."""
    if data.get("agree") is not True:
        return None, "Kubali Masharti na Faragha kwanza."
    return parse_open(data.get("open"))


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


def _version():
    """Toleo la service worker: hubadilika kila sw.js au manifest inapobadilika (cache husasishwa yenyewe)."""
    try:
        raw = (BASE / "templates" / "sw.js").read_bytes() + json.dumps(pwa.MANIFEST, sort_keys=True).encode()
    except OSError:
        raw = b"0"
    return os.environ.get("APP_VERSION") or hashlib.md5(raw).hexdigest()[:8]


APP_VERSION = _version()


# ---------------------------------------------------------------- kurasa
@app.route("/")
def index():
    tpls = catalog.public_list()
    return render_template("index.html", events=load_events(), styles=load_styles(),
                           tpls=tpls[:12], tpl_total=len(tpls))


@app.route("/create")
def create():
    return render_template("create.html",
                           events=[public_event(e) for e in load_events()],
                           styles=load_styles(), ttl=db.TTL_DAYS)


@app.route("/templates")
def templates_page():
    return render_template("catalog.html", tpls=catalog.public_list(), cats=catalog.categories())


@app.route("/t/<tid>")
def template_fill(tid):
    t = catalog.get(tid)
    if not t:
        abort(404)
    return render_template("fill.html", t=t, themes=catalog.catalog()["themes"], ttl=db.TTL_DAYS)


@app.route("/terms")
def terms():
    return render_template("legal.html", page="terms", contact=CONTACT, ttl=db.TTL_DAYS)


@app.route("/privacy")
def privacy():
    return render_template("legal.html", page="privacy", contact=CONTACT, ttl=db.TTL_DAYS)


@app.route("/offline")
def offline():
    return render_template("offline.html")


@app.route("/pwa-check")
def pwa_check():
    return no_cache(app.response_class(render_template("pwa_check.html"), mimetype="text/html"))


@app.route("/sw.js")
def service_worker():
    resp = make_response(render_template("sw.js", version=APP_VERSION))
    resp.mimetype = "application/javascript"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


@app.route("/g/<gid>")
def view_gift(gid):
    g = db.get_gift(gid)
    if not g:
        abort(404)
    now = int(time.time())
    open_at = g["open_at"] if "open_at" in g.keys() else None
    if open_at and now < open_at:               # bado haijafika wakati: ukurasa wa kusubiri (haihesabiwi kama kufunguliwa)
        resp = app.response_class(render_template(
            "waiting.html", og_title=og_title(g["to_raw"], g["from_raw"]),
            to=g["to_raw"], frm=g["from_raw"], open_at=open_at, now=now), mimetype="text/html")
        resp.headers["X-Robots-Tag"] = "noindex"
        return no_cache(resp)
    ua = (request.headers.get("User-Agent") or "").lower()
    if not any(b in ua for b in BOTS):          # usihesabu roboti za onyesho la link
        db.record_view(gid)
    if g["style"] == "tpl":                      # zawadi ya template (katalogi)
        if not catalog.get(g["event"]):
            abort(404)
        page = catalog.render(g["event"], g["cfg"].get("d", {}))
    else:
        cfg = dict(g["cfg"])
        cfg["gid"] = gid                          # kisanduku cha majibu kinahitaji gid
        page = render_gift(g["style"], cfg, g["to_raw"], g["from_raw"])
    resp = app.response_class(page, mimetype="text/html")
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
    if g["style"] == "tpl":
        t = catalog.get(g["event"]) or {}
        ev = {"e": t.get("e", "🎁"), "n": t.get("n", "Template")}
    open_at = g["open_at"] if "open_at" in g.keys() else None
    replies = [{"emoji": r["emoji"], "msg": r["msg"], "time": eat(r["created"])} for r in db.list_replies(gid)]
    return no_cache(app.response_class(render_template(
        "manage.html", gid=gid, token=token, g=g, ev=ev,
        url=url_for("view_gift", gid=gid, _external=True),
        created=eat(g["created"]), first=eat(g["first_view"]), last=eat(g["last_view"]),
        opens=eat(open_at) if open_at else "", replies=replies,
        ttl=db.TTL_DAYS), mimetype="text/html"))


@app.route("/robots.txt")
def robots():
    return app.response_class("User-agent: *\nDisallow: /g/\nDisallow: /m/\nDisallow: /api/\n", mimetype="text/plain")


# ---------------------------------------------------------------- API
def _links(gid, token):
    return dict(id=gid,
                url=url_for("view_gift", gid=gid, _external=True),
                manage_url=url_for("manage", gid=gid, t=token, _external=True),
                days=db.TTL_DAYS)


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
    data = request.get_json(silent=True) or {}
    built, err = build_cfg(data)
    if err:
        return jsonify(error=err), 400
    open_at, err = check_save(data)
    if err:
        return jsonify(error=err), 400
    db.purge()
    gid, token = db.create_gift(built["style"], built["event"], built["to_raw"], built["from_raw"],
                                built["cfg"], open_at)
    return jsonify(dict(_links(gid, token), opens=eat(open_at) if open_at else "")), 201


@app.post("/api/t/<tid>/generate")
def tpl_generate(tid):
    """Hutengeneza HTML ya template (kwa onyesho na kupakua). Haihifadhi chochote."""
    data, err = catalog.validate(tid, (request.get_json(silent=True) or {}).get("d"))
    if err:
        return jsonify(error=err), 400
    return no_cache(app.response_class(catalog.render(tid, data), mimetype="text/html"))


@app.post("/api/t/<tid>/gifts")
def tpl_create(tid):
    """Huhifadhi zawadi ya template na kurudisha link ya kutuma."""
    if not rate_ok(request.remote_addr or "?"):
        return jsonify(error="Umetengeneza zawadi nyingi kwa muda mfupi. Jaribu tena baadaye."), 429
    body = request.get_json(silent=True) or {}
    data, err = catalog.validate(tid, body.get("d"))
    if err:
        return jsonify(error=err), 400
    open_at, err = check_save(body)
    if err:
        return jsonify(error=err), 400
    to_raw, from_raw = catalog.who(tid, data)
    db.purge()
    gid, token = db.create_gift("tpl", tid, to_raw, from_raw, {"t": tid, "d": data}, open_at)
    return jsonify(dict(_links(gid, token), opens=eat(open_at) if open_at else "")), 201


@app.post("/api/gifts/<gid>/reply")
def reply(gid):
    """Jibu la mpokeaji: emoji moja ya orodha na/au ujumbe mfupi (herufi 300)."""
    if not db.get_gift(gid):
        return jsonify(error="Haikupatikana."), 404
    if not _limit_ok(_rhits, (request.remote_addr or "?"), REPLY_LIMIT):
        return jsonify(error="Umetuma majibu mengi. Jaribu tena baadaye."), 429
    body = request.get_json(silent=True) or {}
    msg = CTRL_RE.sub("", str(body.get("m") or "")).strip()[:300]
    emoji = body.get("e") if body.get("e") in REPLY_EMOJI else ""
    if not msg and not emoji:
        return jsonify(error="Andika ujumbe au chagua emoji."), 400
    if not db.add_reply(gid, msg, emoji):
        return jsonify(error="Majibu yamefika kikomo."), 409
    return jsonify(ok=True), 201


@app.post("/api/gifts/<gid>/delete")
def delete_gift(gid):
    g = db.get_gift(gid)
    token = str((request.get_json(silent=True) or {}).get("t", ""))
    if not g or not secrets.compare_digest(token, g["token"]):
        return jsonify(error="Haikupatikana."), 404
    db.delete_gift(gid)
    return jsonify(ok=True)


# ---------------------------------------------------------------- makosa
@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="Faili ni kubwa mno. Tumia picha ndogo au sauti fupi."), 413


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
