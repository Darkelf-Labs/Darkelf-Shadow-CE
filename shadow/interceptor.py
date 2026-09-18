# shadow/interceptor.py


import json

from PySide6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
    QWebEnginePage,
)

from PySide6.QtCore import QUrl, QUrlQuery

from shadow.filters import EasyListEngine
from shadow.utils import is_domain
from shadow.darkelf_pq import DarkelfPQ

class StealthInterceptor(QWebEngineUrlRequestInterceptor):
    SAFE_SCHEMES = {"data", "about", "chrome", "qrc", "blob", "view-source"}

    TRACKING_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign",
        "utm_term", "utm_content",
        "fbclid", "gclid", "mc_eid",
    }

    # Functional human-verification infrastructure.  These hosts are allowed
    # only as challenge resources; broad Google/Cloudflare allowlisting is
    # intentionally avoided.
    CAPTCHA_RESOURCE_HOSTS = {
        "hcaptcha.com",
        "assets.hcaptcha.com",
        "newassets.hcaptcha.com",
        "imgs.hcaptcha.com",
        "recaptcha.net",
        "challenges.cloudflare.com",
        "brunhild.challenges.cloudflare.com",
        "funcaptcha.com",
        "arkoselabs.com",
        "awswaf.com",
        "token.awswaf.com",
    }

    
    COMPATIBILITY_RESOURCE_ALLOW = {
        # TikTok
        ("tiktok.com", "tiktok.com"),
        ("tiktok.com", "tiktokcdn.com"),
        ("tiktok.com", "tiktokcdn-us.com"),
        ("tiktok.com", "ttwstatic.com"),
        ("tiktok.com", "tiktokv.com"),
        
        # Zalo
        ("zalo.me", "zalo.me"),
        ("zalo.me", "zaloapp.com"),
        ("zalo.me", "zadn.vn"),
        ("zalo.me", "zdn.vn"),

        ("zaloapp.com", "zalo.me"),
        ("zaloapp.com", "zaloapp.com"),
        ("zaloapp.com", "zadn.vn"),
        ("zaloapp.com", "zdn.vn"),
        
        # WhatsApp
        ("whatsapp.com", "whatsapp.com"),
        ("whatsapp.com", "whatsapp.net"),
        ("whatsapp.net", "whatsapp.com"),
        ("whatsapp.net", "whatsapp.net"),

        # Discord
        ("discord.com", "discord.com"),
        ("discord.com", "discordapp.com"),
        ("discordapp.com", "discord.com"),
        ("discordapp.com", "discordapp.com"),
    
        # Google / Gmail / Workspace
        ("google.com", "google.com"),
        ("google.com", "googleapis.com"),
        ("google.com", "googleusercontent.com"),
        ("google.com", "gstatic.com"),
        ("google.com", "ggpht.com"),
        ("google.com", "gmail.com"),
        ("google.com", "googlemail.com"),
        ("workspace.google.com", "workspace.google.com"),
        ("workspace.google.com", "accounts.google.com"),

        # Google Accounts
        ("accounts.google.com", "accounts.google.com"),
        ("accounts.google.com", "workspace.google.com"),
        
        ("gmail.com", "google.com"),
        ("gmail.com", "gmail.com"),
        ("gmail.com", "googleapis.com"),
        ("gmail.com", "googleusercontent.com"),
        ("gmail.com", "gstatic.com"),
        ("gmail.com", "ggpht.com"),
        ("gmail.com", "googlemail.com"),
    
        # Outlook
        ("outlook.live.com", "outlook.live.com"),
        ("outlook.live.com", "live.com"),
        ("outlook.live.com", "office.net"),
        ("outlook.live.com", "microsoft.com"),
        ("outlook.live.com", "microsoftonline.com"),
        ("outlook.live.com", "msauth.net"),
        ("outlook.live.com", "msftauth.net"),

        # Microsoft login
        ("login.microsoftonline.com", "microsoftonline.com"),
        ("login.microsoftonline.com", "msauth.net"),
        ("login.microsoftonline.com", "msftauth.net"),
        ("login.microsoftonline.com", "office.net"),
        ("login.microsoftonline.com", "live.com"),

        # Consumer Microsoft account login
        ("login.live.com", "live.com"),
        ("login.live.com", "microsoft.com"),
        ("login.live.com", "msauth.net"),
        ("login.live.com", "msftauth.net"),

        # DarkelfBrowser
        ("darkelfbrowser.com", "darkelfbrowser.com"),

        # Spotify
        ("open.spotify.com", "spotify.com"),
        ("open.spotify.com", "scdn.co"),
        ("open.spotify.com", "spotifycdn.com"),

        # radio.net core application / now-playing API only.
        # Advertising/tracking hosts still go through normal EasyList filtering.
        ("radio.net", "radio.net"),
        ("radio.net", "radio.de"),
        ("radio.net", "api.radio.de"),

        # SourceForge core application resources and Cloudflare challenges.
        # These are required for the site UI and human-verification flow.
        ("sourceforge.net", "sourceforge.net"),
        ("sourceforge.net", "fsdn.com"),
        ("sourceforge.net", "challenges.cloudflare.com"),
        ("sourceforge.net", "brunhild.challenges.cloudflare.com"),

        # Jawa / Cloudflare Turnstile
        ("jawa.gg", "jawa.gg"),
        ("jawa.gg", "challenges.cloudflare.com"),
        ("jawa.gg", "brunhild.challenges.cloudflare.com"),
    }
    
    def __init__(
        self,
        engine: EasyListEngine,
        mini_ai,
        browser=None,
    ):
        super().__init__()

        self.engine = engine
        self.mini_ai = mini_ai

        # Filled immediately or later after browser construction
        self.browser = browser

        self._recent_requests = {}
        self.hsts_hosts: set[str] = set()

        self.pq = DarkelfPQ()
        
    def get_pq_status(self):
        return self.pq.status()
        
    def _captcha_resource_allowed(self, qurl: QUrl) -> bool:
        """Allow only known human-verification/challenge resources.

        Do not allow whole google.com/gstatic.com domains: only their
        /recaptcha/ paths are exempted.
        """
        host = (qurl.host() or "").lower().rstrip(".")
        path = (qurl.path() or "").lower()

        if any(is_domain(host, d) for d in self.CAPTCHA_RESOURCE_HOSTS):
            return True

        if (is_domain(host, "google.com") or is_domain(host, "gstatic.com")) and (
            path.startswith("/recaptcha/")
            or "/recaptcha/" in path
        ):
            return True

        return False

    def _compat_resource_allowed(self, first_party_host, target_host):
        first_party_host = (first_party_host or "").lower().rstrip(".")
        target_host = (target_host or "").lower().rstrip(".")

        for site, resource in self.COMPATIBILITY_RESOURCE_ALLOW:
            site_match = (
                first_party_host == site
                or first_party_host.endswith("." + site)
            )

            resource_match = (
                target_host == resource
                or target_host.endswith("." + resource)
            )

            if site_match and resource_match:
                return True

        return False
        
    def interceptRequest(self, info):
        qurl = info.requestUrl()
        req_url = qurl.toString()
        scheme = (qurl.scheme() or "").lower()
        host = (qurl.host() or "").lower()
        fp_host = (info.firstPartyUrl().host() or "").lower()

        # ============================================================
        # GLOBAL US-ENGLISH LANGUAGE
        # ============================================================
        # Send US-English language preference to ALL HTTP/HTTPS sites.
        if scheme in ("http", "https"):
            info.setHttpHeader(
                b"Accept-Language",
                b"en-US,en;q=0.9"
            )

        # ============================================================
        # YOUTUBE US REGION
        # ============================================================
        # HTTP header that forces every website to use the US region.
        if host == "youtube.com" or host.endswith(".youtube.com"):

            if (
                info.resourceType()
                == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame
            ):
                query = QUrlQuery(qurl)
                changed = False

                # YouTube interface language
                if query.queryItemValue("hl") != "en":
                    query.removeAllQueryItems("hl")
                    query.addQueryItem("hl", "en")
                    changed = True

                # YouTube region
                if query.queryItemValue("gl") != "US":
                    query.removeAllQueryItems("gl")
                    query.addQueryItem("gl", "US")
                    changed = True

                if changed:
                    new_url = QUrl(qurl)
                    new_url.setQuery(query)
                    info.redirect(new_url)
                    return
                    
        # Only rewrite the normal Google homepage/search host.
        if host in ("google.com", "www.google.com"):

            if (
                info.resourceType()
                == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame
            ):
                query = QUrlQuery(qurl)
                changed = False

                # Google interface language
                if query.queryItemValue("hl") != "en":
                    query.removeAllQueryItems("hl")
                    query.addQueryItem("hl", "en")
                    changed = True

                # Google country/region
                if query.queryItemValue("gl") != "us":
                    query.removeAllQueryItems("gl")
                    query.addQueryItem("gl", "us")
                    changed = True

                if changed:
                    new_url = QUrl(qurl)
                    new_url.setQuery(query)
                    info.redirect(new_url)
                    return
                    
        # ------------------------------------------------------------
        # Shopify storefront hCaptcha bootstrap
        # ------------------------------------------------------------
        # Shopify hosts its own loader for storefront form hCaptcha.
        # Allow ONLY the captcha loader path, not the entire Shopify CDN.
        if (
            is_domain(host, "cdn.shopify.com")
            and "/shopifycloud/storefront-forms-hcaptcha/" in qurl.path().lower()
        ):
            self._network_print(
                "CAPTCHA ALLOWED:",
                fp_host,
                "->",
                req_url,
            )
            return
            
        # ============================================================
        # Continue normal Darkelf processing
        # ============================================================
        if self._handle_early_exits(info, scheme, host):
            return
            
        # Resolve type early so later logic can use it consistently
        req_type = self._detect_request_type(info)
        
        method = bytes(info.requestMethod()).decode(
            "utf-8",
            errors="ignore",
        )
        
        # Raw per-request tracing intentionally disabled.  Printing every
        # GET/POST/OPTIONS/image/script request is extremely noisy and can
        # noticeably slow busy pages. Security/blocking events are still logged.
        
        fp_url = info.firstPartyUrl().toString()

        # Minimal targeted UA override only where explicitly desired
        self._apply_special_headers(info, host)

        # Panic / lockdown should happen before redirects or filtering.
        if self._handle_miniai_lockdown(info, req_url):
            return

        # MiniAI URL parsing and PQ hashing used to run on EVERY image, font,
        # stylesheet, script and ad request. On modern pages that means hundreds
        # or thousands of synchronous Python operations in Chromium's request path.
        # Keep security monitoring on navigations and active network calls only.
        active_types = {"document", "subdocument", "xmlhttprequest", "websocket"}
        if req_type in active_types:
            self._monitor_request(req_url)

        # Chromium already upgrades eligible mixed content itself. Avoid an extra
        # Python redirect pass for every insecure image/script/subresource.

        # Strip tracking params only for top-level documents.
        if self._strip_tracking_params_for_document(info, qurl, req_type):
            return

        # Keep PQ state useful without hashing every static asset.
        if req_type in active_types or req_type == "media":
            tab_id = self._extract_tab_id(info)
            seed = self.pq.get_tab_seed(tab_id)
            if req_type == "document":
                self.pq.update_chain(tab_id, req_url)
            self.pq.observe(req_url, req_type, seed)
        
        # Site-specific compatibility exceptions

        # Human-verification resources must load or login, signup, checkout,
        # contact and other form flows can loop/fail.  This exemption is
        # intentionally narrow and runs before EasyList evaluation.
        if self._captcha_resource_allowed(qurl):
            # Allow challenge resources silently.
            return

        if self._compat_resource_allowed(fp_host, host):
            # Allow compatibility resources silently.
            return
            
        if (
            is_domain(fp_host, "fsharetv.com")
            and req_type == "media"
        ):
            self._network_print(
                "MEDIA ALLOWED:",
                fp_host,
                "->",
                req_url,
            )
            return
            
        # Conservative blocking
        try:
            if self.engine and self.engine.should_block(req_url, fp_url, req_type):

                # Blocking remains fully active; routine per-resource block logs
                # are intentionally silent to keep the UI/request thread responsive.
                info.block(True)
                return

        except Exception as e:
            print("Interceptor error:", e)
        
    def _extract_tab_id(self, info) -> str:
        try:
            url = info.requestUrl().toString()

            if "#tab=" in url:
                return url.split("#tab=")[-1][:32]

        except Exception as e:
            print(e)

        return "default"

    def _apply_special_headers(self, info, host: str) -> None:
        try:
            host = (host or "").lower()

            if (
                is_domain(host, "youtube.com")
                or is_domain(host, "youtu.be")
            ):
                ua = (
                    b"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    b"AppleWebKit/605.1.15 (KHTML, like Gecko)"
                )
                info.setHttpHeader(b"User-Agent", ua)

        except Exception as e:
            print(e)
            pass

    def _handle_miniai_lockdown(self, info, req_url: str) -> bool:
        if self.mini_ai and getattr(self.mini_ai, "panic_mode_active", False):
            print("🚨 PANIC MODE: Blocking request:", req_url[:120])
            
            self._network_print(
                "🚨 PANIC MODE: Blocking request:",
                req_url[:120],
            )
            
            info.block(True)
            return True

        if self.mini_ai and getattr(self.mini_ai, "lockdown_active", False):
            self._network_print(
                "🔴 LOCKDOWN MODE:",
                req_url[:120],
            )
            info.block(True)
            return True

        return False

    def _monitor_request(self, req_url: str) -> None:
        if self.mini_ai:
            try:
                self.mini_ai.monitor_network(req_url)
            except Exception as e:
                print("MiniAI error:", e)
                
    def _network_print(self, *parts):
        """
        Print to the terminal and mirror the same line
        into the Darkelf Inspector Network log.
        """

        text = " ".join(str(x) for x in parts)

        # Never emit ordinary HTTP request traces to either the terminal or
        # Inspector. Keep only meaningful Darkelf security/compatibility events.
        first = text.lstrip().split(None, 1)[0].upper() if text.strip() else ""
        if first in {
            "GET", "POST", "HEAD", "OPTIONS", "PUT", "PATCH",
            "DELETE", "CONNECT", "TRACE"
        }:
            return

        print(text)

        if self.browser is None:
            return

        inspector = getattr(self.browser, "darkelf_inspector", None)

        if inspector is None:
            inspector = getattr(self.browser, "dev_console", None)

        if inspector is None:
            return

        try:
            inspector.log_network_event(text)
        except Exception as e:
            print("Inspector network hook:", e)
        
    def _handle_early_exits(self, info, scheme: str, host: str) -> bool:
        if scheme in self.SAFE_SCHEMES:
            return True

        if scheme == "file":
            info.block(True)
            return True

        if (
            host in ("localhost", "127.0.0.1")
            or host.startswith("192.168.")
            or host.startswith("10.")
            or host.startswith(tuple(f"172.{i}." for i in range(16, 32)))
        ):
            return True

        return False

    def _handle_https_upgrade(
        self,
        info,
        qurl: QUrl,
        scheme: str,
        host: str,
        req_type: str | None,
        req_url: str,
    ) -> bool:
        if scheme == "http" and req_type != "document":
            https_url = QUrl(qurl)
            https_url.setScheme("https")
            self.hsts_hosts.add(host)

            if self.mini_ai:
                try:
                    self.mini_ai.on_http_blocked(req_url)
                except Exception as e:
                    print(e)
                    pass
                    
            self._network_print(
                "HTTPS UPGRADE:",
                req_url,
            )
            
            info.redirect(https_url)
            return True

        if scheme == "http" and host in self.hsts_hosts:
            https_url = QUrl(qurl)
            https_url.setScheme("https")
            info.redirect(https_url)
            return True

        return False

    def _strip_tracking_params_for_document(self, info, qurl: QUrl, req_type: str | None) -> bool:
        if req_type != "document":
            return False

        query = QUrlQuery(qurl)
        modified = False

        for param in self.TRACKING_PARAMS:
            if query.hasQueryItem(param):
                query.removeAllQueryItems(param)
                modified = True

        if modified:
            clean_url = QUrl(qurl)
            clean_url.setQuery(query)
            
            self._network_print(
                "TRACKING CLEANUP:",
                clean_url.toString(),
            )

            info.redirect(clean_url)
            return True

        return False

    def _detect_request_type(self, info) -> str | None:
        rt = info.resourceType()
        type_map: dict[object, str] = {}

        pairs = [
            ("ResourceTypeMainFrame", "document"),
            ("ResourceTypeSubFrame", "subdocument"),
            ("ResourceTypeScript", "script"),
            ("ResourceTypeStylesheet", "stylesheet"),
            ("ResourceTypeImage", "image"),
            ("ResourceTypeXhr", "xmlhttprequest"),
            ("ResourceTypeFontResource", "font"),
            ("ResourceTypeMedia", "media"),
            ("ResourceTypePing", "ping"),
            ("ResourceTypeWebSocket", "websocket"),
            ("ResourceTypeWorker", "worker"),
            ("ResourceTypeSharedWorker", "worker"),
            ("ResourceTypeServiceWorker", "serviceworker"),
            ("ResourceTypeCspReport", "csp_report"),
            ("ResourceTypePrefetch", "prefetch"),
            ("ResourceTypeSubResource", "other"),
            ("ResourceTypeObject", "object"),
            ("ResourceTypeFavicon", "image"),
            ("ResourceTypeJson", "xmlhttprequest"),
        ]

        for attr, name in pairs:
            if hasattr(QWebEngineUrlRequestInfo.ResourceType, attr):
                enum_value = getattr(QWebEngineUrlRequestInfo.ResourceType, attr)
                type_map[enum_value] = name

        req_type = type_map.get(rt)
        if req_type is None and hasattr(QWebEngineUrlRequestInfo.ResourceType, "ResourceTypeMainFrame"):
            if rt == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:
                return "document"

        return req_type or "other"
        
class DarkelfWebPage(QWebEnginePage):
    def __init__(self, tab_id, profile, parent=None):
        super().__init__(profile, parent)
        self.tab_id = tab_id


    def createRequest(self, *args, **kwargs):
        req = super().createRequest(*args, **kwargs)
        try:
            req.setRawHeader(b"X-Tab-ID", self.tab_id.encode())
        except Exception as e:
            print(e)
            pass
        return req
        
# ===================== Cosmetic injection helper =====================

def js_inject_style_tag(style_id: str, css: str) -> str:
    # returns JS string that injects/updates a <style> with CSS
    css = css.replace("\\", "\\\\").replace("`", "\\`")
    return f"""
    (function(){{
      try {{
        var id = {json.dumps(style_id)};
        var css = `{css}`;
        var el = document.getElementById(id);
        if (!el) {{
          el = document.createElement('style');
          el.id = id;
          (document.documentElement || document.head || document.body).appendChild(el);
        }}
        el.textContent = css;
      }} catch(e) {{}}
    }})();
    """
