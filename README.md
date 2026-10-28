# 🎁 Zawadi Kiganjani

Mtengenezaji wa zawadi za kugusa moyo kwa Kiswahili. Mtumiaji anachagua tukio, anajaza maelezo,
na anapata faili moja la HTML la kumtumia mtu wake (WhatsApp n.k.).

## Muundo wa mradi

```
zawadi-project/
├── app.py                  # seva ya Flask (kurasa, link za zawadi, API)
├── db.py                   # hifadhidata (SQLite au Postgres) kuhifadhi zawadi
├── styles.json             # orodha ya mitindo (kitabu, kadi, simu)
├── events/                 # kila tukio ni faili lake la JSON
│   ├── 01-kuzaliwa.json
│   ├── 02-shukrani.json
│   └── ...
├── templates/
│   ├── index.html          # ukurasa wa mwanzo (CSS + JS zake ndani)
│   ├── create.html         # ukurasa wa kutengeneza (CSS + JS zake ndani)
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

## Vipengele vikuu

- **Link za zawadi** (`/g/<id>`) na **ukurasa wa mmiliki** (`/m/<id>?t=...`): hali ya zawadi, majibu, kufuta.
- **Majibu ya mpokeaji**: baada ya kuona zawadi, mpokeaji anatuma emoji na/au ujumbe (hadi 10 kwa zawadi). Mtumaji anayaona kwenye ukurasa wake.
- **Zawadi ya tarehe maalum**: mtumaji anachagua tarehe na saa (EAT). Kabla ya hapo mpokeaji anaona kuhesabu muda tu, na zawadi haionekani wala haihesabiwi kama imefunguliwa.
- **Kurekodi sauti** moja kwa moja kwenye ukurasa wa kutengeneza (hadi sekunde 60).
- **Masharti na Faragha** (`/terms`, `/privacy`). Weka `CONTACT_EMAIL` ili barua pepe ya kuripoti ionekane.
- Matukio 13, mitindo 3.

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
| `CONTACT_EMAIL` | barua pepe ya kuripoti (inaonekana kwenye Masharti/Faragha) | haipo |

## Kuweka mtandaoni kwenye Render BURE (Render Free + Neon Postgres)

`render.yaml` (toleo la bure) linatumia web service ya **Free** na hifadhidata ya **Neon** (bure, bila kadi, GB 0.5).

1. Fungua **neon.com**, jiunge (kwa GitHub), **Create project**. Nakili **connection string** (huanza na `postgresql://`).
2. Weka mafaili kwenye GitHub (`app.py` na `render.yaml` kwenye folda kuu).
3. Render: **New +**, **Blueprint**, chagua repository, **Apply**.
4. Render itakuuliza thamani ya `DATABASE_URL`. Bandika connection string ya Neon.
5. Subiri dakika chache. Link itakuwa `https://zawadi.onrender.com`.

Mipaka ya bure: huduma hulala baada ya dakika 15 (ya kwanza hufunguka polepole), saa 750 za bure kwa mwezi
kwa akaunti nzima ya Render, na zawadi hufutwa baada ya siku 30 (`GIFT_TTL_DAYS`) ili GB 0.5 isijae.

Toleo la kulipia (Starter + diski + SQLite, takriban dola 7.25) liko kwenye `render.paid.yaml`.

### Toleo la kulipia, bila Blueprint (kwa mkono)
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
- Matukio na mitindo zaidi
