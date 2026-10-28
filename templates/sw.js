/* Service worker ya Zawadi Kiganjani.
   - Kurasa kuu (/, /create, /terms, /privacy): mtandao kwanza, kisha nakala iliyohifadhiwa, kisha /offline.
   - Picha na mafaili ya /static: nakala kwanza.
   - Zawadi (/g/), ukurasa wa mmiliki (/m/) na /api/ HAZIHIFADHIWI kamwe (faragha). */
const VERSION = "{{ version }}";
const CACHE = "zawadi-" + VERSION;
const SHELL = ["/", "/create", "/offline", "/manifest.webmanifest",
               "/static/icons/icon-192.png", "/static/icons/icon-512.png"];
const PAGES = ["/", "/create", "/terms", "/privacy"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith("zawadi-") && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url), p = u.pathname;
  if (r.method !== "GET" || u.origin !== self.location.origin) return;
  if (p.startsWith("/g/") || p.startsWith("/m/") || p.startsWith("/api/") || p === "/sw.js") return;

  if (r.mode === "navigate") {
    e.respondWith(
      fetch(r).then(res => {
        if (res.ok && PAGES.includes(p)) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(r, copy)); }
        return res;
      }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match("/offline")))
    );
    return;
  }

  if (p.startsWith("/static/") || p === "/manifest.webmanifest") {
    e.respondWith(
      caches.match(r).then(m => m || fetch(r).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(r, copy)); }
        return res;
      }))
    );
  }
});
