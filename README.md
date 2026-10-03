# Darkelf Shadow — Community Edition 7.0.13

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/darkelf-shadow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/darkelf-shadow)

**Privacy-focused browsing with Qt WebEngine, local MiniAI analysis and Smart Canvas protection.**

Available through Python/PyPI and as a native macOS ARM64 application.

## What's new in 7.0.13

- **Session cleanup:** normal application exit—including the red close button, Cmd+Q and Delete and Quit—schedules named-profile website-storage cleanup after the browser releases its files. Authentication files are retained.
- **Profile selection:** Python/PyPI and direct source launches use an off-the-record profile. The recognized native macOS app uses the named `Darkelf` profile.
- **Fullscreen navigation:** opening or switching tabs during video fullscreen restores browser controls.
- **View Source:** HTTP(S) fetches have an 8 MiB response limit; oversized responses show a clear error.
- **Panic and lockdown:** blocking takes priority over redirects, CAPTCHA resources and local-address exemptions. Private-address matching no longer mistakes public hostname prefixes for local IP addresses.
- **Accurate settings:** profile, cookie, cache and JavaScript badges reflect live settings. Smart Canvas compatibility labels and Quantum health descriptions are clearer.
- **Security checks:** the Bandit workflow runs directly, fails on findings and retains its reports.

The filter-startup optimizations and CNN compatibility fixes introduced in 7.0.12 remain included.

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
| macOS ARM64 DMG | Custom Darkelf Qt WebEngine 6.11.2; named `Darkelf` profile, memory HTTP cache and nonpersistent cookies. |

The DMG's named profile is **not off the record**. Website storage—including localStorage, IndexedDB and service-worker data—is scheduled for cleanup after normal application exit. The cleanup preserves the WebAuthn secret and macOS Keychain credentials.

Cleanup can fail if files remain in use or access is denied. Crashes and forced termination cannot guarantee cleanup. Filter caches, saved snapshots and other intentionally saved files can remain on disk.

## Privacy and filtering

- Indexed filtering using EasyList, EasyPrivacy and uBlock-derived sources.
- URL tracking-parameter cleanup and compatibility-aware cosmetic filtering.
- Local MiniAI threat scoring, fingerprint-event monitoring, panic and lockdown modes.
- Canvas, WebGL, audio and other fingerprint mitigations.
- Native WebGL modifications and disabled WebRTC in the custom DMG engine. Standard PyPI installations use JavaScript defenses, with compatibility exceptions.

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

Touch ID/passkey availability depends on the signed app's keychain access group, provisioning, required Apple authorization, platform and website compatibility. Apple-specific authentication issues are **not claimed resolved by 7.0.13**.

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
shasum -a 256 -c Darkelf-Shadow-7.0.13.dmg.sha256
```

Expected result:

```text
Darkelf-Shadow-7.0.13.dmg: OK
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
