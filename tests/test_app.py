"""Majaribio ya Zawadi Kiganjani. Endesha:  python -m unittest discover -s tests -v
(Jaribio la sintaksia ya JavaScript hurukwa ikiwa Node.js haipo.)"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TMP = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(TMP, "test.db")
os.environ.pop("DATABASE_URL", None)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as appmod  # noqa: E402
import catalog  # noqa: E402

PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        appmod._hits.clear()
        cls.c = appmod.app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def post(self, url, body):
        return self.c.post(url, data=json.dumps(body), content_type="application/json")

    # --------------------------------------------------------- kurasa
    def test_pages(self):
        for u in ("/", "/create", "/templates", "/robots.txt"):
            self.assertEqual(self.c.get(u).status_code, 200, u)
        self.assertIn("Templates 40", self.c.get("/templates").get_data(as_text=True))
        self.assertEqual(self.c.get("/t/haipo").status_code, 404)

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

    # --------------------------------------------------------- kuhifadhi
    def test_save_view_manage_delete(self):
        r = self.post("/api/t/harusi/gifts", {"d": {"mke": "Asha", "mume": "Juma", "photo": PNG}})
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
        ev = appmod.load_events()[0]["id"]
        st = appmod.load_styles()[0]["id"]
        body = {"event": ev, "style": st, "to": "Mama", "from": "Juma", "m": ["a", "b", "c"], "ph": [PNG]}
        self.assertEqual(self.post("/api/generate", body).status_code, 200)
        r = self.post("/api/gifts", body)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.c.get("/g/" + r.get_json()["id"]).status_code, 200)

    # --------------------------------------------------------- uthibitisho
    def test_validation(self):
        d, err = catalog.validate("barua", {"to": "x" * 500, "theme": "haipo", "letter": "y" * 9000, "photo": "javascript:alert(1)"})
        self.assertIsNone(err)
        self.assertLessEqual(len(d["to"]), 30)
        self.assertEqual(d["theme"], "usiku")          # select batili -> thamani ya mfano
        self.assertLessEqual(len(d["letter"]), 1500)
        self.assertEqual(d["photo"], "")               # picha batili hukataliwa
        d, _ = catalog.validate("cv", {"link": "javascript:alert(1)"})
        self.assertEqual(d["link"], "")
        d, _ = catalog.validate("cv", {"link": "https://example.com/x"})
        self.assertEqual(d["link"], "https://example.com/x")
        d, _ = catalog.validate("keki", {"at": "x", "age": "30"})
        self.assertEqual(d["age"], "30")
        d, _ = catalog.validate("hesabu", {"at": "bad"})
        self.assertEqual(d["at"], "")
        d, _ = catalog.validate("kitabukuu", {"photos": [PNG] * 40})
        self.assertEqual(len(d["photos"]), catalog.MAX_IMAGES)
        self.assertIsNone(catalog.validate("haipo", {})[0])
        self.assertEqual(self.post("/api/t/haipo/generate", {"d": {}}).status_code, 400)
        self.assertEqual(self.post("/api/t/barua/generate", {"d": "si-kitu"}).status_code, 400)

    def test_script_injection_is_escaped(self):
        evil = '</script><script>alert(1)</script><img src=x onerror=alert(2)> \u2028'
        for tid in ("barua", "duka", "cv", "harusi"):
            page = self.post("/api/t/%s/generate" % tid, {"d": {"to": evil, "name": evil, "who": evil, "mke": evil, "letter": evil, "about": evil}}).get_data(as_text=True)
            self.assertNotIn("</script><script>alert(1)", page, tid)
            self.assertNotIn("<img src=x onerror", page, tid)
            self.assertEqual(page.count("</script>"), 1, tid)   # kuna script moja tu (ya template)

    def test_rate_limit(self):
        appmod._hits.clear()
        codes = [self.post("/api/t/barua/gifts", {"d": {}}).status_code for _ in range(appmod.RATE_LIMIT + 2)]
        self.assertEqual(codes.count(201), appmod.RATE_LIMIT)
        self.assertEqual(codes[-1], 429)
        appmod._hits.clear()


if __name__ == "__main__":
    unittest.main(verbosity=2)
