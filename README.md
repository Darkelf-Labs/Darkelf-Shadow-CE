# Darkelf Shadow — Community Edition 7.0.12

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Privacy-focused browsing with Qt WebEngine, local MiniAI analysis and Smart Canvas protection.**

Darkelf Shadow combines network filtering, fingerprint defenses and session-focused browsing. Available through Python/PyPI and as a native macOS ARM64 application.

## What's new in 7.0.12

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

Download the DMG and matching checksum from [GitHub Releases](https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases). The native release workflow includes Developer ID signing, hardened runtime, notarization and stapling.

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

The custom macOS engine includes native WebAuthn integration and H.264/AVC support. Touch ID/passkey availability depends on the signed app's keychain access group, provisioning, platform and website compatibility. Apple-specific authentication issues are not claimed resolved by 7.0.12.

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
shasum -a 256 -c Darkelf-Shadow-7.0.12.dmg.sha256
```

Expected result:

```text
Darkelf-Shadow-7.0.12.dmg: OK
```

## License and scope

Darkelf Shadow is licensed under **LGPL-3.0-or-later**. The native app packages notices at:

- `Darkelf Shadow.app/Contents/Resources/LICENSE`
- `Darkelf Shadow.app/Contents/Resources/THIRD_PARTY_NOTICES.txt`

Bundled Qt, Chromium, FFmpeg and other components retain their respective licensing requirements.

Provided **AS IS**, without warranty. Darkelf does not guarantee anonymity, zero disk traces or protection against every threat, and does not replace operating-system security.

## Author and acknowledgments

**Dr. Kevin Moore · Darkelf Project — Shadow Edition · 2025–2026**

Thanks to the **Mecha Comet Team** and **Tim Burns** for their support and contributions.
