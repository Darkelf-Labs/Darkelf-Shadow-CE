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


# ------------------------------------------------------------
# Conservative supplemental blocking
# ------------------------------------------------------------

# Exact advertising / analytics hosts known to be used as trackers.
# Do not block all amazonaws.com because legitimate websites use AWS.
SUPPLEMENTAL_TRACKER_HOSTS = {
    "analyticsengine.s3.amazonaws.com",
    "analytics.s3.amazonaws.com",
    "adtago.s3.amazonaws.com",
    "advice-ads.s3.amazonaws.com",
}

# Local bait filenames used by ad-block testing pages.
# These are only blocked when the first-party site is the tester.
ADBLOCK_TEST_BAIT_FILES = {
    "ads.js",
    "pagead.js",
    "advertisement.js",
    "analytics.js",
}

ADBLOCK_TEST_DOMAINS = {
    "adblocktester.pages.dev",
}

# Exact high-confidence tracker/telemetry hosts.  This acts like a compact
# declarative network-request ruleset: exact/suffix host checks happen before
# the large EasyList regex engine, improving both coverage and responsiveness.
# Keep this list host-specific; do not add broad CDN/cloud parent domains.
DECLARATIVE_TRACKER_HOSTS = frozenset({
    # Ad networks / analytics
    "ads30.adcolony.com", "adc3-launch.adcolony.com", "events3alt.adcolony.com", "wd.adcolony.com",
    "analytics.google.com", "click.googleanalytics.com",
    "mouseflow.com", "cdn.mouseflow.com", "api.mouseflow.com", "tools.mouseflow.com",
    "freshmarketer.com", "claritybt.freshmarketer.com", "fwtracks.freshmarketer.com",
    "luckyorange.com", "api.luckyorange.com", "realtime.luckyorange.com", "cdn.luckyorange.com",
    "w1.luckyorange.com", "upload.luckyorange.net", "cs.luckyorange.net", "settings.luckyorange.net",

    # Error / crash reporting
    "notify.bugsnag.com", "sessions.bugsnag.com", "api.bugsnag.com", "app.bugsnag.com",
    "browser.sentry-cdn.com", "app.getsentry.com",

    # Social / advertising telemetry
    "pixel.facebook.com", "an.facebook.com",
    "ads-api.twitter.com",
    "analytics.pointdrive.linkedin.com",
    "events.reddit.com", "events.redditmedia.com",
    "ads.youtube.com",
    "ads-api.tiktok.com", "ads-sg.tiktok.com", "analytics-sg.tiktok.com", "business-api.tiktok.com",

    # Yahoo / Yandex analytics
    "analytics.yahoo.com", "geo.yahoo.com", "udcm.yahoo.com", "analytics.query.yahoo.com",
    "partnerads.ysm.yahoo.com", "log.fc.yahoo.com", "gemini.yahoo.com", "adtech.yahooinc.com",
    "appmetrica.yandex.ru", "metrika.yandex.ru", "adfox.yandex.ru",

    # Device / vendor telemetry
    "iot-eu-logser.realme.com", "iot-logser.realme.com", "bdapi-ads.realmemobile.com", "bdapi-in-ads.realmemobile.com",
    "adx.ads.oppomobile.com", "ck.ads.oppomobile.com", "data.ads.oppomobile.com",
    "api.ad.xiaomi.com", "data.mistat.xiaomi.com", "data.mistat.india.xiaomi.com", "data.mistat.rus.xiaomi.com",
    "sdkconfig.ad.xiaomi.com", "sdkconfig.ad.intl.xiaomi.com", "tracking.rus.miui.com",
    "metrics2.data.hicloud.com", "grs.hicloud.com", "logservice.hicloud.com", "logservice1.hicloud.com", "logbak.hicloud.com",
    "iadsdk.apple.com", "metrics.icloud.com", "metrics.mzstatic.com",
    "books-analytics-events.apple.com", "weather-analytics-events.apple.com", "notes-analytics-events.apple.com",
    "samsungads.com", "smetrics.samsung.com", "samsung-com.112.2o7.net",
})

# Cache location (safe, user-level)
EASYLIST_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".darkelf", "filterlists")
os.makedirs(EASYLIST_CACHE_DIR, exist_ok=True)

# Darkelf's locally compiled subscription.
DARKELF_COMPILED_FILTER = os.path.join(
    EASYLIST_CACHE_DIR,
    "darkelf-standard.txt",
)

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

def _safe_index_token(raw_rule: str) -> str | None:
    """
    Extract a conservative literal token that MUST be present in a matching URL.

    This is only a candidate-selection optimization. If we cannot prove a useful
    literal token exists, return None and keep the rule in the fallback scan.
    Regex rules (/.../) deliberately stay in fallback.
    """
    rule = (raw_rule or "").strip()
    if not rule:
        return None

    if rule.startswith("@@"):
        rule = rule[2:].strip()

    rule, _opts = _split_rule_and_options(rule)
    if not rule:
        return None

    # Arbitrary regex syntax is unsafe to index this way.
    if len(rule) >= 2 and rule.startswith("/") and rule.endswith("/"):
        return None

    # ABP anchors/separators/wildcards split the expression into guaranteed
    # literal runs. Every resulting run is required by the original rule.
    core = rule
    if core.startswith("||"):
        core = core[2:]
    elif core.startswith("|"):
        core = core[1:]
    if core.endswith("|"):
        core = core[:-1]

    parts = re.split(r"[\*\^|]+", core)
    candidates = []

    for part in parts:
        token = part.strip().lower()
        if not token:
            continue

        # Avoid tiny/common strings: they create giant buckets and no speedup.
        # URL-ish punctuation is fine because matching is against the full URL.
        if len(token) < 5:
            continue

        candidates.append(token)

    if not candidates:
        return None

    # Longest literal usually gives the smallest candidate bucket.
    return max(candidates, key=len)

class _NetRule:
    __slots__ = (
        "re", "is_exception", "opts", "raw",
        "domain_allow", "domain_deny",
        "party_mode", "resource_types", "index_token",
    )

    _TYPE_FLAGS = frozenset({
        "script", "xmlhttprequest", "subdocument", "image",
        "stylesheet", "font", "media", "ping", "websocket",
        "worker", "serviceworker", "object", "other",
    })

    def __init__(self, pattern: re.Pattern, is_exception: bool, opts: dict, raw: str = ""):
        self.re = pattern
        self.is_exception = is_exception
        self.opts = opts
        self.raw = raw

        # Precompute ABP option metadata once at load time instead of
        # rebuilding it while scanning the rules for every request.
        dom = opts.get("domain")
        if dom:
            self.domain_allow, self.domain_deny = _parse_domain_list(dom)
        else:
            self.domain_allow = frozenset()
            self.domain_deny = frozenset()

        if "third-party" in opts:
            self.party_mode = 1
        elif "~third-party" in opts:
            self.party_mode = -1
        else:
            self.party_mode = 0

        specified = self._TYPE_FLAGS.intersection(opts)
        self.resource_types = frozenset(specified) if specified else None

        # Safe candidate-index hint. We only index a rule when we can extract
        # a literal substring that MUST occur in every URL matched by that
        # rule. Rules without such a token remain in the fallback bucket.
        self.index_token = None

class EasyListEngine:
    """
    Loads lists -> builds:
      - network rules: list of _NetRule (exceptions first)
      - cosmetic rules: dict[domain or "*"] -> list[selectors]
      - cosmetic exceptions: dict[domain] -> set[selectors]
    """
    def __init__(self):
        self.network_rules: list[_NetRule] = []
        # Candidate indexes built from the SAME network rules. These reduce
        # per-request scanning without removing subscriptions or weakening rules.
        self.rules_by_type: dict[str, list[_NetRule]] = {}
        self.token_rules_by_type: dict[str, dict[str, list[_NetRule]]] = {}
        self.fallback_rules_by_type: dict[str, list[_NetRule]] = {}
        self._rule_order: dict[int, int] = {}
        self.cosmetic: dict[str, list[str]] = {"*": []}
        self.cosmetic_exceptions: dict[str, set[str]] = {}
        # Debug: reason/rule responsible for the most recent block.
        self.last_matched_rule = None

    # ---------- fetch/cache ----------
    def _cache_path_for_url(self, url: str) -> str:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return os.path.join(EASYLIST_CACHE_DIR, f"{h}.txt")

    def _should_refresh(self, path: str) -> bool:
        if not os.path.exists(path):
            return True
        age = _now() - os.path.getmtime(path)
        return age > EASYLIST_REFRESH_EVERY
    
    @staticmethod
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
        
    @staticmethod
    def _compile_darkelf_filter(texts: list[str]) -> str:
        """
        Compile configured upstream subscriptions into one Darkelf Standard
        Protection ruleset while preserving supported Darkelf semantics.

        ``badfilter`` is handled as a cancellation directive: a rule carrying
        ``$badfilter`` disables the otherwise-identical network rule with the
        badfilter option removed.  The directive itself is never emitted as an
        active blocking rule.
        """
        unsupported_options = {
            "permissions", "csp", "redirect", "redirect-rule",
            "removeparam", "urltransform", "replace", "header",
            "strict3p", "strict1p", "ipaddress",
        }

        def canonical_network_key(line: str, drop_badfilter: bool = False):
            """Return a stable identity for an ABP network rule."""
            line = line.strip()
            is_exception = line.startswith("@@")
            body = line[2:].strip() if is_exception else line
            rule, opts = _split_rule_and_options(body)
            if not rule:
                return None

            normalized = []
            for key, value in opts.items():
                if drop_badfilter and key == "badfilter":
                    continue
                if value is True:
                    normalized.append(key)
                else:
                    normalized.append(f"{key}={value}")

            # Option order does not change the identity of an ABP filter.
            normalized.sort()
            prefix = "@@" if is_exception else ""
            return (prefix, rule, tuple(normalized))

        # First pass: collect every badfilter target across every configured
        # subscription. This must happen before compiling ordinary rules because
        # the disabling directive may occur in a later list.
        disabled = set()
        for text in texts:
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("!"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    continue
                if "##" in line or "#@#" in line:
                    continue

                body = line[2:].strip() if line.startswith("@@") else line
                rule, opts = _split_rule_and_options(body)
                if rule and "badfilter" in opts:
                    key = canonical_network_key(line, drop_badfilter=True)
                    if key is not None:
                        disabled.add(key)

        seen = set()
        compiled = []

        for text in texts:
            for raw in text.splitlines():
                line = raw.strip()

                if not line or line.startswith("!"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    continue

                # Cosmetic filters / exceptions are handled by _parse_cosmetic.
                if "##" in line or "#@#" in line:
                    if line not in seen:
                        seen.add(line)
                        compiled.append(line)
                    continue

                network_line = line[2:].strip() if line.startswith("@@") else line
                rule, opts = _split_rule_and_options(network_line)

                if not rule:
                    continue

                # badfilter is metadata, never an active network rule.
                if "badfilter" in opts:
                    continue

                # If a matching badfilter directive exists anywhere in the
                # subscriptions, suppress this corresponding base rule.
                key = canonical_network_key(line)
                if key in disabled:
                    continue

                if any(option in opts for option in unsupported_options):
                    continue

                if line not in seen:
                    seen.add(line)
                    compiled.append(line)

        header = [
            "! Title: Darkelf Standard Protection",
            "! Compiled automatically by shadow/filters.py",
            f"! Rules: {len(compiled)}",
            f"! badfilter cancellations: {len(disabled)}",
            "",
        ]
        return "\n".join(header + compiled) + "\n"

    @staticmethod
    def _write_compiled_filter(text: str) -> None:
        """Atomically write Darkelf's locally compiled subscription."""
        tmp_path = DARKELF_COMPILED_FILTER + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, DARKELF_COMPILED_FILTER)
        except Exception as e:
            print("[Darkelf] Could not write compiled filter:", e)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    def load_and_build(self, urls: list[str]):
        texts = self.fetch_lists(urls)

        # Compile all upstream sources into one Darkelf runtime subscription.
        compiled = self._compile_darkelf_filter(texts)
        self._write_compiled_filter(compiled)

        # Parse ONLY Darkelf Standard at runtime.
        self._parse_texts([compiled])
        self._finalize()

        print(
            "[Darkelf] Compiled filter ready: "
            f"{len(self.network_rules)} network rules, "
            f"{sum(len(v) for v in self.cosmetic.values())} cosmetic rules "
            f"-> {DARKELF_COMPILED_FILTER}"
        )

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
        raw_line = line.strip()
        is_exception = False
        if line.startswith("@@"):
            is_exception = True
            line = line[2:].strip()

        rule, opts = _split_rule_and_options(line)

        # Darkelf implements network blocking, but not response transforms,
        # permission policies, IP-resolution matching, or strict party modes.
        # A rule such as `*$strict3p,ipaddress=...` must be skipped; reducing it
        # to `*` would incorrectly block every request.
        unsupported_options = {
            "permissions",
            "csp",
            "redirect",
            "redirect-rule",
            "removeparam",
            "urltransform",
            "replace",
            "header",
            "strict3p",
            "strict1p",
            "ipaddress",
            "badfilter",
        }

        if any(option in opts for option in unsupported_options):
            return

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

        net_rule = _NetRule(cre, is_exception, opts, raw_line)
        net_rule.index_token = _safe_index_token(raw_line)
        self.network_rules.append(net_rule)

    def _finalize(self):
        # Put exceptions first for fast allow-pass.
        self.network_rules.sort(key=lambda r: (not r.is_exception))

        # Build request-type + literal-token indexes once.
        #
        # Generic rules are NOT blindly scanned for every request anymore.
        # If a rule has a guaranteed literal token, it goes into a token bucket.
        # Only rules that cannot be safely indexed remain in the fallback list.
        # This preserves the same rule set and ordering semantics.
        filterable_types = (
            "script",
            "xmlhttprequest",
            "subdocument",
            "image",
            "ping",
            "other",
        )

        self.rules_by_type = {}
        self.token_rules_by_type = {}
        self.fallback_rules_by_type = {}
        self._rule_order = {
            id(rule): pos
            for pos, rule in enumerate(self.network_rules)
        }

        for req_type in filterable_types:
            applicable = [
                rule for rule in self.network_rules
                if (
                    rule.resource_types is None
                    or req_type in rule.resource_types
                )
            ]
            self.rules_by_type[req_type] = applicable

            token_map: dict[str, list[_NetRule]] = {}
            fallback: list[_NetRule] = []

            for rule in applicable:
                token = rule.index_token
                if token:
                    token_map.setdefault(token, []).append(rule)
                else:
                    fallback.append(rule)

            self.token_rules_by_type[req_type] = token_map
            self.fallback_rules_by_type[req_type] = fallback

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
        req_type: str | None = None,
        *,
        req_host: str | None = None,
        first_party_host: str | None = None,
        request_path: str | None = None,
    ) -> bool:

        # Reset per-request diagnostic state so stale matches are never reported.
        self.last_matched_rule = None

        u = (url or "").lower()

        # The interceptor already has parsed QUrls/hosts. Reuse them when supplied
        # instead of constructing two more QUrl objects for every request.
        fp_host = (first_party_host or _safe_host(first_party_url)).lower().rstrip(".")
        req_host = (req_host or _safe_host(url)).lower().rstrip(".")

        # --------------------------------------------------
        # BASIC SAFETY
        # --------------------------------------------------

        if not req_host or not req_type:
            return False
            
        if req_type == "document":
            return False
            
        # --------------------------------------------------
        # CONSERVATIVE SUPPLEMENTAL BLOCKING
        # --------------------------------------------------

        if request_path is None:
            try:
                request_path = QUrl(url).path().lower()
            except Exception:
                request_path = ""
        else:
            request_path = request_path.lower()

        request_filename = request_path.rsplit("/", 1)[-1]

        # Block exact known tracker hosts.
        # This is intentionally narrow and does not block all AWS traffic.
        if (
            req_type in (
                "script",
                "xmlhttprequest",
                "subdocument",
            )
            and req_host in SUPPLEMENTAL_TRACKER_HOSTS
        ):
            self.last_matched_rule = f"SUPPLEMENTAL_TRACKER_HOSTS: {req_host}"
            return True

        # Compact declarative host rules. These are evaluated in O(1) before
        # candidate collection/regex matching and apply to subresources only
        # (top-level documents were already returned above).
        if req_host in DECLARATIVE_TRACKER_HOSTS:
            self.last_matched_rule = f"DECLARATIVE_TRACKER_HOST: {req_host}"
            return True

        # Block local bait scripts only on known ad-block test pages.
        # This avoids breaking legitimate websites that happen to use
        # filenames such as analytics.js.
        is_adblock_test_page = any(
            is_domain(fp_host, domain)
            for domain in ADBLOCK_TEST_DOMAINS
        )

        if (
            is_adblock_test_page
            and req_type == "script"
            and request_filename in ADBLOCK_TEST_BAIT_FILES
        ):
            self.last_matched_rule = f"ADBLOCK_TEST_BAIT: {request_filename}"
            return True
            
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

        # BrowserLeaks is a diagnostic/fingerprinting site. Do not expose
        # Shadow's filter-list signature by applying EasyList/EasyPrivacy to
        # its synthetic subscription probes. This does NOT disable filtering
        # anywhere else; BrowserLeaks simply receives the normal unfiltered
        # diagnostic resources it requested.
        if is_domain(fp_host, "browserleaks.com"):
            return False

        # --------------------------------------------------
        # NEVER INTERFERE WITH BROWSER TESTS / BENCHMARKS
        # --------------------------------------------------

        TEST_DOMAINS = (
            # Browser security tests
            "browseraudit.com",
            "browseraudit.org",
            # Benchmarks
            "browserbench.org",
            "speedometer.dev",
            "motionmark.io",
            "jetstream2.net",

            # Web platform tests
            "web-platform-tests.org",
        )

        if any(
            is_domain(fp_host, domain)
            or is_domain(req_host, domain)
            for domain in TEST_DOMAINS
        ):
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
                "twimg.com",
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
                "ping",
                "other",
            )
        ):
            return False

        # --------------------------------------------------
        # MEDIA / PRESENTATION COMPATIBILITY
        # --------------------------------------------------

        # Keep actual audio/video streams permissive so playback sites do not
        # regress. Images are deliberately NOT bypassed here: third-party
        # tracking pixels commonly use the image request type and must reach
        # EasyList/EasyPrivacy below. Same-site images were already allowed by
        # the SAME-SITE CORE RESOURCES fast path above.
        if req_type in (
            "media",
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
            # AWS CDN / delivery
            "cloudfront.net",

            # AWS WAF
            "awswaf.com",
            "token.awswaf.com",

            # Google infrastructure
            "gstatic.com",
            "googleapis.com",

            # Cloudflare
            "cloudflare.com",
        )

        # Known tracker hosts on AWS should still be blocked.
        if req_host in SUPPLEMENTAL_TRACKER_HOSTS:
            self.last_matched_rule = f"SUPPLEMENTAL_TRACKER_HOSTS: {req_host}"
            return True

        # Fast-path AWS infrastructure.
        # Skip the expensive EasyList scan for ordinary AWS resources.
        if req_host.endswith(".amazonaws.com"):
            return False

        # Skip other trusted infrastructure.
        if any(
            req_host == domain
            or req_host.endswith("." + domain)
            for domain in SAFE_INFRA
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
        # TRUSTED VIDEO PLAYER CORE
        # --------------------------------------------------

        VIDEO_PLAYER_HOSTS = (
            "vjs.zencdn.net",
            "cdn.jsdelivr.net",
        )

        VIDEO_PLAYER_SCRIPTS = (
            "video.js",
            "videojs-contrib-quality-levels.js",
        )

        if (
            req_type == "script"
            and any(
                req_host == d or req_host.endswith("." + d)
                for d in VIDEO_PLAYER_HOSTS
            )
            and any(
                name in request_filename
                for name in VIDEO_PLAYER_SCRIPTS
            )
        ):
            return False
            
        # --------------------------------------------------
        # PING / OTHER COMPATIBILITY
        # --------------------------------------------------

        # Same-site ping/other requests were already allowed by the
        # SAME-SITE CORE RESOURCES fast path above. Third-party ping/other
        # requests deliberately receive NO blanket bypass here: they continue
        # through the normal Darkelf / EasyList / EasyPrivacy rules below.
        # This keeps site-local beacon-style functionality compatible without
        # exempting third-party tracking beacons from filtering.

        # --------------------------------------------------
        # THIRD-PARTY TRACKER SUBDOCUMENTS
        # --------------------------------------------------

        # Some tracker endpoints arrive through Qt as ``subdocument`` even when
        # upstream ABP subscriptions describe their beacon behavior as ``ping``.
        # Keep ABP resource-type matching strict for compatibility, and block
        # these confirmed tracker hosts explicitly when embedded third-party.
        TRACKER_SUBDOCUMENT_HOSTS = (
            "trackersimulator.org",
            "eviltracker.net",
        )

        if (
            is_third_party
            and req_type == "subdocument"
            and any(is_domain(req_host, d) for d in TRACKER_SUBDOCUMENT_HOSTS)
        ):
            self.last_matched_rule = f"TRACKER_SUBDOCUMENT: {req_host}"
            return True

        # --------------------------------------------------
        # HARD TRACKERS ONLY
        # --------------------------------------------------

        HARD_TRACKERS = (

            # Existing high-confidence trackers
            "adnxs.com",
            "criteo.com",
            "taboola.com",
            "outbrain.com",
            "quantserve.com",

            # Video / display / programmatic advertising
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "adswizz.com",
            "megaphone.fm",
            "teads.tv",
            "spotxchange.com",
            "freewheel.tv",
            "tremorhub.com",
            "connatix.com",
            "amazon-adsystem.com",
            "media.net",
            "adroll.com",
            "pubmatic.com",
            "openx.net",
            "rubiconproject.com",
            "casalemedia.com",
            "revcontent.com",
            "mgid.com",
            "content-ad.net",
            "zemanta.com",
            "ntv.io",
            "sharethrough.com",
            "3lift.com",

            # Mobile advertising
            "unity3d.com",
            "applovin.com",
            "supersonicads.com",
            "vungle.com",
            "chartboost.com",
            "inmobi.com",
            "rayjump.com",
            "fyber.com",
            "smaato.net",

            # Analytics / behavioral tracking
            "google-analytics.com",
            "hotjar.com",
            "mxpnl.com",
            "amplitude.com",
            "segment.com",
            "heapanalytics.com",
            "fullstory.com",
            "crazyegg.com",

            # Social advertising / conversion tracking
            "ads-twitter.com",
            "ads.linkedin.com",
            "licdn.com",
            "pinterest.com",
            "analytics.tiktok.com",
            "sc-static.net",

            # Cross-site identity / measurement
            "bluekai.com",
            "id5-sync.com",
            "crwdcntrl.net",
            "scorecardresearch.com",
            "imrworldwide.com",
            "rlcdn.com",
            "adsrvr.org",
            "agkn.com",
            "tapad.com",
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
            self.last_matched_rule = f"HARD_TRACKER: {req_host}"
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
                self.last_matched_rule = f"HEURISTIC: {req_host}"
                return True

        # --------------------------------------------------
        # RESTRICT EASYLIST EVAL
        # --------------------------------------------------

        easylist_types = {
            "script",
            "xmlhttprequest",
            "subdocument",
            # Privacy tests and real trackers frequently use 1x1 pixels,
            # beacons, or generic requests rather than JavaScript. These must
            # be evaluated by the filter lists instead of being auto-allowed.
            "image",
            "ping",
            "other",
        }

        if req_type not in easylist_types:
            return False

        # --------------------------------------------------
        # EASYLIST EVALUATION
        # --------------------------------------------------

        # Candidate selection:
        #   1. always include rules that could not be safely token-indexed;
        #   2. add only token-indexed rules whose guaranteed literal occurs in
        #      this URL;
        #   3. restore original exceptions-first/network-rule ordering.
        #
        # This avoids regex-testing hundreds of thousands of unrelated generic
        # rules while preserving the complete supported Darkelf ruleset.
        fallback_rules = self.fallback_rules_by_type.get(req_type)
        token_map = self.token_rules_by_type.get(req_type)

        if fallback_rules is None or token_map is None:
            candidate_rules = self.network_rules
        else:
            candidates = list(fallback_rules)
            for token, token_rules in token_map.items():
                if token in u:
                    candidates.extend(token_rules)

            # Rules are shared objects; id->position is used only to restore the
            # exact original exceptions-first order after bucket collection.
            seen_ids = set()
            candidate_rules = []
            for rule in sorted(candidates, key=lambda r: self._rule_order[id(r)]):
                rid = id(rule)
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    candidate_rules.append(rule)

        for rule in candidate_rules:

            # Preserve domain= semantics, but use metadata parsed once when the
            # rule was loaded instead of reparsing the option string here.
            if rule.domain_allow and not any(
                _host_matches_domain(fp_host, d)
                for d in rule.domain_allow
            ):
                continue

            if rule.domain_deny and any(
                _host_matches_domain(fp_host, d)
                for d in rule.domain_deny
            ):
                continue

            if rule.party_mode == 1 and not is_third_party:
                continue

            if rule.party_mode == -1 and is_third_party:
                continue

            # Preserve strict ABP resource-type matching.
            if (
                rule.resource_types is not None
                and req_type not in rule.resource_types
            ):
                continue

            try:

                if rule.re.search(u):

                    # Exceptions ALWAYS WIN

                    if rule.is_exception:
                        self.last_matched_rule = f"ALLOW: {rule.raw}"
                        return False

                    # All exception rules were sorted ahead of blocking rules
                    # in _finalize(). Once a blocking rule matches, no later rule
                    # can override it, so stop instead of scanning ~420k rules.
                    self.last_matched_rule = rule.raw
                    return True

            except re.error:
                # Ignore malformed regex rules and continue checking others.
                continue

        return False
        
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

