# 🕶️ Darkelf Shadow CE

**Version 7.1.0 | macOS ARM64 | Qt 6.12 | Chromium Engine**

Darkelf Shadow CE is a privacy-focused desktop web browser for macOS, developed by **Darkelf Labs** and powered by PySide6 and a customized QtWebEngine/Chromium architecture.

Designed for users who value privacy, control, and native desktop functionality, Darkelf Shadow combines Chromium web compatibility with browser-level privacy defenses and macOS integration.

## ✨ Features

### 🛡️ Privacy & Tracking Protection

- Integrated content-blocking architecture.
- Browser fingerprinting resistance.
- Canvas and WebGL privacy protections.
- WebRTC restrictions designed to reduce network information exposure.
- Privacy-oriented Chromium runtime configuration.
- Controls intended to reduce unnecessary browser tracking.

### 🌐 Chromium-Based Web Engine

- Customized QtWebEngine 6.12 integration.
- Chromium-powered website rendering.
- JavaScript and modern web application support.
- Hardware-accelerated rendering where supported.
- Support for proprietary media codecs in the custom engine build.
- Native QtWebEngine resource and subprocess integration.

### 🍎 Native macOS Integration

- Native macOS application bundle.
- Apple Silicon ARM64 support.
- Developer ID application signing.
- Hardened Runtime configuration.
- Apple notarization and distribution packaging.
- Native window management and fullscreen integration.

### 🔐 Authentication & Web Compatibility

- WebAuthn integration.
- macOS Touch ID authenticator support through the customized QtWebEngine implementation.
- Support for compatible passkey authentication workflows.
- Modern HTTPS and browser authentication capabilities.

Authentication compatibility depends on the website, macOS configuration, and authenticator support.

## 🚀 What's New in 7.1.0

Darkelf Shadow 7.1.0 focuses on improvements to macOS runtime integration, browser subprocess isolation, release validation, and packaging reliability.

Highlights include:

- Refined QtWebEngine renderer process initialization.
- Updated Nuitka integration for macOS framework packaging.
- Improved runtime security configuration and validation.
- Continued support for the custom QtWebEngine 6.12 framework.
- Maintained WebAuthn and Touch ID integration.
- Improved release verification procedures.

## 📦 Installation

Download the latest release from the project's GitHub Releases page.

1. Download the Darkelf Shadow DMG.
2. Open the disk image.
3. Drag Darkelf Shadow into Applications.
4. Launch the application from Applications.

**Platform:** macOS on Apple Silicon (ARM64).

## 🔧 Architecture

Darkelf Shadow combines several components:

| Component | Technology |
|---|---|
| Application | Python / PySide6 |
| Browser engine | Customized QtWebEngine / Chromium |
| Desktop framework | Qt 6.12 |
| Compilation and packaging | Nuitka |
| Platform | macOS ARM64 |
| Distribution | Developer ID signed and Apple notarized |

The customized engine and application-level privacy defenses are maintained as part of the Darkelf Shadow development process.

## 🔒 Security

Darkelf Shadow uses multiple security and privacy mechanisms, including macOS Hardened Runtime, application signing, QtWebEngine's Chromium security architecture, and browser-level content protections.

No browser can guarantee complete anonymity, immunity from malicious websites, or protection from every vulnerability.

Users should keep Darkelf Shadow and macOS updated and exercise appropriate caution when browsing unfamiliar websites.

## 📄 Licensing & Third-Party Software

Darkelf Shadow includes or depends on third-party open-source components, including Qt, QtWebEngine, Chromium, PySide6, and supporting libraries.

Refer to the repository's licensing and third-party notice files for applicable terms and source information.

## 🔗 Project Links

- **GitHub Organization:** https://github.com/Darkelf-Labs
- **Darkelf Shadow CE:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE

---

**Developed by Darkelf Labs.**

*Privacy-focused browsing, powered by a customized Chromium architecture.*
