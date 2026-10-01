#!/bin/bash
set -euo pipefail

# Darkelf Shadow 7.0.12 - macOS ARM64 release build.
# Run from the project root:
#   bash build-macos.sh build
#   ./build/main.app/Contents/MacOS/main   # Test, then close the browser.
#   bash build-macos.sh package
# With no argument, only the build stage runs. Packaging submits to Apple.
# Override PYTHON_BIN, CUSTOM_FRAMEWORK, PROVISION_PROFILE, SIGN_IDENTITY,
# or NOTARY_PROFILE through environment variables when needed.
# The custom engine's existing 7.0.11 directory name is intentional.

VERSION="7.0.12"
APP_NAME="Darkelf Shadow"
BUNDLE_ID="com.darkelfbrowser.shadow"
KEYCHAIN_GROUP="C7352X2Z2S.com.darkelfbrowser.shadow"
PYTHON_BIN="${PYTHON_BIN:-$HOME/pqcrypto_env/bin/python3.11}"
CUSTOM_FRAMEWORK="${CUSTOM_FRAMEWORK:-$HOME/Desktop/Darkelf-QtWebEngine-6.11.2-arm64-7.0.11/lib/QtWebEngineCore.framework}"
PROVISION_PROFILE="${PROVISION_PROFILE:-$HOME/Downloads/Darkelf_Shadow_Developer_ID.provisionprofile}"
SIGN_IDENTITY="${SIGN_IDENTITY:-Developer ID Application: KEVIN JAMES MOORE (C7352X2Z2S)}"
NOTARY_PROFILE="${NOTARY_PROFILE:-Darkelf}"
MAIN_ENTITLEMENTS="entitlements.plist"
HELPER_ENTITLEMENTS="helper-entitlements.plist"
ICON="shadow/assets/Darkelf.icns"
APP="build/main.app"
FINAL_APP="build/$APP_NAME.app"
APP_ZIP="build/Darkelf-Shadow-$VERSION.zip"
DMG_FILE="Darkelf-Shadow-$VERSION.dmg"
MODE="${1:-build}"
TEMP_DIR=""

fail() { echo "ERROR: $*" >&2; exit 1; }
section() { printf '\n== %s ==\n' "$*"; }
require_file() { [[ -f "$1" ]] || fail "Required file not found: $1"; }
require_command() { command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"; }
cleanup() { if [[ -n "$TEMP_DIR" ]]; then rm -rf "$TEMP_DIR"; fi; }
trap cleanup EXIT

case "$MODE" in
    build|package) ;;
    -h|--help)
        echo "Usage: bash build-macos.sh [build|package]"
        echo "Build first, test build/main.app, then package the tested app."
        exit 0 ;;
    *) fail "Unknown stage: $MODE. Use build or package." ;;
esac
[[ "$(uname -s)" == "Darwin" ]] || fail "Run this script on macOS."
[[ "$(uname -m)" == "arm64" ]] || fail "Use a native ARM64 terminal for this custom engine."
require_file main.py
require_file "$ICON"
require_command "$PYTHON_BIN"
for tool in codesign security ditto otool plutil xcrun spctl hdiutil fileicon; do
    require_command "$tool"
done
identities="$(security find-identity -v -p codesigning)"
[[ "$identities" == *"$SIGN_IDENTITY"* ]] || fail "Signing identity not found: $SIGN_IDENTITY"
TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/darkelf-release.XXXXXX")"

# Check the repaired framework without changing its binaries or source copy.
check_framework() {
    local framework="$1" link helper core helper_info core_info
    for link in Helpers QtWebEngineCore Resources Versions/Current; do
        [[ -L "$framework/$link" && -e "$framework/$link" ]] || fail "Missing/broken symlink: $framework/$link"
    done
    [[ ! -e "$framework/Versions/Resources" && ! -L "$framework/Versions/Resources" ]] \
        || fail "Invalid framework path: $framework/Versions/Resources"
    helper="$framework/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"
    core="$framework/Versions/A/QtWebEngineCore"
    [[ -x "$helper" ]] || fail "QtWebEngineProcess is missing or not executable."
    require_file "$core"
    helper_info="$(otool -l "$helper")"
    [[ "$helper_info" == *'@loader_path/../../../../../../..'* ]] || fail "Helper runtime rpath is missing."
    core_info="$(otool -l "$core")"
    if printf '%s\n' "$core_info" | grep -E '/Users/|Qt-Darkelf|/opt/homebrew|pqcrypto' >/dev/null; then
        fail "QtWebEngineCore has an external build-machine runtime path."
    fi
}

verify_app() {
    local app="$1" executable helper details
    check_framework "$app/Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework"
    executable="$app/Contents/MacOS/main"
    helper="$app/Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"
    codesign --verify --strict --verbose=4 "$executable"
    codesign --verify --deep --strict --verbose=4 "$app"
    for executable in "$executable" "$helper"; do
        details="$(codesign -dv --verbose=4 "$executable" 2>&1)"
        [[ "$details" == *runtime* ]] || fail "Hardened Runtime missing: $executable"
    done
    "$PYTHON_BIN" - "$app/Contents/Info.plist" "$VERSION" "$BUNDLE_ID" <<'PY'
import plistlib
import sys
with open(sys.argv[1], 'rb') as handle:
    info = plistlib.load(handle)
for key, expected in [('CFBundleShortVersionString', sys.argv[2]),
                      ('CFBundleVersion', sys.argv[2]), ('CFBundleIdentifier', sys.argv[3])]:
    if info.get(key) != expected:
        raise SystemExit(f'Incorrect {key}: {info.get(key)!r}; expected {expected!r}')
PY
}

notarize() {
    local artifact="$1" report="$2"
    xcrun notarytool submit "$artifact" --keychain-profile "$NOTARY_PROFILE" \
        --wait --output-format json > "$report"
    "$PYTHON_BIN" - "$report" <<'PY'
import json
import sys
with open(sys.argv[1], encoding='utf-8') as handle:
    result = json.load(handle)
print(f"Notarization: {result.get('status')} (submission {result.get('id')})")
if result.get('status') != 'Accepted':
    raise SystemExit('Notarization was not accepted. Inspect the submission with xcrun notarytool log.')
PY
}

if [[ "$MODE" == "build" ]]; then
    section "Preflight - custom engine and signing inputs"
    require_file "$MAIN_ENTITLEMENTS"
    require_file "$HELPER_ENTITLEMENTS"
    require_file "$PROVISION_PROFILE"
    require_file LICENSE
    if [[ -f THIRD_PARTY_NOTICES.txt ]]; then
        NOTICES="THIRD_PARTY_NOTICES.txt"
    elif [[ -f THIRD_PARTY_NOTICES.md ]]; then
        NOTICES="THIRD_PARTY_NOTICES.md"
    else
        fail "THIRD_PARTY_NOTICES.txt or THIRD_PARTY_NOTICES.md is required."
    fi
    plutil -lint "$MAIN_ENTITLEMENTS" "$HELPER_ENTITLEMENTS"
    check_framework "$CUSTOM_FRAMEWORK"
    "$PYTHON_BIN" - "$MAIN_ENTITLEMENTS" "$KEYCHAIN_GROUP" <<'PY'
import plistlib
import sys
import PySide6
if PySide6.__version__ != '6.11.2':
    raise SystemExit(f'The custom engine requires matching PySide6 6.11.2; found {PySide6.__version__}')
with open(sys.argv[1], 'rb') as handle:
    entitlements = plistlib.load(handle)
if sys.argv[2] not in entitlements.get('keychain-access-groups', []):
    raise SystemExit(f'Main entitlements are missing the custom engine keychain group: {sys.argv[2]}')
PY
    "$PYTHON_BIN" -m nuitka --version
    # Fail before removing old output if the configured profile cannot be decoded.
    security cms -D -i "$PROVISION_PROFILE" > "$TEMP_DIR/profile.plist"
    plutil -lint "$TEMP_DIR/profile.plist"

    section "Build app"
    rm -rf build dmg main.build main.dist
    "$PYTHON_BIN" -m nuitka --standalone --macos-create-app-bundle \
        --enable-plugin=pyside6 --include-package=shadow \
        --include-data-dir=shadow/assets=shadow/assets --output-dir=build \
        --macos-app-name="$APP_NAME" --macos-app-version="$VERSION" \
        --macos-app-icon="$PWD/$ICON" --macos-sign-identity="$SIGN_IDENTITY" main.py
    [[ -d "$APP" ]] || fail "Nuitka did not create $APP."

    section "Bundle metadata, provisioning and notices"
    "$PYTHON_BIN" - "$APP/Contents/Info.plist" "$VERSION" "$BUNDLE_ID" "$APP_NAME" <<'PY'
import plistlib
import sys
path, version, bundle_id, name = sys.argv[1:]
with open(path, 'rb') as handle:
    info = plistlib.load(handle)
info.update({
    'CFBundleIdentifier': bundle_id, 'CFBundleDisplayName': name, 'CFBundleName': name,
    'CFBundleExecutable': 'main', 'CFBundleShortVersionString': version, 'CFBundleVersion': version,
    'CFBundleURLTypes': [{'CFBundleURLName': name, 'CFBundleTypeRole': 'Viewer',
                         'CFBundleURLSchemes': ['http', 'https']}],
    'CFBundleDocumentTypes': [{'CFBundleTypeName': 'HTML Document', 'CFBundleTypeRole': 'Viewer',
                             'LSHandlerRank': 'Default', 'LSItemContentTypes': ['public.html', 'public.xhtml']}],
    'LSApplicationCategoryType': 'public.app-category.productivity', 'NSPrincipalClass': 'NSApplication',
    'NSHighResolutionCapable': True, 'NSSupportsAutomaticGraphicsSwitching': True,
    'CFBundleGetInfoString': 'Darkelf Shadow Web Browser',
    'NSBluetoothAlwaysUsageDescription': 'Darkelf Shadow uses Bluetooth only when a website requests a Bluetooth-enabled security key or device.',
})
with open(path, 'wb') as handle:
    plistlib.dump(info, handle)
PY
    cp "$PROVISION_PROFILE" "$APP/Contents/embedded.provisionprofile"
    mkdir -p "$APP/Contents/Resources"
    cp LICENSE "$APP/Contents/Resources/LICENSE"
    cp "$NOTICES" "$APP/Contents/Resources/$(basename "$NOTICES")"

    section "Install verified custom QtWebEngine"
    FW="$APP/Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework"
    [[ -d "$(dirname "$FW")" ]] || fail "Unexpected Nuitka/PySide6 framework layout."
    rm -rf "$FW"
    cp -a "$CUSTOM_FRAMEWORK" "$FW"
    check_framework "$FW"
    # No install_name_tool modifications: use the repaired master as supplied.

    section "Sign helper, framework, main executable, then outer app"
    codesign --force --options runtime --timestamp --entitlements "$HELPER_ENTITLEMENTS" \
        --sign "$SIGN_IDENTITY" "$FW/Helpers/QtWebEngineProcess.app"
    codesign --verify --deep --strict --verbose=4 "$FW/Helpers/QtWebEngineProcess.app"
    codesign --force --options runtime --timestamp --sign "$SIGN_IDENTITY" "$FW"
    codesign --verify --deep --strict --verbose=4 "$FW"
    check_framework "$FW"
    codesign --force --options runtime --timestamp --entitlements "$MAIN_ENTITLEMENTS" \
        --sign "$SIGN_IDENTITY" "$APP/Contents/MacOS/main"
    codesign --force --options runtime --timestamp --entitlements "$MAIN_ENTITLEMENTS" \
        --sign "$SIGN_IDENTITY" "$APP"
    verify_app "$APP"
    echo "Build ready: $APP"
    echo "Test it with: ./build/main.app/Contents/MacOS/main"
    echo "After testing and closing the app: bash build-macos.sh package"
    exit 0
fi

# Package the app from the build stage; this stage does not rebuild it.
# Renamed output is supported when retrying a failed DMG/notarization step.
if [[ ! -d "$APP" && -d "$FINAL_APP" ]]; then APP="$FINAL_APP"; fi
[[ -d "$APP" ]] || fail "No built app found. Run the build stage first."
section "Verify the tested app and exact ZIP"
verify_app "$APP"
rm -f "$APP_ZIP"
ditto -c -k --keepParent "$APP" "$APP_ZIP"
mkdir "$TEMP_DIR/zip-check"
ditto -x -k "$APP_ZIP" "$TEMP_DIR/zip-check"
verify_app "$TEMP_DIR/zip-check/$(basename "$APP")"

section "Notarize and staple app"
notarize "$APP_ZIP" "$TEMP_DIR/app-notarization.json"
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
spctl --assess --type execute --verbose=4 "$APP"
if [[ "$APP" != "$FINAL_APP" ]]; then
    [[ ! -e "$FINAL_APP" ]] || fail "Destination already exists: $FINAL_APP"
    mv "$APP" "$FINAL_APP"
fi

section "Stage and create DMG"
rm -rf dmg
mkdir dmg
cp -a "$FINAL_APP" "dmg/$APP_NAME.app"
verify_app "dmg/$APP_NAME.app"
ln -s /Applications dmg/Applications
rm -f "$DMG_FILE"
hdiutil create -volname "$APP_NAME" -srcfolder dmg -format UDZO -ov "$DMG_FILE"
fileicon set "$DMG_FILE" "$ICON"
fileicon test "$DMG_FILE"
codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DMG_FILE"
codesign --verify --strict --verbose=4 "$DMG_FILE"

section "Notarize and staple DMG"
notarize "$DMG_FILE" "$TEMP_DIR/dmg-notarization.json"
xcrun stapler staple "$DMG_FILE"
xcrun stapler validate "$DMG_FILE"
spctl --assess --type open --context context:primary-signature --verbose=4 "$DMG_FILE"
echo "Release ready: $DMG_FILE"
echo "No GitHub upload or PyPI publication was performed."
