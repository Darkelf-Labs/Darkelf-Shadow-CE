# Darkelf Shadow — Community Edition 7.0.14

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Privacy-focused browsing with Qt WebEngine, local MiniAI analysis and Smart Canvas protection.**

Available through Python/PyPI and as a native macOS ARM64 application.

## What's new in 7.0.14

- **Normal shutdown cleanup:** replaces the detached cleanup worker with cleanup inside the application. WebEngine pages and the profile are destroyed before selected website-session stores are removed.
- **No detached cleanup task:** session wiping no longer starts a worker that continues running after application exit.
- **Authentication retained:** cleanup preserves native authentication configuration, including the WebAuthn secret, and does not delete macOS Keychain credentials.
- **Security checks:** the storage check uses a synchronous Qt process. Updated browser features passed Bandit with no findings or suppressions.
- **WebAuthn request handling:** guards against duplicate requests, reentrant polling and stale request cleanup. These changes do not resolve Apple entitlement requirements or guarantee passkey compatibility.

Developer testing confirmed website-session stores were removed after a native DMG shutdown. Crashes, forced termination, locked files and access failures can still prevent cleanup.

The filter-startup, playback, fullscreen, View Source and privacy-status improvements from earlier 7.x releases remain included.

## Installation

### Python / PyPI

Requires Python 3.11 or newer.

```bash
pip install --upgrade darkelf-shadow
darkelf-shadow
```

### Native macOS ARM64

Download the DMG and matching checksum from [GitHub Releases](https://github.com/Darkelf-Labs/Darkelf-Shadow-CE/releases).

The native release process includes Developer ID signing, hardened runtime, notarization and stapling.

| Distribution | Engine and session model |
|---|---|
| Python / PyPI | Platform PySide6 / Qt WebEngine; off-the-record profile. The custom macOS engine is not included. |
| macOS ARM64 DMG | Custom Darkelf Qt WebEngine 6.11.2; named `Darkelf` profile, web-content caching in memory and nonpersistent cookies. |

The DMG's named profile is **not off the record**. During normal shutdown, Darkelf destroys WebEngine pages and the profile, checks that storage files are closed, then removes selected website stores—including localStorage, IndexedDB, service-worker data, history and caches.

Authentication configuration and macOS Keychain credentials are retained. Cleanup failures are reported rather than treated as successful wipes. Filter caches, saved snapshots and other intentionally saved files can remain on disk.

## Privacy and filtering

- Indexed filtering using EasyList, EasyPrivacy and uBlock-derived sources.
- URL tracking-parameter cleanup and compatibility-aware cosmetic filtering.
- Local MiniAI threat scoring, fingerprint-event monitoring, panic and lockdown modes.
- Canvas, WebGL, audio and other fingerprint mitigations.
- Native WebGL modifications and disabled WebRTC in the custom DMG engine. Standard PyPI installations use application-level defenses, with compatibility exceptions.

The filter engine supports a subset of upstream rule syntax. Unsupported actions are skipped rather than treated as network blockers.

Embedded Darkelf site-boundary rules require no separate `.dat` file or suffix download. Coverage is curated; unknown namespaces use exact-host comparison, and unlisted shared-hosting boundaries remain a coverage gap.

### Smart Canvas

**Smart Canvas adapts protection by site, with compatibility exceptions.**

| Mode | Behavior |
|---|---|
| **BLOCKED** | Canvas readback is disabled. |
| **PROTECTED** | Readback uses Darkelf's domain-sensitive noise. |
| **COMPATIBLE** | Native readback is permitted; the compatibility guard bypasses injected canvas protection. |
| **TRUSTED** | Native readback is permitted for trusted sites or temporary verification grants. |

Automatic human-verification detection grants temporary canvas trust to the exact hostname to reduce verification loops. Closing Darkelf clears the grant.

Detection uses a page-console signal rather than authenticated proof of a challenge; website scripts can imitate that signal. Compatibility exceptions may also bypass other injected fingerprint defenses. Native engine patches operate separately.

### Darkelf Quantum

Quantum maintains session seeds, SHA3 hash chaining, bounded state and watchdog health checks. Its state is cleared when the session ends.

Runtime health indicators do not certify browser security, and state cleanup does not guarantee physical memory zeroization.

### Authentication and media

The custom macOS engine includes native WebAuthn integration and H.264/AVC support.

Touch ID/passkey availability depends on the signed app's keychain access group, provisioning, applicable Apple authorization, platform and website compatibility. **Apple-specific authentication issues are not claimed resolved by 7.0.14.**

H.264 support does not provide DRM support. Widevine is not bundled with Darkelf.

## Optional diagnostics

To investigate website failures:

```bash
DARKELF_DIAGNOSTICS=1 darkelf-shadow
```

For a source checkout:

```bash
DARKELF_DIAGNOSTICS=1 python3.11 main.py
```

This enables website JavaScript warnings/errors and matched network-blocking diagnostics. Launch without the variable to disable optional diagnostics.

## Testing

The [Darkelf-Pytests](https://github.com/Darkelf-Labs/Darkelf-Pytests) repository provides Shadow regression tests and ecosystem checks.

Automated linting, security scans and tests complement developer testing; they are not an independent professional security audit or verification of every DMG engine patch.

## Verify the macOS download

Place the DMG and its matching checksum in the same directory:

```bash
shasum -a 256 -c Darkelf-Shadow-7.0.14.dmg.sha256
```

Expected result:

```text
Darkelf-Shadow-7.0.14.dmg: OK
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
