"""Zawadi Kiganjani - seva ya Flask.

Kuendesha kwenye kompyuta:
    pip install -r requirements.txt
    python app.py          # kisha fungua http://localhost:5000
"""
import html
import json
import re
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE = Path(__file__).parent
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # ukubwa wa juu wa ombi (12 MB)

IMG_RE = re.compile(r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+")
AUD_RE = re.compile(r"data:audio/[\w.+-]+(;codecs=[\w.,+-]+)?;base64,[A-Za-z0-9+/=]+")
MAX_IMG = 1_200_000     # herufi kwa kila picha
MAX_AUDIO = 3_000_000   # herufi kwa sauti
MAX_PHOTOS = 3


def load_events():
    """Husoma matukio yote kutoka folda events/*.json (kila tukio ni faili lake)."""
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((BASE / "events").glob("*.json"))]


def load_styles():
    """Husoma mitindo kutoka styles.json (kila mtindo una templates/gifts/<id>.html)."""
    return json.loads((BASE / "styles.json").read_text(encoding="utf-8"))


def public_event(e):
    """Sehemu ya tukio inayoonyeshwa kwenye ukurasa wa kutengeneza."""
    return {k: e[k] for k in ("id", "e", "n", "f")}


def clean(text, limit):
    """Hukata urefu na kuzuia msimbo hatari (HTML) kwenye maandishi ya mtumiaji."""
    return html.escape(str(text or "").strip()[:limit], quote=True)


@app.route("/")
def index():
    return render_template("index.html", events=load_events(), styles=load_styles())


@app.route("/create")
def create():
    return render_template("create.html",
                           events=[public_event(e) for e in load_events()],
                           styles=load_styles())


@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    events = {e["id"]: e for e in load_events()}
    styles = {s["id"]: s for s in load_styles()}

    ev = events.get(data.get("event"))
    style = styles.get(data.get("style"))
    if not ev:
        return jsonify(error="Tukio halijachaguliwa."), 400
    if not style:
        return jsonify(error="Mtindo haujachaguliwa."), 400

    to_raw = str(data.get("to") or "").strip()[:40]
    if not to_raw:
        return jsonify(error="Andika jina la mpokeaji."), 400

    photos = [p for p in (data.get("ph") or [])[:MAX_PHOTOS]
              if isinstance(p, str) and len(p) <= MAX_IMG and IMG_RE.fullmatch(p)]
    audio = data.get("au")
    if not (isinstance(audio, str) and len(audio) <= MAX_AUDIO and AUD_RE.fullmatch(audio)):
        audio = None

    memories = (data.get("m") or [])[:3]
    memories = [clean(m, 300) for m in memories] + [""] * (3 - len(memories))

    cfg = {
        "to": clean(to_raw, 40),
        "from": clean(data.get("from"), 40),
        "m": memories,
        "ph": photos,
        "au": audio,
        "ev": {"e": ev["e"], "th": ev["th"], "dodge": ev.get("dodge", 0)},
        "P": ev["P"], "C": ev["C"], "Q": ev["Q"],
    }
    page = render_template("gifts/%s.html" % style["id"], cfg=cfg, to_raw=to_raw)
    resp = app.response_class(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="Faili ni kubwa mno. Tumia picha ndogo au sauti fupi."), 413


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
