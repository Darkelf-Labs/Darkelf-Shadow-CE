# 🕶️ Darkelf Shadow — Community Edition 7.0.10 Stable

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Fully Hardened • Ephemeral • Zero-Trace Browser (Qt WebEngine / Chromium Core)**

Darkelf Shadow is a defense-in-depth, privacy-hardened web browser engineered to minimize persistent tracking, reduce attack surface, and actively defend against modern web threats — while maintaining an ephemeral browsing environment.

**Version 7.0.10 Stable** focuses on browser responsiveness, website compatibility, secondary-navigation handling, and filtering efficiency while retaining the custom Darkelf Qt WebEngine 6.11.2 macOS ARM64 build, Touch ID/passkey support, H.264/AVC media compatibility, and the privacy, filtering, canvas, and MiniAI architecture from 7.0.9.

---

## 📦 Installation

### Python / PyPI

If you already have Python 3.11 or newer:

```bash
pip install darkelf-shadow
darkelf-shadow
```

### macOS

Darkelf Shadow Community Edition is also distributed as a signed and notarized macOS application.

The macOS release includes a SHA-256 checksum for independent download verification.

---

# ✨ What's New in 7.0.10

### ⚡ Compatibility-Mode Performance Improvements

Darkelf Shadow 7.0.10 improves responsiveness on websites that require Darkelf's compatibility mode.

Compatibility-mode websites now bypass unnecessary EasyList cosmetic stylesheet injection. This prevents very large collections of cosmetic selectors from imposing unnecessary CSS parsing, selector-matching, and rendering overhead on websites where Darkelf has already deliberately prioritized compatibility.

This provides:

- Faster rendering on compatibility-mode websites
- Reduced cosmetic-filter CSS processing
- Reduced selector-matching overhead
- Improved page responsiveness
- Reduced risk of sluggish or temporarily unresponsive pages
- Preservation of Darkelf's network-level filtering architecture
- Scoped compatibility behavior rather than globally weakening protection

Network-level request filtering remains separate from this optimization and continues to protect normal browsing traffic.

### 🪟 Improved Secondary Navigation & Popup Handling

Darkelf Shadow 7.0.10 improves handling of website-created secondary windows and navigation.

- User-clicked `target="_blank"` links can remain in the current Shadow tab.
- Script-generated popup and popunder navigation is blocked.
- Reduced unwanted blank or Home tabs caused by secondary-window requests.
- Legitimate user navigation is distinguished from script-created secondary navigation.
- Popup handling no longer requires site-specific exceptions for supported cases.

This improves compatibility with websites that use secondary navigation while retaining protection against unwanted advertising popups and popunders.

### 🔑 WebAuthn Diagnostic Cleanup

Temporary WebAuthn capability diagnostics used during development have been removed from normal page loads.

This reduces unnecessary JavaScript capability checks, delayed diagnostic callbacks, terminal output, and development overhead while leaving Darkelf's actual WebAuthn/passkey implementation intact.

Touch ID, passkeys, security keys, and the native Qt WebEngine WebAuthn integration remain part of the supported macOS architecture.

### 🍎 Custom Darkelf Qt WebEngine 6.11.2 for macOS ARM64

The native macOS ARM64 release bundles a custom Darkelf build of Qt WebEngine 6.11.2.

This platform-specific engine adds:

- Native macOS WebAuthn integration
- Touch ID/passkey authentication support
- Darkelf-specific WebAuthn configuration
- Expanded H.264/AVC media compatibility
- Dedicated QtWebEngineProcess and QtWebEngineCore signing
- Apple Hardened Runtime integration
- Developer ID signing, notarization, stapling, and Gatekeeper validation

Windows and Linux continue to use the standard PySide6 / Qt WebEngine platform distribution while retaining Shadow's off-the-record and privacy architecture.

### 🔑 Touch ID, Passkeys & WebAuthn

- Native Touch ID support for compatible WebAuthn/passkey authentication on the custom macOS build.
- Persistent platform configuration required by the macOS authenticator while keeping browser-session privacy controls scoped appropriately.
- WebAuthn secret material is generated locally with restricted file permissions.
- Integrated the macOS application with the required keychain access group and Developer ID provisioning.
- Passkey creation and subsequent passkey sign-in have been tested with a WebAuthn-enabled service.
- Bluetooth privacy declarations remain available for compatible Bluetooth-enabled security keys and devices.

### 🎬 Expanded macOS Media Compatibility

- Enabled Qt WebEngine proprietary-codec support in the custom macOS engine.
- Added H.264/AVC playback capability through the custom Qt WebEngine/Chromium media configuration.
- Improved compatibility with web video sources that depend on H.264.
- Codec support is independent of Darkelf's tracker blocking, fingerprint protections, and MiniAI security layers.
- H.264/AVC and third-party licensing information is documented in the packaged third-party notices.

### 🌐 Cross-Platform Distribution

Darkelf Shadow remains cross-platform through Python/PyPI.

- **macOS ARM64 native DMG:** custom Darkelf Qt WebEngine 6.11.2 with macOS-specific WebAuthn/Touch ID and expanded media support.
- **Windows / Linux:** standard platform PySide6 / Qt WebEngine with Shadow's off-the-record browsing and privacy architecture.
- **Python/PyPI:** installs the platform PySide6 / Qt WebEngine dependency rather than the custom Qt WebEngine framework bundled with the native macOS DMG.

The macOS-specific enhancements therefore do not change Shadow's core cross-platform filtering, MiniAI, fingerprint-protection, and ephemeral-browsing design.

### ⚡ Declarative Tracker Blocking

Darkelf Shadow's network engine combines its existing EasyList/uBlock-compatible filtering architecture with a fast declarative tracker layer.

Frequently encountered tracker and advertising infrastructure can be rejected through fast hostname matching before falling back to the larger filter-rule engine.

This provides:

- Faster request evaluation
- Reduced large-rule scanning
- Improved page responsiveness
- Lower filtering overhead
- Strong tracker blocking without sacrificing the existing filter engine
- Indexed fallback evaluation for complex rules

The traditional EasyList/uBlock-style engine remains available for rules requiring more complex evaluation.

### 🎭 Improved Canvas Protection

Darkelf Shadow retains its randomized canvas protection system with domain-sensitive noise generation.

Canvas access follows three protection states:

| Mode | Behavior |
|------|----------|
| 🔴 BLOCKED | Canvas readback is disabled |
| 🟡 PROTECTED | Readback receives Darkelf's randomized protection |
| 🟢 TRUSTED | Native readback is permitted for explicitly trusted compatibility cases |

This provides stronger protection while allowing sites that legitimately depend on canvas functionality to remain usable.

### 🧩 Improved Website Compatibility

7.0.10 continues compatibility handling for complex modern web applications, including:

- Authentication services
- Microsoft / Outlook web applications
- CAPTCHA and human-verification systems
- Media-heavy websites
- Dynamic JavaScript applications
- Embedded authentication flows
- Websites using secondary-window navigation
- Sites sensitive to large cosmetic-filter stylesheets

Compatibility exceptions remain deliberately scoped rather than globally disabling Darkelf's protections.

### 🤖 Human Verification Handling

Darkelf can detect supported human-verification and authentication workflows and temporarily permit the functionality necessary to complete them.

This reduces CAPTCHA loops while preserving normal privacy protections outside the verification flow.

### 🍎 macOS Improvements

- Updated application metadata for 7.0.10
- Custom Darkelf Qt WebEngine 6.11.2 framework on macOS ARM64
- Native Touch ID/passkey WebAuthn integration
- Expanded H.264/AVC media compatibility
- Improved compatibility-mode rendering performance
- Improved secondary-navigation and popup handling
- Improved browser URL/document registration
- High-resolution display support
- Automatic graphics-switching support
- Bluetooth privacy declaration for Bluetooth-enabled security keys and devices
- Developer ID signing
- Apple Hardened Runtime integration
- Apple notarization and stapling
- Gatekeeper validation
- SHA-256 release verification
- Embedded open-source and third-party licensing notices

Bluetooth access is not automatically granted. macOS remains responsible for requesting user permission if Bluetooth functionality is actually requested.

---

## 🧱 HARDENED BY DESIGN

Darkelf Shadow is architecturally hardened using multiple independent protection layers.

### 🔥 Zero Persistence Architecture

- No persistent browsing profile
- Memory-oriented browsing lifecycle
- Ephemeral cookies and browser state
- Automatic cleanup on process exit

### 🛡️ Network-Level Enforcement

- Deep request interception
- Pre-render request blocking
- Third-party classification
- Declarative tracker blocking
- Indexed EasyList/uBlock-style filtering
- Compatibility-aware request handling

### 🧠 Autonomous Threat Detection — MiniAI

- On-device behavioral analysis
- No cloud AI dependency
- Real-time adaptive defense
- Local threat scoring

### 🚫 Telemetry-Free Core

- No Darkelf analytics
- No Darkelf tracking
- No hidden Darkelf telemetry service

---

# 🚀 HARDENED FEATURE SET

## 🔐 Ephemeral Session Engine

Ephemeral handling of:

- Cookies
- Cache
- LocalStorage
- IndexedDB
- Session state

Designed to minimize recoverable browsing residue after termination.

---

## 🧠 MiniAI Sentinel

Darkelf Shadow includes an on-device security analysis and response layer.

### 🚨 Intrusion Detection

Detection logic covers patterns associated with:

- SQL injection
- Cross-site scripting (XSS)
- Command injection
- Path traversal

### 🦠 Detection Capabilities

- Suspicious request detection
- Tracker and surveillance detection
- Fingerprinting monitoring
- Behavioral anomaly detection
- Burst/flood analysis

---

## ⚡ Automated Response Modes

| Mode | Behavior |
|------|----------|
| 🟢 Standby | Passive monitoring |
| 🔴 Lockdown | Blocks suspicious traffic |
| 🚨 Panic Mode | Network shutdown |

---

## 🌐 Advanced Network Filtering

Darkelf Shadow combines multiple filtering techniques:

- ✔ EasyList
- ✔ EasyPrivacy
- ✔ uBlock-derived filter sources
- ✔ ABP-compatible rule processing
- ✔ Declarative tracker blocking
- ✔ Indexed rule evaluation
- ✔ Heuristic tracker detection
- ✔ Known tracker-domain blocking
- ✔ Third-party request classification
- ✔ Compatibility-aware exceptions
- ✔ Compatibility-aware cosmetic filtering

The fast declarative layer handles known tracker infrastructure while the larger rule engine remains available for complex matching.

Cosmetic filtering is applied separately from network filtering so that compatibility-mode sites can avoid unnecessary stylesheet overhead without disabling Darkelf's broader network protection architecture.

---

## 🔍 Anti-Tracking & URL Sanitization

Darkelf removes common tracking parameters such as:

- `utm_*`
- `fbclid`
- `gclid`
- Campaign and tracking identifiers

This helps reduce cross-site correlation through URL-based tracking.

---

## 🔐 HTTPS Enforcement Layer

- Automatic HTTP → HTTPS upgrade
- In-memory HTTPS/HSTS-style tracking
- Downgrade protection

---

# 🎭 Fingerprint Resistance Layer

Darkelf Shadow includes defenses against several browser-fingerprinting techniques.

### Canvas

- Domain-sensitive randomized noise
- Protected canvas readback
- Explicit trusted-site compatibility
- Readback blocking where appropriate

### Additional Protections

- WebGL protection
- AudioContext protection
- Font fingerprint mitigation
- WebRTC restrictions
- Geolocation restrictions

The objective is to reduce passive fingerprinting without claiming that any browser can guarantee anonymity or fingerprint uniqueness prevention.

---

## 📥 Secure Download Handling

- Controlled download directory
- Filename handling protections
- Optional ephemeral workflows
- Reduced persistence exposure

---

## ⚙️ Chromium / QtWebEngine Hardening

Darkelf disables or restricts unnecessary browser functionality, including:

- ❌ Browser synchronization services
- ❌ Metrics collection
- ❌ Crash-reporting telemetry
- ❌ First-run tracking behavior

Privacy-sensitive functionality is additionally controlled through Darkelf's QtWebEngine configuration and request-interception layers.

---

# 🧩 DEFENSE-IN-DEPTH MODEL

Darkelf Shadow combines:

1. Request Interception Layer
2. Declarative Tracker Blocking
3. EasyList/uBlock-Compatible Filter Engine
4. Third-Party Classification
5. MiniAI Behavioral Analysis
6. Fingerprint Protection
7. Ephemeral Storage Model
8. Compatibility and Authentication Handling

Each layer addresses a different portion of the browser's attack and tracking surface.

---

# 🧪 THREAT INTELLIGENCE CAPABILITIES

MiniAI provides:

- 📊 Threat scoring
- 📈 Real-time event monitoring
- 🧠 Domain risk caching
- 📋 Threat reporting
- 🔄 Adaptive escalation logic

All MiniAI analysis is performed locally.

---

# ⚡ PERFORMANCE

Version 7.0.10 preserves the optimized network-filtering architecture while reducing cosmetic-filter overhead on compatibility-mode sites and retaining the native macOS, WebAuthn/passkey, and media improvements from 7.0.9.

- ⚙️ PySide6 + Qt WebEngine
- 🚀 Chromium rendering core
- ⚡ Fast declarative hostname matching
- 🔎 Indexed filter-rule evaluation
- 🎨 Compatibility-aware cosmetic filtering
- 🧠 In-memory operation
- 💾 Reduced persistent disk activity
- 🚀 Fast startup and clean shutdown

The declarative layer allows many known tracker requests to be decided without unnecessarily traversing the complete filter-rule set.

Compatibility-mode sites can additionally bypass unnecessary large cosmetic-filter stylesheets, reducing CSS processing and rendering overhead while leaving Darkelf's network architecture intact.

---

# 🔒 SECURITY POSTURE SUMMARY

| Category | Status |
|----------|--------|
| Persistent Browser Profile | ❌ None |
| Darkelf Telemetry | ❌ None |
| Tracking Resistance | ✅ Active |
| Declarative Tracker Blocking | ✅ Active |
| EasyList/uBlock Filtering | ✅ Active |
| Fingerprint Defense | ✅ Active |
| Canvas Protection | ✅ BLOCKED / PROTECTED / TRUSTED |
| Threat Detection | ✅ Real-time |
| Network Control | ✅ Enforced |
| Session Model | ✅ Ephemeral |

---

# ⚠️ OPERATIONAL SECURITY NOTES

For stronger system-level protection, Darkelf Shadow can be combined with:

- 🔐 Full-disk encryption (FileVault / LUKS)
- 🔥 OS-level firewall rules
- 🧱 Sandboxed runtime environments
- 🌐 Trusted VPN or network isolation
- 🔑 Hardware security keys where appropriate

Darkelf Shadow is one component of a broader security model and does not guarantee anonymity.

---

# 🔒 Security & Verification

The macOS release includes a SHA-256 checksum.

### Verify on macOS

```bash
shasum -a 256 -c Darkelf-Shadow-7.0.10.dmg.sha256
```

A successful verification should report:

```text
Darkelf-Shadow-7.0.10.dmg: OK
```

The macOS application and DMG release workflow uses Developer ID signing, Apple notarization, and stapling for Gatekeeper verification.

---

# 📜 LICENSE

Licensed under **LGPL-3.0-or-later**

The native macOS application also includes Darkelf and third-party notices under:

`Darkelf Shadow.app/Contents/Resources/licenses/`

Qt, Qt WebEngine, Chromium, FFmpeg, and other bundled components remain subject to their respective licenses. H.264/AVC intellectual-property considerations are documented separately in the third-party notices.

---

# ⚠️ DISCLAIMER

This software is provided **“AS IS”** without warranty.

Darkelf Shadow:

- Does not guarantee anonymity
- Does not guarantee protection against every tracking technique
- Does not replace operating-system security
- Does not replace good operational-security practices
- Is intended for privacy-conscious and advanced users

---

# 👤 AUTHOR

**Dr. Kevin Moore (2025–2026)**
**Darkelf Project — Shadow Edition**

---

# 🤝 Special Thanks

Thank you to:

- **Mecha Comet Team**
- **Tim Burns**

for their support and contributions to the Darkelf project.

---

**Darkelf Shadow Community Edition 7.0.10 Stable**
*Ephemeral by design. Hardened in depth. Privacy without persistence.*
