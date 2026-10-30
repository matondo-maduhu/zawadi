"""Katalogi ya templates (40+) za Zawadi Kiganjani.

Kila template ina:
  - fomu (schema) kwenye catalog/catalog.json  -> ukurasa wa kujaza hutengenezwa kutoka hapa
  - skeleton ya HTML kwenye catalog/pages/<id>.html (ina alama @@HEAD@@, @@THEME@@, @@DATA@@)

Seva huthibitisha data ya mtumiaji dhidi ya fomu, kisha hubadilisha alama hizo na kurudisha ukurasa
kamili (faili moja la HTML, linalojitegemea). Hakuna msimbo wa mtumiaji unaotekelezwa: data huingia kama JSON salama.

Kubadilisha au kuongeza template: hariri tools/templates-src.js, kisha endesha  node tools/build_catalog.js
"""
import html
import json
import re
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).parent / "catalog"

IMG_RE = re.compile(r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_IMG = 700_000          # herufi kwa kila picha (baada ya kupunguzwa kwenye kivinjari)
MAX_IMAGES = 14            # picha nyingi kwa kila sehemu ya "images"
MAX_TOTAL_IMG = 8_500_000  # jumla ya picha zote kwenye zawadi moja


@lru_cache(maxsize=1)
def _load():
    cat = json.loads((BASE / "catalog.json").read_text(encoding="utf-8"))
    cat["by_id"] = {t["id"]: t for t in cat["templates"]}
    return cat


def catalog():
    return _load()


def get(tid):
    return _load()["by_id"].get(tid)


def public_list():
    """Orodha fupi kwa ukurasa wa mwanzo na wa templates (bila fomu nzima)."""
    return [{"id": t["id"], "e": t["e"], "n": t["n"], "d": t["d"], "cats": t["cats"]}
            for t in _load()["templates"]]


def categories():
    return _load()["cats"]


@lru_cache(maxsize=64)
def _skeleton(tid):
    return (BASE / "pages" / (tid + ".html")).read_text(encoding="utf-8")


def _text(v, limit):
    v = CTRL_RE.sub("", str(v if v is not None else "")).replace("\r\n", "\n").replace("\r", "\n")
    return v.strip()[:limit]


def validate(tid, raw):
    """Huthibitisha data. Hurudisha (data, kosa). Sehemu zisizojulikana hupuuzwa; zilizokosekana hupata thamani ya mfano."""
    t = get(tid)
    if not t:
        return None, "Template haijapatikana."
    if not isinstance(raw, dict):
        return None, "Data si sahihi."
    out, total = {}, 0
    for f in t["fields"]:
        k, ty, d = f["k"], f["t"], f.get("d")
        v = raw.get(k, d)
        if ty == "image":
            v = v if isinstance(v, str) and len(v) <= MAX_IMG and IMG_RE.fullmatch(v) else ""
            total += len(v)
        elif ty == "images":
            v = [p for p in (v if isinstance(v, list) else [])[:MAX_IMAGES]
                 if isinstance(p, str) and len(p) <= MAX_IMG and IMG_RE.fullmatch(p)]
            total += sum(len(p) for p in v)
        elif ty == "select":
            ok = [o[0] for o in (f.get("o") or [])]
            v = v if v in ok else d
        elif ty == "date":
            v = v if isinstance(v, str) and DATE_RE.fullmatch(v) else ""
        elif ty == "datetime-local":
            v = v if isinstance(v, str) and DT_RE.fullmatch(v) else ""
        elif ty == "tel":
            v = re.sub(r"[^0-9+ ]", "", str(v or ""))[:20]
        elif ty == "textarea":
            v = _text(v, int(f.get("max") or 3000))
        else:
            v = _text(v, int(f.get("max") or 200)).replace("\n", " ")
            if k == "link" and not re.match(r"https?://", v, re.I):   # viungo vya nje: http(s) tu
                v = ""
        out[k] = v
    if total > MAX_TOTAL_IMG:
        return None, "Picha ni nyingi/kubwa mno. Punguza idadi ya picha."
    return out, None


def who(tid, data):
    """(to_raw, from_raw) kwa ukurasa wa mmiliki na onyesho la link."""
    if data.get("to"):
        to = data["to"]
    elif data.get("mke"):
        to = (data["mke"] + " & " + data.get("mume", "")).strip(" &")
    else:
        to = data.get("who") or data.get("name") or data.get("ttl") or (get(tid) or {}).get("n", "Zawadi")
    return to[:40], str(data.get("from") or "")[:40]


def og_title(tid, to_raw, from_raw):
    t = get(tid) or {}
    if any(f["k"] == "to" for f in t.get("fields", [])) and "bz" not in t.get("cats", []):
        return "🎁 %s amekutumia zawadi, %s" % (from_raw or "Mtu fulani", to_raw)
    return "%s %s" % (t.get("e", "✨"), to_raw)


def _json_safe(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def render(tid, data):
    """Hurudisha ukurasa kamili wa HTML kwa template + data (iliyothibitishwa)."""
    t = get(tid)
    cat = _load()
    th = cat["themes"].get(data.get("theme")) or cat["themes"]["usiku"]
    theme = "--b0:%s;--b1:%s;--ac:%s;--ac2:%s" % tuple(th)
    to_raw, from_raw = who(tid, data)
    title = og_title(tid, to_raw, from_raw)
    head = ('<title>%s</title><meta property="og:title" content="%s">'
            '<meta property="og:description" content="Bonyeza kufungua 🎁">'
            '<meta name="robots" content="noindex">') % (html.escape(title), html.escape(title, quote=True))
    payload = dict(data)
    payload.update(t["base"])
    page = _skeleton(tid)
    return (page.replace("@@HEAD@@", head).replace("@@THEME@@", theme)
                .replace("@@DATA@@", _json_safe(payload)))
