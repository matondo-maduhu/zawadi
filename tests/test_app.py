"""Majaribio ya Zawadi Kiganjani. Endesha:  python -m unittest discover -s tests -v
(Jaribio la sintaksia ya JavaScript hurukwa ikiwa Node.js haipo.)"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TMP = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(TMP, "test.db")
os.environ.pop("DATABASE_URL", None)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app as appmod  # noqa: E402
import catalog  # noqa: E402
import db  # noqa: E402

PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


def eat_future(hours):
    """Tarehe ya mbele kwa muundo wa fomu (saa za Afrika Mashariki)."""
    return (datetime.now(timezone.utc) + timedelta(hours=3 + hours)).strftime("%Y-%m-%dT%H:%M")


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        appmod._hits.clear()
        appmod._rhits.clear()
        cls.c = appmod.app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        appmod._hits.clear()
        appmod._rhits.clear()

    def post(self, url, body):
        return self.c.post(url, data=json.dumps(body), content_type="application/json")

    def old_body(self, **kw):
        ev, st = appmod.load_events()[0]["id"], appmod.load_styles()[0]["id"]
        b = {"event": ev, "style": st, "to": "Mama", "from": "Juma", "m": ["a", "b", "c"], "ph": [PNG], "agree": True}
        b.update(kw)
        return b

    # --------------------------------------------------------- usafi wa mradi (huzuia makosa ya kupakia)
    def test_repo_is_clean(self):
        junk = [p for p in ROOT.rglob("*") if p.is_file() and p.name.lower() == "me.html" and ".git" not in p.parts]
        self.assertEqual(junk, [], "Futa mafaili ya junk: %s" % junk)
        self.assertFalse((ROOT / "index.html").exists(), "index.html ya mzizi ni ya zamani, ifute")
        self.assertFalse((ROOT / "Static").exists(), "Folda ni 'static' (herufi ndogo), si 'Static'")

    def test_app_has_every_route_the_templates_need(self):
        rules = {r.rule for r in appmod.app.url_map.iter_rules()}
        for need in ("/", "/create", "/templates", "/t/<tid>", "/g/<gid>", "/m/<gid>", "/terms", "/privacy", "/offline",
                     "/sw.js", "/pwa-check", "/manifest.webmanifest", "/icons/<name>", "/api/gifts", "/api/generate",
                     "/api/t/<tid>/gifts", "/api/t/<tid>/generate", "/api/gifts/<gid>/reply", "/api/gifts/<gid>/delete"):
            self.assertIn(need, rules, need)

    # --------------------------------------------------------- kurasa na PWA
    def test_pages(self):
        for u in ("/", "/create", "/templates", "/terms", "/privacy", "/offline", "/pwa-check", "/robots.txt"):
            self.assertEqual(self.c.get(u).status_code, 200, u)
        self.assertIn("Templates 40", self.c.get("/templates").get_data(as_text=True))
        self.assertEqual(self.c.get("/t/haipo").status_code, 404)
        self.assertEqual(self.c.get("/ukurasa-usiokuwepo").status_code, 404)

    def test_pwa(self):
        m = self.c.get("/manifest.webmanifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.get_json()["name"], "Zawadi Kiganjani")
        for n in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon-32.png"):
            r = self.c.get("/icons/" + n)
            self.assertEqual((r.status_code, r.mimetype), (200, "image/png"), n)
            self.assertTrue(r.get_data().startswith(b"\x89PNG"), n)
        self.assertEqual(self.c.get("/icons/haipo.png").status_code, 404)
        sw = self.c.get("/sw.js")
        self.assertEqual((sw.status_code, sw.mimetype), (200, "application/javascript"))
        self.assertEqual(sw.headers.get("Service-Worker-Allowed"), "/")
        self.assertIn(appmod.APP_VERSION, sw.get_data(as_text=True))
        home = self.c.get("/").get_data(as_text=True)
        self.assertIn('href="/manifest.webmanifest"', home)
        self.assertIn("serviceWorker", home)
        self.assertIn("/terms", home)

    # --------------------------------------------------------- templates 40
    def test_catalog_size(self):
        self.assertGreaterEqual(len(catalog.public_list()), 40)

    def test_every_template_page_and_generate(self):
        for t in catalog.public_list():
            self.assertEqual(self.c.get("/t/" + t["id"]).status_code, 200, t["id"])
            r = self.post("/api/t/%s/generate" % t["id"], {"d": {}})   # data tupu -> thamani za mfano
            self.assertEqual(r.status_code, 200, t["id"])
            page = r.get_data(as_text=True)
            self.assertNotIn("@@", page, t["id"])
            self.assertIn("const D={", page, t["id"])
            self.assertTrue(page.startswith("<!DOCTYPE html>"))

    @unittest.skipUnless(shutil.which("node"), "Node.js haipo")
    def test_generated_js_syntax(self):
        for t in catalog.public_list():
            page = self.post("/api/t/%s/generate" % t["id"], {"d": {}}).get_data(as_text=True)
            js = re.search(r"<script>(.*)</script>", page, re.S).group(1)
            f = os.path.join(TMP, t["id"] + ".js")
            Path(f).write_text(js, encoding="utf-8")
            r = subprocess.run(["node", "--check", f], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, t["id"] + ": " + r.stderr[:300])

    # --------------------------------------------------------- kuhifadhi na makubaliano
    def test_save_requires_agreement(self):
        self.assertEqual(self.post("/api/t/harusi/gifts", {"d": {}}).status_code, 400)
        self.assertEqual(self.post("/api/t/harusi/gifts", {"d": {}, "agree": "ndiyo"}).status_code, 400)
        b = self.old_body()
        b.pop("agree")
        self.assertEqual(self.post("/api/gifts", b).status_code, 400)
        self.assertEqual(self.post("/api/gifts", self.old_body(agree=False)).status_code, 400)

    def test_save_view_manage_delete_template(self):
        r = self.post("/api/t/harusi/gifts", {"d": {"mke": "Asha", "mume": "Juma", "photo": PNG}, "agree": True})
        self.assertEqual(r.status_code, 201)
        j = r.get_json()
        gid = j["id"]
        v = self.c.get("/g/" + gid)
        self.assertEqual(v.status_code, 200)
        page = v.get_data(as_text=True)
        self.assertIn("<title>💒 Asha &amp; Juma</title>", page)
        self.assertIn('"mke":"Asha"', page)
        self.assertTrue(PNG in page)
        self.assertEqual(v.headers.get("X-Robots-Tag"), "noindex")
        m = self.c.get(j["manage_url"].replace("http://localhost", ""))
        self.assertEqual(m.status_code, 200)
        self.assertIn("Asha &amp; Juma", m.get_data(as_text=True))
        tok = re.search(r"t=([\w\-]+)", j["manage_url"]).group(1)
        self.assertEqual(self.c.get("/m/%s?t=bad" % gid).status_code, 404)
        self.assertEqual(self.post("/api/gifts/%s/delete" % gid, {"t": "bad"}).status_code, 404)
        self.assertEqual(self.post("/api/gifts/%s/delete" % gid, {"t": tok}).status_code, 200)
        self.assertEqual(self.c.get("/g/" + gid).status_code, 404)

    def test_old_flow_still_works(self):
        self.assertEqual(self.post("/api/generate", self.old_body()).status_code, 200)
        r = self.post("/api/gifts", self.old_body())
        self.assertEqual(r.status_code, 201)
        gid = r.get_json()["id"]
        page = self.c.get("/g/" + gid).get_data(as_text=True)
        self.assertRegex(page, r'"gid":\s*"%s"' % gid)   # kisanduku cha majibu kinahitaji gid
        self.assertEqual(self.post("/api/gifts", self.old_body(event="haipo")).status_code, 400)
        self.assertEqual(self.post("/api/gifts", self.old_body(to="")).status_code, 400)

    # --------------------------------------------------------- tarehe maalum (ukurasa wa kusubiri)
    def test_scheduled_open(self):
        r = self.post("/api/gifts", self.old_body(open=eat_future(5)))
        self.assertEqual(r.status_code, 201)
        j = r.get_json()
        self.assertTrue(j["opens"])
        gid = j["id"]
        w = self.c.get("/g/" + gid)
        self.assertEqual(w.status_code, 200)
        self.assertIn("Zawadi inakusubiri, Mama", w.get_data(as_text=True))
        self.assertNotIn("Mama amekutumia", w.get_data(as_text=True))
        g = db.get_gift(gid)
        self.assertFalse(g["first_view"], "ukurasa wa kusubiri haupaswi kuhesabiwa kama kufunguliwa")
        db._run("UPDATE gifts SET open_at=? WHERE id=?", (int(time.time()) - 5, gid))   # wakati umefika
        page = self.c.get("/g/" + gid).get_data(as_text=True)
        self.assertNotIn("Zawadi inakusubiri", page)
        self.assertTrue(db.get_gift(gid)["first_view"])
        m = self.c.get(j["manage_url"].replace("http://localhost", "")).get_data(as_text=True)
        self.assertIn("Imepangwa kufunguka", m)

    def test_scheduled_open_validation(self):
        past = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")   # saa 2 nyuma kwa EAT
        far = (datetime.now(timezone.utc) + timedelta(days=db.TTL_DAYS + 5)).strftime("%Y-%m-%dT%H:%M")
        for bad in (past, far, "si-tarehe"):
            self.assertEqual(self.post("/api/gifts", self.old_body(open=bad)).status_code, 400, bad)
            self.assertEqual(self.post("/api/t/barua/gifts", {"d": {}, "agree": True, "open": bad}).status_code, 400, bad)
        self.assertEqual(self.post("/api/t/barua/gifts", {"d": {}, "agree": True, "open": eat_future(3)}).status_code, 201)

    # --------------------------------------------------------- majibu ya mpokeaji
    def test_replies(self):
        gid = self.post("/api/gifts", self.old_body()).get_json()
        tok = re.search(r"t=([\w\-]+)", gid["manage_url"]).group(1)
        gid = gid["id"]
        self.assertEqual(self.post("/api/gifts/%s/reply" % gid, {"m": "Asante sana 💖 <b>x</b>", "e": "❤️"}).status_code, 201)
        self.assertEqual(self.post("/api/gifts/%s/reply" % gid, {"e": "😍"}).status_code, 201)
        self.assertEqual(self.post("/api/gifts/%s/reply" % gid, {}).status_code, 400)
        self.assertEqual(self.post("/api/gifts/%s/reply" % gid, {"e": "💩"}).status_code, 400)   # emoji isiyo kwenye orodha
        self.assertEqual(self.post("/api/gifts/haipo/reply", {"m": "x"}).status_code, 404)
        m = self.c.get("/m/%s?t=%s" % (gid, tok)).get_data(as_text=True)
        self.assertIn("Asante sana", m)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", m)        # maandishi hayatekelezwi kama HTML
        self.assertNotIn("<b>x</b>", m)
        for i in range(db.REPLY_MAX):
            appmod._rhits.clear()
            self.post("/api/gifts/%s/reply" % gid, {"m": "jibu %d" % i})
        appmod._rhits.clear()
        self.assertEqual(self.post("/api/gifts/%s/reply" % gid, {"m": "la ziada"}).status_code, 409)

    def test_reply_rate_limit(self):
        gid = self.post("/api/gifts", self.old_body()).get_json()["id"]
        codes = [self.post("/api/gifts/%s/reply" % gid, {"m": "x%d" % i}).status_code for i in range(appmod.REPLY_LIMIT + 1)]
        self.assertEqual(codes[-1], 429)

    # --------------------------------------------------------- uthibitisho wa data ya templates
    def test_validation(self):
        d, err = catalog.validate("barua", {"to": "x" * 500, "theme": "haipo", "letter": "y" * 9000, "photo": "javascript:alert(1)"})
        self.assertIsNone(err)
        self.assertLessEqual(len(d["to"]), 30)
        self.assertEqual(d["theme"], "usiku")
        self.assertLessEqual(len(d["letter"]), 1500)
        self.assertEqual(d["photo"], "")
        self.assertEqual(catalog.validate("cv", {"link": "javascript:alert(1)"})[0]["link"], "")
        self.assertEqual(catalog.validate("cv", {"link": "https://example.com/x"})[0]["link"], "https://example.com/x")
        self.assertEqual(catalog.validate("hesabu", {"at": "bad"})[0]["at"], "")
        self.assertEqual(len(catalog.validate("kitabukuu", {"photos": [PNG] * 40})[0]["photos"]), catalog.MAX_IMAGES)
        self.assertIsNone(catalog.validate("haipo", {})[0])
        self.assertEqual(self.post("/api/t/haipo/generate", {"d": {}}).status_code, 400)
        self.assertEqual(self.post("/api/t/barua/generate", {"d": "si-kitu"}).status_code, 400)

    def test_script_injection_is_escaped(self):
        evil = '</script><script>alert(1)</script><img src=x onerror=alert(2)> \u2028'
        for tid in ("barua", "duka", "cv", "harusi"):
            page = self.post("/api/t/%s/generate" % tid, {"d": {"to": evil, "name": evil, "who": evil, "mke": evil, "letter": evil, "about": evil}}).get_data(as_text=True)
            self.assertNotIn("</script><script>alert(1)", page, tid)
            self.assertNotIn("<img src=x onerror", page, tid)
            self.assertEqual(page.count("</script>"), 1, tid)

    def test_rate_limit(self):
        appmod._hits.clear()
        codes = [self.post("/api/t/barua/gifts", {"d": {}, "agree": True}).status_code for _ in range(appmod.RATE_LIMIT + 2)]
        self.assertEqual(codes.count(201), appmod.RATE_LIMIT)
        self.assertEqual(codes[-1], 429)


if __name__ == "__main__":
    unittest.main(verbosity=2)
