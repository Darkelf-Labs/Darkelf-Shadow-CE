# shadow/browser.py

# --- Standard ---
import os
import sys
import json
import re
import secrets
import urllib.request
from urllib.parse import quote_plus
import urllib.parse
import urllib.request

# --- Qt Core ---
from PySide6.QtCore import (
    Qt,
    QUrl,
    QTimer,
    QEvent,
    QSize,
)

# --- Qt GUI ---
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QShortcut,
    QKeySequence,
)

# --- Qt Widgets ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QToolButton,
    QVBoxLayout,
    QTabWidget,
)

# --- Qt WebEngine ---
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
)

# --- Temporary legacy bridge (to be removed later) ---
from shadow.utils import (
    sanitize_url_clearurls,
    DUCK_LITE_HTTPS,
    BOOTUP_CANVAS_SEED,
)


from shadow.browser_downloads import (
    DownloadShelf,
)

from shadow.browser_page import HardenedWebPage
from shadow.browser_homepage import HOMEPAGE

from shadow.browser_ui import BrowserUIMixin
from shadow.browser_features import BrowserFeaturesMixin

devnull = open(os.devnull, "w")
os.dup2(devnull.fileno(), sys.stderr.fileno())

# --------------------------------------------------
# Homepage Themes
# --------------------------------------------------

HOMEPAGE_THEMES = {
    "Aurora": ("#6D28D9", "#A855F7", "#14B8A6"),
    "Nebula": ("#0A2A66", "#0050B3", "#7C3AED"),
    "Void": ("#050505", "#121212", "#2B2B2B"),
    "Matrix": ("#003A1A", "#00AA44", "#00FF66"),
    "Circuit": ("#032D4B", "#0E7490", "#22D3EE"),
    "Graded": ("#1F2937", "#475569", "#9CA3AF"),
}


# ------------------------------------------------
# Main browser class
# ------------------------------------------------
class DarkelfBrowser(BrowserUIMixin, BrowserFeaturesMixin, QMainWindow):
    def __init__(self, profile, mini_ai, engine):
        super().__init__()

        self.accent_color = "#A855F7"

        self.homepage_theme = ""

        self.setWindowTitle("")
        self.resize(1200, 800)

        # ✅ macOS FIX

        self.setUnifiedTitleAndToolBarOnMac(False)

        self.setStyleSheet("""
        QMainWindow {
            background-color: #000000;
        }

        QToolBar {
            background-color: #000000;
            border: none;
        }
        """)

        self.shared_profile = profile
        print("OffTheRecord:", self.shared_profile.isOffTheRecord())

        # ✅ SET THESE FIRST (before ANY use)
        self.easy = engine
        self.mini_ai = mini_ai
        self.mini_ai.ui = self

        self.lockdown_timer = QTimer()

        self.lockdown_timer.timeout.connect(self.mini_ai.check_lockdown_timeout)

        self.lockdown_timer.start(1000)

        print("Loaded network rules:", len(self.easy.network_rules))

        # -----------------------------
        # Session Bookmarks
        # -----------------------------
        self.bookmarks = []

        # -----------------------------
        # TABS
        # -----------------------------
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(False)  # 🔥 IMPORTANT

        self.tabs.setIconSize(QSize(18, 18))
        # + button on tab bar
        self.plus_btn = QToolButton()

        self.plus_btn.setText("+")
        self.plus_btn.setCursor(Qt.PointingHandCursor)

        # slightly tighter sizing
        self.plus_btn.setFixedSize(32, 32)

        # better alignment
        self.plus_btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            color: {self.accent_color};
            border: none;

            font-size: 22px;
            font-weight: 400;

            padding-bottom: 4px;
            padding-right: 6px;
        }}

        QToolButton:hover {{
            color: white;
        }}
        """)

        self.plus_btn.clicked.connect(lambda: self._add_tab(home=True))

        self.tabs.setCornerWidget(self.plus_btn, Qt.TopRightCorner)

        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        self._apply_global_stylesheet()
        # -----------------------------
        # DOWNLOAD SHELF
        # -----------------------------
        self.download_shelf = DownloadShelf()
        self.download_shelf.hide()

        # -----------------------------
        # TOOLBAR (CREATE HERE)
        # -----------------------------
        self.toolbar = self._make_toolbar()

        # 🔥 THIS IS CRITICAL
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # -----------------------------
        # LAYOUT (NO TOOLBAR HERE)
        # -----------------------------
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        container = QWidget()

        self._create_find_bar()

        # Browser shortcuts must also work while Find Bar has focus
        self.find_bar.installEventFilter(self)

        for child in self.find_bar.findChildren(QWidget):
            child.installEventFilter(self)

        layout.addWidget(self.find_bar)
        layout.addWidget(self.tabs)
        layout.addWidget(self.download_shelf)

        container.setLayout(layout)
        self.setCentralWidget(container)
        # -----------------------------
        # STYLING
        # -----------------------------
        self._set_tab_style()
        self.set_accent_color(QColor(self.accent_color))

        # -----------------------------
        # STARTUP TAB
        # -----------------------------
        QApplication.instance().aboutToQuit.connect(self._cleanup_webengine)
        self._add_tab(home=True)

        # -----------------------------
        # DOWNLOADS
        # -----------------------------
        # Download folder is created lazily only when a download starts.
        self._download_dir = None
        self._downloaded_files: list[str] = []
        self._hook_secure_downloads()

        QApplication.instance().aboutToQuit.connect(self._wipe_download_traces)

        # -----------------------------
        # HOTKEYS
        # -----------------------------
        self._actions = []

        self.addr.installEventFilter(self)

        # -----------------------------
        # MINI AI TIMER
        # -----------------------------
        self.miniai_timer = QTimer()
        self.miniai_timer.start(1500)

        # -----------------------------
        # MEMORY CLEANUP
        # -----------------------------
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.memory_cleanup)

        self.maintenance_timer = QTimer(self)
        self.maintenance_timer.timeout.connect(self.memory_cleanup)
        self.maintenance_timer.start(300000)

        self.renderer_cleanup_timer = QTimer(self)
        self.renderer_cleanup_timer.timeout.connect(self.release_renderer_memory)
        self.renderer_cleanup_timer.start(600000)
        
        self.darkelf_inspector = None
            
    def new_tab(self):
        self._add_tab(home=True)
        self.debounce_cleanup()

        if self.darkelf_inspector is not None:
            self.darkelf_inspector.webview = self.current_view()
            
    def reload_page(self):
        view = self.tabs.currentWidget()
        if view:
            view.reload()

    def on_url_entered(self):
        text = self.addr.text().strip()

        if not text:
            return

        has_scheme = (
            re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text)
            is not None
        )

        looks_like_domain = (
            re.match(r"^[\w.-]+\.[A-Za-z]{2,}(/|$)", text)
            is not None
        )

        looks_like_ip_or_local = (
            re.match(
                r"^(localhost|(?:\d{1,3}\.){3}\d{1,3})"
                r"(:\d+)?(/|$)?$",
                text,
            )
            is not None
        )

        if has_scheme:
            url = text

        elif looks_like_domain or looks_like_ip_or_local:
            url = "https://" + text

        else:
            base = DUCK_LITE_HTTPS
            url = base + "?q=" + quote_plus(text)

        # Sanitize URL
        url = sanitize_url_clearurls(url)

        # Load search/URL in CURRENT tab
        view = self.tabs.currentWidget()

        if view is not None:
            view.load(QUrl(url))
        else:
            # Only create a tab if no tab currently exists
            self._add_tab(url=url)

    def eventFilter(self, obj, event):
        if QApplication.activeWindow() is not self:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.ShortcutOverride:
            key = event.key()
            mods = event.modifiers()

            ctrl = bool(mods & Qt.ControlModifier)
            meta = bool(mods & Qt.MetaModifier)
            shift = bool(mods & Qt.ShiftModifier)
            alt = bool(mods & Qt.AltModifier)

            # On this macOS/Qt build Command is arriving as
            # ControlModifier, so support both.
            primary = ctrl or meta

            # New Tab
            if primary and key == Qt.Key_T:
                self.new_tab()
                event.accept()
                return True

            # Close Tab
            if primary and key == Qt.Key_W:
                self.close_tab(self.tabs.currentIndex())
                event.accept()
                return True

            # Reload
            if primary and key == Qt.Key_R:
                self.reload_page()
                event.accept()
                return True

            # Find
            if primary and key == Qt.Key_F:
                self.show_find_bar()
                event.accept()
                return True

            # Find Next / Previous
            if primary and key == Qt.Key_G:
                if shift:
                    self.find_previous()
                else:
                    self.find_next()

                event.accept()
                return True

            # Focus URL Bar
            if primary and key == Qt.Key_L:
                self.addr.setFocus()
                self.addr.selectAll()
                event.accept()
                return True

            # Zoom In
            if primary and key in (Qt.Key_Equal, Qt.Key_Plus):
                self.zoom_in()
                event.accept()
                return True

            # Zoom Out
            if primary and key == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
                return True

            # Reset Zoom
            if primary and key == Qt.Key_0:
                self.reset_zoom()
                event.accept()
                return True

            # Snapshot - Cmd/Ctrl + Shift + S
            if primary and shift and key == Qt.Key_S:
                self.take_snapshot()
                event.accept()
                return True

            # Fullscreen
            if key == Qt.Key_F11:
                self.toggle_fullscreen()
                event.accept()
                return True

            if alt and key in (Qt.Key_Return, Qt.Key_Enter):
                self.toggle_fullscreen()
                event.accept()
                return True

        # ==================================================
        # NORMAL KEY PRESS PATH
        # Keep this because URL bar / other Qt widgets
        # deliver normal KeyPress events.
        # ==================================================
        if event.type() == QEvent.KeyPress:
            key = event.key()
            mods = event.modifiers()
            text = event.text()

            ctrl = bool(mods & Qt.ControlModifier)
            meta = bool(mods & Qt.MetaModifier)
            shift = bool(mods & Qt.ShiftModifier)
            alt = bool(mods & Qt.AltModifier)

            primary = ctrl or meta

            # New Tab
            if primary and key == Qt.Key_T:
                self.new_tab()
                return True

            # Close Tab
            if primary and key == Qt.Key_W:
                self.close_tab(self.tabs.currentIndex())
                return True

            # Reload
            if primary and key == Qt.Key_R:
                self.reload_page()
                return True

            # Find
            if primary and key == Qt.Key_F:
                self.show_find_bar()
                return True

            # Find Next / Previous
            if primary and key == Qt.Key_G:
                if shift:
                    self.find_previous()
                else:
                    self.find_next()
                return True

            # URL Bar
            if primary and key == Qt.Key_L:
                self.addr.setFocus()
                self.addr.selectAll()
                return True

            # Escape URL bar back to webpage
            if key == Qt.Key_Escape and self.addr.hasFocus():
                v = self.current_view()
                if v:
                    v.setFocus()
                return True

            # Tab switching
            if ctrl and key == Qt.Key_Tab:
                if shift:
                    self.prev_tab()
                else:
                    self.next_tab()
                return True

            if ctrl and key == Qt.Key_PageDown:
                self.next_tab()
                return True

            if ctrl and key == Qt.Key_PageUp:
                self.prev_tab()
                return True

            # Zoom In
            if primary and (
                key in (Qt.Key_Plus, Qt.Key_Equal)
                or text in ("+", "=")
            ):
                self.zoom_in()
                return True

            # Zoom Out
            if primary and (
                key == Qt.Key_Minus
                or text == "-"
            ):
                self.zoom_out()
                return True

            # Reset Zoom
            if primary and (
                key == Qt.Key_0
                or text == "0"
            ):
                self.reset_zoom()
                return True

            # Snapshot
            if primary and shift and key == Qt.Key_S:
                self.take_snapshot()
                return True

            # Fullscreen
            if key == Qt.Key_F11:
                self.toggle_fullscreen()
                return True

            if alt and key in (Qt.Key_Return, Qt.Key_Enter):
                self.toggle_fullscreen()
                return True

        return super().eventFilter(obj, event)

    def make_outline_lock_icon(self, color="#ffffff", size=24):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)

        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidth(2)
        p.setPen(pen)

        body_w = size * 0.42
        body_h = size * 0.34

        x = (size - body_w) / 2
        y = size * 0.48

        p.drawRoundedRect(x, y, body_w, body_h, 2, 2)

        p.drawArc(int(x), int(size * 0.18), int(body_w), int(size * 0.50), 0, 180 * 16)

        p.end()
        return QIcon(pix)

    @staticmethod
    def _short_label_from_qurl(qurl):
        try:
            host = qurl.host().lower() if hasattr(qurl, "host") else ""
        except Exception as e:
            print(e)
            host = ""
        if not host:
            return "Home"
        aliases = {
            "youtube.com": "YouTube",
            "www.youtube.com": "YouTube",
            "youtu.be": "YouTube",
            "bbc.com": "BBC",
            "www.bbc.com": "BBC",
            "bbc.co.uk": "BBC",
            "www.bbc.co.uk": "BBC",
            "github.com": "GitHub",
            "twitter.com": "Twitter",
            "x.com": "Twitter",
            "reddit.com": "Reddit",
            "www.reddit.com": "Reddit",
            "duckduckgo.com": "DuckDuckGo",
        }
        if host in aliases:
            return aliases[host]
        if host.startswith("www."):
            host = host[4:]
        parts = host.split(".")
        base = parts[-2] if len(parts) >= 2 else host
        return base.capitalize()

    def _add_tab(self, url=None, home=False):
        profile = self.shared_profile
        tab_seed = secrets.randbits(32) & 0xFFFFFFFF
        canvas_seed = tab_seed ^ BOOTUP_CANVAS_SEED

        view = QWebEngineView(self)
        view.setFocusPolicy(Qt.StrongFocus)
        view.installEventFilter(self)
        view._profile = profile
        
        # Darkelf custom page context menu
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(
            lambda pos, v=view: self.show_page_context_menu(v, pos)
        )
        
        page = HardenedWebPage(view, profile, canvas_seed=canvas_seed)
        page._parent_view = view
        view.setPage(page)
        
        # Capture shortcuts from WebEngine's internal focus widget too
        # Install browser shortcut filter throughout WebEngine.
        # This keeps Cmd+T/W/R/F/G/L working when the webpage owns focus.
        def install_webengine_key_filters(v=view):
            v.installEventFilter(self)

            proxy = v.focusProxy()
            if proxy is not None:
                proxy.installEventFilter(self)

            for child in v.findChildren(QWidget):
                child.installEventFilter(self)

        # WebEngine creates internal widgets asynchronously.
        QTimer.singleShot(0, install_webengine_key_filters)
        QTimer.singleShot(250, install_webengine_key_filters)
        QTimer.singleShot(1000, install_webengine_key_filters)
        
        
        page.fullScreenRequested.connect(self.handle_fullscreen)

        # --------------------------------
        # Keep bookmark icon synchronized
        # --------------------------------

        view.urlChanged.connect(lambda *_: self.update_bookmark_icon())

        view.loadFinished.connect(lambda *_: self.update_bookmark_icon())

        view.titleChanged.connect(lambda *_: self.update_bookmark_icon())
            
        # ---- EasyList Cosmetic Injection ----
        def apply_easylist_cosmetics(v=view):
            try:
                host = v.url().host().lower()
            except Exception as e:
                print(e)
                return

            if not host:
                return

            css = self.easy.css_for_host(host)
            if not css:
                return

            js = """
            (function() {
              try {
                const style = document.createElement('style');
                style.type = 'text/css';
                style.textContent = %s;
                (document.head || document.documentElement || document.body).appendChild(style);
              } catch(e) {}
            })();
            """ % json.dumps(css)

            v.page().runJavaScript(js)

        # Inject once after page load
        view.loadFinished.connect(
            lambda ok, v=view: apply_easylist_cosmetics(v) if ok else None
        )
        
        # Auto-focus URL bar after page finishes loading
       # def focus_urlbar_after_load(ok):
       #     if ok:
       #         self.addr.setFocus()
        #        self.addr.selectAll()

        #view.loadFinished.connect(focus_urlbar_after_load)
        idx = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)

        self.tabs.currentChanged.connect(lambda *_: self.update_bookmark_icon())

        view.urlChanged.connect(self._sync_urlbar)

        def relabel_from_url(qurl, view=view):
            i = self.tabs.indexOf(view)
            if i != -1:
                self.tabs.setTabText(i, self._short_label_from_qurl(qurl))

        view.urlChanged.connect(relabel_from_url)

        def set_icon(icon, view=view):
            i = self.tabs.indexOf(view)
            if i != -1:
                self.tabs.setTabIcon(i, icon)

        view.iconChanged.connect(
            lambda _, v=view: self.update_tab_icon(v)
        )

        view.urlChanged.connect(
            lambda _, v=view: self.update_tab_icon(v)
        )

        if home:
            bg1, bg2, bg3 = HOMEPAGE_THEMES.get(
                self.homepage_theme, HOMEPAGE_THEMES["Nebula"]
            )

            html = (
                HOMEPAGE.replace("ACCENT_COLOR", self.accent_color)
                .replace("BG1", bg1)
                .replace("BG2", bg2)
                .replace("BG3", bg3)
            )

            view.setHtml(html)
            view._is_homepage = True

            view.loadFinished.connect(
                lambda *_,
                v=view: self.update_tab_icon(v)
            )
            
        elif url and url.startswith("view-source:"):
            real_url = url.replace("view-source:", "")
            view.load(QUrl(real_url))
            view.page().toHtml(lambda html: self._show_source_tab(html))

        else:
            view.load(QUrl(url or "https://duckduckgo.com/lite/"))

            # ---- Accent Color Injection ----

        def apply_accent(v):
            js = f"""
            try {{
                document.documentElement.style.setProperty('--accent', '{self.accent_color}');
            }} catch(e) {{}}
            """
            v.page().runJavaScript(js)

        view.loadFinished.connect(lambda ok, v=view: apply_accent(v) if ok else None)

    def _show_source_tab(self, html):
        view = QWebEngineView(self)
        view.setHtml(
            f"<pre style='white-space:pre-wrap;font-family:monospace'>{html.replace('<','&lt;')}</pre>"
        )
        idx = self.tabs.addTab(view, "Source")
        self.tabs.setCurrentIndex(idx)

    def open_source(self, url):
        """
        Open the HTML source of the current page.

        Only HTTP and HTTPS URLs are permitted.
        """

        try:
            parsed = urllib.parse.urlparse(url)

            # Only allow web pages.
            if parsed.scheme.lower() not in ("http", "https"):
                raise ValueError(f"Blocked unsupported URL scheme: {parsed.scheme}")

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

            # Safe because the scheme has already been validated.
            with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310
                html = response.read().decode("utf-8", errors="replace")

            self._show_source_tab(html)

        except Exception as e:
            self._show_source_tab(f"<h2>Unable to load source</h2><pre>{e}</pre>")

    def close_tab(self, idx=None):
        if idx is None:
            idx = self.tabs.currentIndex()

        if idx < 0:
            return

        w = self.tabs.widget(idx)

        self.tabs.removeTab(idx)

        if isinstance(w, QWebEngineView):
            try:
                w.page().runJavaScript(
                    "document.querySelectorAll('video,audio').forEach(m=>{try{m.pause();m.src='';}catch(e){}})"
                )
            except Exception as e:
                print(f"[Darkelf] Failed to stop media cleanup: {e}")

            try:
                w.page().triggerAction(QWebEnginePage.Stop)
                w.page().setAudioMuted(True)
                w.setUrl(QUrl("about:blank"))
            except Exception as e:
                print(f"[Darkelf] Failed to clean up WebEngine page: {e}")
                
            w.page().deleteLater()
            w.deleteLater()

        if self.tabs.count() == 0:
            self._add_tab(home=True)

        new_view = self.current_view()
        if new_view:
            new_view.setFocus()

        self.debounce_cleanup()

    def next_tab(self):
        count = self.tabs.count()
        if count <= 1:
            return

        self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % count)

        v = self.current_view()
        if v:
            v.setFocus()

    def prev_tab(self):
        count = self.tabs.count()
        if count <= 1:
            return

        self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % count)

        v = self.current_view()
        if v:
            v.setFocus()
        
    def reset_zoom(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(1.0)

    def _cleanup_webengine(self):

        self._destroy_quantum_state()

        # Close tabs from last to first
        for i in reversed(range(self.tabs.count())):
            self.close_tab(i)

    def handle_fullscreen(self, request):
        if request.toggleOn():
            self.showFullScreen()
        else:
            self.showNormal()

        request.accept()

    def _close_tab_current(self):
        self.close_tab(self.tabs.currentIndex())

    def current_view(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def go_back(self):
        v = self.current_view()
        if v:
            v.back()

    def go_fwd(self):
        v = self.current_view()
        if v:
            v.forward()

    def reload(self):
        v = self.current_view()
        if v:
            v.reload()

    def go_home(self):
        v = self.current_view()
        if not v:
            return

        bg1, bg2, bg3 = HOMEPAGE_THEMES.get(
            self.homepage_theme, HOMEPAGE_THEMES["Nebula"]
        )

        html = (
            HOMEPAGE.replace("ACCENT_COLOR", self.accent_color)
            .replace("BG1", bg1)
            .replace("BG2", bg2)
            .replace("BG3", bg3)
        )

        v.setHtml(html)
        v._is_homepage = True

    def refresh_homepage(self):
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)

            if getattr(view, "_is_homepage", False):

                bg1, bg2, bg3 = HOMEPAGE_THEMES.get(
                    self.homepage_theme, HOMEPAGE_THEMES["Aurora"]
                )

                html = (
                    HOMEPAGE.replace("ACCENT_COLOR", self.accent_color)
                    .replace("BG1", bg1)
                    .replace("BG2", bg2)
                    .replace("BG3", bg3)
                )

                view.setHtml(html)

    def zoom_in(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(v.zoomFactor() + 0.1)

    def zoom_out(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(v.zoomFactor() - 0.1)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _sync_urlbar(self, url=None):
        v = self.current_view()
        if not v:
            return

        qurl = v.url() if url is None else url
        u = qurl.toString()

        if u.startswith("data:text/html"):
            self.addr.setText("")
            self.lock_action.setVisible(False)
            return

        self.addr.setText(u)

        if qurl.scheme() == "https":
            self.lock_action.setVisible(True)
        else:
            self.lock_action.setVisible(False)

    def closeEvent(self, event):
        try:
            if hasattr(self, "mini_ai"):
                self.mini_ai.shutdown()
        except Exception as e:
            print("[MiniAI] shutdown error:", e)

        super().closeEvent(event)

