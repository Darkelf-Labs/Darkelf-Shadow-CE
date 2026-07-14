# shadow/filters.py

import ipaddress
import os
import re
import time
import hashlib
import http.client

from urllib.parse import urlparse
from PySide6.QtCore import QUrl

EASYLIST_URLS = [
    # Core
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",

    # Annoyances
    "https://secure.fanboy.co.nz/fanboy-annoyance.txt",

    # Social widgets
    "https://easylist.to/easylist/fanboy-social.txt",

    # Anti-adblock
    "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",

    # AdGuard Tracking Protection
    "https://filters.adtidy.org/extension/chromium/filters/3.txt",

    # ✅ uBlock Origin — Privacy
    "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/privacy.txt",

    # ✅ uBlock Origin — Unbreak (fixes site breakage)
    "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/unbreak.txt",

    # ✅ uBlock Origin — Badware
    "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/badware.txt",
]

# Cache location (safe, user-level)
EASYLIST_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".darkelf", "filterlists")
os.makedirs(EASYLIST_CACHE_DIR, exist_ok=True)

# How often to refresh lists (seconds)
EASYLIST_REFRESH_EVERY = 24 * 60 * 60  # 24h

# Hard cap on a single downloaded list (protects against
# malicious or corrupted filter mirrors exhausting memory).
MAX_LIST_BYTES = 16 * 1024 * 1024  # 16 MiB

# ===================== ABP -> regex helpers =====================

def _now() -> float:
    return time.time()

def _safe_host(u: str) -> str:
    try:
        return QUrl(u).host().lower()
    except Exception as e:
        print(e)
        return ""

def _wildcard_to_re(s: str) -> str:
    # ABP wildcard "*" -> ".*"
    # Escape regex special chars except "*" which we convert.
    out = []
    for ch in s:
        if ch == "*":
            out.append(".*")
        elif ch in ".^$+?{}[]\\|()":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)

def _abp_anchor_boundary() -> str:
    # ABP '^' = separator boundary (end of host, or non-alnum/._%-)
    # A common approximation:
    return r"(?:[^A-Za-z0-9_\-.%]|$)"

def _abp_rule_to_regex(rule: str) -> str | None:
    """
    Convert a basic ABP network filter rule into a regex string.
    Supports: ||, |, ^, *, plain substrings.
    Ignores: full option parsing, $domain=..., etc. (we parse options elsewhere)
    """
    rule = rule.strip()
    if not rule or rule.startswith("!"):
        return None

    # Regex rules: /.../
    if len(rule) >= 2 and rule[0] == "/" and rule[-1] == "/":
        body = rule[1:-1]
        # basic sanity
        if body:
            return body
        return None

    anchored_start = False
    anchored_end = False

    if rule.startswith("||"):
        core = rule[2:]
        core = core.replace("^", "{ABP_BOUNDARY}")
        core_re = _wildcard_to_re(core)
        core_re = core_re.replace("{ABP_BOUNDARY}", _abp_anchor_boundary())
        return r"^(?:[^:/?#]+:)?//(?:[^/?#]*\.)?" + core_re + _abp_anchor_boundary()

        
    if rule.startswith("|"):
        anchored_start = True
        rule = rule[1:]
    if rule.endswith("|"):
        anchored_end = True
        rule = rule[:-1]

    rule = rule.replace("^", "{ABP_BOUNDARY}")
    core_re = _wildcard_to_re(rule)
    core_re = core_re.replace("{ABP_BOUNDARY}", _abp_anchor_boundary())

    if anchored_start and anchored_end:
        return r"^" + core_re + r"$"
    if anchored_start:
        return r"^" + core_re
    if anchored_end:
        return core_re + r"$"
    return core_re

def _split_rule_and_options(line: str) -> tuple[str, dict]:
    """
    ABP options come after $:  rule$script,image,third-party
    We keep only a few options that are easy/valuable in an interceptor.
    """
    line = line.strip()
    if "$" not in line:
        return line, {}

    rule, optstr = line.split("$", 1)
    opts = {}
    for raw in optstr.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if "=" in raw:
            k, v = raw.split("=", 1)
            opts[k.strip()] = v.strip()
        else:
            opts[raw] = True
    return rule.strip(), opts

def _parse_domain_list(v: str) -> tuple[set[str], set[str]]:
    """
    domain=example.com|~foo.com
    Returns (allow_domains, deny_domains)
    """
    allow, deny = set(), set()
    for part in v.split("|"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("~"):
            deny.add(part[1:].lower())
        else:
            allow.add(part.lower())
    return allow, deny

def _host_matches_domain(host: str, domain: str) -> bool:
    host = host.lower()
    domain = domain.lower()
    return host == domain or host.endswith("." + domain)

def _domain_option_allows(first_party_host: str, opts: dict) -> bool:
    """
    If rule has domain=... limit, check if first party host is eligible.
    """
    dom = opts.get("domain")
    if not dom:
        return True
    allow, deny = _parse_domain_list(dom)
    # If allow list present: must match one of them.
    if allow:
        ok = any(_host_matches_domain(first_party_host, d) for d in allow)
        if not ok:
            return False
    # If deny list present: must NOT match any of them.
    if deny:
        bad = any(_host_matches_domain(first_party_host, d) for d in deny)
        if bad:
            return False
    return True
    
def base_domain(host: str) -> str:
    """
    Returns the eTLD+1 (base domain) for a given host.
    Example: 'lite.duckduckgo.com' or 'duckduckgo.com' -> 'duckduckgo.com'
    """
    host = (host or "").split(":")[0]  # Remove port if present
    parts = host.lower().split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host.lower()

def _third_party_check(req_host: str, first_party_host: str) -> bool:
    """
    Use base domains for robust first-party check across subdomains.
    """
    if not req_host or not first_party_host:
        return True
    return base_domain(req_host) != base_domain(first_party_host)
    
def is_domain(host: str, domain: str) -> bool:
    host = (host or "").lower()
    domain = domain.lower()
    return host == domain or host.endswith("." + domain)
# ===================== Filter structures =====================

class _NetRule:
    __slots__ = ("re", "is_exception", "opts")
    def __init__(self, pattern: re.Pattern, is_exception: bool, opts: dict):
        self.re = pattern
        self.is_exception = is_exception
        self.opts = opts

class EasyListEngine:
    """
    Loads lists -> builds:
      - network rules: list of _NetRule (exceptions first)
      - cosmetic rules: dict[domain or "*"] -> list[selectors]
      - cosmetic exceptions: dict[domain] -> set[selectors]
    """
    def __init__(self):
        self.network_rules: list[_NetRule] = []
        self.cosmetic: dict[str, list[str]] = {"*": []}
        self.cosmetic_exceptions: dict[str, set[str]] = {}

    # ---------- fetch/cache ----------
    def _cache_path_for_url(self, url: str) -> str:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return os.path.join(EASYLIST_CACHE_DIR, f"{h}.txt")

    def _should_refresh(self, path: str) -> bool:
        if not os.path.exists(path):
            return True
        age = _now() - os.path.getmtime(path)
        return age > EASYLIST_REFRESH_EVERY

    def _is_private_host(host: str) -> bool:
        """
        SSRF guard for the filter fetcher.
        Blocks loopback, link-local (including cloud metadata),
        private IPv4/IPv6, and other non-global IPs.
        """
        host = (host or "").strip("[]").lower()

        if not host or host in ("localhost", "localhost.localdomain"):
            return True

        try:
            ip = ipaddress.ip_address(host)
            return not ip.is_global
        except ValueError:
            return (
                host.endswith(".local")
                or host.endswith(".internal")
            )

    def fetch_lists(self, urls: list[str]) -> list[str]:
        texts = []

        for url in urls:
            path = self._cache_path_for_url(url)

            if self._should_refresh(path):
                try:
                    parsed = urlparse(url)

                    # 🔒 Only allow HTTP/HTTPS
                    if parsed.scheme not in ("http", "https"):
                        print("[EasyList] Blocked unsafe scheme:", url)
                        continue

                    host = (parsed.hostname or "").lower()

                    if self._is_private_host(host):
                        print("[EasyList] Blocked internal address:", url)
                        continue
                        
                    # 🔥 NO urllib — use http.client instead
                    if parsed.scheme == "https":
                        conn = http.client.HTTPSConnection(host, timeout=15)
                    else:
                        conn = http.client.HTTPConnection(host, timeout=15)

                    path_with_query = parsed.path or "/"
                    if parsed.query:
                        path_with_query += "?" + parsed.query

                    conn.request(
                        "GET",
                        path_with_query,
                        headers={
                            "User-Agent": "Darkelf/1.0 (EasyList Fetcher)",
                            "Accept": "text/plain,*/*",
                        },
                    )

                    response = conn.getresponse()

                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    data = response.read(MAX_LIST_BYTES + 1)
                    conn.close()

                    if len(data) > MAX_LIST_BYTES:
                        print("[EasyList] List exceeds size cap, skipping:", url)
                        continue

                    text = data.decode("utf-8", errors="replace")

                    with open(path, "w", encoding="utf-8", errors="ignore") as f:
                        f.write(text)

                except Exception as e:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                    else:
                        print("[EasyList] fetch failed:", url, e)
                        text = ""
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

            if text:
                texts.append(text)

        return texts
        
    def load_and_build(self, urls: list[str]):
        texts = self.fetch_lists(urls)
        self._parse_texts(texts)
        self._finalize()

    def _parse_texts(self, texts: list[str]):
        self.network_rules.clear()
        self.cosmetic = {"*": []}
        self.cosmetic_exceptions.clear()

        for text in texts:
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("!"):
                    continue
                # Ignore metadata headers like: [Adblock Plus 2.0]
                if line.startswith("[") and line.endswith("]"):
                    continue

                # Cosmetic rules:
                #  - example.com##.ad
                #  - ##.global-ad
                #  - example.com#@#.ad   (exception)
                if "##" in line or "#@#" in line:
                    self._parse_cosmetic(line)
                    continue

                # Network rules:
                self._parse_network(line)

    def _parse_cosmetic(self, line: str):
        is_exc = "#@#" in line
        sep = "#@#" if is_exc else "##"
        parts = line.split(sep, 1)
        if len(parts) != 2:
            return
        domain_part = parts[0].strip()  # can be empty = global
        selector = parts[1].strip()
        if not selector:
            return

        # ABP also has extended selectors (:has, etc). We'll keep them; CSS injection may ignore unsupported ones.
        domains = []
        if domain_part:
            domains = [d.strip().lower() for d in domain_part.split(",") if d.strip()]
        else:
            domains = ["*"]

        if is_exc:
            for d in domains:
                self.cosmetic_exceptions.setdefault(d, set()).add(selector)
        else:
            for d in domains:
                self.cosmetic.setdefault(d, []).append(selector)

    def _parse_network(self, line: str):
        is_exception = False
        if line.startswith("@@"):
            is_exception = True
            line = line[2:].strip()

        rule, opts = _split_rule_and_options(line)

        # Skip unsupported rule types (resource redirects, etc.)
        # Keep only rules that look like URL filters.
        if not rule:
            return

        # Convert ABP -> regex
        rx = _abp_rule_to_regex(rule)
        if not rx:
            return

        try:
            cre = re.compile(rx, re.I)
        except re.error:
            return

        self.network_rules.append(_NetRule(cre, is_exception, opts))

    def _finalize(self):
        # Put exceptions first for fast allow-pass.
        self.network_rules.sort(key=lambda r: (not r.is_exception))

        # De-dup cosmetic selectors per domain (keep stable order)
        for d, sels in list(self.cosmetic.items()):
            seen = set()
            out = []
            for s in sels:
                if s in seen:
                    continue
                seen.add(s)
                out.append(s)
            self.cosmetic[d] = out
            
    def should_block(
        self,
        url: str,
        first_party_url: str,
        req_type: str | None = None
    ) -> bool:

        u = (url or "").lower()

        fp_host = _safe_host(first_party_url)
        req_host = _safe_host(url)

        # --------------------------------------------------
        # BASIC SAFETY
        # --------------------------------------------------

        if not req_host or not req_type:
            return False

        if req_type == "document":
            return False

        # --------------------------------------------------
        # INTERNAL / DEVTOOLS BYPASS
        # --------------------------------------------------

        if u.startswith((
            "devtools://",
            "chrome://",
            "chrome-devtools://",
            "chrome-extension://",
            "blob:",
            "about:",
        )):
            return False

        # --------------------------------------------------
        # NEVER INTERFERE WITH TEST PAGES
        # --------------------------------------------------

        if is_domain(fp_host, "browserleaks.com"):
            return False

        # --------------------------------------------------
        # SAME-SITE DETECTION
        # --------------------------------------------------

        def _site_key(host: str) -> str:

            parts = [
                p
                for p in (host or "").split(".")
                if p
            ]

            return (
                ".".join(parts[-2:])
                if len(parts) >= 2
                else (host or "")
            )

        fp_site = _site_key(fp_host)
        req_site = _site_key(req_host)

        same_site = bool(
            fp_site
            and
            req_site
            and
            fp_site == req_site
        )
    
        is_third_party = (
            not same_site
            and
            _third_party_check(req_host, fp_host)
        )

        # --------------------------------------------------
        # RELATED DOMAIN FAMILIES
        # --------------------------------------------------

        RELATED_FAMILIES = (

            (
                "youtube.com",
                "googlevideo.com",
                "ytimg.com",
                "youtubei.googleapis.com",
                "gstatic.com",
            ),

            (
                "wikipedia.org",
                "wikimedia.org",
                "wmfusercontent.org",
            ),

            (
                "github.com",
                "githubusercontent.com",
                "githubassets.com",
            ),

            (
                "amazon.com",
                "media-amazon.com",
                "ssl-images-amazon.com",
                "images-amazon.com",
                "images-na.ssl-images-amazon.com",
                "m.media-amazon.com",
                "a0.awsstatic.com",
                "a1.awsstatic.com",
                "a2.awsstatic.com",
                "a3.awsstatic.com",
                "a4.awsstatic.com",
                "a5.awsstatic.com",
                "a6.awsstatic.com",
                "a7.awsstatic.com",
            ),

            (
                "walmart.com",
            ),

            (
                "ebay.com",
                # X / Twitter
                "x.com",
                "twitter.com",
                "twing.com",
                "t.co",

                # Reddit
                "reddit.com",
                "redd.it",
                "redditmedia.com",
                "redditstatic.com",

                # Instagram
                "instagram.com",
                "cdninstagram.com",
                "fbcdn.net",

                # Facebook
                "facebook.com",
                "fbcdn.net",
                "fbsbx.com",            ),
        )

        for family in RELATED_FAMILIES:

            if (
                any(fp_host.endswith(x) for x in family)
                and
                any(req_host.endswith(x) for x in family)
            ):

                same_site = True
                is_third_party = False
                break

        # --------------------------------------------------
        # NEVER BLOCK SAME-SITE CORE RESOURCES
        # --------------------------------------------------

        if (
            same_site
            and
            req_type in (
                "script",
                "xmlhttprequest",
                "stylesheet",
                "font",
                "media",
                "image",
            )
        ):
            return False

        # --------------------------------------------------
        # NEVER BLOCK MEDIA PIPELINE
        # --------------------------------------------------

        if req_type in (
            "media",
            "image",
            "font",
            "stylesheet",
        ):
            return False

        # --------------------------------------------------
        # YOUTUBE SAFE MODE
        # --------------------------------------------------

        YOUTUBE_SAFE = (

            "youtube.com",
            "youtu.be",
            "youtubei.googleapis.com",
            "ytimg.com",
            "googlevideo.com",
            "gstatic.com",
            "youtube-nocookie.com",
            "i.ytimg.com",
        )

        if any(
            req_host == d
            or
            req_host.endswith("." + d)
            for d in YOUTUBE_SAFE
        ):
            return False

        # --------------------------------------------------
        # SAFE INFRASTRUCTURE
        # --------------------------------------------------

        SAFE_INFRA = (

            "amazonaws.com",
            "cloudfront.net",
            "awswaf.com",
            "token.awswaf.com",

            "gstatic.com",
            "googleapis.com",

            "cloudflare.com",
            "cloudflareinsights.com",
        )

        if any(
            req_host == x
            or
            req_host.endswith("." + x)
            for x in SAFE_INFRA
        ):
            return False

        # --------------------------------------------------
        # SAFE DOMAINS
        # --------------------------------------------------

        SAFE_DOMAINS = (

            "bbc.co.uk",
            "bbci.co.uk",

            "github.com",
            "githubusercontent.com",

            "walmart.com",

            "youtube.com",
        )

        if any(fp_host.endswith(d) for d in SAFE_DOMAINS):
            return False

        # --------------------------------------------------
        # HARD TRACKERS ONLY
        # --------------------------------------------------

        HARD_TRACKERS = (

            "adnxs.com",
            "criteo.com",
            "taboola.com",
            "outbrain.com",
            "quantserve.com",
        )

        if (
            is_third_party
            and
            any(
                req_host == t
                or
                req_host.endswith("." + t)
                for t in HARD_TRACKERS
            )
        ):
            return True

        # --------------------------------------------------
        # LIGHT HEURISTICS
        # --------------------------------------------------

        if (
            is_third_party
            and
            req_type in (
                "script",
                "xmlhttprequest",
            )
        ):

            high_signal = (

                "pagead",
                "adsystem",
                "adservice",
                "adserver",
                "gampad",
                "prebid",
                "openrtb",
                "criteo",
                "taboola",
                "outbrain",
                "adnxs",
            )

            if (
                any(k in req_host for k in high_signal)
                and
                not (
                    fp_host == "youtube.com"
                    or fp_host.endswith(".youtube.com")
                )
            ):
                return True

        # --------------------------------------------------
        # RESTRICT EASYLIST EVAL
        # --------------------------------------------------

        if req_type not in (
            "script",
            "xmlhttprequest",
            "subdocument",
        ):
            return False

        # --------------------------------------------------
        # EASYLIST EVALUATION
        # --------------------------------------------------

        matched = False

        for rule in self.network_rules:

            if not _domain_option_allows(
                fp_host,
                rule.opts
            ):
                continue

            if (
                "third-party" in rule.opts
                and
                not is_third_party
            ):
                continue

            if (
                "~third-party" in rule.opts
                and
                is_third_party
            ):
                continue

            type_flags = {

                "script",
                "xmlhttprequest",
                "subdocument",
            }

            specified = [
                t
                for t in type_flags
                if t in rule.opts
            ]

            if specified and req_type not in specified:
                continue

            try:

                if rule.re.search(u):

                    # Exceptions ALWAYS WIN

                    if rule.is_exception:
                        return False

                    matched = True

            except re.error:
                # Ignore malformed regex rules and continue checking others
                continue
                
        return matched
        
    def css_for_host(self, host: str) -> str:
        host = (host or "").lower()
        selectors = []

        selectors += self.cosmetic.get("*", [])

        if host:
            parts = host.split(".")
            for i in range(len(parts) - 1):
                dom = ".".join(parts[i:])
                selectors += self.cosmetic.get(dom, [])

        exc = set(self.cosmetic_exceptions.get("*", set()))
        if host:
            parts = host.split(".")
            for i in range(len(parts) - 1):
                dom = ".".join(parts[i:])
                exc |= self.cosmetic_exceptions.get(dom, set())

        selectors = [s for s in selectors if s not in exc]

        if not selectors:
            return ""

        lines = []
        for sel in selectors:
            sel = sel.replace("`", "")
            lines.append(
                f"{sel} {{ display: none !important; visibility: hidden !important; }}"
            )

        return "\n".join(lines)


