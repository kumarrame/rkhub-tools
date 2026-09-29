# RKHUB Tools 🇮🇳

**Digital India & CSC Services Utility Portal** — CSC / Jan Seva Kendra operators के लिए
document tools, image tools, government direct links, schemes और calculators का एक ही डैशबोर्ड।

> **सरकारी नहीं, पर दावा ईमानदार।**
> This is **NOT** a Government website and is not affiliated with any Government department.

---

## ✨ Features

- 🎨 Government-style UI (Digital India / UMANG / CSC Seva inspired look)
- 🔒 Hindi **Data Privacy Guarantee** banner + "100% Safe" tag
- 🌗 **Day / Night (Dark/Light) toggle** — `localStorage` se yaad rehta hai
- 📰 Animated **Latest Updates** ticker with pause/play button
- 🔍 Instant **live search** across all tools (`/` key shortcut)
- 🧮 4 **fully working calculators**
- 🖼️ 8 **working client-side document/image tools**
- 🔗 19 **official Government portals** (PM-Kisan, Aadhaar, E-Shram, PM-JAY, Passport, EPFO, …)
- 📞 Owner contact in top bar, contact section और footer
- 📱 Fully responsive (mobile / tablet / desktop) + accessible (ARIA, skip-link, focus rings)
- 🔐 **100% client-side processing — कोई फाइल upload या store नहीं होती**
- 🖨️ `prefers-reduced-motion` support + print styles

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

**Direct Portals (12)**

PM-Kisan • Aadhaar (UIDAI) • E-Shram • Ayushman Bharat (PM-JAY) • Voter ID (ECI) •
Parivahan (DL/RC) • PAN Card (NSDL) • Ration Card (NFSA) • Passport Seva •
EPFO Member Portal (UAN) • e-District / CSC Digital Seva • DHBVN / UHBVN Power Utilities

**Schemes & Services (7)**

PMMVY (Matru Vandana Yojana) • Haryana ULB Property Tax & Grievance • Haryana Pension Portal •
PM Surya Ghar (Rooftop Solar) • Parivar Pehchan Patra (Family ID) • Saral Haryana •
Meri Fasal Mera Byora (MFMB)

**Calculators (4)**

28. Official Form Age Calculator (exact Y/M/D + next birthday)
29. Stamp Duty & Fee Estimator (Haryana / Delhi / UP / MH / KA / custom)
30. CSC Commission & Tax Calculator (gross, TDS, GST, net, profit)
31. File Size Unit Converter (Bytes ⇄ KB ⇄ MB ⇄ GB ⇄ TB)

---

## 📁 Project Structure

```
rkhub-tools/
├── app.py                     # Flask app — OWNER, SITE, CATEGORIES, TOOLS, ICONS, routes
├── requirements.txt           # Flask==3.0.3
├── README.md                  # This file
│
├── static/
│   ├── css/
│   │   └── style.css          # Theming (light/dark), layout, all components
│   ├── js/
│   │   ├── main.js            # Theme, nav, ticker, live search, back-to-top
│   │   └── tools.js           # All 10 working tool engines (client-side)
│   └── images/
│       └── logo.svg           # RK monogram logo
│
└── templates/
    ├── index.html             # Home — hero, search, all 5 categories, contact
    └── tool_view.html         # Tool workspace / calculator / 404
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
- **Naya tool engine** → `ENGINES` router map (static/js/tools.js) + ek `{% if tool.slug == '...' %}`
  block (templates/tool_view.html)

---

## 🔒 Privacy

Har tool sirf browser ke andar chalta hai — `FileReader`, `Canvas` aur `Blob` API use
hote hain. **Koi bhi document server par upload, store ya log nahi hota.** PDF Compressor
aur Image-to-PDF ke liye `pdf-lib` / `jsPDF` CDN se load hote hain; file data inhe bhi
browser mein hi milta hai.

---

## ⚠️ Disclaimer

यह पोर्टल किसी भी सरकार / सरकारी विभाग का आधिकारिक पोर्टल **नहीं** है।
यह केवल CSC ऑपरेटर्स की सुविधा हेतु बनाया गया स्वतंत्र उपयोगिता मंच है।
सभी लिंक संबंधित विभागों की आधिकारिक वेबसाइटों पर जाते हैं।

**Owner:** RAMESH KUMAR — CSC Operator / Jan Seva Kendra
**Phone:** +91 99912-44415 • **Email:** rameshrajput044@gmail.com

© 2026 RKHUB Tools. All Rights Reserved. Made in India 🇮🇳
