# 🕶️ Darkelf Shadow — Community Edition 7.0.8 Stable

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Fully Hardened • Ephemeral • Zero-Trace Browser (Qt WebEngine / Chromium Core)**

Darkelf Shadow is a defense-in-depth, privacy-hardened web browser engineered to minimize persistent tracking, reduce attack surface, and actively defend against modern web threats — while maintaining an ephemeral browsing environment.

**Version 7.0.8 Stable** introduces major improvements to network-filtering performance, compatibility, canvas fingerprint protection, authentication handling, and macOS integration.

---

## 📦 Installation

### Python / PyPI

If you already have Python 3.10 or newer (up to 3.14):

```bash
pip install darkelf-shadow
darkelf-shadow
```

### macOS

Darkelf Shadow Community Edition is also distributed as a signed and notarized macOS application.

The macOS release includes a SHA-256 checksum for independent download verification.

---

# ✨ What's New in 7.0.8

### ⚡ Declarative Tracker Blocking

Darkelf Shadow's network engine now combines its existing EasyList/uBlock-compatible filtering architecture with a fast declarative tracker layer.

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

7.0.8 expands compatibility handling for complex modern web applications, including:

- Authentication services
- Microsoft / Outlook web applications
- CAPTCHA and human-verification systems
- Media-heavy websites
- Dynamic JavaScript applications
- Embedded authentication flows

Compatibility exceptions remain deliberately scoped rather than globally disabling Darkelf's protections.

### 🤖 Human Verification Handling

Darkelf can detect supported human-verification and authentication workflows and temporarily permit the functionality necessary to complete them.

This reduces CAPTCHA loops while preserving normal privacy protections outside the verification flow.

### 🍎 macOS Improvements

- Updated application metadata
- Improved browser URL/document registration
- High-resolution display support
- Automatic graphics-switching support
- Bluetooth privacy declaration for Bluetooth-enabled security keys and devices
- Developer ID signing
- Apple notarization workflow
- Gatekeeper validation
- SHA-256 release verification

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

The fast declarative layer handles known tracker infrastructure while the larger rule engine remains available for complex matching.

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

Version 7.0.8 substantially restructures network-rule evaluation for improved responsiveness.

- ⚙️ PySide6 + Qt WebEngine
- 🚀 Chromium rendering core
- ⚡ Fast declarative hostname matching
- 🔎 Indexed filter-rule evaluation
- 🧠 In-memory operation
- 💾 Reduced persistent disk activity
- 🚀 Fast startup and clean shutdown

The declarative layer allows many known tracker requests to be decided without unnecessarily traversing the complete filter-rule set.

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
shasum -a 256 -c Darkelf-Shadow-7.0.8.dmg.sha256
```

A successful verification should report:

```text
Darkelf-Shadow-7.0.8.dmg: OK
```

The macOS application and DMG release workflow uses Developer ID signing, Apple notarization, and stapling for Gatekeeper verification.

---

# 📜 LICENSE

Licensed under **LGPL-3.0-or-later**

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

**Darkelf Shadow Community Edition 7.0.8 Stable**  
*Ephemeral by design. Hardened in depth. Privacy without persistence.*
