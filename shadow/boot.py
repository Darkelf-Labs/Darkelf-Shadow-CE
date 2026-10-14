# shadow/boot.py

from PySide6.QtCore import QThread, Signal, QPropertyAnimation, QUrl
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineScript,
)

from shadow.filters import EasyListEngine, EASYLIST_URLS
from shadow.miniai import DarkelfMiniAISentinel
from shadow.browser import DarkelfBrowser
from shadow.interceptor import StealthInterceptor


import sys
import platform
import traceback
import plistlib
from pathlib import Path
from xml.parsers.expat import ExpatError

def _is_native_darkelf_app():
    """Select native authentication storage only for the Darkelf app bundle.

    A standard PyPI or main.py launch must stay off the record, including on
    Apple Silicon. Bundle identification selects a distribution mode; it is
    not a code-signature or engine-patch verification.
    """
    if sys.platform != "darwin" or platform.machine().lower() != "arm64":
        return False

    candidates = [sys.executable]
    if sys.argv:
        candidates.append(sys.argv[0])

    for candidate in candidates:
        if not candidate:
            continue
        try:
            executable = Path(candidate).resolve()
            macos_dir = executable.parent
            contents_dir = macos_dir.parent
            bundle_dir = contents_dir.parent
            if (
                macos_dir.name != "MacOS"
                or contents_dir.name != "Contents"
                or bundle_dir.suffix.lower() != ".app"
                or not executable.is_file()
            ):
                continue
            with (contents_dir / "Info.plist").open("rb") as stream:
                info = plistlib.load(stream)
            if (
                isinstance(info, dict)
                and info.get("CFBundleIdentifier") == "com.darkelfbrowser.shadow"
                and info.get("CFBundleExecutable") == executable.name
            ):
                return True
        except (OSError, ValueError, plistlib.InvalidFileException, ExpatError):
            # Missing/unreadable bundle metadata defaults to ephemeral storage.
            continue

    return False


# ------------------ BOOT WORKER ------------------

class BootWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(object, object)  # engine, ai

    def run(self):
        try:
            # ---- INIT ----
            self.progress.emit(5, "Initializing environment...")

            # ---- FILTERS ----
            self.progress.emit(50, "Loading filter engine...")
            engine = EasyListEngine()

            engine.load_and_build(EASYLIST_URLS, progress=self.progress.emit)

            self.progress.emit(65, "Filters ready")

            # ---- MINI AI ----
            self.progress.emit(70, "Starting MiniAI...")
            ai = DarkelfMiniAISentinel()

            # ---- FINAL ----
            self.progress.emit(90, "Preparing UI...")
            self.msleep(200)

            self.progress.emit(100, "Launching...")

            self.finished.emit(engine, ai)

        except Exception as e:
            print("BOOT ERROR:", e)


# ------------------ UI UPDATE ------------------

def update_progress(splash, val, text):
    splash.status.setText(text)

    anim = QPropertyAnimation(splash.bar, b"value")
    anim.setDuration(300)
    anim.setStartValue(splash.bar.value())
    anim.setEndValue(val)
    anim.start()

    splash._anim = anim  # prevent GC


# ------------------ BOOT DONE ------------------

def boot_done(splash, app, engine, ai):

    try:
        app.setQuitOnLastWindowClosed(True)

        # -----------------------------
        # DISTRIBUTION-AWARE PROFILE SETUP
        # -----------------------------

        if _is_native_darkelf_app():
            # Native DMG app: named profile for custom-engine authentication.
            profile = QWebEngineProfile("Darkelf", app)
        else:
            # PyPI, source launches and other standard builds: off the record.
            profile = QWebEngineProfile(app)

        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

        # Force English for server-side content negotiation
        profile.setHttpAcceptLanguage("en-US,en;q=0.9")
        # -----------------------------
        # SETTINGS
        # -----------------------------
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        
        # -----------------------------
        # GLOBAL SCRIPT INJECTION
        # -----------------------------
        script = QWebEngineScript()

        script.setName("darkelf_global_patch")
        script.setInjectionPoint(
            QWebEngineScript.DocumentCreation
        )
        script.setWorldId(
            QWebEngineScript.MainWorld
        )
        script.setRunsOnSubFrames(True)

        #
        # Reserved for future browser-wide
        # privacy patches and JS hardening.
        #
        script.setSourceCode("")

        profile.scripts().insert(script)
        
        # -----------------------------
        # INTERCEPTOR
        # -----------------------------
        interceptor = StealthInterceptor(engine, ai)
        profile.setUrlRequestInterceptor(interceptor)

        profile._darkelf_interceptor = interceptor

        app._profile = profile
        app._interceptor = interceptor

        # -----------------------------
        # CREATE BROWSER
        # -----------------------------

        browser = DarkelfBrowser(profile, ai, engine)

        interceptor.browser = browser

        # Existing reference
        app._browser = browser

        # Reference used by BrowserApplication.event()
        app.browser_window = browser

        # Handle URLs passed on initial launch

        for arg in sys.argv[1:]:
            if arg.startswith(("http://", "https://")):
                browser.open_url(QUrl(arg))
                break

        # -----------------------------
        # SHOW WINDOW
        # -----------------------------

        browser.show()
        browser.raise_()
        browser.activateWindow()

        browser.repaint()
        browser.update()

        # -----------------------------
        # CLOSE SPLASH LAST
        # -----------------------------
        fade = QPropertyAnimation(
            splash,
            b"windowOpacity",
        )

        fade.setDuration(300)

        fade.setStartValue(1)

        fade.setEndValue(0)

        fade.finished.connect(splash.close)

        fade.start()

        splash._fade = fade
        

    except Exception as e:
        print("BROWSER CRASH:", e)
        traceback.print_exc()

