# shadow/utils.py

import os
import re
import secrets
import time
from PySide6.QtCore import QUrl

def is_domain(host: str, domain: str) -> bool:
    """
    Returns True if host matches domain or is a subdomain of it.
    Example:
        youtube.com → youtube.com ✅
        www.youtube.com → youtube.com ✅
        evil-youtube.com → youtube.com ❌
    """
    host = (host or "").lower().strip(".")
    domain = (domain or "").lower().strip(".")

    return host == domain or host.endswith("." + domain)
    
# ===================== Secure No-Trace Downloads =====================

def _safe_download_dir() -> str:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    folder = os.path.join(desktop, "Darkelf Temp Folder")
    os.makedirs(folder, exist_ok=True)
    return folder


def _randomized_filename(suggested: str) -> str:
    suggested = (suggested or "download").strip()
    suggested = re.sub(r"[^A-Za-z0-9._-]+", "_", suggested)[:120] or "download"

    base, ext = os.path.splitext(suggested)
    token = secrets.token_hex(6)

    base = (base[:60] or "download")
    ext = ext[:12]
    return f"{base}_{token}{ext}"


# ===================== URL Sanitization =====================

def sanitize_url_clearurls(url: str) -> str:
    clear_params = [
        "utm_source", "utm_medium", "utm_campaign", "utm_term",
        "utm_content", "utm_id",
        "fbclid", "gclid",
        "mc_campaign", "mc_eid", "mc_cid",
        "pk_campaign", "pk_kwd"
    ]

    url_parts = QUrl(url)
    query = url_parts.query()

    new_query = "&".join([
        part for part in query.split("&")
        if not any(part.startswith(p + "=") for p in clear_params)
    ])

    url_parts.setQuery(new_query)
    return url_parts.toString()


# ===================== Session / Rotation =====================

SESSION_SEED = secrets.token_hex(16)
_last_rotation = 0


def rotate_internal_seed():
    global SESSION_SEED
    SESSION_SEED = secrets.token_hex(16)
    print("[Darkelf] 🔁 Internal seed rotated")


def should_rotate():
    global _last_rotation
    now = time.time()
    if now - _last_rotation > 10:
        _last_rotation = now
        return True
    return False


# ===================== Browser Seeds =====================

BOOTUP_CANVAS_SEED = secrets.randbits(32) & 0xFFFFFFFF


# ===================== Search Endpoints =====================

DUCK_LITE_HTTPS = "https://duckduckgo.com/lite/"

# ===================== Chromium Flags (SAFE INIT) =====================

def apply_chromium_flags():
    # 🔥 ALWAYS overwrite (no accumulation)
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-sync "
    "--metrics-recording-only "
    "--no-first-run "
    "--disable-breakpad "
    "disable_2d_canvas_auto_flush"
)
