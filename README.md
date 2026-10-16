# Darkelf QtWebEngine 6.12.0 — macOS Patch Kit

Custom **QtWebEngine 6.12.0 ARM64** integration for **Darkelf Shadow 7.0.30**, a native macOS privacy browser.

## What's new in 7.0.30

- **Qt / PySide6 6.12.0** with a custom **QtWebEngine 6.12.0** framework for Apple Silicon.
- **Python 3.14.8** application runtime, packaged with **Nuitka 4.1.3**.
- Improved splash-to-homepage transition, eliminating the observed black-screen startup delay.
- Native macOS Developer ID signing, Touch ID/passkey entitlements, and Apple notarization workflow.

## Darkelf engine integration

Darkelf's macOS engine work includes:

- Touch ID and platform WebAuthn/passkey integration.
- iCloud/WebAuthn integration changes.
- Native WebGL modifications.
- Custom media-codec build configuration, including H.264-related support.

**Note:** Codec support does not imply DRM support. WebRTC and other compile-time settings should be confirmed against the distributed 6.12.0 binary.

## Repository files

| Path | Purpose |
| --- | --- |
| `patches/` | Darkelf engine patch sources |
| `apply-patch.sh` | Patch application helper |
| `build-darkelf-qtwebengine.sh` | Custom QtWebEngine build helper |
| `darkelf-webauthn.entitlements.plist` | macOS signing entitlement reference |
| `verify-darkelf-webauthn.sh` | WebAuthn verification helper |
| `BUILDING.md`, `QT_SOURCE.md` | Build and corresponding-source documentation |
| `QT_RELINKING.md` | LGPL library replacement guidance |
| `LICENSE.md`, `THIRD_PARTY_NOTICES.md` | Licensing and third-party notices |

## Building

The **7.0.30 macOS browser release uses QtWebEngine 6.12.0**. Build and patch instructions must target the matching 6.12.0 source tree and Qt installation. Verify that the checked-in scripts and patches have been ported to 6.12.0 before running them; do not use 6.11.2-specific commands against 6.12.0 source.

The engine build and the Darkelf Shadow application-signing/notarization workflow are separate processes. Publish the exact 6.12.0 source revision, applied patches, build configuration, and corresponding-source information for reproducible distribution.

## Security and licensing

macOS WebAuthn integration uses the Keychain access group `C7352X2Z2S.com.darkelfbrowser.shadow`. Signed entitlements must match the compiled application. Verify actual passkey registration and authentication.

Darkelf's original contributions are described under LGPL-3.0 in [LICENSE.md](LICENSE.md). Qt, Chromium, FFmpeg, and other components retain their applicable licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [QT_SOURCE.md](QT_SOURCE.md), and [QT_RELINKING.md](QT_RELINKING.md). H.264 support does not grant patent rights.

The standard cross-platform PyPI edition uses stock PySide6/QtWebEngine packages; this repository documents the custom macOS engine integration.

**Previous engine:** Darkelf Shadow 7.0.29 used QtWebEngine 6.11.2.
