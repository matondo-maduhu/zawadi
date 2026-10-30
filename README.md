# 🎁 Zawadi Kiganjani

Mtengenezaji wa zawadi za kugusa moyo kwa Kiswahili. Mtumiaji anapata faili moja la HTML (au link) la kumtumia
mtu wake kupitia WhatsApp n.k. Kuna njia mbili za kutengeneza:

1. **Templates 40** (`/templates`): kitabu, harusi, siri za kufungua hatua kwa hatua, terminal ya hacker, AI ya siri,
   escape room, kamera ya kioo, barua ya moto, duka la WhatsApp, menyu, CV na zaidi. Kila template ina fomu yake.
2. **Njia ya zamani** (`/create`): chagua tukio (10) kisha mtindo (kitabu, kadi, simu).

## Muundo wa mradi

```
zawadi-project/
├── app.py                  # seva ya Flask (kurasa, link za zawadi, API)
├── db.py                   # hifadhidata (SQLite au Postgres) kuhifadhi zawadi
├── catalog.py              # templates 40: kuthibitisha data na kutengeneza HTML
├── catalog/
│   ├── catalog.json        # orodha ya templates + fomu (schema) ya kila moja
│   └── pages/<id>.html     # skeleton ya kila template (ina alama @@HEAD@@ @@THEME@@ @@DATA@@)
├── tools/
│   ├── templates-src.js    # CHANZO cha templates 40 (hapa ndipo unapohariri)
│   └── build_catalog.js    # hujenga upya catalog/ kutoka templates-src.js
├── tests/test_app.py       # majaribio ya kiotomatiki (python -m unittest discover -s tests -v)
├── styles.json             # orodha ya mitindo ya njia ya zamani (kitabu, kadi, simu)
├── events/                 # kila tukio ni faili lake la JSON
│   ├── 01-kuzaliwa.json
│   ├── 02-shukrani.json
│   └── ...
├── templates/
│   ├── index.html          # ukurasa wa mwanzo (CSS + JS zake ndani)
│   ├── create.html         # ukurasa wa kutengeneza (njia ya zamani: tukio + mtindo)
│   ├── catalog.html        # orodha ya templates (kutafuta + makundi)
│   ├── fill.html           # fomu ya template moja (inatengenezwa kutoka schema) + onyesho + link
│   ├── manage.html         # ukurasa wa mmiliki: ameifungua? futa zawadi
│   ├── 404.html            # ukurasa wa "haipatikani"
│   ├── gifts/
│   │   ├── book.html       # mtindo wa kitabu   (CSS + JS zake ndani)
│   │   ├── cards.html      # mtindo wa kadi     (CSS + JS zake ndani)
│   │   └── phone.html      # mtindo wa simu     (CSS + JS zake ndani)
│   └── partials/
│       └── engine.js       # muziki + fataki, unaingizwa kwenye kila zawadi
├── requirements.txt
├── Procfile                # kwa Render/Railway/Heroku
├── render.yaml             # Render: toleo la BURE (Free + Postgres ya Neon)
├── render.paid.yaml        # Render: toleo la KULIPIA (Starter + diski ya kudumu)
└── static/
```

## Kuendesha kwenye kompyuta

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Kisha fungua http://localhost:5000

## Jinsi ya kuongeza vitu

**Tukio jipya**: nakili faili lolote kwenye `events/`, mfano `07-ubatizo.json`, na ubadilishe maneno.
Hakuna haja ya kugusa code. Vitu vya kuandika:
- `id`, `e` (emoji), `n` (jina), `th` (rangi 3: mandhari mbili na rangi kuu), `f` (maswali 3 kwa mtumiaji)
- `P` (kurasa 6: `[emoji, kichwa, maelezo]`), `C` (kuponi 3), `Q` (swali la mwisho)
- Unaweza kutumia `{to}`, `{from}`, `{m1}`, `{m2}`, `{m3}` ndani ya maandishi.
- `"dodge": 1` hufanya kitufe cha "hapana" kikimbie.

**Mtindo mpya**: tengeneza `templates/gifts/jina.html` (nakili `book.html` kama mfano), kisha
ongeza mstari kwenye `styles.json`.

## Templates 40: jinsi zinavyofanya kazi

Kila template ni kitu kimoja kwenye `tools/templates-src.js`: `{id, e, n, d, f:[fields], b:(data)=>html}`.
`node tools/build_catalog.js` huzigeuza kuwa:
- `catalog/catalog.json`: orodha na **fomu** ya kila template (aina za sehemu: `text`, `textarea`, `select`, `tel`, `date`, `datetime-local`, `image`, `images`)
- `catalog/pages/<id>.html`: ukurasa wa template wenye alama tatu ambazo seva huzibadilisha.

Mtiririko: mtumiaji anafungua `/t/<id>` (fomu hutengenezwa kutoka schema) → `POST /api/t/<id>/generate` (onyesho/kupakua)
au `POST /api/t/<id>/gifts` (huhifadhi, hurudisha link `/g/<id>`). Zawadi za templates huhifadhiwa kwenye jedwali lile lile
la `gifts` (`style="tpl"`, `event=<id ya template>`), kwa hiyo ukurasa wa mmiliki (`/m/...`), kufuta, siku 90 na kikomo cha 15 kwa saa
vinafanya kazi vilevile.

**Usalama:** `catalog.validate()` hukagua kila sehemu (aina, urefu, chaguo halali, picha za `data:image` tu, viungo vya `http(s)` tu).
Data huingia kwenye ukurasa kama JSON salama (`<`, `>`, `&` hubadilishwa) na templates huiandika kwa `textContent`, si HTML.
Picha: hadi 14 kwa sehemu ya `images`, kila moja chini ya 700 KB, jumla chini ya 8.5 MB.

**Kuongeza au kubadilisha template**
1. Hariri `tools/templates-src.js` (ongeza kipengele kwenye `TPL`; angalia templates zilizopo kama mfano).
2. `node tools/build_catalog.js` (Node.js inahitajika kwenye kompyuta yako tu, si kwenye seva).
3. `python -m unittest discover -s tests -v` kuhakikisha kila kitu kinapita.
4. Weka template mpya kwenye kundi kwa kuongeza `id` yake kwenye `CM` mwishoni mwa `templates-src.js`.

## Link za zawadi

Mtumiaji akibonyeza **"Tengeneza Link ya Kutuma"**, zawadi huhifadhiwa kwenye hifadhidata na anapata:
- **Link ya mpokeaji**: `https://tovuti-yako/g/abc123` (inafunguka moja kwa moja, bila kupakua faili)
- **Link ya mmiliki**: `/m/abc123?t=...` (kuona kama amefungua, mara ngapi, na kufuta zawadi)

Zawadi hufutwa yenyewe baada ya siku 90. Hesabu ya "amefungua" haihesabu roboti za onyesho la link
(WhatsApp, Facebook n.k.). Kikomo: zawadi 15 kwa saa kwa kila IP.

### Mazingira (environment variables)
| Jina | Maana | Kawaida |
|---|---|---|
| `DATABASE_URL` | anwani ya Postgres (ikiwekwa, Postgres inatumika) | haipo |
| `DATABASE_PATH` | njia ya faili la SQLite (kama hakuna DATABASE_URL) | `data/zawadi.db` |
| `GIFT_TTL_DAYS` | zawadi hufutwa baada ya siku ngapi | `90` |

## Kuweka mtandaoni kwenye Render (SQLite + diski ya kudumu)

`render.paid.yaml` linaeleza kila kitu (Starter, diski ya GB 1, `DATABASE_PATH=/var/data/zawadi.db`).
Ili kulitumia, libadilishe jina kuwa `render.yaml` kwenye repo yako (`render.yaml` ya sasa ni toleo la bure).

1. Weka **mafaili yaliyofunguliwa** kwenye GitHub (`app.py` na `render.yaml` ziwe kwenye folda kuu; folda `events/`, `templates/`, `catalog/` zibaki kama zilivyo).
2. Fungua render.com na ujiunge kwa GitHub.
3. **New +**, kisha **Blueprint**, chagua repository yako, kisha **Apply**.
4. Render itaomba taarifa za malipo (Starter ni mpango wa kulipia). Thibitisha.
5. Subiri dakika 3 hadi 5. Link itakuwa `https://zawadi.onrender.com` (au jina lililo karibu nalo).
6. Jaribu: tengeneza zawadi, fungua link yake, fungua ukurasa wa mmiliki.
7. Hakikisha diski inafanya kazi: bonyeza **Manual Deploy**, kisha angalia kama zawadi yako ya jaribio bado ipo.

### Bila Blueprint (kwa mkono)
New +, Web Service, chagua repo. Runtime `Python 3`, Build `pip install -r requirements.txt`,
Start `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`, Instance Type `Starter`.
Kisha **Disks**, Add Disk: Mount Path `/var/data`, Size 1 GB. Kisha **Environment**:
`DATABASE_PATH=/var/data/zawadi.db`.

### Kujaribu bure (zawadi hupotea)
Chagua Instance Type `Free` na usiweke diski. Tovuti itafanya kazi, lakini itakuwa inalala baada ya dakika 15
na zawadi zote hupotea ikianzishwa upya. Ni kwa kuona muonekano tu.

## Mbadala: Railway (programu + Postgres mahali pamoja)

1. Weka **mafaili yaliyofunguliwa** kwenye GitHub (`app.py` iwe kwenye folda kuu ya repository), si faili la ZIP.
2. Fungua railway.com, ingia kwa GitHub.
3. **New Project**, kisha **Deploy from GitHub repo**, chagua repository yako.
4. Kwenye mradi huo bonyeza **+ New**, kisha **Database**, kisha **Add PostgreSQL**.
5. Fungua huduma ya programu yako, kisha **Variables**, ongeza `DATABASE_URL` yenye thamani `${{Postgres.DATABASE_URL}}` (Railway inaunganisha yenyewe).
6. **Settings**, kisha **Networking**, kisha **Generate Domain** kupata link ya tovuti.
7. **Settings**, kisha **Usage limit**: weka kikomo cha matumizi ili usishangazwe na bili.

Programu inajua yenyewe kutumia Postgres ikiwa `DATABASE_URL` ipo, na SQLite ikiwa haipo.

### Bei (angalia railway.com/pricing kabla ya kulipa)
- Trial: mkopo wa dola 5 mara moja, kwa majaribio.
- Free: dola 1 ya matumizi kwa mwezi (haitoshi kuendesha programu saa 24).
- Hobby: dola 5 kwa mwezi, inajumuisha dola 5 za matumizi.
- Pro: dola 20 kwa mwezi, Railway inapendekeza kwa programu za kibiashara.

### Mwenyeji mwingine
Mradi huo huo unafanya kazi Render (Start Command `gunicorn app:app`), PythonAnywhere (SQLite, weka `DATABASE_PATH`),
au VPS. Weka `DATABASE_URL` kama una Postgres, au `DATABASE_PATH` kama unatumia SQLite kwenye diski ya kudumu.

## Hatua zinazofuata
- Malipo (M-Pesa/Tigo Pesa/Airtel Money kupitia ClickPesa, Selcom au Flutterwave)
- Akaunti za watumiaji na historia ya zawadi
- Matukio na templates zaidi (ongeza kwenye `tools/templates-src.js`)
