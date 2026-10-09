
# 🕶️ Darkelf Shadow CE v7.0.26

[![Weekly Downloads](https://img.shields.io/pypi/dw/darkelf-shadow?label=Weekly%20Downloads&color=brightgreen)](https://pypistats.org/packages/darkelf-shadow)

**A privacy-focused web browser for macOS, powered by a customized QtWebEngine and Chromium foundation.**

Darkelf Shadow CE is an independent, open-source browser developed by **Darkelf Labs**, focused on tracking protection, fingerprinting resistance, integrated ad blocking, and native macOS browsing.

## ✨ Features

### 🛡️ Privacy & Fingerprinting Protection

- Canvas readback protection and site-specific controls
- WebGL fingerprinting resistance
- WebRTC disabled to reduce potential IP exposure
- Geolocation restrictions
- Battery API fingerprinting protections
- Media-device enumeration protections
- Tracker and advertising-domain blocking
- Privacy-oriented browsing sessions

Privacy defenses may affect some websites and cannot guarantee anonymity.

### 🚫 Integrated Ad & Tracker Blocking

- Network request filtering
- Advertising and tracker blocking
- Cosmetic filtering
- Custom Darkelf filtering rules
- Site compatibility exceptions
- Optimized rule compilation and loading

No separate ad-blocking extension is required.

### ⚙️ Customized QtWebEngine

Darkelf Shadow uses a customized **QtWebEngine 6.11.2** framework with Chromium-based rendering, native macOS WebAuthn integration, H.264 codec support, WebRTC restrictions, and privacy modifications.

### 🔐 WebAuthn & Touch ID

- WebAuthn authentication on compatible websites
- Native macOS authentication dialogs
- Touch ID where supported
- macOS Keychain integration

**Compatibility:** GitHub Touch ID authentication has been tested during development. Passkey support may vary by website and macOS configuration. Apple's additional browser passkey entitlement is pending approval and is not included.

### 🍎 Native macOS Experience

- Apple Silicon (ARM64) support
- Native application menus and windows
- Keyboard shortcuts and fullscreen browsing
- Custom browser interface
- Developer ID signing and Apple notarization workflow

## 🆕 What's New in v7.0.26

- Continued WebAuthn and Touch ID integration work
- Updated Developer ID provisioning and signing checks
- Additional validation of application entitlements
- Custom QtWebEngine packaging and runtime refinements
- Continued privacy and site compatibility improvements
- Updated macOS distribution workflow

## 💻 System Requirements

| Component | Requirement |
|---|---|
| Operating system | macOS |
| Processor | Apple Silicon (ARM64) |
| Rendering engine | Custom QtWebEngine 6.11.2 |
| Application framework | Python 3.11 / PySide6 |
| Distribution | DMG |

## 📦 Installation

1. Visit the [official releases page](https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases).
2. Download `Darkelf-Shadow-7.0.26.dmg` **once the release is published**.
3. Open the DMG and drag **Darkelf Shadow.app** into **Applications**.
4. Launch Darkelf Shadow from Applications.

Only install releases distributed through the official Darkelf Labs repository.

## 🧪 Privacy Testing

- [EFF Cover Your Tracks](https://coveryourtracks.eff.org/)
- [CreepJS](https://abrahamjuliot.github.io/creepjs/)
- [BrowserLeaks](https://browserleaks.com/)
- [AmIUnique](https://amiunique.org/)
- [Speedometer 3](https://browserbench.org/Speedometer3.0/)

Results vary by hardware, operating system, configuration, and test methodology.

## 🏗️ Architecture

```text
Darkelf Shadow CE
├── Native macOS Application
│   ├── Python 3.11 / PySide6
│   └── macOS Integration
├── Custom QtWebEngine 6.11.2
│   ├── Chromium Rendering
│   ├── WebAuthn Integration
│   ├── H.264 Media Support
│   └── Privacy Modifications
├── Darkelf Privacy Engine
│   ├── Canvas / WebGL Protection
│   ├── WebRTC Restrictions
│   └── Device API Protections
├── Darkelf Filtering Engine
│   ├── Network / Cosmetic Filtering
│   └── Compatibility Rules
└── macOS Distribution
    ├── Nuitka Build
    ├── Developer ID Signing
    ├── Provisioning Profile
    └── Apple Notarization
```

## 🔍 Security & Privacy Philosophy

Darkelf Shadow emphasizes privacy by default, integrated protection, transparency, compatibility, and user control.

## ⚠️ Known Limitations

- Some sites may require compatibility exceptions.
- Strict fingerprinting protection can interfere with website features.
- WebRTC-dependent applications may not function.
- Widevine DRM is not bundled; protected streaming media may not play.
- Touch ID and WebAuthn support depend on the authentication provider.
- The macOS build targets Apple Silicon.

## 📥 Downloads & Source Code

- **Repository:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE
- **Releases:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases
- **Darkelf Labs:** https://github.com/Darkelf-Labs

## 📜 License & Third-Party Notices

Darkelf Shadow CE is distributed under the license included in its repository. Third-party technologies, including Qt, PySide6, QtWebEngine, and Chromium-related components, remain subject to their respective licenses. Consult `LICENSE` and `THIRD_PARTY_NOTICES.txt`.

## 🚀 Project Status

**Version: 7.0.26 — release build in progress.** Publish the DMG only after successful signature verification and Apple notarization.

**Developed by Darkelf Labs**

*Privacy. Security. Independence.*
