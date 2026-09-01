# shadow/miniai.py

import time
import re
from collections import deque
from urllib.parse import urlparse, unquote

class DarkelfMiniAISentinel:
    """
    Aggressive + Expanded Edition for Darkelf Shadow (PyQt5) - Enhanced for modern trackers,
    ClearURLs, AdGuard, full fingerprint monitoring, and advanced reporting.
    """

    MAX_URL_LENGTH = 2048
    CRITICAL_WINDOW_SECONDS = 60

    def __init__(self):
        self.enabled = True
        self.events = deque(maxlen=500)
        self.tracker_hits = 0
        self.suspicious_hits = 0
        self.malware_hits = 0
        self.exploit_attempts = 0
        self.fingerprint_attempts = 0
        self.intrusion_attempts = 0
        self.http_blocks_attempts = 0
        self.session_start = time.time()
        self.unique_domains = set()
        self.redirects = []
        # Aggressive lockdown!
        self.lockdown_active = False
        self.lockdown_threshold = 4  # 4 critical event triggers lockdown
        self.lockdown_triggered_at = None
        self.tracker_window = deque(maxlen=50)
        self.domain_risk_cache = {}
        self.ui = None

        # --- Panic Mode ---
        self.panic_mode_active = False
        self.panic_threshold = 8  # number of critical events within window
        self.panic_triggered_at = None
        self.critical_events = deque(maxlen=20)

        # --- Enhancements to reduce false positives ---
        # Only treat these as "tools" when they appear as separate tokens in path/query/fragment
        # (not as part of random words/domains).
        self.hacker_tools = [
            "nmap",
            "sqlmap",
            "metasploit",
            "burpsuite",
            "nikto",
            "dirbuster",
            "hydra",
            "wireshark",
            "tcpdump",
            "ettercap",
            "aircrack",
            "hashcat",
            "johntheripper",
            "cobalt",
            "mimikatz",
        ]

        # Intrusion patterns: keep your list, but we will apply smarter matching below.
        self.intrusion_patterns = {
            "sql_injection": ["union select", "or 1=1", "'; drop", "exec(", "script>"],
            "xss": ["<script", "javascript:", "onerror=", "onload=", "eval("],
            "path_traversal": ["../", "..\\", "%2e%2e", "etc/passwd", "windows/system"],
            "command_injection": ["| cat", "; ls", "&& whoami", "cmd.exe", "/bin/bash"],
            "malware": ["ransomware", "cryptolocker", "wannacry", "trojan", "backdoor"],
            "exploit": ["metasploit", "shellcode", "exploit-db", "cve-", "0day"],
            "phishing": [
                "verify-account",
                "suspended-account",
                "confirm-identity",
                "urgent-action",
            ],
            "exfil": [
                "download.php?file=",
                "data:application/octet-stream",
                "data:text/plain;base64",
            ],
        }

        # Add AdGuard/clearurls-specific domains
        # Fix: "clearurls" is not a domain; keep it for URL keyword detection but not domain matching.
        # Fix: TLD markers (".tk" etc.) should match exact TLD, not substring anywhere in domain.
        self.high_risk_domains = [
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "adguard.com",
            "facebook.net",
            "scorecardresearch.com",
            "quantserve.com",
            "taboola.com",
            "outbrain.com",
            "criteo.com",
            "adnxs.com",
        ]
        self.high_risk_tlds = {".tk", ".ml", ".ga", ".cf", ".gq"}

        # Trusted high-traffic infrastructure (prevents false positives)
        self.trusted_cdn_domains = {
            "youtube.com",
            "ytimg.com",
            "googlevideo.com",
            "gstatic.com",
            "fonts.gstatic.com",
            "googleusercontent.com",
            "cloudflare.com",
            "cdnjs.cloudflare.com",
        }

        self.fingerprint_apis = {
            "canvas": 0,
            "webgl": 0,
            "audio": 0,
            "font": 0,
            "battery": 0,
            "geolocation": 0,
            "media_devices": 0,
            "webrtc": 0,
        }
        self.request_timestamps = deque(maxlen=100)
        self.anomaly_threshold = 150  # Aggressive!
        self.flood_threshold = 3500

        # Static assets that should not trigger anomaly detection
        self.static_extensions = (
            ".svg",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
            ".woff",
            ".woff2",
            ".ttf",
            ".css",
            ".ico",
        )

        print("[MiniAI] Aggressive & Expanded Sentinel ready (threshold=4)")

    # --- Helper methods (new) ---
    def _safe_parse_url(self, url_norm: str):
        """
        Parse URL once and return (parsed, domain, path, query, fragment).
        This reduces false positives by applying stricter checks to path/query rather than entire URL string.
        """
        try:
            p = urlparse(url_norm)
            domain = (p.netloc or "").lower()
            path = (p.path or "").lower()
            query = (p.query or "").lower()
            fragment = (p.fragment or "").lower()
            return p, domain, path, query, fragment
        except Exception as e:
            print(e)
            return None, "", "", "", ""

    def _domain_matches(self, domain: str, candidate: str) -> bool:
        """
        True if domain is exactly candidate or a subdomain of it.
        Avoids substring false positives like 'notdoubleclick.net.example.com' containing 'doubleclick.net'.
        """
        if not domain or not candidate:
            return False
        domain = domain.strip(".")
        candidate = candidate.strip(".")
        return domain == candidate or domain.endswith("." + candidate)

    def _has_high_risk_tld(self, domain: str) -> bool:
        """
        Match exact TLD (.tk, .ml, ...) rather than substring anywhere.
        """
        if not domain:
            return False
        # domain might include port (example.com:8080)
        host = domain.split(":")[0]
        host = host.strip(".")
        dot = host.rfind(".")
        if dot == -1:
            return False
        tld = host[dot:]
        return tld in self.high_risk_tlds

    def _token_present(self, haystack: str, token: str) -> bool:
        """
        Word-boundary-ish token detection for URLs:
        consider separators commonly seen in URLs rather than only \b (which doesn't handle '-' well).
        """
        if not haystack or not token:
            return False
        # Treat these as separators: / ? & = # : . - _ +
        pattern = (
            r"(?:^|[\/\?\&\=\#\:\.\-\_\+])"
            + re.escape(token)
            + r"(?:$|[\/\?\&\=\#\:\.\-\_\+])"
        )
        return re.search(pattern, haystack) is not None

    def monitor_network(self, url, headers=None):

        if not self.enabled or not url:
            return

        if self.panic_mode_active:
            print("🚨 [MiniAI] PANIC MODE: All requests blocked:", str(url)[:80])
            return

        # AUTO-RELEASE LOCKDOWN AFTER 5 MINUTES
        if self.lockdown_active:
            print("[MiniAI] LOCKDOWN: Absolute block:", str(url)[:80])
            return

        now = time.time()

        # Normalize carefully: decode twice like you do, but keep within MAX_URL_LENGTH.
        url_norm = unquote(unquote(str(url)))[: self.MAX_URL_LENGTH]
        url_norm_l = url_norm.lower()

        parsed, domain, path, query, fragment = self._safe_parse_url(url_norm_l)

        if domain:
            self.unique_domains.add(domain)

        event = {
            "url": url_norm_l,
            "timestamp": now,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
            "threats": [],
            "risk_level": "low",
        }

        # --- Domain Risk Cache ---
        if domain:
            if domain in self.domain_risk_cache:
                cached = self.domain_risk_cache[domain]

                # Apply cached risk level
                event["threats"].append("DOMAIN_CACHE")
                event["risk_level"] = min(
                    event["risk_level"],
                    cached.get("risk", "low"),
                    key=lambda r: ["low", "medium", "high", "critical"].index(r),
                )

                # Track how many times we've seen it
                cached["seen"] += 1

            else:
                # First time seeing this domain
                self.domain_risk_cache[domain] = {
                    "risk": event["risk_level"],
                    "seen": 1,
                }
        # -------------------------
        # 1) Intrusion pattern detection (reduced false positives)
        # -------------------------
        # Apply most string patterns to query+path+fragment, not full URL (domain can contain misleading substrings).
        focus = f"{path}?{query}#{fragment}"

        for key, patterns in self.intrusion_patterns.items():
            for pat in patterns:
                # Keep your behavior but only match on focus string to reduce domain-based false positives
                if pat in focus:
                    self.intrusion_attempts += 1
                    event["threats"].append(f"INTRUSION:{key.upper()}:{pat}")
                    # Escalate repeated intrusions
                    if self.intrusion_attempts >= 3:
                        event["risk_level"] = "critical"
                        self.intrusion_attempts = 0
                    # Only some categories should immediately be critical.
                    if key in (
                        "sql_injection",
                        "path_traversal",
                        "command_injection",
                        "exfil",
                    ):
                        event["risk_level"] = "critical"
                    elif key in ("xss", "phishing", "malware", "exploit"):
                        # still serious, but don't always auto-lockdown unless other indicators confirm
                        if event["risk_level"] == "low":
                            event["risk_level"] = "high"

        # Hacker tools: only treat as critical when present as tokens in path/query/fragment
        tool_focus = f"{path}&{query}#{fragment}"
        for tool in self.hacker_tools:
            if self._token_present(tool_focus, tool):
                self.intrusion_attempts += 1
                event["threats"].append("TOOL:" + tool.upper())
                event["risk_level"] = "critical"

        # Regex detection (tightened)
        # - Use word boundaries and safer patterns.
        # - Apply to focus only.
        regexes = [
            (
                r"(?:\bunion\b\s+\bselect\b|\bor\b\s+1\s*=\s*1\b|\bdrop\b\s+\btable\b|\binsert\b\s+\binto\b)",
                "critical",
            ),
            (r"(?:<script\b|javascript:|\bonerror\s*=|\bonload\s*=)", "high"),
            (r"(?:\.\./|\.\.\\|%2e%2e)", "critical"),
            (r"(?:;|\|\||&&)\s*(?:whoami|ls|cat|bash|cmd(?:\.exe)?)\b", "critical"),
        ]
        for reg, risk in regexes:
            try:
                if re.search(reg, focus, flags=re.IGNORECASE):
                    event["threats"].append(f"INTRUSION-REGEX:{risk}")
                    # Preserve your intent: critical triggers lockdown
                    if risk == "critical":
                        event["risk_level"] = "critical"
                    elif event["risk_level"] == "low":
                        event["risk_level"] = risk
            except re.error:
                # fail safe: if regex is invalid for some reason, skip it
                pass

        # -------------------------
        # 2) Domain-level risk (fixed matching)
        # -------------------------
        if domain:
            for bad in self.high_risk_domains:
                if self._domain_matches(domain, bad):
                    event["threats"].append(f"HIGH_RISK_DOMAIN:{bad}")
                    if event["risk_level"] == "low":
                        event["risk_level"] = "medium"

            if self._has_high_risk_tld(domain):
                event["threats"].append("HIGH_RISK_TLD")
                if event["risk_level"] == "low":
                    event["risk_level"] = "medium"

        # -------------------------
        # 3) Passive tracker/fingerprint/malware/exploit detection (reduced false positives)
        # -------------------------
        # Malware: require stronger context than just substring "trojan" etc anywhere.
        malware_terms = (
            "malware",
            "virus",
            "trojan",
            "ransomware",
            "backdoor",
            "cryptolocker",
            "wannacry",
        )
        if any(self._token_present(focus, t) for t in malware_terms) or (
            "c2" in query and ("panel" in path or "gate" in path)
        ):
            self.malware_hits += 1
            event["threats"].append("MALWARE")
            event["risk_level"] = "critical"

        # Exploit: "exploit" and "payload" are common benign words; only escalate if combined with other exploit indicators.
        exploit_indicators = ("shellcode", "metasploit", "exploit-db", "cve-", "0day")
        if any(x in focus for x in exploit_indicators) or (
            ("payload" in focus or "exploit" in focus)
            and ("cve-" in focus or "shellcode" in focus)
        ):
            self.exploit_attempts += 1
            event["threats"].append("EXPLOIT")
            event["risk_level"] = "critical"

        # Phishing: keep your detection, but use focus and token-ish checks
        if any(
            x in focus
            for x in (
                "verify-account",
                "suspended-account",
                "confirm-identity",
                "urgent-action",
            )
        ) or self._token_present(focus, "phish"):
            self.suspicious_hits += 1
            event["threats"].append("PHISHING")
            if event["risk_level"] in ("low", "medium"):
                event["risk_level"] = "high"

        # Trackers: keep broad detection, but avoid counting "clearurls" as domain risk; it's a keyword only.
        if any(
            x in url_norm_l
            for x in (
                "tracker",
                "analytics",
                "beacon",
                "doubleclick",
                "facebook.net",
                "clearurls",
                "adguard",
            )
        ):
            self.tracker_hits += 1
            self.tracker_window.append(now)

            tracker_burst = sum(1 for t in self.tracker_window if (now - t) < 2)

            if tracker_burst > 25:
                event["threats"].append("TRACKER_STORM")
                event["risk_level"] = "high"
            event["threats"].append("TRACKER")
            if event["risk_level"] == "low":
                event["risk_level"] = "medium"

        # Fingerprint API triggers (simulate Cover Your Tracks test)
        # Reduce false positives: check in focus first; fallback to full URL if needed.
        fp_focus = focus if focus else url_norm_l
        for k in self.fingerprint_apis:
            if self._token_present(fp_focus, k) or (
                k in fp_focus and k in ("webgl", "webrtc", "canvas")
            ):
                self.fingerprint_apis[k] += 1
                event["threats"].append(f"FINGERPRINT:{k}")
                if event["risk_level"] == "low":
                    event["risk_level"] = "medium"
                self.fingerprint_attempts += 1

        # -------------------------
        # 4) Anomaly detection windows (bugfix + keep aggressive intent)
        # -------------------------
        self.request_timestamps.append(now)

        last1s = sum(1 for t in self.request_timestamps if (now - t) < 1.0)

        trusted_domain = any(
            self._domain_matches(domain, d) for d in self.trusted_cdn_domains
        )

        is_static_asset = any(path.endswith(ext) for ext in self.static_extensions)

        # Burst detection
        if (
            last1s > self.anomaly_threshold
            and not trusted_domain
            and not is_static_asset
        ):
            event["threats"].append("ANOMALY:burst")
            if event["risk_level"] in ("low", "medium"):
                event["risk_level"] = "high"

        if last1s > self.flood_threshold and not trusted_domain and not is_static_asset:
            event["threats"].append("ANOMALY:REQUEST_FLOOD")
            event["risk_level"] = "critical"

        # Rapid redirect loop detection (unchanged)
        if len(self.redirects) > 7:
            event["threats"].append("ANOMALY:redirect_loop")
            if event["risk_level"] in ("low", "medium"):
                event["risk_level"] = "high"

        self.events.append(event)

        # -------------------------
        # 5) Lockdown trigger
        # -------------------------
        real_attack = any(
            kw in t.upper()
            for t in event.get("threats", [])
            for kw in ("INTRUSION", "MALWARE", "EXPLOIT", "TOOL")
        )

        if event.get("risk_level") == "critical" and real_attack:

            self.critical_events.append(now)

            print("\n🔴 [MiniAI] CRITICAL threat detected!")
            print("Threats:", event.get("threats"))

            recent = [
                t
                for t in self.critical_events
                if (now - t) < self.CRITICAL_WINDOW_SECONDS
            ]

            # Trigger lockdown only after threshold
            if len(recent) >= self.lockdown_threshold:

                if not self.lockdown_active:
                    self.lockdown_active = True
                    self.lockdown_triggered_at = now

                    print("🔒 Darkelf MiniAI LOCKDOWN ENGAGED")

            # Panic mode
            if len(recent) >= self.panic_threshold:
                self.trigger_panic_mode("Multiple critical intrusion events")

            print("🛑 Event:", event)

    def on_http_blocked(self, url):

        https_url = url.replace("http://", "https://", 1)

        self.http_blocks_attempts += 1

        event = {
            "url": url,
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "threats": ["HTTP_AUTO_UPGRADE"],
            "risk_level": "medium",
            "upgrade_to": https_url,
        }

        self.events.append(event)

        print(f"[MiniAI] 🔒 HTTP upgraded: {url[:60]} → {https_url[:60]}")

    # Expanded statistics/report as passive mode
    def get_statistics(self):

        uptime = time.time() - self.session_start

        # ---- Threat Score Calculation ----
        threat_score = (
            self.tracker_hits * 1
            + self.suspicious_hits * 1
            + self.fingerprint_attempts * 2
            + self.intrusion_attempts * 4
            + self.malware_hits * 6
            + self.exploit_attempts * 6
            + self.http_blocks_attempts * 1
        )

        return {
            "uptime_seconds": uptime,
            "total_events": len(self.events),
            "unique_domains": len(self.unique_domains),
            # NEW
            "threat_score": threat_score,
            "lockdown": {
                "active": self.lockdown_active,
                "threshold": self.lockdown_threshold,
                "triggered_at": self.lockdown_triggered_at,
            },
            "threats": {
                "trackers": self.tracker_hits,
                "suspicious": self.suspicious_hits,
                "malware": self.malware_hits,
                "exploits": self.exploit_attempts,
                "intrusions": self.intrusion_attempts,
                "fingerprinting": self.fingerprint_attempts,
                "http_blocks": self.http_blocks_attempts,
            },
            "fingerprinting_apis": dict(self.fingerprint_apis),
            "recent_threats": [
                e
                for e in list(self.events)[-10:]
                if e["risk_level"] in ("high", "critical")
            ],
            "panic": {
                "active": self.panic_mode_active,
                "triggered_at": self.panic_triggered_at,
            },
        }

    def get_threat_report(self):
        stats = self.get_statistics()
        uptime_min = stats["uptime_seconds"] / 60

        if self.panic_mode_active:
            lockdown_status = "🚨 PANIC"
        elif stats["lockdown"]["active"]:
            lockdown_status = "🔴 LOCKDOWN"
        else:
            lockdown_status = "🟢 STANDBY"
        domain_stats = {}
        for event in self.events:
            dom = urlparse(event["url"]).netloc or "unknown"
            if dom not in domain_stats:
                domain_stats[dom] = {
                    "trackers": 0,
                    "fingerprinting": 0,
                    "malware": 0,
                    "intrusions": 0,
                    "http_blocks": 0,
                    "risk_level": "low",
                }
            for threat in event["threats"]:
                if "TRACKER" in threat:
                    domain_stats[dom]["trackers"] += 1
                elif "FINGERPRINT" in threat:
                    domain_stats[dom]["fingerprinting"] += 1
                elif "MALWARE" in threat or "EXPLOIT" in threat:
                    domain_stats[dom]["malware"] += 1
                elif "INTRUSION" in threat or "TOOL" in threat:
                    domain_stats[dom]["intrusions"] += 1
                elif "HTTP_AUTO_UPGRADE" in threat:
                    domain_stats[dom]["http_blocks"] += 1
            if event["risk_level"] == "critical":
                domain_stats[dom]["risk_level"] = "critical"
            elif (
                event["risk_level"] == "high"
                and domain_stats[dom]["risk_level"] != "critical"
            ):
                domain_stats[dom]["risk_level"] = "high"
            elif (
                event["risk_level"] == "medium"
                and domain_stats[dom]["risk_level"] == "low"
            ):
                domain_stats[dom]["risk_level"] = "medium"
        sorted_domains = sorted(
            domain_stats.items(),
            key=lambda x: (
                x[1]["trackers"]
                + x[1]["fingerprinting"]
                + x[1]["malware"]
                + x[1]["intrusions"]
                + x[1]["http_blocks"]
            ),
            reverse=True,
        )
        report = f"""
╔══════════════════════════════════════════════════════════╗
║         DARKELF MiniAI - THREAT REPORT                   ║
╚══════════════════════════════════════════════════════════╝
Session Uptime:     {uptime_min:.1f} min
Total Events:       {stats['total_events']}
Unique Domains:     {stats['unique_domains']}
Lockdown Status:    {lockdown_status}
THREAT SUMMARY:
├─ Trackers:        {stats['threats']['trackers']}
├─ Suspicious:      {stats['threats']['suspicious']}
├─ Malware:         {stats['threats']['malware']}
├─ Exploits:        {stats['threats']['exploits']}
├─ Intrusions:      {stats['threats']['intrusions']}
├─ HTTP Blocks:     {stats['threats'].get('http_blocks', 0)}
└─ Fingerprinting:  {stats['threats']['fingerprinting']}
FINGERPRINTING DEFENSE STATUS:
├─ Canvas:          {stats['fingerprinting_apis']['canvas']} attempts → NOISE
├─ WebGL:           {stats['fingerprinting_apis']['webgl']} attempts → SPOOFED
├─ Audio:           {stats['fingerprinting_apis']['audio']} attempts → ZEROED
├─ Font:            {stats['fingerprinting_apis']['font']} attempts → HIDDEN
├─ Battery:         {stats['fingerprinting_apis']['battery']} attempts → SPOOFED
├─ Geolocation:     {stats['fingerprinting_apis']['geolocation']} attempts → BLOCKED
├─ Media Devices:   {stats['fingerprinting_apis']['media_devices']} attempts → EMPTY
└─ WebRTC:          {stats['fingerprinting_apis']['webrtc']} attempts → DISABLED
TOP 10 THREAT DOMAINS:
"""
        for i, (dom, threats) in enumerate(sorted_domains[:10], 1):
            tracker_icon = "🔴" if threats["trackers"] > 0 else "⚪"
            fp_icon = "🟡" if threats["fingerprinting"] > 0 else "⚪"
            malware_icon = "🚨" if threats["malware"] > 0 else "⚪"
            intrusion_icon = "⛔" if threats["intrusions"] > 0 else "⚪"
            http_icon = "🔒" if threats["http_blocks"] > 0 else "⚪"
            risk_color = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "⚪",
            }.get(threats["risk_level"], "⚪")
            report += (
                f"\n{i:2d}. {risk_color} {dom[:45]:<45}\n"
                f"    Track: {tracker_icon} {threats['trackers']:2d}"
                f" | FP: {fp_icon} {threats['fingerprinting']:2d}"
                f" | Mal: {malware_icon} {threats['malware']:2d}"
                f" | Intru: {intrusion_icon} {threats['intrusions']:2d}"
                f" | HTTP: {http_icon} {threats['http_blocks']:2d}"
            )
        report += f"\n\nRECENT HIGH-RISK EVENTS: {len(stats['recent_threats'])}"
        for event in stats["recent_threats"][-5:]:
            report += f"\n  • {event['datetime']} | {event['risk_level'].upper()} | {', '.join(event['threats'][:2])}"
        report += "\n" + "=" * 62
        if self.panic_mode_active:
            report += "\n  🚨 PANIC MODE ACTIVE - Browser compromised state"
        elif stats["lockdown"]["active"]:
            report += "\n  🔴 LOCKDOWN ACTIVE - All requests blocked"
        else:
            report += "\n  ✅ No fingerprint leaks. All tracker attempts defended."

        report += "\n" + "=" * 62
        return report

    def is_locked_down(self):
        return self.lockdown_active

    def reset_lockdown(self, admin_override=False):
        if not admin_override:
            print("[MiniAI] Lockdown reset requires admin_override=True")
            return False
        self.lockdown_active = False
        self.lockdown_triggered_at = None
        self.events.clear()
        print("[MiniAI] 🟢 Lockdown reset - System restored")
        return True

    def trigger_panic_mode(self, reason="unknown"):
        if self.panic_mode_active:
            return

        self.panic_mode_active = True
        self.lockdown_active = True
        self.panic_triggered_at = time.time()

        print("\n🚨🚨🚨 DARKELF PANIC MODE ACTIVATED 🚨🚨🚨")
        print("Reason:", reason)
        print("All browser network activity halted.")
        print("User intervention required.\n")

        # Future integrations
        # close tabs
        # disable JS
        # clear cookies
        # isolate profile

    def reset_panic(self, admin_override=False):
        if not admin_override:
            print("[MiniAI] Panic reset requires admin_override=True")
            return False

        self.panic_mode_active = False
        self.lockdown_active = False
        self.panic_triggered_at = None
        self.lockdown_triggered_at = None
        self.critical_events.clear()

        print("[MiniAI] 🟢 Panic mode cleared - system restored")
        return True

    def check_lockdown_timeout(self):

        now = time.time()

        # -------------------------
        # Auto-release LOCKDOWN
        # -------------------------
        if (
            self.lockdown_active
            and self.lockdown_triggered_at
            and now - self.lockdown_triggered_at > 300
        ):
            print("[MiniAI] 🟢 Lockdown auto-released")

            self.lockdown_active = False
            self.lockdown_triggered_at = None

            # Clear old attack history
            self.critical_events.clear()

        # -------------------------
        # Auto-release PANIC MODE
        # -------------------------
        if (
            self.panic_mode_active
            and self.panic_triggered_at
            and now - self.panic_triggered_at > 300
        ):
            print("[MiniAI] 🟢 Panic auto-released")

            self.panic_mode_active = False
            self.panic_triggered_at = None

            # Also clear lockdown state
            self.lockdown_active = False
            self.lockdown_triggered_at = None

            # Full recovery reset
            self.critical_events.clear()

    def shutdown(self):
        if not self.enabled:
            return
        self.enabled = False
        try:
            print(self.get_threat_report())
        except Exception as e:
            print("[MiniAI] Report failed:", e)
