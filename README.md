# 🕶️ Darkelf Shadow CE

**Latest Release: 7.1.2**

Darkelf Shadow CE is a privacy-focused macOS browser built with Python, PySide6, and a customized QtWebEngine/Chromium framework developed and maintained by Darkelf Labs.

## ✨ What's New in 7.1.2

- Custom QtWebEngine 6.140.0 rebuilt against the Qt 6.12.1 SDK.
- Chromium 140.0.7339.225 browser engine.
- Continued compatibility with PySide6 and Qt 6.12.0 application libraries.
- Preservation of custom Darkelf WebAuthn and Touch ID modifications.
- Binary-level verification of custom WebAuthn identifiers.
- Support for locally registered passkeys using macOS Keychain.
- Proprietary media codec support.
- WebRTC disabled at the custom engine build level.
- Improved Chromium sandbox configuration and runtime verification.
- Updated Python 3.14 and Nuitka 4.1.3 compilation environment.
- Enhanced framework integrity, code-signing and release verification procedures.
- Refined macOS-inspired interface with translucent panels and context menus.

## 📦 Installation

Download the latest release from the project's GitHub Releases page.

1. Download `Darkelf-Shadow-7.1.2.dmg`.
2. Open the disk image.
3. Drag Darkelf Shadow into Applications.
4. Launch the application from Applications.

**Platform:** macOS on Apple Silicon (ARM64).

A SHA-256 checksum is provided alongside the release for download integrity verification.

## 🔧 Architecture

Darkelf Shadow combines several components:

| Component | Technology / Version |
|---|---|
| Application | Darkelf Shadow CE 7.1.2 |
| Programming language | Python 3.14 |
| Python bindings | PySide6 6.12.0 |
| Desktop framework | Qt 6.12.0 |
| Custom engine build SDK | Qt 6.12.1 |
| Browser engine | Customized QtWebEngine 6.140.0 |
| Chromium engine | 140.0.7339.225 |
| Compilation and packaging | Nuitka 4.1.3 |
| Architecture | Native Apple Silicon ARM64 |
| Distribution | Developer ID signing and Apple notarization |
| Passkey authentication | WebAuthn/FIDO2 with native macOS Touch ID |
| Passkey storage | macOS Keychain with a dedicated Darkelf access group |
| Proprietary media codecs | Enabled |
| WebRTC | Disabled at engine build level |

### Customized QtWebEngine Framework

Darkelf Shadow maintains a customized QtWebEngine framework independently of the standard QtWebEngine binaries distributed with PySide6.

The custom QtWebEngine 6.140.0 framework is compiled against the Qt 6.12.1 SDK using the existing Darkelf-patched source tree.

The application continues to use PySide6 6.12.0 and its associated Qt application libraries. During release packaging, the standard QtWebEngineCore framework is replaced with the independently compiled Darkelf framework.

This approach preserves compiled engine-level modifications without requiring those modifications to be implemented solely at the Python application level.

## ⚙️ Custom Engine Configuration

The Darkelf QtWebEngine build incorporates:

- Custom WebAuthn authenticator integration.
- Native macOS Touch ID support.
- Dedicated Darkelf Keychain access-group configuration.
- Persistent WebAuthn metadata-secret management.
- Proprietary media codec support.
- Build-level WebRTC disablement.
- Native Apple Silicon ARM64 compilation.
- Release-mode optimization.
- Chromium subprocess sandbox configuration and verification.

The customized engine and application-level privacy defenses are maintained as part of the Darkelf Shadow development process.

## 🔐 WebAuthn, Touch ID & Passkey Support

Darkelf Shadow supports native macOS Touch ID authentication through its customized QtWebEngine/Chromium integration.

Users can register and authenticate with supported websites using WebAuthn/FIDO2 passkeys.

### Supported Capabilities

- Native macOS Touch ID authentication.
- WebAuthn/FIDO2 authentication through Chromium.
- Registration of local, device-bound passkeys.
- Persistent passkey authentication across browser restarts.
- Dedicated macOS Keychain access group for Darkelf Shadow.
- Persistent WebAuthn metadata-secret management.
- Passkey registration and authentication previously tested with Microsoft.
- Touch ID passkey authentication previously tested with GitHub.

### Independent Passkey Storage

Darkelf Shadow uses its own macOS Keychain access group:

`C7352X2Z2S.com.darkelfbrowser.shadow.webauthn`

This separates Darkelf's locally managed passkeys from credentials managed by Apple Passwords and iCloud Keychain.

Passkeys previously created in Safari or Apple Passwords are not automatically accessible through Darkelf Shadow's custom authenticator.

Users may need to register a separate passkey for Darkelf Shadow on websites where they already use an Apple iCloud Keychain passkey.

Darkelf Shadow does not currently provide an independent cloud-based passkey synchronization service.

### Compiled WebAuthn Modifications

The custom QtWebEngine framework contains Darkelf-specific WebAuthn modifications, including:

- `kDarkelfWebAuthnKeychainAccessGroup`
- `kDarkelfWebAuthnSecretFile`
- `darkelfWebAuthnMetadataSecret()`

The following identifiers have been verified within the custom QtWebEngine binary rebuilt against Qt 6.12.1:

- `C7352X2Z2S.com.darkelfbrowser.shadow.webauthn`
- `.darkelf-webauthn-secret`

These identifiers provide binary-level evidence that the custom WebAuthn modifications have been retained in the rebuilt framework.

## 🛡️ Credential Privacy

Darkelf Shadow distinguishes between traditional browser password storage and user-authorized WebAuthn passkeys.

### Traditional Website Passwords

Darkelf Shadow is not designed to operate as a traditional browser password manager or automatically maintain a vault of saved website usernames and passwords.

### WebAuthn Passkeys

When a user explicitly registers a passkey, Darkelf Shadow uses its dedicated macOS Keychain configuration to manage the local credential.

A persistent WebAuthn metadata secret is maintained in the browser profile to support authentication across browser sessions.

These passkeys are separate from ordinary browsing history, cookies, and traditional password-autofill features.

### Privacy Considerations

- Darkelf Shadow does not operate a cloud-based credential vault.
- Locally registered passkeys are not automatically synchronized by Darkelf Shadow.
- Passkeys may persist independently of ordinary browsing-data cleanup.
- Removing browser history or cookies does not necessarily delete registered passkeys.
- Users should retain alternative account recovery methods.

The browser's privacy protections and persistent, user-authorized authentication credentials serve different purposes.

## 🎨 macOS Interface

Darkelf Shadow provides a customized desktop browsing experience inspired by native macOS interface design.

Interface features include:

- Translucent dark panels.
- Refined context menus.
- Rounded window and panel corners.
- Consistent visual styling across browser components.
- macOS fullscreen and window-management integration.
- Native Apple Silicon application architecture.

## 🔒 Security

Darkelf Shadow incorporates multiple security and privacy mechanisms, including:

- macOS Hardened Runtime.
- Developer ID application signing.
- Apple notarization.
- QtWebEngine's Chromium security architecture.
- Chromium subprocess sandboxing.
- Browser-level content protections.
- WebAuthn/FIDO2 authentication support.
- Native macOS Touch ID integration.
- Dedicated Keychain access-group configuration for local passkeys.
- Custom framework integrity verification.
- SHA-256 release checksums.

No browser can guarantee complete anonymity, immunity from malicious websites, or protection from every vulnerability.

Users should keep Darkelf Shadow and macOS updated and exercise appropriate caution when browsing unfamiliar websites.

## 🔍 Release Integrity & Verification

Darkelf Shadow incorporates a structured release workflow designed to verify the integrity of the customized browser engine and packaged application.

### Pre-release Verification

The release workflow includes:

- Python, PySide6, Qt and Nuitka version validation.
- Custom QtWebEngine framework version validation.
- Chromium version validation.
- Compiled Darkelf WebAuthn identifier verification.
- SHA-256 comparison between the custom engine and bundled framework before signing.
- Framework structure and symbolic-link validation.
- Dynamic-library dependency inspection.
- QtWebEngine helper-process verification.
- ARM64 V8 snapshot validation.
- Developer ID provisioning-profile verification.
- Keychain entitlement validation.

### Runtime Verification

The release workflow requires runtime testing of:

- Custom QtWebEngine initialization.
- Website rendering and navigation.
- Chromium renderer subprocesses.
- Chromium sandbox enforcement.
- Native macOS Touch ID authentication.
- Existing WebAuthn passkey compatibility.
- Browser settings and interface functionality.
- Fullscreen and macOS window-management behavior.

### Distribution Verification

The distribution workflow includes:

- Hardened Runtime code signing.
- Application and framework signature verification.
- Apple notarization.
- Notarization ticket stapling.
- macOS Gatekeeper assessment.
- DMG signing and notarization.
- SHA-256 checksum generation and verification.

## 📁 Release Files

| File | Description |
|---|---|
| `Darkelf-Shadow-7.1.2.dmg` | macOS Apple Silicon installer |
| `Darkelf-Shadow-7.1.2.dmg.sha256` | SHA-256 integrity checksum |

To verify the downloaded disk image, place both files in the same directory and execute:

`shasum -a 256 -c Darkelf-Shadow-7.1.2.dmg.sha256`

A successful verification should return:

`Darkelf-Shadow-7.1.2.dmg: OK`

## 📄 Licensing & Third-Party Software

Darkelf Shadow includes or depends on third-party open-source components, including Qt, QtWebEngine, Chromium, PySide6, and supporting libraries.

Refer to the repository's licensing and third-party notice files for applicable terms, source information and relinking provisions.

- `LICENSE`
- `LICENSE.LGPL21`
- `GPL-3.0.txt`
- `THIRD_PARTY_NOTICES.txt`
- `QT_SOURCE.md`
- `QT_RELINKING.md`

Third-party components remain subject to their respective licenses.

## 🔗 Project Links

- **GitHub Organization:** https://github.com/Darkelf-Labs
- **Darkelf Shadow CE:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE
- **Releases:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases

---

**Developed by Darkelf Labs.**

*Privacy-focused browsing. Customized browser technology. Native macOS integration.*
