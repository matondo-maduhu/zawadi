# 🎁 Zawadi Kiganjani

Mtengenezaji wa zawadi za kugusa moyo kwa Kiswahili. Mtumiaji anachagua tukio, anajaza maelezo,
na anapata faili moja la HTML la kumtumia mtu wake (WhatsApp n.k.).

## Muundo wa mradi

```
zawadi-project/
├── app.py                  # seva ya Flask (njia: /, /create, /api/generate)
├── styles.json             # orodha ya mitindo (kitabu, kadi, simu)
├── events/                 # kila tukio ni faili lake la JSON
│   ├── 01-kuzaliwa.json
│   ├── 02-shukrani.json
│   └── ...
├── templates/
│   ├── index.html          # ukurasa wa mwanzo (CSS + JS zake ndani)
│   ├── create.html         # ukurasa wa kutengeneza (CSS + JS zake ndani)
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

## Kuweka mtandaoni

GitHub Pages haiwezi kuendesha Flask (inaweka tovuti za kudumu tu). Tumia mojawapo:
- **Render.com** (bure): New Web Service, unganisha repo ya GitHub,
  Build Command `pip install -r requirements.txt`, Start Command `gunicorn app:app`.
- **PythonAnywhere** (bure): pakia mafaili, tengeneza Web App ya Flask, elekeza kwenye `app.py`.

## Hatua zinazofuata
- Malipo (M-Pesa/Tigo Pesa/Airtel Money kupitia ClickPesa, Selcom au Flutterwave)
- Kikomo cha maombi (Flask-Limiter) ili kuzuia matumizi mabaya
- Akaunti za watumiaji na historia ya zawadi
