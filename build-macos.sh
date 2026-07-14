#!/bin/bash
set -euo pipefail

###############################################################################
# Darkelf Shadow - macOS Release Build
#
# Produces:
#   build/Darkelf Shadow.app
#   Darkelf-Shadow-7.0.0.dmg
#
# Requirements:
#   - Run from the project root.
#   - Activate the Python environment containing Nuitka and PySide6.
#   - Apple Developer ID certificate installed in Keychain.
#   - notarytool profile named "Darkelf".
#   - entitlements.plist in the project root.
#   - fileicon installed: brew install fileicon
#
# Notes:
#   - The app is signed with Hardened Runtime before notarization.
#   - The DMG contains Darkelf Shadow.app and an Applications shortcut.
#   - The custom DMG icon is applied before signing and notarization.
###############################################################################

APP_NAME="Darkelf Shadow"
APP_SLUG="Darkelf-Shadow"
BUNDLE_ID="com.kevinmoore.darkelfshadow"
VERSION="7.0.0"

MAIN_SCRIPT="main.py"
ICON="shadow/assets/Darkelf.icns"
ENTITLEMENTS="entitlements.plist"

BUILD_DIR="build"
DMG_STAGE_DIR="dmg"
NUITKA_APP="$BUILD_DIR/main.app"
FINAL_APP="$BUILD_DIR/$APP_NAME.app"
APP_ZIP="$BUILD_DIR/Darkelf-Shadow-$VERSION.zip"
DMG_FILE="$APP_SLUG-$VERSION.dmg"

SIGN_IDENTITY="Developer ID Application: KEVIN JAMES MOORE (C7352X2Z2S)"
NOTARY_PROFILE="Darkelf"

section() {
    echo
    echo "==========================================================="
    echo "$1"
    echo "==========================================================="
}

require_file() {
    if [[ ! -f "$1" ]]; then
        echo "ERROR: Required file not found: $1" >&2
        exit 1
    fi
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: Required command not found: $1" >&2
        exit 1
    fi
}

section "Preflight checks"

require_file "$MAIN_SCRIPT"
require_file "$ICON"
require_file "$ENTITLEMENTS"

require_command python
require_command codesign
require_command ditto
require_command hdiutil
require_command xcrun
require_command fileicon

python -m nuitka --version

codesign --find-identity -v -p codesigning | grep -F "$SIGN_IDENTITY" >/dev/null || {
    echo "ERROR: Signing identity not found:" >&2
    echo "  $SIGN_IDENTITY" >&2
    exit 1
}

section "Cleaning previous build and release artifacts"

rm -rf "$BUILD_DIR"
rm -rf "$DMG_STAGE_DIR"
rm -rf main.build
rm -rf main.dist
rm -f main.bin
rm -f main.zip
rm -f "$APP_ZIP"
rm -f "$DMG_FILE"

section "Building with Nuitka"

python -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --enable-plugin=pyside6 \
    --include-package=shadow \
    --include-data-dir=shadow/assets=shadow/assets \
    --output-dir="$BUILD_DIR" \
    --macos-app-name="$APP_NAME" \
    --macos-app-version="$VERSION" \
    --macos-app-icon="$ICON" \
    --macos-sign-identity="$SIGN_IDENTITY" \
    "$MAIN_SCRIPT"

if [[ ! -d "$NUITKA_APP" ]]; then
    echo "ERROR: Nuitka did not create $NUITKA_APP" >&2
    exit 1
fi

section "Renaming app bundle"

mv "$NUITKA_APP" "$FINAL_APP"

section "Updating bundle metadata"

PLIST="$FINAL_APP/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Delete :CFBundleIdentifier" "$PLIST" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Delete :CFBundleShortVersionString" "$PLIST" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Delete :CFBundleVersion" "$PLIST" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Delete :CFBundleDisplayName" "$PLIST" >/dev/null 2>&1 || true

/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $BUNDLE_ID" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $APP_NAME" "$PLIST"

section "Signing app with Hardened Runtime"

codesign \
    --force \
    --deep \
    --options runtime \
    --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGN_IDENTITY" \
    "$FINAL_APP"

section "Verifying app signature"

codesign --verify --deep --strict --verbose=4 "$FINAL_APP"

MAIN_EXECUTABLE="$FINAL_APP/Contents/MacOS/main"
WEBENGINE_PROCESS="$FINAL_APP/Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework/Versions/A/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"

codesign -dv --verbose=4 "$MAIN_EXECUTABLE" 2>&1 | grep -q "runtime" || {
    echo "ERROR: Hardened Runtime is missing from the main executable." >&2
    exit 1
}

codesign -dv --verbose=4 "$WEBENGINE_PROCESS" 2>&1 | grep -q "runtime" || {
    echo "ERROR: Hardened Runtime is missing from QtWebEngineProcess." >&2
    exit 1
}

section "Creating app ZIP for notarization"

ditto -c -k --keepParent "$FINAL_APP" "$APP_ZIP"

section "Submitting app to Apple notary service"

xcrun notarytool submit \
    "$APP_ZIP" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

section "Stapling and validating app"

xcrun stapler staple "$FINAL_APP"
xcrun stapler validate "$FINAL_APP"

section "Gatekeeper assessment for app"

spctl --assess --type execute --verbose=4 "$FINAL_APP"

section "Preparing DMG contents"

rm -rf "$DMG_STAGE_DIR"
mkdir -p "$DMG_STAGE_DIR"

ditto "$FINAL_APP" "$DMG_STAGE_DIR/$APP_NAME.app"
ln -s /Applications "$DMG_STAGE_DIR/Applications"

echo "DMG contents:"
ls -la "$DMG_STAGE_DIR"

section "Creating compressed DMG"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGE_DIR" \
    -format UDZO \
    -ov \
    "$DMG_FILE"

section "Applying custom icon to DMG file"

fileicon set "$DMG_FILE" "$ICON"
fileicon test "$DMG_FILE"

section "Signing DMG"

codesign \
    --force \
    --timestamp \
    --sign "$SIGN_IDENTITY" \
    "$DMG_FILE"

codesign --verify --verbose=4 "$DMG_FILE"

section "Submitting DMG to Apple notary service"

xcrun notarytool submit \
    "$DMG_FILE" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

section "Stapling and validating DMG"

xcrun stapler staple "$DMG_FILE"
xcrun stapler validate "$DMG_FILE"

section "Release completed successfully"

echo "App:"
echo "  $FINAL_APP"
echo
echo "DMG:"
echo "  $DMG_FILE"
echo
echo "The DMG contains:"
echo "  - $APP_NAME.app"
echo "  - Applications -> /Applications"
echo
echo "Notes:"
echo "  - The app and DMG are signed, notarized, and stapled."
echo "  - The DMG file has the Darkelf custom icon."
echo "  - Upload only $DMG_FILE to the GitHub Release assets."
echo "  - GitHub automatically provides source ZIP and TAR archives from the tag."
