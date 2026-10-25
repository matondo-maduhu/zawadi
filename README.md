# 🎁 Zawadi Kiganjani

Mtengenezaji wa zawadi za kugusa moyo kwa Kiswahili. Mtumiaji anachagua tukio, anajaza maelezo,
na anapata faili moja la HTML la kumtumia mtu wake (WhatsApp n.k.).

## Muundo wa mradi

```
zawadi-project/
├── app.py                  # seva ya Flask (kurasa, link za zawadi, API)
├── db.py                   # hifadhidata ya SQLite (kuhifadhi zawadi)
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

## Link za zawadi

Mtumiaji akibonyeza **"Tengeneza Link ya Kutuma"**, zawadi huhifadhiwa kwenye hifadhidata na anapata:
- **Link ya mpokeaji**: `https://tovuti-yako/g/abc123` (inafunguka moja kwa moja, bila kupakua faili)
- **Link ya mmiliki**: `/m/abc123?t=...` (kuona kama amefungua, mara ngapi, na kufuta zawadi)

Zawadi hufutwa yenyewe baada ya siku 90. Hesabu ya "amefungua" haihesabu roboti za onyesho la link
(WhatsApp, Facebook n.k.). Kikomo: zawadi 15 kwa saa kwa kila IP.

### Mazingira (environment variables)
| Jina | Maana | Kawaida |
|---|---|---|
| `DATABASE_PATH` | njia ya faili la hifadhidata | `data/zawadi.db` |
| `GIFT_TTL_DAYS` | zawadi hufutwa baada ya siku ngapi | `90` |

## Kuweka mtandaoni

GitHub Pages haiwezi kuendesha Flask (inaweka tovuti za kudumu tu). Tumia mwenyeji wa Python.

**MUHIMU: hifadhidata inahitaji diski ya kudumu.** Kwenye mipango ya bure ya baadhi ya huduma
(mfano Render bure), mafaili hupotea kila seva inapoanzishwa upya, na zawadi zote zingefutika.

- **PythonAnywhere** (mpango wa bure una diski ya kudumu): pakia mafaili, tengeneza Web App ya Flask
  (Python 3.10+), elekeza WSGI kwenye `app.py` (`from app import app as application`).
  Njia nyepesi kuanzia.
- **Render** (mpango wa kulipia wenye Persistent Disk): Build `pip install -r requirements.txt`,
  Start `gunicorn app:app`, ongeza Disk iliyofungwa kwenye `/var/data`, kisha weka
  `DATABASE_PATH=/var/data/zawadi.db`.
- **VPS** (DigitalOcean, Hetzner n.k.): gunicorn + Nginx, na hifadhi nakala ya `data/` mara kwa mara.

Ukikua, badilisha SQLite kuwa Postgres (badilisha `db.py` pekee).

## Hatua zinazofuata
- Malipo (M-Pesa/Tigo Pesa/Airtel Money kupitia ClickPesa, Selcom au Flutterwave)
- Akaunti za watumiaji na historia ya zawadi
- Matukio na mitindo zaidi
