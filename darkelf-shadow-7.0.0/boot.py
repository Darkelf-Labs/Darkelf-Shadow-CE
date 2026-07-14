# shadow/boot.py

from PySide6.QtCore import QThread, Signal, QPropertyAnimation
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineScript,
)

from shadow.filters import EasyListEngine, EASYLIST_URLS
from shadow.miniai import DarkelfMiniAISentinel
from shadow.browser import DarkelfBrowser
from shadow.interceptor import StealthInterceptor


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

            self.progress.emit(55, "Downloading filters...")
            engine.load_and_build(EASYLIST_URLS)

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

import traceback


def boot_done(splash, app, engine, ai):

    try:
        app.setQuitOnLastWindowClosed(True)

        # -----------------------------
        # PROFILE SETUP (FINAL FIX)
        # -----------------------------

        # 🔥 CRITICAL: empty storage name = off-the-record in PySide6
        profile = QWebEngineProfile("", app)

        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

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
        
        app._browser = browser

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
