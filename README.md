# 🎁 Zawadi Kiganjani

Mtengenezaji wa zawadi za kugusa moyo kwa Kiswahili. Mtumiaji anapata faili moja la HTML (au link) la kumtumia mtu wake
kupitia WhatsApp n.k. Kuna njia mbili za kutengeneza:

1. **Templates 40** (`/templates`): kitabu, harusi, siri za kufungua hatua kwa hatua, terminal ya hacker, AI ya siri,
   escape room, kamera ya kioo, barua ya moto, duka la WhatsApp, menyu, CV na zaidi. Kila template ina fomu yake.
2. **Njia ya zamani** (`/create`): chagua tukio (13) kisha mtindo (kitabu, kadi, simu), ongeza picha 3 na sauti
   (unaweza kurekodi hapo hapo).

## Vipengele
- **Link ya kutuma** (`/g/<id>`) + **ukurasa wa mmiliki** (`/m/<id>?t=<token>`): anaona lini zawadi ilifunguliwa, majibu aliyotuma mpokeaji, na anaweza kuifuta.
- **Tarehe maalum**: mtumiaji anapanga zawadi ifunguke baadaye (saa za Afrika Mashariki). Kabla ya hapo mpokeaji huona ukurasa wa kuhesabu muda (`waiting.html`) na kufunguliwa hakuhesabiwi.
- **Majibu ya mpokeaji**: emoji moja + ujumbe mfupi (herufi 300), hadi majibu 10 kwa zawadi.
- **PWA**: inasakinishwa kama app (kitufe kwenye ukurasa wa mwanzo), ina ukurasa wa nje ya mtandao. `/pwa-check` hukagua hali.
- **Masharti na Faragha** (`/terms`, `/privacy`): mtumiaji lazima akubali kabla ya kutengeneza link.
- Zawadi hufutwa kiotomatiki baada ya siku 90 (`GIFT_TTL_DAYS`), na kuna kikomo cha zawadi 15 kwa saa kwa kila IP.

## Muundo wa mradi
```
zawadi/
├── app.py                  # seva ya Flask (kurasa, link, majibu, PWA, API)
├── db.py                   # hifadhidata (SQLite au Postgres): zawadi, majibu, tarehe maalum
├── pwa.py                  # manifest + ikoni za PWA zinatoka kwenye msimbo (HAKUNA folda ya static inayohitajika)
├── catalog.py              # templates 40: kuthibitisha data na kutengeneza HTML
├── catalog/
│   ├── catalog.json        # orodha ya templates + fomu (schema) ya kila moja
│   └── pages/<id>.html     # skeleton ya kila template (alama @@HEAD@@ @@THEME@@ @@DATA@@)
├── tools/
│   ├── templates-src.js    # CHANZO cha templates 40 (hapa ndipo unapohariri)
│   └── build_catalog.js    # hujenga upya catalog/ kutoka templates-src.js
├── tests/test_app.py       # majaribio ya kiotomatiki
├── events/*.json           # matukio 13 (mfano 01-kuzaliwa.json)
├── styles.json             # mitindo ya njia ya zamani (kitabu, kadi, simu)
├── templates/
│   ├── index.html  create.html  catalog.html  fill.html  manage.html  waiting.html
│   ├── legal.html  offline.html  pwa_check.html  404.html  sw.js
│   ├── gifts/{book,cards,phone}.html   # mitindo ya njia ya zamani (+ kisanduku cha majibu)
│   └── partials/engine.js              # muziki + madoido ya pamoja
├── static/.gitkeep         # folda ni "static" (herufi ndogo); haina faili zinazohitajika
├── requirements.txt  Procfile
├── render.yaml             # Render: toleo la BURE (Free + Postgres ya Neon)
└── render.paid.yaml        # Render: toleo la KULIPIA (Starter + diski ya kudumu)
```

## Kuendesha kwenye kompyuta
```bash
pip install -r requirements.txt
python app.py                         # http://localhost:5000
python -m unittest discover -s tests -v   # majaribio (17)
```

## Vigeu vya mazingira
| Jina | Maana |
|---|---|
| `DATABASE_URL` | Postgres (mfano Neon). Ikiwekwa, SQLite haitumiki. |
| `DATABASE_PATH` | Njia ya faili la SQLite (chaguo-msingi `data/zawadi.db`; kwenye diski ya Render: `/var/data/zawadi.db`). |
| `GIFT_TTL_DAYS` | Siku za kuhifadhi zawadi (chaguo-msingi 90). |
| `CONTACT_EMAIL` | Barua pepe inayoonekana kwenye ukurasa wa Masharti. |
| `APP_VERSION` | (hiari) toleo la service worker; vinginevyo hutokana na `sw.js` + manifest. |

## Templates 40: jinsi zinavyofanya kazi
Kila template ni kipengele kimoja kwenye `tools/templates-src.js`: `{id, e, n, d, f:[fields], b:(data)=>html}`.
`node tools/build_catalog.js` huzigeuza kuwa `catalog/catalog.json` (fomu) na `catalog/pages/<id>.html` (skeleton).
Mtiririko: `/t/<id>` (fomu hutengenezwa kutoka schema) → `POST /api/t/<id>/generate` (onyesho/kupakua) au
`POST /api/t/<id>/gifts` (huhifadhi, hurudisha link). Zawadi za templates huhifadhiwa kwenye jedwali la `gifts`
(`style="tpl"`, `event=<id ya template>`), kwa hiyo kila kitu cha link, mmiliki, tarehe maalum na kufuta kinafanya kazi vilevile.

**Usalama:** `catalog.validate()` hukagua kila sehemu (aina, urefu, chaguo halali, picha za `data:image` tu, viungo vya `http(s)` tu).
Data huingia kwenye ukurasa kama JSON salama (`<`, `>`, `&` hubadilishwa) na templates huiandika kwa `textContent`.
Picha: hadi 14 kwa sehemu moja, kila moja chini ya 700 KB, jumla chini ya 8.5 MB.

**Kuongeza au kubadilisha template:** hariri `tools/templates-src.js` → `node tools/build_catalog.js` (Node.js inahitajika kwenye kompyuta yako tu, si kwenye seva)
→ `python -m unittest discover -s tests -v` → ongeza `id` kwenye `CM` (makundi) mwishoni mwa `templates-src.js`.

## Kuweka mtandaoni (Render)
- **Bure:** `render.yaml` (Free + Postgres ya Neon). Weka `DATABASE_URL` ya Neon wakati wa Apply.
- **Kulipia (zawadi hazipotei):** badilisha `render.paid.yaml` kuwa `render.yaml` (Starter + diski ya GB 1, `DATABASE_PATH=/var/data/zawadi.db`).

Weka **mafaili yaliyofunguliwa** kwenye GitHub (siyo zip), kila moja kwenye folda yake. Usipakie `data/` wala `__pycache__/`.
Baada ya kupakia, Render hujenga upya yenyewe (dakika 3 hadi 5).

## Makosa ya kawaida ya kupakia (yamethibitishwa na majaribio)
- Faili za `me.html` (tupu) zinazotengenezwa na simu wakati wa kutengeneza folda: zifute.
- `index.html` ya mzizi ni toleo la zamani lisilotumika: ifute (ukurasa wa mwanzo uko kwenye `templates/index.html`).
- Folda `Static/` yenye herufi kubwa haitumiki kwenye Linux. PWA inatoka kwenye `pwa.py`; hakuna haja ya folda ya static.
- Usiandike juu ya `app.py`, `create.html`, `index.html` kwa toleo la zamani. Jaribio `test_app_has_every_route_the_templates_need` hukukumbusha.

## Mawazo yajayo
- Malipo (M-Pesa/Tigo Pesa) kwa templates za kulipia
- Mapendekezo ya templates kulingana na tukio
- Kuhifadhi rasimu ya fomu
