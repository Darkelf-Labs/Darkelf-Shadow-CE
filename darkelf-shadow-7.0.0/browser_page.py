import json
import secrets
import platform

from shadow.browser_icons import detect_nav_platform


from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)

from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineScript,
)

from PySide6.QtWidgets import QMessageBox

class HardenedWebPage(QWebEnginePage):
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
        prof = self.profile()
        self.interceptor = getattr(prof, "_darkelf_interceptor", None)
        self.inject_darkelf_letterboxing()
        self.hw_concurrency_spoof = secrets.choice([2, 4, 6, 8])
        self.inject_all_scripts()


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
        script_obj.setSourceCode(script_source)
        script_obj.setInjectionPoint(injection_point or QWebEngineScript.DocumentCreation)
        script_obj.setRunsOnSubFrames(subframes)
        script_obj.setWorldId(QWebEngineScript.MainWorld)
        scripts.insert(script_obj)
        
    def inject_darkelf_letterboxing(self):
        script = """
        (() => {

            const detectPlatform = () => {
                try {
                    const p = navigator.platform.toLowerCase();
                    if (p.includes('mac')) return 'mac';
                    if (p.includes('win')) return 'windows';
                    if (p.includes('linux')) return 'linux';
                    return 'windows';
                } catch (e) {
                    return 'windows';
                }
            };

            const personas = [
                [1920,1080],
                [1536,864],
                [1440,900],
                [1366,768],
                [1280,720]
            ];

            const pickPersona = () => {
                try {
                    const p = personas[Math.floor(Math.random() * personas.length)];
                    return { width: p[0], height: p[1] };
                } catch(e) {
                    return { width: 1920, height: 1080 };
                }
            };

            const frameSizes = {
                windows: 140,
                mac: 80,
                linux: 120
            };

            const persona = pickPersona();

            const applyPatch = (win) => {
                try {

                    const platform = detectPlatform();
                    const frame = frameSizes[platform] || 140;

                    const width = persona.width;
                    const height = persona.height;

                    const safeDefine = (obj, key, getter) => {
                        try {
                            Object.defineProperty(obj, key, {
                                get: getter,
                                configurable: false
                            });
                        } catch(e) {}
                    };

                    safeDefine(win.screen, "width", () => width);
                    safeDefine(win.screen, "height", () => height);
                    safeDefine(win.screen, "availWidth", () => width);
                    safeDefine(win.screen, "availHeight", () => height);

                    safeDefine(win, "innerWidth", () => width);
                    safeDefine(win, "innerHeight", () => height);

                    safeDefine(win, "outerWidth", () => width);
                    safeDefine(win, "outerHeight", () => height + frame);

                } catch (e) {}
            };

            applyPatch(window);

            new MutationObserver((muts) => {
                for (const m of muts) {
                    m.addedNodes.forEach((node) => {
                        if (node.tagName === 'IFRAME') {
                            try {
                                const w = node.contentWindow;
                                applyPatch(w);
                            } catch (e) {}
                        }
                    });
                }
            }).observe(document, { childList: true, subtree: true });

            console.log('[DarkelfAI] Darkelf Letterboxing persona applied.');

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

            // Iframe defense
            new MutationObserver((muts) => {
                for (const m of muts) {
                    m.addedNodes.forEach((node) => {
                        if (node.tagName === 'IFRAME') {
                            try {
                                const w = node.contentWindow;
                                targets.forEach(([obj, key]) => block(w, key));
                                targets.forEach(([obj, key]) => block(w.navigator, key));
                            } catch (e) {}
                        }
                    });
                }
            }).observe(document, { childList: true, subtree: true });

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

    def inject_canvas_protection(self):
        script = f"""
        (() => {{
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

            function safePatch(proto, method, wrapper) {{
                const original = proto[method];
                Object.defineProperty(proto, method, {{
                    value: wrapper(original),
                    configurable: false,
                    writable: false
                }});
            }}

            // ---- Patch toDataURL ----
            safePatch(HTMLCanvasElement.prototype, 'toDataURL', function(original) {{
                return function() {{
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
                    const imageData = original.call(this, x, y, w, h);
                    applyNoise(imageData);
                    return imageData;
                }};
            }});

        }})();
        """
        self.inject_script(
            script,
            injection_point=QWebEngineScript.DocumentCreation,
            subframes=True)
                    
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

            const seed = hashString(window.__darkelfSeed || location.hostname);

            const rand = mulberry32(seed);

            // ----- 1️⃣ Fake installed font set -----

            const commonFonts = [
                "Arial","Verdana","Tahoma","Times New Roman",
                "Courier New","Georgia","Trebuchet MS",
                "Comic Sans MS","Impact","Calibri"
            ];

            const fakeInstalled = new Set();

            commonFonts.forEach(font => {
                if (rand() > 0.4) { // randomized allowlist
                    fakeInstalled.add(font.toLowerCase());
                }
            });

            // Patch document.fonts.check()
            if (document.fonts && document.fonts.check) {
                const origCheck = document.fonts.check;
                document.fonts.check = function(str) {
                    const match = str.match(/^\d+px\s+["']?([^"']+)["']?/);
                    if (match) {
                        const font = match[1].toLowerCase();
                        return fakeInstalled.has(font);
                    }
                    return origCheck.apply(this, arguments);
                };
            }

            // ----- 2️⃣ Canvas text metric perturbation -----

            const amplitude = 0.01;

            const origMeasureText = CanvasRenderingContext2D.prototype.measureText;
            CanvasRenderingContext2D.prototype.measureText = function(text) {
                const metrics = origMeasureText.apply(this, arguments);

                const noise = (rand() - 0.5) * amplitude;

                // Proxy metrics object
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
            subframes=True)
                                    
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

            new MutationObserver((muts) => {

                for (const m of muts) {

                    m.addedNodes.forEach((node) => {

                        if (!node.tagName)
                            return;

                        if (node.tagName.toLowerCase() === "iframe") {

                            try {
                                apply(node.contentWindow);
                            } catch(e) {}

                        }

                    });

                }

            }).observe(document,{childList:true,subtree:true});

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

            // observe iframes
            new MutationObserver((muts) => {
                for (const m of muts) {
                    m.addedNodes.forEach((node) => {
                        if (!node.tagName)
                            return;

                        if (node.tagName.toLowerCase() === "iframe") {
                            try {
                                const w = node.contentWindow;
                                apply(w);
                            } catch (e) {}
                        }
                    });
                }
            }).observe(document, { childList: true, subtree: true });

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

    def _host_matches_domain(self, host, domain):
        host = (host or "").lower().rstrip(".")
        domain = (domain or "").lower().rstrip(".")
        return bool(host) and bool(domain) and (host == domain or host.endswith("." + domain))

    def acceptNavigationRequest(self, url, navtype, isMainFrame):

        if url.scheme() == "file":
            QMessageBox.warning(
                None,
                "Navigation blocked",
                "File URLs are blocked for privacy."
            )
            return False

        current_host = self.url().host().lower()
        target_host = url.host().lower()
        target_path = url.path().lower()

        is_duckduckgo_page = self._host_matches_domain(current_host, "duckduckgo.com")

        is_clicked_link = (
            navtype == QWebEnginePage.NavigationTypeLinkClicked
            and isMainFrame
        )

        is_external_host = (
            target_host
            and not self._host_matches_domain(target_host, "duckduckgo.com")
        )

        is_ddg_result_redirect = (
            self._host_matches_domain(target_host, "duckduckgo.com")
            and (
                target_path.startswith("/l/")
                or "uddg=" in url.toString()
            )
        )

        if (
            is_clicked_link
            and is_duckduckgo_page
            and (
                is_external_host
                or is_ddg_result_redirect
            )
        ):
            parent = getattr(self, "_parent_view", None)
            browser = parent.window() if parent else None

            if browser and hasattr(browser, "_add_tab"):
                browser._add_tab(url=url.toString())
                return False

        return super().acceptNavigationRequest(
            url,
            navtype,
            isMainFrame
        )

    def createWindow(self, _type):
        parent_view = getattr(self, "_parent_view", None)
        main_window = parent_view.window() if parent_view else None

        if (
            main_window is not None
            and hasattr(main_window, "_add_tab")
            and hasattr(main_window, "tabs")
        ):
            main_window._add_tab(home=True)

            view = main_window.tabs.currentWidget()

            if view is not None:
                page = view.page()
                page._parent_view = view
                return page

        view = QWebEngineView(parent_view)

        try:
            page = HardenedWebPage(view, self.profile())
        except TypeError:
            page = HardenedWebPage(view)

        view.setPage(page)

        page._parent_view = view

        try:
            page.fullScreenRequested.connect(
                view.window().handle_fullscreen
            )
        except Exception as e:
            print("createWindow fullscreen:", e)

        view.resize(1000, 700)
        view.show()

        if not hasattr(self, "_spawned_views"):
            self._spawned_views = []

        self._spawned_views.append(view)

        return page
        
