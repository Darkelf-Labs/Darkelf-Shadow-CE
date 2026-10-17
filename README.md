# 🕶️ Darkelf Shadow CE

Darkelf Shadow CE is a privacy-focused macOS browser built with Python, PySide6, and a customized QtWebEngine/Chromium framework.

- Continued support for the custom QtWebEngine 6.12 framework.
- Maintained native WebAuthn/FIDO2 and macOS Touch ID integration.
- Support for locally registered passkeys using macOS Keychain.
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
| Passkey authentication | WebAuthn/FIDO2 with native macOS Touch ID |
| Passkey storage | macOS Keychain with a dedicated Darkelf access group |

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
- Passkey registration and authentication successfully tested with Microsoft.
- Touch ID passkey authentication successfully tested with GitHub.

### Independent Passkey Storage

Darkelf Shadow uses its own macOS Keychain access group:

`C7352X2Z2S.com.darkelfbrowser.shadow.webauthn`

This separates Darkelf's locally managed passkeys from credentials managed by Apple Passwords/iCloud Keychain.

Passkeys previously created in Safari or Apple Passwords are not automatically accessible through Darkelf Shadow's custom authenticator.

Users may need to register a separate passkey for Darkelf Shadow on websites where they already use an Apple iCloud Keychain passkey.

Darkelf Shadow does not currently provide an independent cloud-based passkey synchronization service.

## 🛡️ Credential Privacy

Darkelf Shadow distinguishes between traditional browser password storage and user-authorized WebAuthn passkeys.

**Traditional website passwords**

Darkelf Shadow is not designed to operate as a traditional browser password manager or automatically maintain a vault of saved website usernames and passwords.

**WebAuthn passkeys**

When a user explicitly registers a passkey, Darkelf Shadow uses its dedicated macOS Keychain configuration to manage the local credential.

A persistent WebAuthn metadata secret is maintained in the browser profile to support authentication across browser sessions.

These passkeys are separate from ordinary browsing history, cookies, and traditional password-autofill features.

**Privacy considerations**

- Darkelf Shadow does not operate a cloud-based credential vault.
- Locally registered passkeys are not automatically synchronized by Darkelf Shadow.
- Passkeys may persist independently of ordinary browsing-data cleanup.
- Removing browser history or cookies does not necessarily delete registered passkeys.
- Users should retain alternative account recovery methods.

The browser's privacy protections and persistent, user-authorized authentication credentials serve different purposes.

## 🔒 Security

Darkelf Shadow uses multiple security and privacy mechanisms, including:

- macOS Hardened Runtime.
- Developer ID application signing.
- Apple notarization.
- QtWebEngine's Chromium security architecture.
- Browser-level content protections.
- WebAuthn/FIDO2 authentication support.
- Native macOS Touch ID integration.
- Dedicated Keychain access-group configuration for local passkeys.

No browser can guarantee complete anonymity, immunity from malicious websites, or protection from every vulnerability.

Users should keep Darkelf Shadow and macOS updated and exercise appropriate caution when browsing unfamiliar websites.

## 📄 Licensing & Third-Party Software

Darkelf Shadow includes or depends on third-party open-source components, including Qt, QtWebEngine, Chromium, PySide6, and supporting libraries.

Refer to the repository's licensing and third-party notice files for applicable terms and source information.

## 🔗 Project Links

- **GitHub Organization:** https://github.com/Darkelf-Labs
- **Darkelf Shadow CE:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE
- **Releases:** https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases

---

**Developed by Darkelf Labs.**
