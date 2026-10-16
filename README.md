# Darkelf QtWebEngine — macOS Patch Kit

Custom QtWebEngine integration for **Darkelf Shadow**, a native macOS privacy browser.

## Darkelf Shadow 7.0.30 highlights

- **Python 3.14.8** application runtime.
- **Qt / PySide6 6.12.0** and a custom **QtWebEngine 6.12.0 ARM64** framework.
- **Nuitka 4.1.3** for macOS application packaging.
- Refined splash-to-homepage transition to avoid the startup black screen.
- Developer ID signing, Touch ID/passkey entitlements, and Apple notarization in the macOS release workflow.

**Previous release:** Darkelf Shadow 7.0.29 used Python 3.11, Nuitka 4.1.3, and custom QtWebEngine 6.11.2.

## Custom engine features

The Darkelf patch-kit work covers macOS Touch ID / platform WebAuthn, iCloud/WebAuthn integration, native WebGL changes, and proprietary-codec build configuration including H.264-related support. The checked-in **6.11.2** build script disables WebRTC. These settings must be verified separately for each **6.12.0** binary; codec enablement does not imply DRM support.

## Repository contents

| Path | Purpose |
| --- | --- |
| `patches/` | Touch ID, iCloud/WebAuthn, and native WebGL patches for the documented 6.11.2 line |
| `apply-patch.sh` | Apply the documented patch series |
| `build-darkelf-qtwebengine.sh` | Build the documented QtWebEngine 6.11.2 line |
| `darkelf-webauthn.entitlements.plist` | macOS signing entitlement reference |
| `verify-darkelf-webauthn.sh` | WebAuthn verification |
| `BUILDING.md`, `QT_SOURCE.md` | Build and corresponding-source details |
| `QT_RELINKING.md` | LGPL library replacement guidance |
| `LICENSE.md`, `THIRD_PARTY_NOTICES.md` | Licensing and third-party notices |

## Build documentation

The checked-in scripts and patches document **QtWebEngine 6.11.2**. Do **not** apply them to 6.12.0 without a separately validated port. For the documented 6.11.2 build:

```sh
./apply-patch.sh "$HOME/Desktop/qtwebengine-everywhere-src-6.11.2"
export QT_PREFIX="/path/to/Qt/6.11.2/macos"
./build-darkelf-qtwebengine.sh
```

The patch-kit build script does not create or notarize a Darkelf Shadow DMG. The 7.0.30 macOS release workflow is separate. A reproducible 6.12.0 patch series and exact corresponding-source manifest should be published before treating this repository as complete 6.12.0 build instructions.

## WebAuthn and licensing

The macOS integration uses the Keychain access group `C7352X2Z2S.com.darkelfbrowser.shadow`; signed entitlements must match the compiled configuration. Verify real passkey registration and authentication, not just API detection.

Darkelf's original contributions are described under LGPL-3.0 in [LICENSE.md](LICENSE.md). Qt, Chromium, FFmpeg, and other dependencies retain their respective licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [QT_SOURCE.md](QT_SOURCE.md), and [QT_RELINKING.md](QT_RELINKING.md). H.264 codec support does not grant patent rights.

The standard cross-platform PyPI distribution uses stock PySide6/QtWebEngine packages rather than this custom macOS framework.
