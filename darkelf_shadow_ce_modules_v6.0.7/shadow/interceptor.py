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

    def __init__(self, engine: EasyListEngine, mini_ai):
        super().__init__()
        self.engine = engine
        self.mini_ai = mini_ai
        self.hsts_hosts: set[str] = set()

        self.pq = DarkelfPQ()
        
    def get_pq_status(self):
        return self.pq.status()
        
    def interceptRequest(self, info):
        qurl = info.requestUrl()
        req_url = qurl.toString()
        scheme = (qurl.scheme() or "").lower()
        host = (qurl.host() or "").lower()

        # Resolve type early so later logic can use it consistently
        req_type = self._detect_request_type(info)
        fp_url = info.firstPartyUrl().toString()

        # Early exits for schemes and local resources
        if self._handle_early_exits(info, scheme, host):
            return

        tab_id = self._extract_tab_id(info)

        seed = self.pq.get_tab_seed(tab_id)
        self.pq.update_chain(tab_id, req_url)
        
        # Minimal targeted UA override only where explicitly desired
        self._apply_special_headers(info, host)

        # Panic / lockdown should happen before any redirects or filtering
        if self._handle_miniai_lockdown(info, req_url):
            return

        # Passive monitoring only
        self._monitor_request(req_url)

        # Upgrade insecure subresources to HTTPS
        if self._handle_https_upgrade(info, qurl, scheme, host, req_type, req_url):
            return

        # Strip tracking params only for top-level documents
        if self._strip_tracking_params_for_document(info, qurl, req_type):
            return

        # Lightweight replay observation for dynamic requests
        self.pq.observe(
            req_url,
            req_type,
            seed
        )

        # Conservative blocking
        try:
            if self.engine and self.engine.should_block(req_url, fp_url, req_type):
                print("BLOCKED:", req_type, fp_url, "->", req_url)
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

            if is_domain(host, "youtube.com") or is_domain(host, "youtu.be"):
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
            info.block(True)
            return True

        if self.mini_ai and getattr(self.mini_ai, "lockdown_active", False):
            print("🔴 LOCKDOWN MODE: Request blocked:", req_url[:120])
            info.block(True)
            return True

        return False

    def _monitor_request(self, req_url: str) -> None:
        if self.mini_ai:
            try:
                self.mini_ai.monitor_network(req_url)
            except Exception as e:
                print("MiniAI error:", e)

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
        ]

        for attr, name in pairs:
            if hasattr(QWebEngineUrlRequestInfo.ResourceType, attr):
                enum_value = getattr(QWebEngineUrlRequestInfo.ResourceType, attr)
                type_map[enum_value] = name

        req_type = type_map.get(rt)
        if req_type is None and hasattr(QWebEngineUrlRequestInfo.ResourceType, "ResourceTypeMainFrame"):
            if rt == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:
                return "document"

        return req_type
        
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
