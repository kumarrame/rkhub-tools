"""
================================================================================
  RKHUB Tools — Digital India & CSC Services Utility Portal
  Backend  : Flask (Python 3)
  Audience : CSC (Common Service Centre) / Jan Seva Kendra operators
  Privacy  : Every tool runs 100% client-side (Canvas + FileReader).
             No document is ever uploaded to or stored on this server.
================================================================================
  Run:
      pip install -r requirements.txt
      python app.py
      -> open http://127.0.0.1:5000
================================================================================
"""

import datetime as _dt

from flask import Flask, jsonify, render_template

# ==============================================================================
# APP FACTORY
# ==============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = "rkhub-tools-csc-utility-hub-2026"
# Nothing is ever POSTed, but keep a hard ceiling just in case.
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB


# ==============================================================================
# OWNER / OPERATOR DETAILS  (hardcoded as per spec)
# ==============================================================================

OWNER = {
    "name": "RAMESH KUMAR",
    "phone": "+91 99912-44415",
    "phone_raw": "+919991244415",
    "email": "rameshrajput044@gmail.com",
    "role": "CSC Operator / Jan Seva Kendra",
    "centre": "Jan Seva Kendra",
    "city": "Haryana, India",
}

# Contact number doubles as the WhatsApp number.
from urllib.parse import quote as _urlquote

_WA_NUMBER = OWNER["phone_raw"].replace("+", "")
_WA_TEXT = "Namaste Ramesh Kumar, mujhe RKHUB Tools ke baare me jaankari chahiye."
_WA_TEXT_Q = _urlquote(_WA_TEXT, safe="")
OWNER["whatsapp"] = "https://wa.me/%s?text=%s" % (_WA_NUMBER, _WA_TEXT_Q)
OWNER["whatsapp_api"] = "https://api.whatsapp.com/send?phone=%s&text=%s" % (
    _WA_NUMBER,
    _WA_TEXT_Q,
)

SITE = {
    "name": "RKHUB Tools",
    "badge": "CSC Utility Hub",
    "title": "RKHUB Tools — Digital India & CSC Services Utility Portal",
    "subtitle": "All essential daily CSC document processing & utility tools in one place.",
    "tagline_hi": "सरकारी नहीं, पर दावा ईमानदार।",
    "tagline_en": "Not a Government website — but honest about it.",
    "tagline_marks": ["100% Client-Side", "0 Files Stored", "Made in India"],
    "disclaimer": (
        "RKHUB Tools is NOT a Government website and is not affiliated with, "
        "endorsed by, or connected to any Government department, agency or "
        "public body. It is an independent utility platform built purely to "
        "help CSC / Jan Seva Kendra operators."
    ),
    "year": _dt.date.today().year,
}


# ==============================================================================
# NEWS TICKER ITEMS
# ==============================================================================

NEWS = [
    "PMMVY / Pradhan Mantri Matru Vandana Yojana Registration Active",
    "Haryana ULB / Property Tax & Grievance Registration Portal Active",
    "PM-Kisan Installment Update & eKYC Status Check",
    "Aadhaar Mobile Link & Document Update Guidelines",
    "Ayushman Bharat Golden Card — eKYC & Download Active",
    "E-Shram Card Registration & UAN Linking Window Open",
]


# ==============================================================================
# CATEGORIES
# ==============================================================================

CATEGORIES = [
    {
        "id": "document",
        "label": "Document Tools",
        "label_hi": "दस्तावेज़ टूल्स",
        "icon": "pdf",
        "description": "PDF compress, image to PDF, signature aur document crop — sab kuch browser me.",
    },
    {
        "id": "image",
        "label": "Image Tools",
        "label_hi": "इमेज टूल्स",
        "icon": "image",
        "description": "Passport photo maker aur format converter — print-ready output in seconds.",
    },
    {
        "id": "portals",
        "label": "Direct Portals",
        "label_hi": "सरकारी पोर्टल",
        "icon": "link",
        "description": "One click direct access to all major Government service portals.",
    },
    {
        "id": "schemes",
        "label": "Schemes & Services",
        "label_hi": "योजनाएँ और सेवाएँ",
        "icon": "scheme",
        "description": "Welfare schemes, property tax, pension aur grievance registration portals.",
    },
    {
        "id": "calculators",
        "label": "Calculators",
        "label_hi": "कैलकुलेटर",
        "icon": "calculator",
        "description": "Age, stamp duty, CSC commission aur file size — instant & accurate.",
    },
]


# ==============================================================================
# INLINE SVG ICON PATHS  (24x24, stroke based — rendered via Jinja macro)
# ==============================================================================

ICONS = {
    "pdf": (
        '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 3v5h5"/>'
        '<path d="M8.5 17v-3.2h1.3a1.1 1.1 0 0 1 0 2.2H8.5"/>'
        '<path d="M12.8 17v-3.2h1.1a1.6 1.6 0 0 1 0 3.2z"/>'
    ),
    "image": (
        '<rect x="3" y="4" width="18" height="16" rx="2"/>'
        '<circle cx="8.5" cy="9.5" r="1.6"/>'
        '<path d="m4 17 4.5-4.5a2 2 0 0 1 2.8 0L16 17"/>'
        '<path d="m14 15 1.8-1.8a2 2 0 0 1 2.8 0L20 15"/>'
    ),
    "signature": (
        '<path d="M3 17.5c2.5 0 3-9 5-9s1 8 3 8 2.5-5 4-5 1.5 3 3 3h3"/>'
        '<path d="M3 21h18"/>'
    ),
    "crop": '<path d="M6.5 2.5v15h15"/><path d="M2.5 6.5h15v15"/>',
    "camera": (
        '<path d="M3 8.5A2.5 2.5 0 0 1 5.5 6h1.7a1 1 0 0 0 .83-.45l.94-1.4A1 1 0 0 1 9.8 3.7h4.4a1 1 0 0 1 .83.45l.94 1.4a1 1 0 0 0 .83.45h1.7A2.5 2.5 0 0 1 21 8.5v9A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5z"/>'
        '<circle cx="12" cy="13" r="3.5"/>'
    ),
    "convert": '<path d="M4 8h13l-3-3"/><path d="M20 16H7l3 3"/>',
    "calculator": (
        '<rect x="4" y="2.5" width="16" height="19" rx="2"/>'
        '<rect x="7" y="5.5" width="10" height="4" rx="1"/>'
        '<circle cx="8.5" cy="13" r=".9"/><circle cx="12" cy="13" r=".9"/>'
        '<circle cx="15.5" cy="13" r=".9"/><circle cx="8.5" cy="17" r=".9"/>'
        '<circle cx="12" cy="17" r=".9"/><circle cx="15.5" cy="17" r=".9"/>'
    ),
    "calendar": (
        '<rect x="3" y="5" width="18" height="16" rx="2"/>'
        '<path d="M3 10h18M8 3v4M16 3v4"/><circle cx="12" cy="15" r="1"/>'
    ),
    "stamp": (
        '<path d="M9 3h6a2 2 0 0 1 2 2c0 2-2 2.5-2 4h-4c0-1.5-2-2-2-4a2 2 0 0 1 2-2z"/>'
        '<rect x="4" y="13" width="16" height="4" rx="1.5"/><path d="M5 21h14"/>'
    ),
    "rupee": (
        '<path d="M7 4h10M7 8h10M7 12h4c3 0 4-2 4-4"/><path d="m9 13 6 7"/>'
    ),
    "filesize": (
        '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 3v5h5"/><path d="M8 13h8M8 17h5"/>'
    ),
    "link": (
        '<path d="M10.5 13.5a4 4 0 0 0 5.7 0l2.8-2.8a4 4 0 1 0-5.7-5.7L11.9 6.4"/>'
        '<path d="M13.5 10.5a4 4 0 0 0-5.7 0L5 13.3a4 4 0 1 0 5.7 5.7l1.4-1.4"/>'
    ),
    "scheme": (
        '<path d="M12 3 4 6.2V12c0 4.6 3.4 8.4 8 9.6 4.6-1.2 8-5 8-9.6V6.2z"/>'
        '<path d="M12 8.5v3.5M12 15h.01"/>'
    ),
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "kisan": (
        '<path d="M12 21V10"/><path d="M12 10c0-3 2-5.5 5-6-.3 3.4-2.2 5.6-5 6z"/>'
        '<path d="M12 13c0-2.4-1.6-4.4-4-4.8.2 2.8 1.7 4.5 4 4.8z"/>'
    ),
    "card": (
        '<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19"/>'
        '<circle cx="8" cy="14.5" r="2"/><path d="M13 13.5h5M13 16.5h3"/>'
    ),
    "worker": (
        '<circle cx="12" cy="7" r="3"/><path d="M5 21v-2a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v2"/>'
        '<path d="M3.5 7h17"/>'
    ),
    "health": (
        '<path d="M12 21s-7.5-4.6-7.5-10A4.5 4.5 0 0 1 12 7.5 4.5 4.5 0 0 1 19.5 11c0 5.4-7.5 10-7.5 10z"/>'
        '<path d="M12 10v5M9.5 12.5h5"/>'
    ),
    "vote": (
        '<path d="M4 13h16v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/>'
        '<path d="M6 13V4h8l3 3v6"/><path d="m9 8 2 2 4-4"/>'
    ),
    "vehicle": (
        '<path d="M4 16v-3.2L5.8 8A2 2 0 0 1 7.7 6.7h8.6A2 2 0 0 1 18.2 8L20 12.8V16"/>'
        '<path d="M3 16h18"/><circle cx="7.5" cy="17.5" r="1.6"/><circle cx="16.5" cy="17.5" r="1.6"/>'
    ),
    "pan": (
        '<rect x="2.5" y="5" width="19" height="14" rx="2"/><circle cx="8" cy="11" r="2"/>'
        '<path d="M5 16.5a3.2 3.2 0 0 1 6 0"/><path d="M14 10h5M14 14h3"/>'
    ),
    "ration": (
        '<path d="M4 9.5 12 4l8 5.5"/><path d="M6 10.5V20h12v-9.5"/><path d="M9.5 20v-5h5v5"/>'
    ),
    "print": (
        '<path d="M7 8.5V3.5h10v5"/><rect x="3.5" y="8.5" width="17" height="8" rx="2"/>'
        '<path d="M7 14h10v6.5H7z"/><circle cx="17" cy="11.5" r="1"/>'
    ),
    "idcard": (
        '<rect x="2" y="5" width="20" height="14" rx="2.5"/>'
        '<circle cx="8" cy="11" r="2.2"/><path d="M4.8 16.2a3.5 3.5 0 0 1 6.4 0"/>'
        '<path d="M14 10h5M14 13.5h5M14 17h3"/>'
    ),
    "matru": (
        '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1.5A5.5 5.5 0 0 1 9.5 14h5a5.5 5.5 0 0 1 5.5 5.5V21"/>'
        '<path d="M12 4.5c0-1 1-1.5 2-1.5"/>'
    ),
    "building": (
        '<path d="M4 21V6.5L12 3l8 3.5V21"/><path d="M2.5 21h19"/>'
        '<path d="M9 21v-5h6v5"/><path d="M9 10h.01M15 10h.01M9 13.5h.01M15 13.5h.01"/>'
    ),
    "pension": (
        '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'
        '<path d="M9 3.2 10.5 5M15 3.2 13.5 5"/>'
    ),
    "phone": (
        '<path d="M6.5 3h3l1.5 4-2 1.5a12 12 0 0 0 5.5 5.5l1.5-2 4 1.5v3a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 4.5 5.2 2 2 0 0 1 6.5 3z"/>'
    ),
    "mail": (
        '<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>'
    ),
    "pin": (
        '<path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/>'
    ),
    "whatsapp": (
        '<path d="M20.5 11.6a8.5 8.5 0 0 1-12.6 7.5L3.5 20.5l1.5-4.3A8.5 8.5 0 1 1 20.5 11.6z"/>'
        '<path d="M8.9 8.4c.2-.5.4-.5.6-.5h.5c.2 0 .4 0 .6.5l.7 1.7c.1.2 0 .4-.1.6l-.5.6c-.1.2-.3.3-.1.6a6.8 6.8 0 0 0 3 2.6c.3.1.4.1.6-.1l.6-.7c.2-.2.3-.2.6-.1l1.6.8c.3.1.4.3.4.5v.6c-.1.4-.6.9-1 1-.4.2-1 .3-3.2-.4a8.6 8.6 0 0 1-4.3-4.4c-.6-1.3-.2-2.4.2-3z"/>'
    ),
    "user": (
        '<circle cx="12" cy="8" r="3.6"/><path d="M5 21v-1.5A5.5 5.5 0 0 1 10.5 14h3a5.5 5.5 0 0 1 5.5 5.5V21"/>'
    ),
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "sun": (
        '<circle cx="12" cy="12" r="4.2"/>'
        '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8'
        'M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"/>'
    ),
    "moon": '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>',
    "shield": (
        '<path d="M12 3 5 6v5.5c0 4.4 3 8.1 7 9.5 4-1.4 7-5.1 7-9.5V6z"/>'
        '<path d="m9 12 2.2 2.2L15.5 10"/>'
    ),
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
    "pause": '<path d="M9 5v14M15 5v14"/>',
    "play": '<path d="M7 4.5v15l13-7.5z"/>',
    "upload": (
        '<path d="M12 16V4"/><path d="m7.5 8.5 4.5-4.5 4.5 4.5"/>'
        '<path d="M4 15v3.5A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V15"/>'
    ),
    "download": (
        '<path d="M12 4v12"/><path d="m7.5 11.5 4.5 4.5 4.5-4.5"/>'
        '<path d="M4 15v3.5A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V15"/>'
    ),
    "arrow": '<path d="M4 12h15"/><path d="m13 6 6 6-6 6"/>',
    "external": (
        '<path d="M14 4h6v6"/><path d="M20 4 11 13"/>'
        '<path d="M18 14v5a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19V7.5A1.5 1.5 0 0 1 5 6h5"/>'
    ),
    "check": '<path d="m5 12.5 4.5 4.5L19 7"/>',
    "seal": (
        '<circle cx="12" cy="9.5" r="5.5"/>'
        '<path d="m9.2 9.6 1.9 1.9 3.7-3.9"/>'
        '<path d="M8.5 14.5 7 21.5l5-2.2 5 2.2-1.5-7"/>'
    ),
    "hand": (
        '<path d="M9 11V5.5a1.6 1.6 0 0 1 3.2 0V11"/>'
        '<path d="M12.2 10.5V4.6a1.6 1.6 0 0 1 3.2 0v5.9"/>'
        '<path d="M15.4 11V6.6a1.6 1.6 0 0 1 3.2 0V13"/>'
        '<path d="M6.4 12.4 5.2 11a1.6 1.6 0 0 0-2.3 2.2l3.6 5.2A7 7 0 0 0 12.4 21h1.9a5 5 0 0 0 5-5v-4.2"/>'
    ),
    "spark": '<path d="M12 3v5M12 16v5M3 12h5M16 12h5M6.3 6.3l3.5 3.5M14.2 14.2l3.5 3.5M17.7 6.3l-3.5 3.5M9.8 14.2l-3.5 3.5"/>',
    "lock": (
        '<rect x="4.5" y="10" width="15" height="10.5" rx="2"/>'
        '<path d="M8 10V7.5a4 4 0 0 1 8 0V10"/>'
    ),
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "cake": (
        '<path d="M4 20h16"/><path d="M5 20v-6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v6"/>'
        '<path d="M4 14c1.5 0 1.5 1.5 3 1.5S8.5 14 10 14s1.5 1.5 3 1.5S14.5 14 16 14s1.5 1.5 3 1.5"/>'
    ),
    "passport": (
        '<rect x="5" y="3" width="14" height="18" rx="2"/>'
        '<circle cx="12" cy="9.5" r="3"/>'
        '<path d="M9 16h6"/>'
    ),
    "coins": (
        '<ellipse cx="12" cy="6.5" rx="6.5" ry="2.6"/>'
        '<path d="M5.5 6.5v4.8c0 1.4 2.9 2.6 6.5 2.6s6.5-1.2 6.5-2.6V6.5"/>'
        '<path d="M5.5 11.3v4.8c0 1.4 2.9 2.6 6.5 2.6s6.5-1.2 6.5-2.6v-4.8"/>'
    ),
    "monitor": (
        '<rect x="3" y="4" width="18" height="12" rx="2"/>'
        '<path d="M8.5 20h7M12 16v4"/>'
    ),
    "bolt": '<path d="M13 2 4.5 13.5H11l-1 8.5L19.5 10H13z"/>',
    "family": (
        '<circle cx="8" cy="8.5" r="3"/><circle cx="16" cy="10" r="2.4"/>'
        '<path d="M3 19.5v-1.3A4.2 4.2 0 0 1 7.2 14h1.6A4.2 4.2 0 0 1 13 18.2v1.3"/>'
        '<path d="M14.8 19.5v-1.3a4.1 4.1 0 0 1 2.2-3.6"/>'
    ),
    "certificate": (
        '<rect x="4" y="3" width="16" height="12.5" rx="1.6"/>'
        '<path d="M7 7.2h10M7 10.6h6"/>'
        '<circle cx="12" cy="16.8" r="2.7"/>'
        '<path d="M10.2 18.9 9 22.4l3-1.5 3 1.5-1.2-3.5"/>'
    ),
}


# ==============================================================================
# TOOLS  (31 total — internal engines + external Government portals)
# ==============================================================================

TOOLS = [
    # ---------------------------------------------------- A. DOCUMENT TOOLS ---
    {
        "slug": "pdf-compressor",
        "name": "PDF Compressor & Resizer",
        "name_hi": "पीडीएफ कंप्रेसर",
        "category": "document",
        "icon": "pdf",
        "accent": "red",
        "badge": "Popular",
        "tag": "PDF",
        "summary": "Compress heavy PDF for online form upload. Light / Medium / Strong target sizes.",
        "keywords": "pdf compress reduce shrink resize size upload form compress",
        "kind": "internal",
    },
    {
        "slug": "image-to-pdf",
        "name": "Image to PDF Converter",
        "name_hi": "इमेज से पीडीएफ",
        "category": "document",
        "icon": "image",
        "accent": "navy",
        "badge": "Free",
        "tag": "PDF",
        "summary": "Merge multiple JPG / PNG images into one ordered PDF. A4, Letter or auto page size.",
        "keywords": "image jpg png to pdf convert merge combine document pages",
        "kind": "internal",
    },
    {
        "slug": "signature-extractor",
        "name": "Signature & Thumb Extractor",
        "name_hi": "सिग्नेचर और अंगूठा",
        "category": "document",
        "icon": "signature",
        "accent": "amber",
        "badge": "B&W",
        "tag": "Edit",
        "summary": "Cut a clean signature or thumb impression from a scanned page. Contrast + threshold control.",
        "keywords": "signature thumb impression extract black white contrast threshold scan b&w",
        "kind": "internal",
    },
    {
        "slug": "document-crop",
        "name": "Document Crop & Auto-Enhance",
        "name_hi": "डॉक्यूमेंट क्रॉप",
        "category": "document",
        "icon": "crop",
        "accent": "navy",
        "badge": "Enhance",
        "tag": "Edit",
        "summary": "Trim scanned certificates edge-to-edge and auto-enhance them for a clear upload.",
        "keywords": "document crop trim enhance sharpen scan certificate autocrop",
        "kind": "internal",
    },

    # ------------------------------------------------------ B. IMAGE TOOLS ---
    {
        "slug": "passport-photo",
        "name": "Passport Photo Maker",
        "name_hi": "पासपोर्ट फोटो मेकर",
        "category": "image",
        "icon": "camera",
        "accent": "red",
        "badge": "3.5×4.5",
        "tag": "Photo",
        "summary": "3.5 cm x 4.5 cm passport size photo @300 DPI with background colour changer.",
        "keywords": "passport photo 3.5 4.5 size background change crop stamp print sheet",
        "kind": "internal",
    },
    {
        "slug": "format-converter",
        "name": "JPG to PNG / WebP Converter",
        "name_hi": "इमेज कन्वर्टर",
        "category": "image",
        "icon": "convert",
        "accent": "amber",
        "badge": "Free",
        "tag": "Image",
        "summary": "Convert images between JPG, PNG and WebP with quality and max-width control.",
        "keywords": "jpg png webp convert format image quality resize compress",
        "kind": "internal",
    },
    {
        "slug": "photo-sheet",
        "name": "Photo Sheet Printer",
        "name_hi": "फोटो शीट प्रिंटर",
        "category": "image",
        "icon": "print",
        "accent": "red",
        "badge": "4–36",
        "tag": "Print",
        "summary": "Ek photo se 4 se 36 passport-size photos ek A4 sheet pe print-ready layout me.",
        "keywords": "photo sheet print passport multiple photos a4 4 6 8 12 24 sheet cutting",
        "kind": "internal",
    },
    {
        "slug": "pvc-card",
        "name": "PVC Card Maker",
        "name_hi": "पीवीसी कार्ड मेकर",
        "category": "image",
        "icon": "idcard",
        "accent": "navy",
        "badge": "CR80",
        "tag": "Card",
        "summary": "Photo, naam, DOB, blood group ke saath printable PVC card banayein — CR80 size.",
        "keywords": "pvc card id card maker cr80 visiting card aadhaar pan voter design print",
        "kind": "internal",
    },

    # -------------------------------------------------- C. DIRECT PORTALS ---
    {
        "slug": "pm-kisan",
        "name": "PM-Kisan Samman Nidhi",
        "name_hi": "पीएम किसान सम्मान निधि",
        "category": "portals",
        "icon": "kisan",
        "accent": "green",
        "badge": "Official",
        "tag": "Portal",
        "summary": "eKYC, beneficiary status, installment tracking aur new farmer registration.",
        "keywords": "pm kisan samman nidhi ekyc installment farmer status registration",
        "kind": "external",
        "url": "https://pmkisan.gov.in/",
    },
    {
        "slug": "aadhaar-services",
        "name": "Aadhaar Services & Download",
        "name_hi": "आधार सेवाएँ",
        "category": "portals",
        "icon": "card",
        "accent": "red",
        "badge": "Official",
        "tag": "Portal",
        "summary": "Aadhaar download, PVC card order, mobile linking, address update & verification.",
        "keywords": "aadhaar uidai download pvc mobile link address update mera aadhaar",
        "kind": "external",
        "url": "https://myaadhaar.uidai.gov.in/",
    },
    {
        "slug": "e-shram",
        "name": "E-Shram & Labour Registration",
        "name_hi": "ई-श्रम श्रमिक पंजीकरण",
        "category": "portals",
        "icon": "worker",
        "accent": "amber",
        "badge": "",
        "tag": "Portal",
        "summary": "Register unorganised workers, download UAN card and update the e-Shram profile.",
        "keywords": "e shram eshram labour worker uan card registration unorganised",
        "kind": "external",
        "url": "https://eshram.gov.in/",
    },
    {
        "slug": "pmjay",
        "name": "Ayushman Bharat Golden Card",
        "name_hi": "आयुष्मान भारत गोल्डन कार्ड",
        "category": "portals",
        "icon": "health",
        "accent": "green",
        "badge": "₹5 Lakh",
        "tag": "Portal",
        "summary": "Eligibility check, Golden Card download, hospital empanelment and claim support.",
        "keywords": "ayushman bharat pmjay golden card health insurance hospital claim",
        "kind": "external",
        "url": "https://pmjay.gov.in/",
    },
    {
        "slug": "voter-id",
        "name": "Voter ID Card Services (ECI)",
        "name_hi": "वोटर आईडी कार्ड सेवाएँ",
        "category": "portals",
        "icon": "vote",
        "accent": "navy",
        "badge": "",
        "tag": "Portal",
        "summary": "New voter registration (Form 6), correction, duplicate Voter ID and status check.",
        "keywords": "voter id nvsp eci form 6 form 8 correction duplicate election commission",
        "kind": "external",
        "url": "https://voters.eci.gov.in/",
    },
    {
        "slug": "parivahan",
        "name": "Parivahan — DL & Vehicle RC",
        "name_hi": "परिवहन — डीएल और आरसी",
        "category": "portals",
        "icon": "vehicle",
        "accent": "amber",
        "badge": "",
        "tag": "Portal",
        "summary": "Driving licence, vehicle RC transfer, fitness, permit and challan services.",
        "keywords": "parivahan driving licence dl rc vehicle transfer fitness permit challan",
        "kind": "external",
        "url": "https://parivahan.gov.in/parivahan/",
    },
    {
        "slug": "pan-card",
        "name": "PAN Card Apply & Correction",
        "name_hi": "पैन कार्ड आवेदन एवं सुधार",
        "category": "portals",
        "icon": "pan",
        "accent": "red",
        "badge": "NSDL / UTI",
        "tag": "Portal",
        "summary": "New PAN application, correction, reprint and Aadhaar-PAN linking.",
        "keywords": "pan card nsdl utiitsl apply correction reprint link aadhaar new pan",
        "kind": "external",
        "url": "https://onlineservices.nsdl.com/",
    },
    {
        "slug": "ration-card",
        "name": "Ration Card Online (NFSA)",
        "name_hi": "राशन कार्ड ऑनलाइन",
        "category": "portals",
        "icon": "ration",
        "accent": "green",
        "badge": "NFSA",
        "tag": "Portal",
        "summary": "New ration card, member add / delete, e-KYC and One Nation One Card portability.",
        "keywords": "ration card nfsa one nation one card ekyc add member delete",
        "kind": "external",
        "url": "https://nfsa.gov.in/",
    },
    {
        "slug": "passport-seva",
        "name": "Passport Seva",
        "name_hi": "पासपोर्ट सेवा",
        "category": "portals",
        "icon": "passport",
        "accent": "red",
        "badge": "Official",
        "tag": "Portal",
        "summary": "New passport application, appointment booking, status tracking aur police clearance.",
        "keywords": "passport seva passportindia application appointment renewal tatkal status pcc mea",
        "kind": "external",
        "url": "https://www.passportindia.gov.in/",
    },
    {
        "slug": "epfo-uan",
        "name": "EPFO Member Portal (UAN)",
        "name_hi": "ईपीएफओ सदस्य पोर्टल (UAN)",
        "category": "portals",
        "icon": "coins",
        "accent": "amber",
        "badge": "PF",
        "tag": "Portal",
        "summary": "PF balance, passbook download, UAN activation aur online withdrawal claim.",
        "keywords": "epfo uan pf balance passbook provident fund withdrawal claim member portal pension",
        "kind": "external",
        "url": "https://unifiedportal-mem.epfindia.gov.in/",
    },
    {
        "slug": "csc-digital-seva",
        "name": "e-District / CSC Digital Seva",
        "name_hi": "ई-डिस्ट्रिक्ट / CSC डिजिटल सेवा",
        "category": "portals",
        "icon": "monitor",
        "accent": "navy",
        "badge": "VLE",
        "tag": "Portal",
        "summary": "CSC VLE official portal — citizen services, certificates, bill payments aur recharges.",
        "keywords": "csc digital seva e district vle common service centre citizen services portal login",
        "kind": "external",
        "url": "https://digitalseva.csc.gov.in/",
    },
    {
        "slug": "dhbvn-uhbvn",
        "name": "DHBVN / UHBVN Power Utilities",
        "name_hi": "डीएचबीवीएन / यूएचबीवीएन बिजली",
        "category": "portals",
        "icon": "bolt",
        "accent": "green",
        "badge": "Bill",
        "tag": "Portal",
        "summary": "Haryana bijli bill payment, new connection, load change aur complaint registration.",
        "keywords": "dhbvn uhbvn haryana electricity bill payment new connection load complaint power",
        "kind": "external",
        "url": "https://uhbvn.org.in/",
    },

    # ------------------------------------------- D. SCHEMES & SERVICES ---
    {
        "slug": "pmmvy",
        "name": "PMMVY — Matru Vandana Yojana",
        "name_hi": "प्रधानमंत्री मातृ वंदना योजना",
        "category": "schemes",
        "icon": "matru",
        "accent": "red",
        "badge": "Active",
        "tag": "Scheme",
        "summary": "Matru Vandana Yojana new registration, beneficiary status and instalment payment status.",
        "keywords": "pmmvy matru vandana yojana pmv scheme pregnant women registration benefit",
        "kind": "external",
        "url": "https://pmmvy.wcd.gov.in/",
    },
    {
        "slug": "haryana-ulb",
        "name": "Haryana ULB — Property Tax",
        "name_hi": "हरियाणा ULB — प्रॉपर्टी टैक्स",
        "category": "schemes",
        "icon": "building",
        "accent": "navy",
        "badge": "Haryana",
        "tag": "Scheme",
        "summary": "ULB property tax payment, house tax receipt and online grievance registration.",
        "keywords": "haryana ulb property tax house tax grievance complaint municipal corporation",
        "kind": "external",
        "url": "https://ulbharyana.gov.in/",
    },
    {
        "slug": "pension-portal",
        "name": "Pension Portal (Haryana)",
        "name_hi": "पेंशन पोर्टल",
        "category": "schemes",
        "icon": "pension",
        "accent": "green",
        "badge": "Haryana",
        "tag": "Scheme",
        "summary": "Old age pension, widow pension, disability pension application and beneficiary status.",
        "keywords": "pension old age widow disability social justice haryana laghu nagi",
        "kind": "external",
        "url": "https://pension.socialjusticehry.gov.in/",
    },
    {
        "slug": "pm-surya-ghar",
        "name": "PM Surya Ghar — Rooftop Solar",
        "name_hi": "पीएम सूर्य घर — रूफटॉप सोलर",
        "category": "schemes",
        "icon": "sun",
        "accent": "amber",
        "badge": "Solar",
        "tag": "Scheme",
        "summary": "Rooftop solar registration, vendor selection aur subsidy application — up to 300 units free.",
        "keywords": "pm surya ghar rooftop solar subsidy registration free electricity 300 units scheme",
        "kind": "external",
        "url": "https://pmsuryaghar.gov.in/",
    },
    {
        "slug": "parivar-pehchan-patra",
        "name": "Parivar Pehchan Patra (PPP)",
        "name_hi": "परिवार पहचान पत्र (PPP)",
        "category": "schemes",
        "icon": "family",
        "accent": "navy",
        "badge": "Family ID",
        "tag": "Scheme",
        "summary": "Haryana Family ID download, member update, income verification aur split / merge.",
        "keywords": "parivar pehchan patra ppp family id haryana meraparivar update income split merge",
        "kind": "external",
        "url": "https://meraparivar.haryana.gov.in/",
    },
    {
        "slug": "saral-haryana",
        "name": "Saral Haryana Portal",
        "name_hi": "सरल हरियाणा पोर्टल",
        "category": "schemes",
        "icon": "certificate",
        "accent": "green",
        "badge": "Haryana",
        "tag": "Scheme",
        "summary": "Caste, income aur residence certificates plus saari state schemes ek hi jagah.",
        "keywords": "saral haryana caste income residence domicile certificate state schemes edisha",
        "kind": "external",
        "url": "https://saralharyana.gov.in/",
    },
    {
        "slug": "meri-fasal-mera-byora",
        "name": "Meri Fasal Mera Byora (MFMB)",
        "name_hi": "मेरी फसल मेरा ब्यौरा",
        "category": "schemes",
        "icon": "kisan",
        "accent": "amber",
        "badge": "Haryana",
        "tag": "Scheme",
        "summary": "Crop registration for MSP purchase, land verification aur e-Kharid enrolment.",
        "keywords": "meri fasal mera byora mfmb haryana crop registration msp kharid farmer fasal",
        "kind": "external",
        "url": "https://fasal.haryana.gov.in/",
    },

    # -------------------------------------------------- E. CALCULATORS ---
    {
        "slug": "age-calculator",
        "name": "Official Form Age Calculator",
        "name_hi": "आयु कैलकुलेटर",
        "category": "calculators",
        "icon": "calendar",
        "accent": "red",
        "badge": "Popular",
        "tag": "Calculator",
        "summary": "Exact age in years / months / days as on any date, plus next birthday and total days.",
        "keywords": "age calculator dob date of birth years months days form fill",
        "kind": "internal",
    },
    {
        "slug": "stamp-duty",
        "name": "Stamp Duty & Fee Estimator",
        "name_hi": "स्टांप ड्यूटी एस्टीमेटर",
        "category": "calculators",
        "icon": "stamp",
        "accent": "amber",
        "badge": "",
        "tag": "Calculator",
        "summary": "Estimate stamp duty, registration fee and total government charge on property value.",
        "keywords": "stamp duty registration fee property estimate haryana delhi up govt charge",
        "kind": "internal",
    },
    {
        "slug": "csc-commission",
        "name": "CSC Commission & Tax Calculator",
        "name_hi": "CSC कमीशन कैलकुलेटर",
        "category": "calculators",
        "icon": "rupee",
        "accent": "navy",
        "badge": "",
        "tag": "Calculator",
        "summary": "Calculate service commission, TDS, GST and net profit after expenses — instantly.",
        "keywords": "csc commission tax tds gst calculator earning profit vle operator",
        "kind": "internal",
    },
    {
        "slug": "file-size-converter",
        "name": "File Size Unit Converter",
        "name_hi": "फाइल साइज कन्वर्टर",
        "category": "calculators",
        "icon": "filesize",
        "accent": "green",
        "badge": "",
        "tag": "Calculator",
        "summary": "Live Bytes → KB → MB → GB → TB conversion with exact precision.",
        "keywords": "file size kb mb gb tb bytes convert unit upload limit",
        "kind": "internal",
    },
]


# ==============================================================================
# DERIVED DATA + CONTEXT PROCESSOR
# ==============================================================================

_CAT_IDS = {c["id"] for c in CATEGORIES}


def tools_by_cat():
    """Return an ordered dict-like list of (category, [tools]) pairs."""
    out = []
    for cat in CATEGORIES:
        items = [t for t in TOOLS if t["category"] == cat["id"]]
        out.append((cat, items))
    return out


def find_tool(slug):
    for t in TOOLS:
        if t["slug"] == slug:
            return t
    return None


@app.context_processor
def inject_globals():
    grouped = tools_by_cat()
    internal = [t for t in TOOLS if t["kind"] == "internal"]
    external = [t for t in TOOLS if t["kind"] == "external"]
    return {
        "OWNER": OWNER,
        "SITE": SITE,
        "NEWS": NEWS,
        "CATEGORIES": CATEGORIES,
        "TOOLS": TOOLS,
        "ICONS": ICONS,
        "GROUPED": grouped,
        "INTERNAL_TOOLS": internal,
        "EXTERNAL_TOOLS": external,
        "STATS": {
            "total": len(TOOLS),
            "internal": len(internal),
            "external": len(external),
            "portals": len(external),
            "stored": 0,
        },
    }


# ==============================================================================
# ROUTES
# ==============================================================================

@app.route("/")
def index():
    return render_template("index.html", page="home")


@app.route("/tool/<slug>")
def tool_view(slug):
    tool = find_tool(slug)
    if tool is None:
        return render_template("tool_view.html", page="tool", tool=None, notfound=True), 404
    if tool["kind"] == "external":
        # External portals never need a workspace page — bounce to the portal.
        from flask import redirect
        return redirect(tool["url"], code=302)
    return render_template("tool_view.html", page="tool", tool=tool, notfound=False)


@app.route("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "app": SITE["name"],
            "version": "1.0.0",
            "tools": len(TOOLS),
            "internal": len([t for t in TOOLS if t["kind"] == "internal"]),
            "external": len([t for t in TOOLS if t["kind"] == "external"]),
            "files_stored": 0,
        }
    )


@app.errorhandler(404)
def handle_404(_err):
    return render_template("tool_view.html", page="404", tool=None, notfound=True), 404


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    print("=" * 62)
    print(f"  {SITE['name']}  ->  http://127.0.0.1:5000")
    print(f"  Owner  : {OWNER['name']}  |  {OWNER['phone']}")
    print(f"  Tools  : {len(TOOLS)} total  ({len([t for t in TOOLS if t['kind'] == 'internal'])} internal / "
          f"{len([t for t in TOOLS if t['kind'] == 'external'])} portals)")
    print("=" * 62)
    app.run(host="0.0.0.0", port=5000, debug=True)
