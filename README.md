# RKHUB Tools 🇮🇳

**Independent Digital Utilities Hub** — service-centre operators के लिए document
tools, image tools, official portal links, welfare schemes और calculators का एक ही
डैशबोर्ड।

> **सरकारी नहीं, पर दावा ईमानदार।**
> This is **NOT** a Government website and is not affiliated with any Government department.

---

## ✨ Features

- 🌗 **Day / Night (Dark/Light) toggle** — `localStorage` se yaad rehta hai
- 🔍 Instant **live search** across all 31 tools (`/` key shortcut)
- 🧮 4 **fully working calculators**
- 🖼️ 8 **working client-side document/image tools**
- 🔗 19 **official Government portals** (PM-Kisan, Aadhaar, E-Shram, PM-JAY, Passport, EPFO, …)
- 📞 Owner contact in top bar, contact section और footer
- 📱 Fully responsive (mobile / tablet / desktop) + accessible (ARIA, skip-link, focus rings)
- 🔐 **100% client-side processing — कोई फाइल upload या store नहीं होती**
- 🖨️ `prefers-reduced-motion` support + print styles
- 🛡️ Strict **Content-Security-Policy** — zero third-party requests, zero inline handlers
- ⚡ Server-side **gzip** and **ETag** revalidation on every response

## 🛠 31 Tools

**Document Tools (4)**

1. PDF Compressor & Resizer — पीडीएफ कंप्रेसर
2. Image to PDF Converter — इमेज से पीडीएफ
3. Signature & Thumb Extractor (B&W + threshold) — सिग्नेचर और अंगूठा
4. Document Crop & Auto-Enhance — डॉक्यूमेंट क्रॉप

**Image Tools (4)**

5. Passport Photo Maker (3.5 × 4.5 cm @300 DPI + background changer) — पासपोर्ट फोटो मेकर
6. JPG to PNG / WebP Converter — इमेज कन्वर्टर
7. Photo Sheet Printer (4–36 copies on A4) — फोटो शीट प्रिंटर
8. PVC Card Maker (CR80 85.6 × 54 mm) — पीवीसी कार्ड मेकर

**Calculators (4)**

9. Official Form Age Calculator (exact Y/M/D + next birthday)
10. Stamp Duty & Fee Estimator (Haryana / Delhi / UP / MH / KA / custom)
11. CSC Commission & Tax Calculator (gross, TDS, GST, net, profit)
12. File Size Unit Converter (Bytes ⇄ KB ⇄ MB ⇄ GB ⇄ TB)

**Direct Portals (12)**

PM-Kisan • Aadhaar (UIDAI) • E-Shram • Ayushman Bharat (PM-JAY) • Voter ID (ECI) •
Parivahan (DL/RC) • PAN Card (NSDL) • Ration Card (NFSA) • Passport Seva •
EPFO Member Portal (UAN) • e-District / CSC Digital Seva • DHBVN / UHBVN Power Utilities

**Schemes & Services (7)**

PMMVY (Matru Vandana Yojana) • Haryana ULB Property Tax & Grievance • Haryana Pension Portal •
PM Surya Ghar (Rooftop Solar) • Parivar Pehchan Patra (Family ID) • Saral Haryana •
Meri Fasal Mera Byora (MFMB)

> 12 tools built in-house + 19 direct links to official portals = **31**.

---

## 📁 Project Structure

```
rkhub-tools/
├── app.py                     # Flask app — OWNER, SITE, CATEGORIES, TOOLS, ICONS, routes
├── requirements.txt           # Flask==3.0.3, gunicorn==23.0.0
├── render.yaml                # Render blueprint (env vars + start command)
├── Procfile                   # Same start command for Heroku / Dokku
├── THIRD_PARTY_NOTICES.md     # Licences + SHA-384 of the vendored bundles
├── README.md                  # This file
│
├── static/
│   ├── css/style.css          # Theming (light/dark), layout, all components
│   ├── js/
│   │   ├── main.js            # Theme, nav, ticker, live search, back-to-top
│   │   └── tools.js           # All 12 working tool engines (client-side)
│   ├── vendor/                # pdf-lib + jsPDF, served locally (no CDN)
│   └── images/                # logo.svg + rkhub-logo.* raster sizes
│
├── templates/
│   ├── _brand_logo.html       # Shared logo markup
│   ├── index.html             # Home — hero, search, all 5 categories, contact
│   └── tool_view.html         # Tool workspace / calculator / 404
│
└── tools/
    └── build_logo.py          # Regenerates the PNG/WebP favicon set
```

---

## 🚀 Run Locally (VS Code)

```bash
# 1. Project folder mein jayein
cd rkhub-tools

# 2. (Optional) virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/binactivate

# 3. Dependencies install karein
pip install -r requirements.txt

# 4. Server chalayein
python app.py
```

Browser mein kholें → **http://127.0.0.1:5000**

Health check → **http://127.0.0.1:5000/api/health**

> VS Code mein: `File → Open Folder → rkhub-tools` chunein. Python extension ho toh
> `app.py` kholkar **Run ▶** dabayein.

---

## ⚙️ Environment Variables

Sab optional hain — app bina kisi env var ke bhi chalta hai. Production me
inhe set karein.

| Variable | Default | Kya karta hai |
| --- | --- | --- |
| `TRUST_PROXY` | `0` | `1` karne par rate limiter `X-Forwarded-For` se asli client IP padhta hai. **Render / Railway / Fly / nginx ke peeche ye `1` hona chahiye**, warna saare visitors ka ek hi `remote_addr` dikhega aur limiter poori site ko ek client samajhkar block kar dega. Sirf tab safe hai jab proxy header ingress par overwrite karta ho — seedha exposed origin par `1` mat rakhein. |
| `CANONICAL_URL` | `https://rkhub-tools.onrender.com` | `robots.txt` / `sitemap.xml` ke absolute URLs. |
| `SECRET_KEY` | random per boot | Flask signing key. Aaj koi session use nahi hota, isliye random fallback theek hai — par koi bhi session/cookie feature add karne se pehle ise dashboard me set kar dein, warna har restart par badal jayega. |
| `TRUSTED_HOSTS` | unset | Comma-separated Host allow-list. Set karne par unknown Host reject hote hain (host-header poisoning se bachav). Default mein unset hai taaki custom domain jodne par site na tootey. |
| `FLASK_DEBUG` | `0` | `1` se debugger enable — **production me kabhi on mat rakhein.** |

---

## 🚢 Deploy (Render)

`render.yaml` blueprint ready hai: push karte hi Render service ban jaata hai.

```bash
git push origin main
```

Do cheezein manually karni hain:

1. **Dashboard → Environment → `SECRET_KEY`** → `sync: false` se generate karwa lein.
2. Domain badalne par `CANONICAL_URL` update kar dein.

### Workers: 1, threads: 4 — jaan-boojh kar

Start command hai:

```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --worker-class gthread --timeout 60
```

Yeh ek worker + threads hai, **2 workers nahi**, jaan-boojh kar:

- Rate limiter ke counters process memory me hain, isliye har worker ka apna alag
  set hota hai. 2 workers par documented "120 page views/minute" chupke se **240**
  ho jata tha, aur ek visitor ka traffic doosre worker ko kabhi dikhta hi nahi.
- `gthread` I/O-bound kaam me concurrency deta hai, bina state ki doosri copy banaye.

**Agar kabhi 2+ workers ya 2+ instances chahiye, limiter ko pehle Redis jaisi
shared store par le jaana zaroori hai**, warna per-process buckets ka matlab hi
nahi rehta.

---

## 🔒 Security & Performance

| Layer | Kya hota hai |
| --- | --- |
| CSP | `script-src 'self'` — koi CDN, koi inline `<script>`, koi `onclick`/`onsubmit` handler nahi. Isiliye `pdf-lib`/`jsPDF` locally vendored hain (`static/vendor/`), kyunki CDN har visitor ka IP leak karta. |
| Input validation | `X-Forwarded-For` ko IP address validate karne ke baad hi rate-limit key banta hai, warna attacker random IPs bana ke bucket dict bharna / limiter bypass kar sakta. |
| Rate limiting | Per-client fixed window: **120** page views/min, **600** static/min, **60** API/min. `/api/health` platform monitor ke liye exempt hai. `429` ke saath `Retry-After`. |
| Body cap | `MAX_CONTENT_LENGTH` = 32 MB, koi bhi POST nahi hota. |
| Caching | Static `public, max-age=600, must-revalidate` + `ETag`. `immutable` jaan-boojh kar nahi lagaya — filenames content-hashed nahi hain, to ek saal purana bundle pin ho jata. |
| Compression | Custom dependency-free gzip (`apply_gzip`); `pdf-lib.min.js` ~525 KB → ~206 KB. Werkzeug aise middleware ship hi nahi karta. |
| Secret hygiene | Koi secret repo me commit nahi hota — `SECRET_KEY` render.yaml me commented out hai. |

> Rate limiter **fixed** window hai (pehli request se anchored), true sliding window
> nahi — window boundary par theoretical 2× burst ho sakta hai. Yahan jaan-boojh kar
> chhoda gaya hai kyunki limiter ka kaam CPU abuse rokna hai, hard quota lagana nahi.

---

## ⚙️ Customise

Sab data `app.py` ke andar hai — naya tool ya portal jodne ke liye `TOOLS` list mein
ek dict add karein:

```python
{
    "slug": "my-tool",              # URL: /tool/my-tool
    "name": "My New Tool",
    "name_hi": "मेरा नया टूल",
    "category": "document",         # CATEGORIES ka id
    "icon": "pdf",                  # ICONS dict ka key
    "accent": "red",                # red | amber | navy | green
    "badge": "New",
    "tag": "PDF",
    "summary": "Short description.",
    "keywords": "search keywords",
    "kind": "internal",             # ya "external" + "url"
},
```

- **Owner details** → `OWNER` dict (app.py)
- **News ticker** → `NEWS` list (app.py)
- **Categories** → `CATEGORIES` list (app.py)
- **Naya SVG icon** → `ICONS` dict (app.py), 24×24 stroke-based paths
- **Naya tool engine** → `ENGINES` map (static/js/tools.js) + ek `{% if tool.slug == '...' %}`
  block (templates/tool_view.html)

> Naya engine banana ho to `ENGINES` map ke entries aur `app.py` ke `kind: "internal"`
> slugs ek saath update karein — `node --check static/js/tools.js` se syntax verify
> kar lein.

---

## 🔒 Privacy

Har tool sirf browser ke andar chalta hai — `FileReader`, `Canvas` aur `Blob` API use
hote hain. **Koi bhi document server par upload, store ya log nahi hota.** PDF Compressor
aur Image-to-PDF ke liye `pdf-lib` / `jsPDF` `static/vendor/` se apne hi origin se
load hote hain (koi CDN nahi), isliye file data inhe bhi browser mein hi milta hai.

Server par sirf yeh log hota hai: request path, status, user-agent, aur
`TRUST_PROXY=1` hone par woh IP jo proxy ne `X-Forwarded-For` me bheja.

---

## ⚠️ Disclaimer

यह पोर्टल किसी भी सरकार / सरकारी विभाग का आधिकारिक पोर्टल **नहीं** है।
यह केवल सेवा-सेंटर ऑपरेटरों की सुविधा हेतु बनाया गया स्वतंत्र उपयोगिता मंच है।
सभी लिंक संबंधित विभागों की आधिकारिक वेबसाइटों पर जाते हैं।

**Owner:** RAMESH KUMAR — CSC Operator / Jan Seva Kendra
**Phone:** +91 99912-44415 • **Email:** rameshrajput044@gmail.com

© 2026 RKHUB Tools. All Rights Reserved. Made in India 🇮🇳
