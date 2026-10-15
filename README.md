
# Darkelf Shadow — Community Edition 7.0.29

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Privacy-focused browsing with Qt WebEngine, local MiniAI analysis and Smart Canvas protection.**

Darkelf Shadow combines network filtering, fingerprint defenses and session-focused browsing. Available through Python/PyPI and as a native macOS ARM64 application.

## What's new in 7.0.29

- **Refined floating panels:** Settings and Darkelf Inspector now use a cleaner, unified black rounded-panel design. Removed the redundant outer glass-like layer and excess inset spacing for a more consistent macOS appearance.
- **Redesigned Bookmarks panel:** the Bookmarks manager now uses a matching frameless floating panel instead of the previous traditional dialog-style window, while preserving existing bookmark-management functionality.
- **Improved application shutdown:** corrected red-button closing behavior so the browser exits completely instead of leaving the application running in the macOS Dock.
- **Cleaner WebEngine shutdown:** refined tab and WebEngine cleanup to prevent the browser from creating a replacement homepage tab while the application is closing.
- **Faster visual window closing:** improved the shutdown sequence so the main browser window hides before remaining cleanup operations finish, reducing the appearance of a delayed close.
- **Improved DMG presentation:** refined native macOS release packaging to support a custom mounted-volume icon instead of the generic disk-image icon.
- **More reliable release builds:** strengthened Nuitka module inclusion and build validation to prevent missing browser-module errors in packaged applications.
- **Release verification:** maintained Developer ID signing, hardened runtime, Apple notarization, stapling and SHA-256 checksum verification for the native macOS distribution.

### Previous 7.0.28 improvements retained

- **Refined macOS window appearance:** improved rounded-corner rendering on startup, with consistent corner handling during window resizing, restoration and fullscreen transitions.
- **Improved window dragging:** refined the frameless title-bar movement implementation to avoid conflicting native and manual drag operations and reduce macOS window-management warnings.
- **Navigation and tab cursor fixes:** corrected unwanted resize-cursor behavior over browser navigation buttons and the tab bar.
- **Faster window closing:** refined shutdown handling to make the browser window disappear promptly while preserving its cleanup process.
- **Redesigned browsing-data confirmation:** the Nuke/Wipe confirmation uses a black rounded panel consistent with Darkelf's native macOS interface. The underlying browsing-data cleanup behavior remains unchanged.
- **Code quality:** removed an unused import from the browser module to satisfy Ruff's F401 lint check.

### Previous 7.0.27 improvements retained

- **Native-looking black macOS window:** a frameless Qt main window replaces the gray system title bar with custom red, yellow and green traffic-light controls. The browser retains its existing toolbar and tabs.
- **Window arrangements:** click the green button to toggle fullscreen, or hover for approximately 1.8 seconds to open a dark rounded arrangement panel. Position the current Shadow window in the left or right half, any of three columns, or one of four screen quarters. Maximizing/restoring is also available. This does not automatically tile other applications.
- **Floating panels:** Settings and Darkelf Inspector use separate black rounded panels instead of traditional dialog-style windows.
- **Refined Settings:** Appearance layouts fit the floating panel, and About uses the available width more effectively.
- **Accent-aware controls:** the arrangement panel reflects the selected browser accent, with custom-painted traffic lights and a delayed hover menu to prevent accidental opening.

### Earlier 7.x improvements retained

- **Faster filter startup:** cached list downloads and merged subscriptions, direct matching for simple rules, and regex compilation for complex rules. Local filter startup fell from approximately 38 seconds to 6 seconds with about 417,000 network rules; timings vary by system and cache state.
- **CNN playback fix:** unsupported cookie-modification rules are skipped instead of blocking requests. Scriptlet and other unsupported page-action rules no longer become network blockers. CNN10 playback was verified in developer testing.
- **Independent Darkelf site boundaries:** embedded rules replace the copied Public Suffix List, with no separate `.dat` file or suffix download. Coverage is curated rather than worldwide; unknown namespaces use exact-host comparison and can cause extra blocking between related subdomains. Unlisted shared-hosting boundaries remain a coverage gap.
- **Browser usability:** video fullscreen hides browser controls and restores them on exit; delayed keyboard-filter installation checks for deleted Qt views.
- **Quieter operation:** repeated canvas messages are reduced and automatic terminal threat reports are removed. Optional diagnostics expose website JavaScript warnings/errors and matched network blockers.

## Installation

### Python / PyPI

Requires Python 3.11 or newer.

```bash
pip install --upgrade darkelf-shadow
darkelf-shadow
```

### Native macOS ARM64

Download the DMG and matching checksum from [GitHub Releases](https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases).

The native release workflow includes Developer ID signing, hardened runtime, Apple notarization and stapling. Verify the published build before installation.

| Distribution | Engine and session model |
|---|---|
| Python / PyPI | Platform PySide6 / Qt WebEngine; off-the-record profile. The custom macOS engine is not included. |
| macOS ARM64 DMG | Custom Darkelf Qt WebEngine 6.11.2; named profile for native authentication, memory HTTP cache and nonpersistent cookies. |

The DMG's named profile is **not off the record**. Native authentication configuration and credentials can persist separately from browsing-session cookies. Downloads, filter caches and other saved files can also remain on disk.

## Privacy and filtering

- Indexed filtering using EasyList, EasyPrivacy and uBlock-derived sources, plus declarative tracker-host checks and scoped compatibility exceptions.
- URL tracking-parameter cleanup and compatibility-aware cosmetic filtering.
- Local MiniAI threat scoring, fingerprint-event monitoring and response modes, without a cloud AI dependency.
- Canvas, WebGL, audio and other fingerprint mitigations. The custom DMG engine includes native WebGL modifications and disabled WebRTC; engine-specific patches do not transfer through standard PyPI dependencies.

The filter engine supports a subset of upstream rule syntax. Unsupported actions are skipped rather than implemented as request blockers.

### Smart Canvas

| Mode | Behavior |
|---|---|
| **BLOCKED** | Canvas readback is disabled. |
| **PROTECTED** | Readback uses Darkelf's domain-sensitive noise. |
| **TRUSTED** | Native readback is permitted for trusted compatibility cases. |

Supported human-verification flows can receive an automatic, temporary session trust grant to reduce verification loops. Closing Darkelf clears that grant.

### Authentication and media

The custom macOS engine includes native WebAuthn integration and H.264/AVC support. Touch ID/passkey availability depends on the signed app's keychain access group, provisioning, platform and website compatibility.

Version 7.0.29 focuses on browser interface, application shutdown and native distribution improvements. It does not introduce additional authentication-engine changes.

H.264 support does not supply DRM support. Protected streams may require a compatible DRM module; Widevine is not bundled with Darkelf.

## Optional diagnostics

Normal launches keep routine diagnostics quiet. To investigate website failures:

```bash
DARKELF_DIAGNOSTICS=1 darkelf-shadow
```

For a source checkout:

```bash
DARKELF_DIAGNOSTICS=1 python3.11 main.py
```

This prints website JavaScript warnings/errors and blocked requests with their matching rules. Launch without the variable to return to quiet operation.

## Verify the macOS download

Place the DMG and checksum in the same directory, then run:

```bash
shasum -a 256 -c Darkelf-Shadow-7.0.29.dmg.sha256
```

Expected result:

```text
Darkelf-Shadow-7.0.29.dmg: OK
```

The checksum verifies that the downloaded DMG matches the published checksum file. It does not independently establish the identity or trustworthiness of the publisher.

## License and scope

Darkelf Shadow is licensed under **LGPL-3.0-or-later**. The native app packages notices at:

- `Darkelf Shadow.app/Contents/Resources/LICENSE`
- `Darkelf Shadow.app/Contents/Resources/THIRD_PARTY_NOTICES.txt`

Bundled Qt, Chromium, FFmpeg and other components retain their respective licensing requirements.

Provided **AS IS**, without warranty. Darkelf does not guarantee anonymity, zero disk traces or protection against every threat, and does not replace operating-system security.

## Author and acknowledgments

**Dr. Kevin Moore · Darkelf Project — Shadow Edition · 2025–2026**

Thanks to the **Mecha Comet Team**.

