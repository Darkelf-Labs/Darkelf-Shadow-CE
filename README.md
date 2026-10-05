# Darkelf Shadow — Community Edition 7.0.16

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Privacy-focused browsing with Qt WebEngine, local MiniAI analysis and Smart Canvas protection.**

Available through Python/PyPI and as a native macOS ARM64 application.

## What's new in 7.0.16

- **Find bar alignment:** centered chevrons and close icons replace font characters. Buttons and the input field use matching heights, and the close icon follows the selected accent color.
- **Cleaner Inspector:** removed redundant Requests and Blocked counters from the bottom status strip.
- **Clearer MiniAI status:** inactive Lockdown and Panic modes display **STANDBY**; triggered modes display **ACTIVE**.
- **Updated Inspector documentation:** removed obsolete Network tab instructions and header references. The shortcut guide now documents Cmd+Q and closing the last browser window.
- **About correction:** corrected the acknowledgment name to **Tim Burns**.

Developer testing confirmed the updated Find bar alignment. These interface changes preserve existing filtering, protection and shutdown behavior.

Hovered-link previews, corrected Google Maps navigation, English language preferences, normal shutdown cleanup, faster filter startup, playback fixes, fullscreen navigation and bounded View Source downloads remain included.

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

Authentication configuration and macOS Keychain credentials are retained. Cleanup failures are reported rather than treated as successful wipes. Crashes, forced termination, locked files and access failures can prevent cleanup. Filter caches, saved snapshots and other intentionally saved files can remain on disk.

Session cleanup does not automatically remove historical profiles created by older builds.

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

### Darkelf Inspector

The Inspector provides **Console, Quantum, MiniAI, Shortcuts and Help** tabs.

- **Console:** inspect results and execute JavaScript in the active page.
- **Quantum:** view session-state and runtime-health telemetry.
- **MiniAI:** view threat statistics and defensive states.
- **Shortcuts:** review browser keyboard controls, including Cmd+Q.
- **Help:** read documentation matching the current Inspector interface.

**STANDBY** means Lockdown or Panic blocking is inactive while MiniAI continues monitoring. **ACTIVE** means that defensive mode has been triggered.

### Darkelf Quantum

Quantum maintains session seeds, SHA3 hash chaining, bounded state and watchdog health checks. Its state is cleared when the session ends.

Runtime health indicators do not certify browser security, and state cleanup does not guarantee physical memory zeroization.

### Authentication and media

The custom macOS engine includes native WebAuthn integration and H.264/AVC support.

Touch ID/passkey availability depends on the signed app's keychain access group, provisioning, applicable Apple authorization, platform and website compatibility. **Apple-specific authentication issues are not claimed resolved by 7.0.16.**

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

The updated Find bar, Inspector and About files passed syntax checks. Targeted Ruff checks passed for the Find bar and Inspector changes.

Automated linting, security scans and tests complement developer testing; they are not an independent professional security audit or verification of every DMG engine patch.

## Verify the macOS download

Place the DMG and its matching checksum in the same directory:

```bash
shasum -a 256 -c Darkelf-Shadow-7.0.16.dmg.sha256
```

Expected result:

```text
Darkelf-Shadow-7.0.16.dmg: OK
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
