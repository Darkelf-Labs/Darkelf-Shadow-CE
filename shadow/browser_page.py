import json
import secrets
import platform

from shadow.browser_icons import detect_nav_platform

from PySide6.QtCore import QTimer



from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineScript,
    QWebEngineSettings,
)

from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit

class HardenedWebPage(QWebEnginePage):

    # ============================================================
    # CANVAS PRIVACY POLICY
    # ============================================================
    # PROTECTED: Qt canvas readback is enabled, while Darkelf's
    # deterministic canvas protection remains active.
    CANVAS_PROTECTED_DOMAINS = {
        "espn.com",
        "target.com",
        "spotify.com",
        "chase.com",
        "bankofamerica.com",
        "wellsfargo.com",
        "capitalone.com",
        "citi.com",
        "sourceforge.net",
        "fsharetv.com",
        "rophimx.net",
        "duckduckgo.com",
        "google.com",
        "gmail.com",
        "googleusercontent.com",
        "gstatic.com",
        "outlook.com",
        "office.net",
        "darkelfbrowser.com",
    }

    # TRUSTED: normal/native canvas behavior. Keep this list very small.
    CANVAS_TRUSTED_DOMAINS = {
        "github.com",
        "coveryourtracks.eff.org",
        "login.microsoftonline.com",
        "outlook.live.com",
        "outlook.office.com",
        "outlook.office365.com",
        "microsoft.com",
        "appleid.apple.com",
    }

    # Path-scoped protected exceptions.
    CANVAS_PROTECTED_URLS = {
        ("browserleaks.com", "/proxy"),
    }

    COMPATIBILITY_MODE_DOMAINS = {
        "degreeinfo.com",

        # Google / Gmail / Workspace
        "google.com",
        "gmail.com",
        "googleapis.com",
        "googleusercontent.com",
        "gstatic.com",
        "ggpht.com",
        "googlemail.com",
        "workspace.google.com",
        "accounts.google.com",
        "github.com",
        "appleid.apple.com",
        
        # TikTok
        "tiktok.com",
        "tiktokcdn.com",
        "tiktokcdn-us.com",
        "ttwstatic.com",
        "tiktokv.com",
        
        # Messaging
        "zalo.me",
        "zaloapp.com",
        "zadn.vn",
        "whatsapp.com",
        "whatsapp.net",
        "discord.com",
        "discordapp.com",
        
        # Microsoft / Outlook
        "outlook.live.com",
        "login.microsoftonline.com",
        "login.live.com",

        # Darkelf website
        "darkelfbrowser.com",

        # Spotify
        "spotify.com",

        # Sites that rely on strict bot/authentication challenges
        "sourceforge.net",
    }
    
    def _compatibility_mode(self, host):
        host = (host or "").lower().rstrip(".")

        for domain in self.COMPATIBILITY_MODE_DOMAINS:
            if self._host_matches_domain(host, domain):
                return True

        return False
        
    def __init__(self, parent=None, profile=None, canvas_seed=None):
        view = parent

        if profile is not None:
            try:
                super().__init__(profile, view)
            except TypeError:
                super().__init__(view)
        else:
            super().__init__(view)
        self._canvas_seed = canvas_seed or (secrets.randbits(32) & 0xFFFFFFFF)
        self._parent_view = view

        # WebAuthn / passkey UX (Qt WebEngine 6.11+). Keep authentication
        # separate from Darkelf canvas trust and network-filter policy.
        self._webauth_request = None
        self._webauth_touch_box = None
        # Retain a non-bound callable for QWebEngineWebAuthUxRequest.stateChanged.
        # This avoids Nuitka/PySide's compiled bound-method connect workaround,
        # which can recurse during an active WebAuthn transaction.
        self._webauth_state_callback = (
            lambda state: self._on_webauth_state_changed(state)
        )
        if hasattr(self, "webAuthUxRequested"):
            self.webAuthUxRequested.connect(self._handle_webauth_request)

        # Temporary WebAuthn capability diagnostics. Prints what Chromium/Qt
        # exposes to each successfully loaded page; does not alter capabilities.
        self.loadFinished.connect(
            lambda ok: self.debug_webauthn_capabilities() if ok else None
        )

        # Session-only native canvas permissions. These are intentionally not
        # persisted to disk: closing Darkelf resets user-granted access.
        self._canvas_session_trusted = set()
        self._canvas_prompted_hosts = set()
        prof = self.profile()
        self.interceptor = getattr(prof, "_darkelf_interceptor", None)
        
        settings = self.settings()

        # Canvas privacy
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ReadingFromCanvasEnabled,
            False
        )

        # Disable hyperlink ping tracking
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled,
            False
        )

        # Block insecure active content on HTTPS pages
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent,
            False
        )

        # Harden local/file origins
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            False
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            False
        )

        # Prevent website screen capture
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScreenCaptureEnabled,
            False
        )

        # Restrict WebRTC to public interfaces
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly,
            True
        )
        
        self.inject_darkelf_letterboxing()
        self.hw_concurrency_spoof = secrets.choice([2, 4, 6, 8])
        self.inject_all_scripts()

    def debug_webauthn_capabilities(self):
        url = self.url().toString()
        print(f"[Darkelf WebAuthn DIAG] starting for {url}")
        js = r"""(() => JSON.stringify({href:location.href,secureContext:window.isSecureContext,publicKeyCredential:typeof PublicKeyCredential!=="undefined",credentialsAPI:!!(navigator.credentials&&typeof navigator.credentials.get==="function"),hasPlatformMethod:typeof PublicKeyCredential!=="undefined"&&typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable==="function",hasConditionalMethod:typeof PublicKeyCredential!=="undefined"&&typeof PublicKeyCredential.isConditionalMediationAvailable==="function"}))();"""
        self.runJavaScript(js, lambda result: print(f"[Darkelf WebAuthn IMMEDIATE] {result!r}"))
        async_js = r"""(() => { window.__darkelfWebAuthnAsync='PENDING'; (async()=>{const r={href:location.href,platformAuthenticator:'UNSUPPORTED',conditionalMediation:'UNSUPPORTED'}; try{if(typeof PublicKeyCredential!=="undefined"&&typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable==="function")r.platformAuthenticator=await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();}catch(e){r.platformAuthenticator='ERROR: '+String(e);} try{if(typeof PublicKeyCredential!=="undefined"&&typeof PublicKeyCredential.isConditionalMediationAvailable==="function")r.conditionalMediation=await PublicKeyCredential.isConditionalMediationAvailable();}catch(e){r.conditionalMediation='ERROR: '+String(e);} window.__darkelfWebAuthnAsync=JSON.stringify(r);})(); return 'started'; })();"""
        self.runJavaScript(async_js, lambda result: print(f"[Darkelf WebAuthn ASYNC] {result!r}"))
        QTimer.singleShot(500, self._report_webauthn_async)
        QTimer.singleShot(1500, self._report_webauthn_async)

    def _report_webauthn_async(self):
        try:
            self.runJavaScript("window.__darkelfWebAuthnAsync || 'NO_RESULT'", lambda result: print(f"[Darkelf WebAuthn RESULT] {result!r}"))
        except RuntimeError as e:
            print(f"[Darkelf WebAuthn] diagnostic read failed: {e}")

    # ============================================================
    # WEBAUTHN / PASSKEY UX
    # ============================================================
    def _handle_webauth_request(self, request):
        """Attach Darkelf's UI to a Qt WebEngine WebAuthn request."""
        if request is None:
            return

        # Cancel any older unfinished request owned by this page.
        old = self._webauth_request
        if old is not None and old is not request:
            try:
                old.cancel()
            except RuntimeError:
                pass

        # Qt may emit webAuthUxRequested more than once for the same request.
        # Connect stateChanged only once per request.  Avoid Qt.UniqueConnection:
        # PySide/Nuitka's patched connect() can recurse for Python callables.
        if request is not self._webauth_request:
            self._webauth_request = request
            try:
                request.stateChanged.connect(self._webauth_state_callback)
            except RuntimeError as e:
                print(f"[Darkelf WebAuthn] stateChanged connect failed: {e}")
                self._finish_webauth_request(request)
                return

        self._update_webauth_ux(request)

    def _on_webauth_state_changed(self, _state):
        """Update the active WebAuthn request after a Qt state transition."""
        request = self._webauth_request
        if request is not None:
            self._update_webauth_ux(request)

    @staticmethod
    def _webauth_enum_name(value):
        """Return a stable enum name across PySide6 enum representations."""
        name = getattr(value, "name", None)
        if name:
            return str(name).split(".")[-1]
        return str(value).split(".")[-1]

    def _webauth_parent(self):
        return self._parent_view

    def _close_webauth_touch_box(self):
        box = self._webauth_touch_box
        self._webauth_touch_box = None
        if box is not None:
            try:
                box.close()
                box.deleteLater()
            except RuntimeError:
                pass

    def _finish_webauth_request(self, request):
        if request is self._webauth_request:
            self._webauth_request = None
        self._close_webauth_touch_box()

    def _update_webauth_ux(self, request):
        """Render the current Qt WebAuthn state without changing privacy policy."""
        if request is None or request is not self._webauth_request:
            return

        try:
            state_name = self._webauth_enum_name(request.state())
            rp_id = request.relyingPartyId() or self.url().host() or "this site"
        except RuntimeError:
            self._finish_webauth_request(request)
            return

        # A state transition means any previous touch/security-key notice is stale.
        if state_name != "FinishTokenCollection":
            self._close_webauth_touch_box()

        if state_name == "NotStarted":
            return

        if state_name == "SelectAccount":
            try:
                accounts = list(request.userNames())
            except RuntimeError:
                accounts = []

            if not accounts:
                request.cancel()
                return

            account, ok = QInputDialog.getItem(
                self._webauth_parent(),
                "Darkelf Passkey",
                f"{rp_id} is requesting a passkey.\nChoose an account:",
                accounts,
                0,
                False,
            )
            if ok and account:
                request.setSelectedAccount(account)
            else:
                request.cancel()
            return

        if state_name == "CollectPin":
            try:
                pin_request = request.pinRequest()
                min_len = int(pin_request.minPinLength())
                attempts = int(pin_request.remainingAttempts())
                reason_name = self._webauth_enum_name(pin_request.reason())
                error_name = self._webauth_enum_name(pin_request.error())
            except (AttributeError, RuntimeError, TypeError, ValueError):
                min_len = 0
                attempts = -1
                reason_name = "Challenge"
                error_name = "NoError"

            if reason_name == "Set":
                prompt = "Set a PIN for your security key."
            elif reason_name == "Change":
                prompt = "Enter a new PIN for your security key."
            else:
                prompt = "Enter the PIN for your security key."

            details = []
            if min_len > 0:
                details.append(f"Minimum length: {min_len}")
            if attempts >= 0 and reason_name == "Challenge":
                details.append(f"Attempts remaining: {attempts}")
            if error_name != "NoError":
                details.append(f"Authenticator response: {error_name}")
            if details:
                prompt += "\n\n" + "\n".join(details)

            pin, ok = QInputDialog.getText(
                self._webauth_parent(),
                "Darkelf Passkey — Security Key PIN",
                prompt,
                QLineEdit.EchoMode.Password,
            )
            if ok:
                request.setPin(pin)
            else:
                request.cancel()
            return

        if state_name == "FinishTokenCollection":
            # This state can remain active while the user touches/inserts a FIDO
            # authenticator. Use a modeless box so stateChanged can close it.
            if self._webauth_touch_box is None:
                box = QMessageBox(self._webauth_parent())
                box.setIcon(QMessageBox.Icon.Information)
                box.setWindowTitle("Darkelf Passkey")
                box.setText(f"Complete passkey authentication for {rp_id}.")
                box.setInformativeText(
                    "Use Touch ID, your passkey device, or touch/insert your "
                    "security key when prompted."
                )
                cancel_button = box.addButton(
                    "Cancel",
                    QMessageBox.ButtonRole.RejectRole,
                )
                box.buttonClicked.connect(
                    lambda button, req=request, cancel=cancel_button:
                    req.cancel() if button is cancel else None
                )
                self._webauth_touch_box = box
                box.open()
            return

        if state_name == "RequestFailed":
            try:
                reason = self._webauth_enum_name(request.requestFailureReason())
            except RuntimeError:
                reason = "Unknown"

            box = QMessageBox(self._webauth_parent())
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("Passkey authentication failed")
            box.setText(f"{rp_id} could not complete passkey authentication.")
            box.setInformativeText(f"Reason: {reason}")
            retry_button = box.addButton("Retry", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            box.exec()

            if box.clickedButton() is retry_button:
                request.retry()
            else:
                request.cancel()
            return

        if state_name in ("Cancelled", "Completed"):
            self._finish_webauth_request(request)

    def inject_script(self, script_source, injection_point=None, subframes=True, name=None):
        scripts = self.scripts()
        # Remove old with same name if requested
        if name:
            for s in list(scripts.toList()):
                try:
                    if s.name() == name:
                        scripts.remove(s)
                except Exception as e:
                    print(e)
                    pass
        script_obj = QWebEngineScript()
        if name:
            script_obj.setName(name)
        # Authentication-sensitive first-party sites need Chromium's native
        # browser surface.  Do not inject Darkelf fingerprint modifications
        # into those documents or into their challenge/authentication frames.
        compat_domains = sorted(self.COMPATIBILITY_MODE_DOMAINS)
        compat_json = json.dumps(compat_domains)
        guarded_source = f"""
        (() => {{
            const __darkelfCompatDomains = {compat_json};
            const __darkelfMatches = (host) => {{
                host = (host || '').toLowerCase().replace(/\.$/, '');
                return __darkelfCompatDomains.some(
                    d => host === d || host.endsWith('.' + d)
                );
            }};

            let __darkelfCompat = __darkelfMatches(location.hostname);

            // Challenge/auth frames are commonly cross-origin.  Their referrer
            // still identifies the compatibility-mode first party.
            if (!__darkelfCompat && document.referrer) {{
                try {{
                    __darkelfCompat = __darkelfMatches(
                        new URL(document.referrer).hostname
                    );
                }} catch (e) {{}}
            }}

            if (__darkelfCompat) {{
                console.debug('[DarkelfAI] Compatibility mode: native browser APIs');
                return;
            }}

            {script_source}
        }})();
        """
        script_obj.setSourceCode(guarded_source)
        script_obj.setInjectionPoint(injection_point or QWebEngineScript.DocumentCreation)
        script_obj.setRunsOnSubFrames(subframes)
        script_obj.setWorldId(QWebEngineScript.MainWorld)
        scripts.insert(script_obj)
        
    def inject_darkelf_letterboxing(self):
        script = """
        (() => {
            if (window.__darkelf_letterboxing_applied) return;

            try {
                Object.defineProperty(window, "__darkelf_letterboxing_applied", {
                    value: true,
                    configurable: false,
                    enumerable: false
                });
            } catch (e) {}

            /*
            * Darkelf screen normalization.
            *
            * Keep the reported physical screen stable while allowing Chromium
            * to report the REAL viewport dimensions through innerWidth /
            * innerHeight.
            *
            * This prevents contradictions such as:
            *
            * screen.width  = 1280
            * innerWidth    = 1280
            *
            * while Chromium's actual viewport is 1440px wide.
            */

            const SCREEN_WIDTH  = 1440;
            const SCREEN_HEIGHT = 900;

            const applyPatch = (win) => {
                try {
                    if (!win || !win.screen) return;

                    const safeDefine = (obj, key, getter) => {
                        try {
                            Object.defineProperty(obj, key, {
                                get: getter,
                                configurable: true,
                                enumerable: true
                            });
                        } catch (e) {}
                    };

                    /*
                    * ---------------------------------------------------------
                    * Screen
                    * ---------------------------------------------------------
                    */

                    safeDefine(
                        win.screen,
                        "width",
                        () => SCREEN_WIDTH
                    );

                    safeDefine(
                        win.screen,
                        "height",
                        () => SCREEN_HEIGHT
                    );

                    safeDefine(
                        win.screen,
                        "availWidth",
                        () => SCREEN_WIDTH
                    );

                    safeDefine(
                        win.screen,
                        "availHeight",
                        () => SCREEN_HEIGHT
                    );

                    /*
                    * ---------------------------------------------------------
                    * IMPORTANT:
                    *
                    * Do NOT override:
                    *
                    *     innerWidth
                    *     innerHeight
                    *
                    * Chromium should expose the real viewport.
                    * ---------------------------------------------------------
                    */


                    /*
                    * outerWidth / outerHeight
                    *
                    * Keep them bounded by the normalized screen rather than
                    * reporting a window larger than the screen.
                    */

                    safeDefine(
                        win,
                        "outerWidth",
                        () => SCREEN_WIDTH
                    );

                    safeDefine(
                        win,
                        "outerHeight",
                        () => SCREEN_HEIGHT
                    );

                } catch (e) {}
            };


            // Main browsing context
            applyPatch(window);


            /*
            * QWebEngineScript already runs with subframes=True. Each iframe
            * document therefore receives screen normalization directly.
            * Avoid a permanent DOM-wide MutationObserver on busy pages.
            */

            console.log(
                "[DarkelfAI] Screen normalization applied: " +
                SCREEN_WIDTH + "x" + SCREEN_HEIGHT
            );

        })();
        """

        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True
        )

    # --- Inject WebRTC block, geo override, and canvas noise all at DocumentCreation ---
    def stealth_webrtc_block(self):
        script = """
        (() => {
            const block = (target, key) => {
                try {
                    Object.defineProperty(target, key, {
                        get: () => undefined,
                        set: () => {},
                        configurable: false
                    });
                    delete target[key];
                } catch (e) {
                    // Silently ignore expected errors (e.g. non-configurable)
                }
            };

            const targets = [
                [window, 'RTCPeerConnection'],
                [window, 'webkitRTCPeerConnection'],
                [window, 'mozRTCPeerConnection'],
                [window, 'RTCDataChannel'],
                [navigator, 'mozRTCPeerConnection'],
                [navigator, 'mediaDevices']
            ];

            targets.forEach(([obj, key]) => block(obj, key));

            // subframes=True applies the same WebRTC protection inside iframe
            // documents directly, so no permanent DOM observer is needed.

            console.log('[DarkelfAI] WebRTC APIs neutralized.');
        })();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)
        
    def block_webrtc_sdp_logging(self):
        script = """
        (function() {
            if (!window.RTCPeerConnection) return;
            const OriginalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {
                const pc = new OriginalRTCPeerConnection(...args);
                const wrap = (method) => {
                    if (pc[method]) {
                        const original = pc[method].bind(pc);
                        pc[method] = async function(...mArgs) {
                            const result = await original(...mArgs);
                            if (result && result.sdp) {
                                result.sdp = result.sdp.replace(/(\\d{1,3}\\.){3}\\d{1,3}/g, "0.0.0.0");
                                result.sdp = result.sdp.replace(/ice-ufrag:.+\\r\\n/g, '');
                                result.sdp = result.sdp.replace(/ice-pwd:.+\\r\\n/g, '');
                            }
                            return result;
                        };
                    }
                };
                wrap("createOffer");
                wrap("createAnswer");
                return pc;
            };
        })();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)
        
    def inject_geolocation_override(self):
        script = """
        (function() {
            // Completely remove navigator.geolocation
            Object.defineProperty(navigator, "geolocation", {
                get: function () {
                    return undefined;
                },
                configurable: true
            });

            // Fake permissions API to return denied
            if (navigator.permissions && navigator.permissions.query) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {
                    if (parameters.name === "geolocation") {
                        return Promise.resolve({ state: "denied" });
                    }
                    return originalQuery(parameters);
                };
            }
        })();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)

    def inject_human_verification_detector(self):
        """
        Detect embedded human-verification providers without maintaining a
        per-website allowlist. Detection only grants native canvas to the
        current first-party host for this Darkelf session.
        """
        script = r"""
        (() => {
            if (window.__darkelfChallengeDetectorInstalled) return;
            window.__darkelfChallengeDetectorInstalled = true;

            const challengeHosts = [
                "challenges.cloudflare.com",
                "hcaptcha.com",
                "recaptcha.net",
                "arkoselabs.com",
                "funcaptcha.com",
                "awswaf.com",
                "token.awswaf.com"
            ];

            function isChallengeURL(value) {
                try {
                    const u = new URL(value, location.href);
                    const h = (u.hostname || "").toLowerCase();
                    if (challengeHosts.some(d => h === d || h.endsWith("." + d))) {
                        return true;
                    }
                    if ((h === "google.com" || h.endsWith(".google.com") ||
                         h === "gstatic.com" || h.endsWith(".gstatic.com")) &&
                        u.pathname.toLowerCase().includes("/recaptcha/")) {
                        return true;
                    }
                    if (u.pathname.toLowerCase().includes("/cdn-cgi/challenge-platform/")) {
                        return true;
                    }
                } catch (e) {}
                return false;
            }

            let challengeObserver = null;
            let challengeTimer = null;

            function stopChallengeObserver() {
                try {
                    if (challengeObserver) {
                        challengeObserver.disconnect();
                        challengeObserver = null;
                    }
                } catch (e) {}
                try {
                    if (challengeTimer) {
                        clearTimeout(challengeTimer);
                        challengeTimer = null;
                    }
                } catch (e) {}
            }

            function report(value) {
                if (!isChallengeURL(value)) return;
                if (window.__darkelfChallengeReported) return;
                window.__darkelfChallengeReported = true;
                stopChallengeObserver();
                console.warn("[DarkelfAI] HUMAN_VERIFICATION_DETECTED");
            }

            // The main document itself can be a provider challenge URL.
            report(location.href);

            function scan(root) {
                try {
                    if (root && root.querySelectorAll) {
                        root.querySelectorAll("iframe[src],script[src]").forEach(
                            el => report(el.src || el.getAttribute("src") || "")
                        );
                    }
                } catch (e) {}
            }

            if (document.documentElement) scan(document);

            if (!window.__darkelfChallengeReported) {
                challengeObserver = new MutationObserver(mutations => {
                    for (const mutation of mutations) {
                        for (const node of mutation.addedNodes) {
                            if (!node || node.nodeType !== 1) continue;
                            if (node.tagName === "IFRAME" || node.tagName === "SCRIPT") {
                                report(node.src || node.getAttribute("src") || "");
                                if (window.__darkelfChallengeReported) return;
                            }
                            scan(node);
                            if (window.__darkelfChallengeReported) return;
                        }
                    }
                });
                challengeObserver.observe(document, {childList: true, subtree: true});

                // Challenge widgets normally appear during initial page setup.
                // Stop watching a busy SPA after 15 seconds.
                challengeTimer = setTimeout(stopChallengeObserver, 15000);
            }
        })();
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True,
            name="Darkelf Human Verification Detector"
        )

    def inject_canvas_protection(self):
        script = f"""
        (() => {{
            // Install once per JS world/document to prevent repeated attempts
            // to redefine non-configurable canvas methods.
            if (window.__darkelf_canvas_protection_installed) return;
            try {{
                Object.defineProperty(window, "__darkelf_canvas_protection_installed", {{
                    value: true, configurable: false, enumerable: false
                }});
            }} catch (e) {{
                if (window.__darkelf_canvas_protection_installed) return;
                window.__darkelf_canvas_protection_installed = true;
            }}

            // Trusted sites receive normal/native canvas behavior.
            const trustedDomains = {json.dumps(sorted(
                set(self.CANVAS_TRUSTED_DOMAINS) | set(self._canvas_session_trusted)
            ))};
            const currentHost = (location.hostname || "").toLowerCase().replace(/\.$/, "");
            const isTrusted = trustedDomains.some(
                d => currentHost === d || currentHost.endsWith("." + d)
            );
            if (isTrusted) {{
                console.log("[DarkelfAI] Canvas JS protection bypassed for TRUSTED site: " + currentHost);
                return;
            }}

            // Per-tab random seed, provided by Python
            const tabSeed = {self._canvas_seed};

            // Per-domain hash
            function hashString(str) {{
                let h = 2166136261;
                for (let i = 0; i < str.length; i++) {{
                    h ^= str.charCodeAt(i);
                    h = Math.imul(h, 16777619);
                }}
                return h >>> 0;
            }}
            const domainHash = hashString(location.hostname);

            // FINAL seed is combination of tabSeed and domainHash
            const seed = tabSeed ^ domainHash;

            function pixelNoise(seed, index) {{
                let x = seed ^ index;
                x = Math.imul(x ^ (x >>> 15), 0x85ebca6b);
                x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
                x = x ^ (x >>> 16);
                return (x & 0xff);
            }}

            function applyNoise(imageData) {{
                const data = imageData.data;
                for (let i = 0; i < data.length; i++) {{
                    const n = (pixelNoise(seed, i) % 12) - 4;
                    data[i] = Math.min(255, Math.max(0, data[i] + n));
                }}
            }}

            function cloneImageData(ctx, src) {{
                const copy = ctx.createImageData(src.width, src.height);
                copy.data.set(src.data);
                return copy;
            }}

            function reportReadback(method) {{
                try {{
                    const key = "__darkelf_canvas_reported_" + method;
                    if (!window[key]) {{
                        window[key] = true;
                        console.warn("[DarkelfAI] CANVAS_READBACK_ATTEMPT:" + method + ":" + currentHost);
                    }}
                }} catch (e) {{}}
            }}

            function safePatch(proto, method, wrapper) {{
                try {{
                    if (!proto || typeof proto[method] !== "function") return false;
                    const marker = "__darkelf_canvas_" + method + "_patched";
                    if (proto[marker]) return true;

                    const desc = Object.getOwnPropertyDescriptor(proto, method);
                    if (desc && desc.configurable === false) return false;

                    const original = proto[method];
                    Object.defineProperty(proto, method, {{
                        value: wrapper(original),
                        configurable: false,
                        writable: false
                    }});
                    try {{
                        Object.defineProperty(proto, marker, {{
                            value: true, configurable: false, enumerable: false
                        }});
                    }} catch (e) {{}}
                    return true;
                }} catch (e) {{
                    return false;
                }}
            }}

            // ---- Patch toDataURL ----
            safePatch(HTMLCanvasElement.prototype, 'toDataURL', function(original) {{
                return function() {{
                    reportReadback('toDataURL');
                    try {{
                        const ctx = this.getContext('2d');
                        if (!ctx) return original.apply(this, arguments);

                        const w = this.width;
                        const h = this.height;
                        if (!w || !h) return original.apply(this, arguments);

                        const originalData = ctx.getImageData(0, 0, w, h);
                        const modifiedData = cloneImageData(ctx, originalData);
        
                        applyNoise(modifiedData);
                        ctx.putImageData(modifiedData, 0, 0);

                        const result = original.apply(this, arguments);

                        ctx.putImageData(originalData, 0, 0);

                        return result;
                    }} catch (e) {{
                        return original.apply(this, arguments);
                    }}
                }};
            }});

            // ---- Patch toBlob ----
            safePatch(HTMLCanvasElement.prototype, 'toBlob', function(original) {{
                return function(callback, type, quality) {{
                    reportReadback('toBlob');
                    try {{
                        const ctx = this.getContext('2d');
                        if (!ctx) return original.apply(this, arguments);

                        const w = this.width;
                        const h = this.height;
                        if (!w || !h) return original.apply(this, arguments);

                        const originalData = ctx.getImageData(0, 0, w, h);
                        const modifiedData = cloneImageData(ctx, originalData);
    
                        applyNoise(modifiedData);
                        ctx.putImageData(modifiedData, 0, 0);

                        original.call(this, function(blob) {{
                            ctx.putImageData(originalData, 0, 0);
                            callback(blob);
                        }}, type, quality);

                    }} catch (e) {{
                        return original.apply(this, arguments);
                    }}
                }};
            }});

            // ---- Patch getImageData (non-mutating/read) ----
            safePatch(CanvasRenderingContext2D.prototype, 'getImageData', function(original) {{
                return function(x, y, w, h) {{
                    reportReadback('getImageData');
                    const imageData = original.call(this, x, y, w, h);
                    applyNoise(imageData);
                    return imageData;
                }};
            }});

        }})();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)
        
    def inject_fingerprint_hardware_protection(self):
        script = """
        (() => {
          // Always spoof deviceMemory as missing/undefined (shows N/A)
          try {
            Object.defineProperty(navigator, "deviceMemory", {
              get: () => undefined,
              configurable: true
            });
          } catch(e){}
          // Optional: continue randomizing hardwareConcurrency as before
          try {
            const cpuRand = Math.floor(Math.random() * 11) + 2;
            Object.defineProperty(navigator, "hardwareConcurrency", {
              get: () => cpuRand,
              configurable: true
            });
          } catch(e){}
        })();
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True)
                        
    def inject_webgl_fingerprint_per_domain(self):
        script = """
        (() => {
            function stringHash(s) {
                let h = 2166136261;
                for (let i = 0; i < s.length; i++) {
                    h ^= s.charCodeAt(i);
                    h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
                }
                return h >>> 0;
            }

            const SEED = stringHash(location.hostname);

            function seededRand(seed) {
                let a = seed + 0x6D2B79F5;
                a = Math.imul(a ^ a >>> 15, a | 1);
                a ^= a + Math.imul(a ^ a >>> 7, a | 61);
                return ((a ^ a >>> 14) >>> 0) / 4294967296;
            }

            // 🔥 REALISTIC GPU PROFILES
            const PLATFORM = navigator.platform.toLowerCase();

            const PROFILES = {
                mac: [
                    {
                        vendor: "Google Inc. (Apple)",
                        renderer: "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"
                    },
                    {
                        vendor: "Google Inc. (Apple)",
                        renderer: "ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)"
                    }
                ],
                win: [
                    {
                        vendor: "Google Inc. (Intel)",
                        renderer: "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"
                    },
                    {
                        vendor: "Google Inc. (NVIDIA)",
                        renderer: "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"
                    }
                ],
                linux: [
                    {
                        vendor: "Google Inc. (X.Org)",
                        renderer: "ANGLE (AMD, AMD Radeon RX 580 (POLARIS10), OpenGL 4.6)"
                    },
                    {
                        vendor: "Google Inc. (Mesa)",
                        renderer: "ANGLE (Intel, Mesa Intel(R) UHD Graphics 620 (KBL GT2), OpenGL 4.6)"
                    }
                ]
            };

            function pickProfile() {
                let list;

                if (PLATFORM.includes("mac")) list = PROFILES.mac;
                else if (PLATFORM.includes("win")) list = PROFILES.win;
                else list = PROFILES.linux;

                // deterministic per-domain but still realistic
                return list[SEED % list.length];
            }

            const PROFILE = pickProfile();

            function patchWebGL(ctxName) {
                let proto = window[ctxName] && window[ctxName].prototype;
                if (!proto) return;

                let _getParameter = proto.getParameter;

                proto.getParameter = function(param) {
                    switch (param) {
                        case 37445: return PROFILE.vendor;   // UNMASKED_VENDOR_WEBGL
                        case 37446: return PROFILE.renderer; // UNMASKED_RENDERER_WEBGL
                        case 7936:  return PROFILE.vendor;   // VENDOR
                        case 7937:  return PROFILE.renderer; // RENDERER
                        case 35724: return "WebGL GLSL ES 3.00 (OpenGL ES GLSL ES 3.0 Chromium)";
                        case 7938:  return "WebGL 2.0 (OpenGL ES 3.0 Chromium)";
                    }

                    return _getParameter.apply(this, arguments);
                };
            }

            patchWebGL('WebGLRenderingContext');
            patchWebGL('WebGL2RenderingContext');
        })();
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True)
            
    def inject_audio_randomized_defense(self):
        script = r"""
        (function() {

            function hashString(str) {
                let h = 2166136261 >>> 0;
                for (let i = 0; i < str.length; i++) {
                    h ^= str.charCodeAt(i);
                    h = Math.imul(h, 16777619);
                }
                return h >>> 0;
            }

            function mulberry32(a) {
                return function() {
                    var t = a += 0x6D2B79F5;
                    t = Math.imul(t ^ t >>> 15, t | 1);
                    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
                    return ((t ^ t >>> 14) >>> 0) / 4294967296;
                }
            }

            const domain = location.hostname;
            const seed = hashString(domain);
            const rand = mulberry32(seed);

            const amplitude = 1e-7; // very small noise

            function perturb(data) {
                for (let i = 0; i < data.length; i++) {
                    data[i] += (rand() - 0.5) * amplitude;
                }
                return data;
            }

            const origGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function() {
                const data = origGetChannelData.apply(this, arguments);
                return perturb(data);
            };

            if (AudioBuffer.prototype.copyFromChannel) {
                const origCopy = AudioBuffer.prototype.copyFromChannel;
                AudioBuffer.prototype.copyFromChannel = function(dest, channel, start) {
                    origCopy.apply(this, arguments);
                    perturb(dest);
                };
            }

        })();
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True)

    def inject_battery_defense(self):
        script = r"""
        if ("getBattery" in navigator) {
          navigator.getBattery = function() {
            return Promise.resolve({
              charging: true,
              chargingTime: 0,
              dischargingTime: Infinity,
              level: 1,
              addEventListener: function(){},
              removeEventListener: function(){},
              onchargingchange: null,
              onlevelchange: null
            });
          };
        }
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True)
            
    def inject_font_protection(self):
        script = r"""
        (function() {

            function hashString(str) {
                let h = 2166136261 >>> 0;

                for (let i = 0; i < str.length; i++) {
                    h ^= str.charCodeAt(i);
                    h = Math.imul(h, 16777619);
                }

                return h >>> 0;
            }

            function mulberry32(a) {
                return function() {
                    var t = a += 0x6D2B79F5;
                    t = Math.imul(t ^ t >>> 15, t | 1);
                    t ^= t + Math.imul(t ^ t >>> 7, t | 61);

                    return ((t ^ t >>> 14) >>> 0) / 4294967296;
                }
            }

            const seed = hashString(
                window.__darkelfSeed || location.hostname
            );

            const rand = mulberry32(seed);


            // --------------------------------------------------
            // 1. Fixed conservative font allowlist
            // --------------------------------------------------
            //
            // Keep the exposed font set small and stable.
            // Font availability is intentionally NOT randomized.

            const commonFonts = [
                "Arial",
                "Times New Roman",
                "Courier New",
                "Verdana",
                "Georgia"
            ];

            const fakeInstalled = new Set(
                commonFonts.map(font => font.toLowerCase())
            );


            // --------------------------------------------------
            // Patch document.fonts.check()
            // --------------------------------------------------

            if (document.fonts && document.fonts.check) {

                const origCheck = document.fonts.check;

                document.fonts.check = function(str) {

                    const match = str.match(
                        /^\d+px\s+["']?([^"']+)["']?/
                    );

                    if (match) {
                        const font = match[1].toLowerCase();
                        return fakeInstalled.has(font);
                    }

                    return origCheck.apply(this, arguments);
                };
            }


            // --------------------------------------------------
            // 2. Canvas text metric perturbation
            // --------------------------------------------------

            const amplitude = 0.01;

            const origMeasureText =
                CanvasRenderingContext2D.prototype.measureText;

            CanvasRenderingContext2D.prototype.measureText =
                function(text) {

                    const metrics =
                        origMeasureText.apply(this, arguments);

                    const noise =
                        (rand() - 0.5) * amplitude;

                    return new Proxy(metrics, {

                        get(target, prop) {

                            if (prop === "width") {
                                return target.width + noise;
                            }

                            return target[prop];
                        }

                    });
                };

        })();
        """

        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True
        )
                                    
    def inject_resize_observer_suppressor(self):
        suppressor_js = """
        try {
          new ResizeObserver(() => {}).observe(document.body);
        } catch (e) {}
        window.addEventListener("error", function(e) {
          if (e && e.message && e.message.indexOf('ResizeObserver loop limit exceeded') > -1)
            e.preventDefault();
        }, true);
        """
        self.inject_script(suppressor_js, name="__darkelf_resize_observer_patch__")
                    
    def inject_hw_concurrency_spoof(self):
        script = """
        (() => {

            const values = [2,4,6,8];

            const hashHost = (host) => {
                let h = 0;
                for (let i = 0; i < host.length; i++) {
                    h = ((h << 5) - h) + host.charCodeAt(i);
                    h |= 0;
                }
                return Math.abs(h);
            };

            const getValue = () => {
                try {
                    const host = location.hostname || "default";
                    const idx = hashHost(host) % values.length;
                    return values[idx];
                } catch(e) {
                    return values[Math.floor(Math.random()*values.length)];
                }
            };

            const patch = (nav) => {
                try {

                    Object.defineProperty(nav, "hardwareConcurrency", {
                        get() { return getValue(); },
                        configurable: false,
                        enumerable: true
                    });

                    Object.defineProperty(Navigator.prototype, "hardwareConcurrency", {
                        get() { return getValue(); },
                        configurable: false,
                        enumerable: true
                    });

                } catch(e) {}
            };

            const apply = (win) => {
                try {

                    if (!win || win.__darkelf_hw_patch)
                        return;

                    win.__darkelf_hw_patch = true;

                    patch(win.navigator);

                } catch(e) {}
            };

            apply(window);

            // subframes=True applies this patch inside iframe documents directly;
            // no permanent DOM MutationObserver is required.

            console.log("[DarkelfAI] hardwareConcurrency domain-randomized");

        })();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)

    def inject_iframe_environment_harmonizer(self):
        spoof = {
            "platform": detect_nav_platform(),
            "vendor": "Google Inc.",
            "userAgent": None,
            "deviceMemory": None,
            "languages": ["en-US", "en"],
            "language": "en-US",
            "maxTouchPoints": 0,
        }

        js = f"""
        (() => {{
          if (window.__darkelf_iframe_harmonizer) return;
          window.__darkelf_iframe_harmonizer = true;

          const SPOOF = {json.dumps(spoof)};
          try {{ SPOOF.userAgent = navigator.userAgent; }} catch(e) {{}}

          function def(obj, prop, getter) {{
            try {{
              Object.defineProperty(obj, prop, {{
                get: getter,
                configurable: true
              }});
            }} catch(e) {{}}
          }}

          function applyToWindow(w) {{
            if (!w || w.__darkelf_spoofed) return;

            try {{ w.__darkelf_spoofed = true; }} catch(e) {{}}

            try {{
              const nav = w.navigator;
              if (!nav) return;

              const proto = Object.getPrototypeOf(nav);

              def(proto,"platform",() => SPOOF.platform);
              def(proto,"vendor",() => SPOOF.vendor);
              def(proto,"userAgent",() => SPOOF.userAgent);
              def(proto,"deviceMemory",() => SPOOF.deviceMemory);
              def(proto,"languages",() => SPOOF.languages.slice());
              def(proto,"language",() => SPOOF.language);
              def(proto,"maxTouchPoints",() => SPOOF.maxTouchPoints);

            }} catch(e) {{}}
          }}

          applyToWindow(window);

        }})();
        """
        self.inject_script(js, injection_point=QWebEngineScript.DocumentCreation, subframes=True)
                
    def inject_stealth_chrome_environment(self):
        script = """
        (() => {

            // ---------- deterministic hash ----------
            const hashString = (str) => {
                let h = 0;
                for (let i = 0; i < str.length; i++) {
                    h = (h << 5) - h + str.charCodeAt(i);
                    h |= 0;
                }
                return Math.abs(h);
            };

            // ---------- seeded shuffle ----------
            const seededShuffle = (array, seed) => {
                let arr = array.slice();
                for (let i = arr.length - 1; i > 0; i--) {
                    seed = (seed * 9301 + 49297) % 233280;
                    const j = Math.floor((seed / 233280) * (i + 1));
                    [arr[i], arr[j]] = [arr[j], arr[i]];
                }
                return arr;
            };

            // ---------- PATCH: plugins ----------
            const patchPlugins = (nav, win) => {
                try {
                    if (!nav) return;

                    const host = (win.location && win.location.hostname) || "default";
                    const seed = hashString(host);

                    const basePlugins = [
                        { name: "Chrome PDF Plugin", filename: "internal-pdf-viewer" },
                        { name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai" },
                        { name: "Native Client", filename: "internal-nacl-plugin" }
                    ];

                    let plugins;

                    // 🔥 Modern Chrome behavior: sometimes empty
                    if (seed % 3 === 0) {
                        plugins = [];
                    } else {
                        plugins = seededShuffle(basePlugins, seed);

                        // Slight variation (2–3 plugins)
                        const cut = 2 + (seed % 2);
                        plugins = plugins.slice(0, cut);
                    }

                    // emulate PluginArray
                    plugins.length = plugins.length;
                    plugins.item = (i) => plugins[i];
                    plugins.namedItem = (name) =>
                        plugins.find(p => p.name === name);

                    Object.defineProperty(nav, 'plugins', {
                        get: () => plugins,
                        configurable: true
                    });

                    // keep mimeTypes consistent
                    Object.defineProperty(nav, 'mimeTypes', {
                        get: () => [],
                        configurable: true
                    });

                } catch (e) {}
            };

            const patchChromeRuntime = (win) => {
                try {
                    if (!win.chrome)
                        win.chrome = {};

                    if (!win.chrome.runtime) {
                        Object.defineProperty(win.chrome, 'runtime', {
                            get: () => ({}),
                            configurable: true
                        });
                    }
                } catch (e) {}
            };

            const patchPermissions = (nav) => {
                try {
                    if (nav.permissions && nav.permissions.query) {

                        const originalQuery = nav.permissions.query.bind(nav.permissions);

                        nav.permissions.query = function(parameters) {

                            if (parameters && parameters.name === 'notifications') {
                                return Promise.resolve({
                                    state: Notification.permission
                                });
                            }

                            return originalQuery(parameters);
                        };
                    }
                } catch (e) {}
            };

            const apply = (win) => {
                try {
                    if (!win || win.__darkelf_chrome_env)
                        return;

                    win.__darkelf_chrome_env = true;

                    patchPlugins(win.navigator, win); // ✅ updated
                    patchChromeRuntime(win);
                    patchPermissions(win.navigator);

                } catch (e) {}
            };

            // apply to main window
            apply(window);

            // subframes=True applies this environment inside iframe documents
            // directly, avoiding another permanent DOM observer.

            console.log('[DarkelfAI] Chrome environment randomized per domain');

        })();
        """
        self.inject_script(script, injection_point=QWebEngineScript.DocumentCreation, subframes=True)
        
    def inject_youtube_js_spoof(self):
        script = """
        (() => {
            try {
                const host = location.hostname || "";

                const isYouTube =
                    host.includes("youtube.com") ||
                    host.includes("youtu.be") ||
                    host.includes("ytimg.com") ||
                    host.includes("googlevideo.com");

                if (!isYouTube) return;

                const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)";

                Object.defineProperty(navigator, "userAgent", {
                    get: () => UA,
                    configurable: true
                });

                Object.defineProperty(navigator, "appVersion", {
                    get: () => UA,
                    configurable: true
                });

                Object.defineProperty(navigator, "platform", {
                    get: () => "MacIntel",
                    configurable: true
                });

                Object.defineProperty(navigator, "vendor", {
                    get: () => "Apple Computer, Inc.",
                    configurable: true
                });

            } catch(e) {}
        })();
        """

        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True
        )
        
    def inject_global_chrome_spoof(self):
        system = platform.system()

        if system == "Darwin":
            platform_part = "Macintosh; Intel Mac OS X 10_15_7"

        elif system == "Windows":
            platform_part = "Windows NT 10.0; Win64; x64"

        elif system == "Linux":
            platform_part = "X11; Linux x86_64"

        else:
            platform_part = "X11; Linux x86_64"

        chrome_ua = (
            f"Mozilla/5.0 ({platform_part}) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )

        # IMPORTANT:
        self.profile().setHttpUserAgent(chrome_ua)

        script = f"""
        (() => {{
            try {{
                const UA = "{chrome_ua}";

                Object.defineProperty(navigator, "userAgent", {{
                    get: () => UA,
                    configurable: true
                }});

                Object.defineProperty(navigator, "appVersion", {{
                    get: () => UA,
                    configurable: true
                }});

                Object.defineProperty(navigator, "vendor", {{
                    get: () => "Google Inc.",
                    configurable: true
                }});

                Object.defineProperty(navigator, "platform", {{
                    get: () => "{platform_part}",
                    configurable: true
                }});

            }} catch(e) {{}}
        }})();
        """

        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True
        )
        
    def inject_all_scripts(self):
        self.stealth_webrtc_block()
        self.block_webrtc_sdp_logging()
        self.inject_geolocation_override()
        self.inject_human_verification_detector()
        self.inject_canvas_protection()
        self.inject_fingerprint_hardware_protection()
        self.inject_audio_randomized_defense()
        self.inject_battery_defense()
        self.inject_webgl_fingerprint_per_domain()
        self.inject_font_protection()
        self.inject_resize_observer_suppressor()
        self.inject_hw_concurrency_spoof()
        self.inject_iframe_environment_harmonizer()
        self.inject_stealth_chrome_environment()
        self.inject_youtube_js_spoof()
        self.inject_global_chrome_spoof()
        
    def _canvas_mode(self, host, path=""):
        """Return blocked, protected, or trusted for this document."""
        host = (host or "").lower().rstrip(".")
        path = path or ""

        if not host:
            return "blocked"

        # A user may grant native/TRUSTED canvas access for the current
        # Darkelf session. Closing Darkelf clears this set.
        for domain in self._canvas_session_trusted:
            if self._host_matches_domain(host, domain):
                return "trusted"

        for domain in self.CANVAS_TRUSTED_DOMAINS:
            if self._host_matches_domain(host, domain):
                return "trusted"

        for domain in self.CANVAS_PROTECTED_DOMAINS:
            if self._host_matches_domain(host, domain):
                return "protected"

        for allowed_host, allowed_path in self.CANVAS_PROTECTED_URLS:
            if (
                self._host_matches_domain(host, allowed_host)
                and path.startswith(allowed_path)
            ):
                return "protected"

        return "blocked"

    def _apply_canvas_readback_policy(self, url):
        """Apply Darkelf's three-level canvas policy."""
        try:
            scheme = url.scheme().lower()

            if scheme == "data":
                self.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ReadingFromCanvasEnabled,
                    True
                )
                self._darkelf_canvas_mode = "protected"
                return

            if scheme not in ("http", "https"):
                self.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ReadingFromCanvasEnabled,
                    False
                )
                self._darkelf_canvas_mode = "blocked"
                print(
                    f"[DarkelfAI] Canvas mode=BLOCKED for "
                    f"internal {scheme or 'unknown'} document"
                )
                return

            host = url.host().lower().rstrip(".")
            path = url.path()
            mode = self._canvas_mode(host, path)

            # Preserve Darkelf's original randomized first-party-domain
            # canvas JavaScript exactly. Qt only enforces the hard BLOCKED tier:
            #   BLOCKED   -> native Qt readback disabled
            #   PROTECTED -> Qt readback enabled; original randomized JS applies
            #   TRUSTED   -> Qt readback enabled; original JS bypasses protection
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.ReadingFromCanvasEnabled,
                mode != "blocked"
            )
            self._darkelf_canvas_mode = mode

            print(
                f"[DarkelfAI] Canvas mode={mode.upper()} "
                f"for {host or '<no-host>'}{path}"
            )

        except Exception as e:
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.ReadingFromCanvasEnabled,
                False
            )
            self._darkelf_canvas_mode = "blocked"
            print(
                "[DarkelfAI] Canvas policy error; "
                f"defaulting to BLOCKED: {e}"
            )

    def _host_matches_domain(self, host, domain):
        host = (host or "").lower().rstrip(".")
        domain = (domain or "").lower().rstrip(".")
        return bool(host) and bool(domain) and (host == domain or host.endswith("." + domain))

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Handle Darkelf privacy and human-verification messages from page JS."""

        challenge_marker = "[DarkelfAI] HUMAN_VERIFICATION_DETECTED"
        if isinstance(message, str) and message.startswith(challenge_marker):
            try:
                current_url = self.url()
                host = current_url.host().lower().rstrip(".")

                if host and self._canvas_mode(host, current_url.path()) != "trusted":
                    # Temporary compatibility grant: native canvas only for the
                    # current first-party host and only until Darkelf closes.
                    self._canvas_session_trusted.add(host)
                    self.inject_canvas_protection()
                    self._apply_canvas_readback_policy(current_url)

                    print(
                        f"[DarkelfAI] Human verification detected; "
                        f"canvas session permission=TRUSTED for {host}"
                    )
                    # Never auto-reload here. Persistent challenge widgets can be
                    # rediscovered on every document and create reload loops.
                    return
            except Exception as e:
                print(f"[DarkelfAI] Human verification compatibility error: {e}")

        marker = "[DarkelfAI] CANVAS_READBACK_ATTEMPT:"

        if isinstance(message, str) and message.startswith(marker):
            try:
                parts = message[len(marker):].split(":", 1)
                method = parts[0] if parts else "canvas readback"

                current_url = self.url()
                host = current_url.host().lower().rstrip(".")

                # Ask only after an ACTUAL canvas readback attempt. Until the
                # user grants native access, Darkelf's JS wrappers protect the
                # returned canvas data rather than blanket-blocking canvas at Qt.
                if host and self._canvas_mode(host, current_url.path()) != "trusted":
                    if host not in self._canvas_prompted_hosts:
                        self._canvas_prompted_hosts.add(host)

                        box = QMessageBox(self._parent_view)
                        box.setIcon(QMessageBox.Icon.Information)
                        box.setWindowTitle("Canvas readback detected")
                        box.setText(f"{host} requested canvas readback ({method}).")
                        box.setInformativeText(
                            "Darkelf protected this readback attempt for privacy. "
                            "You can allow native canvas output for this site for "
                            "the current Darkelf session and reload the page. "
                            "The permission is cleared when Darkelf closes."
                        )
                        allow_button = box.addButton(
                            "Allow This Session + Reload",
                            QMessageBox.ButtonRole.AcceptRole
                        )
                        box.addButton(
                            "Keep Protected",
                            QMessageBox.ButtonRole.RejectRole
                        )
                        box.exec()

                        if box.clickedButton() is allow_button:
                            self._canvas_session_trusted.add(host)

                            # Rebuild only the named canvas protection script so
                            # the granted host receives native canvas behavior
                            # after reload. No permanent domain allowlist needed.
                            self.inject_canvas_protection()
                            self._apply_canvas_readback_policy(current_url)

                            print(
                                f"[DarkelfAI] Canvas session permission=TRUSTED "
                                f"for {host}"
                            )
                            self.triggerAction(QWebEnginePage.WebAction.Reload)
                            return
            except Exception as e:
                print(f"[DarkelfAI] Canvas prompt error: {e}")

        # Do not forward ordinary website console noise to Terminal.
        # Darkelf's own markers are handled above; page JS errors/warnings stay silent.
        return

    def acceptNavigationRequest(self, url, navtype, isMainFrame):

        if isMainFrame:
            self._apply_canvas_readback_policy(url)

        if url.scheme() == "file":
            QMessageBox.warning(
                None,
                "Navigation blocked",
                "File URLs are blocked for privacy."
            )
            return False

        return super().acceptNavigationRequest(
            url,
            navtype,
            isMainFrame
        )
        
    def createWindow(self, _type):
        """
        Reuse the current tab for navigation that requests a new
        window/tab, including target="_blank" and window.open().
        """
        parent_view = getattr(self, "_parent_view", None)

        if parent_view is not None:
            return self

        return super().createWindow(_type)
        
