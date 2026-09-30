"""
================================================================================
  RKHUB Tools — Independent Digital Utilities Hub
  Backend  : Flask (Python 3)
  Audience : Common Service Centre (CSC) / Jan Seva Kendra operators
  Privacy  : Every tool runs 100% client-side (Canvas + FileReader).
             No document is ever uploaded to or stored on this server.

  Trademark note: "Digital India", "CSC", "Common Service Centre" and
  "Jan Seva Kendra" are marks/proper names of third parties. This project
  uses them only descriptively, to identify its intended audience and the
  official portals it links to. See NOTICE.md.
================================================================================
  Run:
      pip install -r requirements.txt
      python app.py
      -> open http://127.0.0.1:5000
================================================================================
"""

import datetime as _dt
import gzip
import ipaddress
import os
import secrets
import time

from flask import Flask, jsonify, redirect, render_template, request

# ==============================================================================
# APP FACTORY
# ==============================================================================

app = Flask(__name__)

# Never ship a checked-in secret. In production, set SECRET_KEY in the
# environment. The random fallback is safe because it is regenerated on every
# restart, which simply invalidates old sessions instead of failing loudly.
_ENV_SECRET = os.environ.get("SECRET_KEY", "").strip()
app.config["SECRET_KEY"] = _ENV_SECRET or secrets.token_hex(32)

# Nothing is ever POSTed, but keep a hard ceiling just in case.
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

# Debug mode must never default to on: the Werkzeug debugger exposes a console
# that can execute arbitrary Python if an error page is ever reached.
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

# Reject requests whose Host header is not on the allow-list (mitigates
# host-header poisoning and cache-poisoning via absolute URL generation).
_trusted_hosts = [
    h.strip()
    for h in os.environ.get("TRUSTED_HOSTS", "").split(",")
    if h.strip()
]
if _trusted_hosts:
    app.config["TRUSTED_HOSTS"] = _trusted_hosts

# Trust X-Forwarded-For for client identification. MUST be enabled on any
# platform that fronts the app with a proxy (Render, Railway, Fly, nginx),
# otherwise every visitor shares the proxy's remote_addr and the rate limiter
# treats the entire internet as one client. See _client_key().
#
# Only safe because the platform overwrites the header on ingress. Leave it
# off when the app is exposed directly, or a client could spoof its address
# and bypass the limiter entirely.
app.config["TRUST_PROXY"] = os.environ.get("TRUST_PROXY", "0") == "1"

# Compress HTML/CSS/JS/JSON. The vendored JS libs are large and highly
# compressible, so this is the single biggest latency win available.
#
# Flask has no built-in gzip and Werkzeug does not ship a GzipMiddleware (that
# import would raise ModuleNotFoundError on every boot), so compression is done
# in after_request below instead. It costs a little CPU per response but keeps
# the dependency list at exactly one package.
GZIP_MIN_BYTES = 500
GZIP_CONTENT_TYPES = (
    "text/",
    "application/javascript",
    "application/json",
    "application/xml",
    "image/svg+xml",
)

# Emit security headers on every response. Applied in after_request rather than
# per-route so a new route cannot accidentally ship without them.
CSP = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        # 'unsafe-inline' is required for the per-tool style="--accent:..." and
        # width/height attributes emitted by the Jinja templates, and for the
        # existing inline JSON bootstrap payload in main.js. Script-src stays
        # strict with NO 'unsafe-inline' and NO 'unsafe-eval'.
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self'",
        # All tooling is client-side, so no outbound connections are expected.
        "connect-src 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "manifest-src 'self'",
        "upgrade-insecure-requests",
    ]
)

# Cache policy for static assets. HTML must stay revalidatable so a deploy is
# visible immediately.
#
# The static filenames are NOT content-hashed (they are plain style.css,
# main.js, tools.js), so a long "immutable" max-age is deliberately NOT used:
# it would let a returning visitor keep a stale copy of main.js for a year
# with no revalidation, which is how a deploy silently fails to reach users.
#
# A short max-age plus must-revalidate gets almost all of the benefit: repeat
# views inside the window are served from cache with no request at all, and
# the first view after a deploy gets a cheap 304 from the ETag that send_file
# already sets. Raising this to a year is only safe once the URLs carry a
# content hash (e.g. style.<hash>.css).
_STATIC_CACHE = "public, max-age=600, must-revalidate"
_HTML_CACHE = "no-cache"


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
    "badge": "Operator Utility Hub",
    # "Digital India" is a registered trademark of MeitY/NeGD and its usage
    # guidelines prohibit using the name as a product or service name. It is
    # deliberately absent from the title. Scheme names below are used purely
    # descriptively, to identify the official portals that are linked.
    "title": "RKHUB Tools — Independent Digital Utilities Hub",
    "subtitle": "All essential daily operator document & utility tools in one place.",
    "tagline_hi": "सरकारी नहीं, पर दावा ईमानदार।",
    "tagline_en": "Not a Government website — but honest about it.",
    # Note: "Made in India" is a Government of India trademarked certification
    # mark that normally requires registration. The owner's decision is to keep
    # the plain-text footer credit in templates/index.html rather than drop it,
    # so the mark is not restyled into a certification claim anywhere (no logo,
    # no badge). These three badges are the unambiguous alternative.
    "tagline_marks": ["100% Client-Side", "0 Files Stored", "No Sign-Up"],
    "disclaimer": (
        "RKHUB Tools is NOT a Government website and is not affiliated with, "
        "endorsed by, sponsored by, or connected to any Government department, "
        "agency, or public body. It is an independent utility platform built to "
        "help service-centre operators. References to government schemes and "
        "portals are descriptive only; all official work happens on the "
        "respective Government portal."
    ),
    # Used to build absolute URLs for robots.txt and sitemap.xml.
    "canonical": os.environ.get(
        "CANONICAL_URL", "https://rkhub-tools.onrender.com"
    ).rstrip("/"),
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
        # Deliberately positioned as an organisation / membership / event card
        # generator. The previous copy invited use as a counterfeit government
        # ID, which carries trademark, consumer-protection and criminal risk.
        "summary": (
            "Organisation, membership, event ya staff ke liye printable CR80 "
            "PVC card banayein — koi Government ID nahi."
        ),
        "keywords": (
            "pvc card id card maker cr80 membership staff event library "
            "organisation card design print blank card template"
        ),
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
_CAT_BY_ID = {c["id"]: c for c in CATEGORIES}


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


# ==============================================================================
# RATE LIMITING
# ==============================================================================
#  Windowed request counter kept in process memory. This is intentionally
#  dependency-free and works correctly for a single-process deployment
#  (gunicorn 1 worker + threads, see Procfile). If the app is ever scaled
#  horizontally, swap this for a shared store such as Redis.
#
#  Note this is a fixed window anchored at a client's first request, not a
#  true sliding window: the bucket resets once the window elapses regardless of
#  the individual timestamps inside it. The consequence is a theoretical 2x
#  burst across a window boundary (limit at the end of one window, then limit
#  again immediately after the reset). That trade-off is accepted here because
#  the limiter exists to bound CPU abuse, not to enforce a hard quota.
#
#  Worker count matters here. The bucket dict is per-process, so N workers
#  means N independent limiters and the effective ceiling becomes
#  N x the number below. With --workers 2 the documented "120 page views per
#  minute" was silently 240, and no single visitor's traffic was ever visible
#  to the other worker. The Procfile therefore pins one worker with threads.
#
#  Design goals:
#    * Protect the server from being used as a free CPU/memory amplifier.
#    * Never punish the normal visitor: a page view plus a few static assets
#      must stay comfortably under the ceiling, and a rate-limited response
#      must be short-circuited BEFORE any template is rendered.
# ==============================================================================

RATE_LIMIT = {
    # Health checks are called by the platform's uptime monitor, so they are
    # deliberately exempt.
    "exempt_paths": {"/api/health"},
    # Per-window limits. The window is a fixed 60 seconds.
    "window": 60,
    "limits": {
        # HTML pages: cheap to serve, so allow generous headroom for a human
        # clicking through tools.
        "page": 120,
        # Static assets: a single page load requests several; allow a lot.
        "static": 600,
        # JSON/redirect endpoints: tightest, since nothing legitimate loops here.
        "api": 60,
    },
    # Cap the number of tracked client keys so a spoofed-IP flood cannot grow
    # the dict without bound (memory-exhaustion vector).
    "max_tracked_clients": 8192,
}

# path -> (window_start, [timestamps])
_rate_buckets: dict = {}
_rate_last_sweep = time.monotonic()


def _valid_ip(value: str) -> bool:
    """True if value is a bare IPv4/IPv6 address.

    Used to reject junk before it becomes a dict key. Without this check an
    attacker can send an arbitrary X-Forwarded-For and mint an unlimited
    number of rate-limit buckets, which both defeats the limiter and burns
    memory.
    """
    if not value or len(value) > 45:
        return False
    for ch in value:
        if ch not in "0123456789abcdefABCDEF.:%[] ":
            return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _client_key() -> str:
    """Best-effort client identity.

    Behind a reverse proxy (Render, any PaaS) every request shares one
    remote_addr, so the limiter would treat the whole internet as a single
    client and lock out real visitors. When TRUST_PROXY is on, the left-most
    X-Forwarded-For entry is the original client.

    Trusting that header is only safe because the platform strips and
    rewrites it on the way in; a directly exposed origin would let a client
    spoof any address and escape the limiter entirely. That is exactly why
    this stays off unless the deployment explicitly turns it on.
    """
    if app.config.get("TRUST_PROXY"):
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Left-most entry is the original client; the rest were appended
            # by each proxy in the chain.
            candidate = forwarded.split(",")[0].strip()
            if _valid_ip(candidate):
                return candidate
            # Malformed header: fall through to remote_addr rather than
            # bucketing every junk value separately.
    return request.remote_addr or "unknown"


def _limit_for(path: str) -> int:
    if path.startswith("/static/"):
        return RATE_LIMIT["limits"]["static"]
    if path.startswith("/api/"):
        return RATE_LIMIT["limits"]["api"]
    return RATE_LIMIT["limits"]["page"]


@app.before_request
def apply_rate_limit():
    # _rate_last_sweep is rebound below, so it must be declared global. Without
    # this, Python treats the name as function-local and every request raises
    # UnboundLocalError. _rate_buckets is only mutated, never rebound, so it
    # needs no declaration.
    global _rate_last_sweep

    if app.config.get("DEBUG"):
        return None
    path = request.path
    if path in RATE_LIMIT["exempt_paths"]:
        return None

    now = time.monotonic()
    window = RATE_LIMIT["window"]
    limit = _limit_for(path)
    key = (path.split("/")[1] if path.startswith("/") else "", _client_key())

    # Periodic sweep so stale buckets do not accumulate.
    if now - _rate_last_sweep > window:
        cutoff = now - window
        stale = [k for k, v in _rate_buckets.items() if v[0] <= cutoff]
        for k in stale:
            _rate_buckets.pop(k, None)
        _rate_last_sweep = now

    start, hits = _rate_buckets.get(key, (now, []))

    if len(_rate_buckets) >= RATE_LIMIT["max_tracked_clients"] and key not in _rate_buckets:
        # Fail open rather than grow unbounded; the bucket cap is a memory
        # guard, not an abuse decision.
        return None

    if now - start >= window:
        start, hits = now, []

    hits.append(now)

    if len(hits) > limit:
        retry_after = max(1, int(window - (now - start)) + 1)
        resp = jsonify({"error": "rate_limited", "retry_after_seconds": retry_after})
        resp.status_code = 429
        resp.headers["Retry-After"] = str(retry_after)
        return resp

    _rate_buckets[key] = (start, hits)
    return None


@app.after_request
def apply_gzip(resp):
    """Compress the response body when the client accepts gzip.

    Static files arrive from send_file with direct_passthrough=True and an
    unbuffered file wrapper. That wrapper cannot be compressed, but the
    vendored JS is exactly the payload worth compressing, so the flag is
    cleared and the body is materialised before compressing. The files are
    capped by MAX_CONTENT_LENGTH concerns only in the sense that they are
    build-time assets of known size (largest is ~525 kB), so buffering is
    bounded and safe here.
    """
    if "gzip" not in request.headers.get("Accept-Encoding", ""):
        return resp
    if resp.headers.get("Content-Encoding"):
        return resp
    if resp.status_code < 200 or resp.status_code in (204, 304):
        return resp
    if not (resp.mimetype or "").startswith(GZIP_CONTENT_TYPES):
        return resp

    if resp.direct_passthrough:
        # Materialise the file wrapper so the body can be read and replaced.
        resp.direct_passthrough = False

    data = resp.get_data()
    if len(data) < GZIP_MIN_BYTES:
        return resp

    compressed = gzip.compress(data, compresslevel=6)
    # Only worth it if we actually saved something meaningful.
    if len(compressed) >= len(data):
        return resp

    resp.set_data(compressed)
    resp.headers["Content-Encoding"] = "gzip"
    resp.headers["Content-Length"] = str(len(compressed))
    # Caches must key on Accept-Encoding now that the body varies by it.
    resp.headers.add("Vary", "Accept-Encoding")
    return resp


@app.after_request
def apply_security_headers(resp):
    resp.headers.setdefault("Content-Security-Policy", CSP)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault(
        "Permissions-Policy",
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()",
    )
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    resp.headers.setdefault("X-Robots-Tag", "index, follow")

    # Only meaningful over TLS; harmless and cheap over plain HTTP.
    resp.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )

    if request.path.startswith("/static/"):
        # Assign, do not setdefault: Flask's send_file() has already set its
        # own Cache-Control, so setdefault() would silently do nothing and the
        # policy below would never take effect.
        resp.headers["Cache-Control"] = _STATIC_CACHE
    else:
        # setdefault is correct here: routes such as robots.txt and
        # sitemap.xml deliberately set their own longer cache, and that
        # must not be clobbered.
        resp.headers.setdefault("Cache-Control", _HTML_CACHE)

    return resp


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
        "CATEGORY_BY_ID": _CAT_BY_ID,
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
        # Only the allow-listed tool["url"] values are ever redirected to, and
        # those are hardcoded HTTPS government/portal URLs, never user input.
        return redirect(tool["url"], code=302)
    return render_template("tool_view.html", page="tool", tool=tool, notfound=False)


@app.route("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "app": SITE["name"],
            "version": "2.0.0",
            "tools": len(TOOLS),
            "internal": len([t for t in TOOLS if t["kind"] == "internal"]),
            "external": len([t for t in TOOLS if t["kind"] == "external"]),
            "files_stored": 0,
        }
    )


@app.route("/robots.txt")
def robots_txt():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "\n"
        f"Sitemap: {SITE['canonical']}/sitemap.xml\n"
    )
    resp = app.response_class(body, mimetype="text/plain; charset=utf-8")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/sitemap.xml")
def sitemap_xml():
    urls = [f"  <url><loc>{SITE['canonical']}/</loc>"
            f"<changefreq>weekly</changefreq>"
            f"<priority>1.0</priority></url>"]
    for t in TOOLS:
        if t["kind"] == "internal":
            urls.append(f"  <url><loc>{SITE['canonical']}/tool/{t['slug']}</loc>"
                        f"<changefreq>monthly</changefreq>"
                        f"<priority>0.7</priority></url>")
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    resp = app.response_class(body, mimetype="application/xml; charset=utf-8")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.errorhandler(404)
def handle_404(_err):
    return render_template("tool_view.html", page="404", tool=None, notfound=True), 404


@app.errorhandler(413)
def handle_413(_err):
    return (
        "<!doctype html><meta charset=utf-8>"
        "<title>Request too large</title>"
        "<p style='font:16px system-ui;padding:2rem'>"
        "This request exceeds the 32&nbsp;MB limit.</p>",
        413,
    )


@app.errorhandler(429)
def handle_429(_err):
    return (
        "<!doctype html><meta charset=utf-8>"
        "<title>Too many requests</title>"
        "<p style='font:16px system-ui;padding:2rem'>"
        "Too many requests. Please wait a moment and try again.</p>",
        429,
    )


@app.errorhandler(500)
def handle_500(_err):
    """Never leak a stack trace or config value to the browser."""
    return (
        "<!doctype html><meta charset=utf-8>"
        "<title>Server error</title>"
        "<p style='font:16px system-ui;padding:2rem'>"
        "Something went wrong on our side. Please try again.</p>",
        500,
    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    _internal = len([t for t in TOOLS if t["kind"] == "internal"])
    _external = len([t for t in TOOLS if t["kind"] == "external"])
    print("=" * 62)
    print(f"  {SITE['name']}  ->  http://127.0.0.1:5000")
    print(f"  Owner  : {OWNER['name']}  |  {OWNER['phone']}")
    print(f"  Tools  : {len(TOOLS)} total  ({_internal} internal / {_external} portals)")
    if not _ENV_SECRET:
        print("  Note   : SECRET_KEY not set - using an ephemeral random key.")
    if app.config["DEBUG"]:
        print("  WARNING: FLASK_DEBUG=1 is active. Never do this in production.")
    print("=" * 62)
    # Local development only. Production uses gunicorn (see Procfile).
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
