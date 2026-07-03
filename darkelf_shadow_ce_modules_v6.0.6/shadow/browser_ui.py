# --------------------------------------------------
# Qt Core
# --------------------------------------------------

from PySide6.QtCore import (
    Qt,
    QSize,
    QPointF,
)

# --------------------------------------------------
# Qt Gui
# --------------------------------------------------

from PySide6.QtGui import (
    QAction,
    QColor,
    QPalette,
    QPainter,
    QPen,
    QPixmap,
    QIcon,
)

# --------------------------------------------------
# Qt Widgets
# --------------------------------------------------

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QToolBar,
    QToolButton,
    QVBoxLayout,
)

# --------------------------------------------------
# Qt WebEngine
# --------------------------------------------------

from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)

from PySide6.QtWebEngineCore import (
    QWebEnginePage,
)

from importlib import resources

# --------------------------------------------------
# Darkelf
# --------------------------------------------------

from shadow.browser_icons import (
    make_nav_arrow_icon,
    make_reload_icon,
    make_bookmark_icon,
    make_bookmark_filled_icon,
    make_find_icon,
    make_keyboard_icon,
    make_java_icon,
    make_quantum_icon,
    make_shield_icon,
    make_nuke_icon,
    make_settings_icon,
    make_source_icon,
    make_cut_icon,
    make_copy_icon,
    make_paste_icon,
    make_delete_icon,
    make_select_all_icon,
)

from shadow.browser_downloads import (
    create_color_palette_menu,
)

from shadow.darkelf_context_menu import (
    DarkelfContextMenu,
)

from shadow.settings_dialog import (
    DarkelfSettingsDialog,
)

from PySide6.QtGui import QIcon


# -----------------------------
# Icon cache
# -----------------------------
_icon_cache = {}

def cached_icon(factory, color, size):
    key = (factory.__name__, color, size)

    if key not in _icon_cache:
        _icon_cache[key] = factory(color, size)

    return _icon_cache[key]


# --------------------------------------------------
# Browser UI Mixin
# --------------------------------------------------


class BrowserUIMixin:
    """
    UI components for DarkelfBrowser.
    Handles toolbar, menus, dialogs, styling, and other
    presentation-related functionality.
    """

    # Context Menu
    def create_darkelf_menu(self):
        return DarkelfContextMenu(self, self)
        
    def _update_urlbar_style(self):
        c = self.accent_color

        self.addr.setStyleSheet(f"""
        QLineEdit {{
            background: #10131a;
            color: #eafaf0;

            border: 1px solid #252b36;
            border-radius: 12px;

            padding: 8px 12px;

            selection-background-color: {c};
            selection-color: #0a0b10;
        }}

        QLineEdit:focus {{
            border: 1px solid {c};
        }}
        """)
        
    def show_page_context_menu(self, view, pos):

        menu = self.create_darkelf_menu()

        #
        # Navigation
        #

        act = menu.addAction(
            make_nav_arrow_icon("left", self.accent_color, 18),
            "Back",
        )
        act.setEnabled(view.history().canGoBack())
        act.triggered.connect(view.back)

        act = menu.addAction(
            make_nav_arrow_icon("right", self.accent_color, 18),
            "Forward",
        )
        act.setEnabled(view.history().canGoForward())
        act.triggered.connect(view.forward)

        menu.addAction(
            make_reload_icon(self.accent_color, 18),
            "Reload",
            view.reload,
        )

        menu.section()

        menu.addAction(
            make_find_icon(self.accent_color, 18),
            "Find in Page",
            self.show_find_bar,
        )

        menu.addAction(
            make_bookmark_icon(self.accent_color, 18),
            "Bookmark Page",
            self.bookmark_current_page,
        )

        menu.section()

        menu.addSeparator()

        copy_action = menu.addAction(make_copy_icon(self.accent_color, 18), "Copy")

        copy_action.triggered.connect(
            lambda: QApplication.clipboard().setText(view.selectedText())
        )

        paste_action = menu.addAction(make_paste_icon(self.accent_color, 18), "Paste")

        paste_action.triggered.connect(
            lambda: view.page().triggerAction(QWebEnginePage.Paste)
        )

        menu.addSeparator()

        self.view_source_action = menu.addAction(
            make_source_icon(self.accent_color, 18),
            "View Source",
            lambda: self.open_source(view.url().toString()),
        )

        menu.exec(view.mapToGlobal(pos))

    def show_urlbar_context_menu(self, pos):

        menu = self.create_darkelf_menu()

        menu.addAction(
            make_nav_arrow_icon("left", self.accent_color, 18),
            "Undo",
            self.addr.undo,
        ).setEnabled(self.addr.isUndoAvailable())

        menu.addAction(
            make_nav_arrow_icon("right", self.accent_color, 18),
            "Redo",
            self.addr.redo,
        ).setEnabled(self.addr.isRedoAvailable())

        menu.section()

        menu.addAction(
            make_cut_icon(self.accent_color, 18), "Cut", self.addr.cut
        ).setEnabled(self.addr.hasSelectedText())

        menu.addAction(
            make_copy_icon(self.accent_color, 18), "Copy", self.addr.copy
        ).setEnabled(self.addr.hasSelectedText())

        menu.addAction(make_paste_icon(self.accent_color, 18), "Paste", self.addr.paste)

        menu.addAction(
            make_delete_icon(self.accent_color, 18), "Delete", self.addr.del_
        )

        menu.section()

        menu.addAction(
            make_select_all_icon(self.accent_color, 18),
            "Select All",
            self.addr.selectAll,
        )

        menu.exec(self.addr.mapToGlobal(pos))

    # Toolbar

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
        
    def _make_clear_x_icon(self, color="#ffffff", size=24):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)

        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)

        m = size * 0.25  # margin
        p.drawLine(QPointF(m, m), QPointF(size - m, size - m))
        p.drawLine(QPointF(size - m, m), QPointF(m, size - m))

        p.end()
        return QIcon(pix)
        
    def _make_toolbar(self):

        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(24, 24))

        self.menu_btn = QToolButton()

        self.menu_btn.setText("≡")
        self.menu_btn.setFixedSize(40, 40)

        self.menu_btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            color: white;
            border: none;

            font-size: 28px;
            font-weight: 900;

            padding: 0px;
            margin: 0px;
        }}

        QToolButton:hover {{
            color: {self.accent_color};
        }}
        """)

        self.menu_btn.setPopupMode(QToolButton.InstantPopup)
        self.menu_btn.setPopupMode(QToolButton.InstantPopup)

        menu = QMenu(self)

        menu.setAttribute(Qt.WA_TranslucentBackground)

        menu.setStyleSheet("""
        QMenu {
            background: #0b0f14;
            border: 1px solid #222;
            border-radius: 14px;
            padding: 8px;
        }

        QMenu::item {
            color: white;
            padding: 10px 28px 10px 14px;
            margin: 2px;
            border-radius: 10px;
        }

        QMenu::item:selected {
            background: rgba(168,85,247,0.20);
            border: 1px solid #A855F7;
            color: white;
        }

        QMenu::separator {
            height: 1px;
            background: #222;
            margin: 6px 8px;
        }
        """)

        bookmark_action = menu.addAction(
            make_bookmark_icon(self.accent_color, 20), "Bookmarks"
        )

        find_action = menu.addAction(make_find_icon(self.accent_color, 20), "Find")

        bookmark_action.triggered.connect(self.show_bookmark_manager)

        self.bookmark_action = bookmark_action
        self.find_action = find_action

        find_action.triggered.connect(self.show_find_bar)

        menu.addSeparator()

        js_action = menu.addAction(make_java_icon(self.accent_color, 16), "JavaScript")

        js_action.triggered.connect(lambda: self.java_action.trigger())

        quantum_action = menu.addAction(
            make_quantum_icon(self.accent_color, 18), "Darkelf Quantum"
        )

        quantum_action.triggered.connect(self.show_quantum_status)

        self.quantum_menu_action = quantum_action

        miniai_action = menu.addAction(
            make_shield_icon(self.accent_color, 16),
            "MiniAI Console",
            self.show_miniai_status,
        )

        menu.addSeparator()

        self.color_btn = QToolButton()
        self.color_btn.setMenu(create_color_palette_menu(self, self.set_accent_color))
        self.color_btn.setPopupMode(QToolButton.InstantPopup)

        def show_palette():
            pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())

            self.color_btn.menu().exec(pos)

        hotkeys_action = menu.addAction(
            make_keyboard_icon(self.accent_color, 22), "Keyboard Shortcuts"
        )

        hotkeys_action.triggered.connect(self.show_hotkey_help)

        menu.addSeparator()

        nuke_action = menu.addAction(
            make_nuke_icon(self.accent_color, 22), "Nuke Browser"
        )

        nuke_action.triggered.connect(self.nuke_all_data)

        self.js_menu_action = js_action
        self.miniai_menu_action = miniai_action
        self.hotkeys_action = hotkeys_action
        self.nuke_menu_action = nuke_action

        self.menu_btn.setMenu(menu)

        c = self.accent_color

        self.back_action = QAction(make_nav_arrow_icon("left", c, 22), "Back", self)
        self.fwd_action = QAction(make_nav_arrow_icon("right", c, 22), "Forward", self)
        self.reload_action = QAction(make_reload_icon(c, 22), "Reload", self)

        # update toolbar icons
        self.back_action.setIcon(make_nav_arrow_icon("left", c, 22))
        self.fwd_action.setIcon(make_nav_arrow_icon("right", c, 22))
        self.reload_action.setIcon(make_reload_icon(c, 22))

        # update menu icons

        if hasattr(self, "bookmark_action"):
            self.bookmark_action.setIcon(make_bookmark_icon(c, 20))

        if hasattr(self, "find_action"):
            self.find_action.setIcon(make_find_icon(c, 20))

        if hasattr(self, "js_menu_action"):
            self.js_menu_action.setIcon(make_java_icon(c, 16))

        if hasattr(self, "miniai_menu_action"):
            self.miniai_menu_action.setIcon(make_shield_icon(c, 16))

        if hasattr(self, "hotkeys_action"):
            self.hotkeys_action.setIcon(make_keyboard_icon(c, 22))

        if hasattr(self, "nuke_menu_action"):
            self.nuke_menu_action.setIcon(make_nuke_icon(c, 22))

        if hasattr(self, "view_source_action"):
            self.view_source_action.setIcon(make_source_icon(c, 18))

        if hasattr(self, "settings_action"):
            self.settings_action.setIcon(make_settings_icon(c, 18))

        self.java_action = QAction(
            make_java_icon(self.accent_color, 22), "JavaScript", self
        )
        self.miniai_action = QAction(
            make_shield_icon(self.accent_color, 22), "MiniAI Monitor", self
        )
        self.miniai_action.triggered.connect(self.show_miniai_status)

        self.nuke_action = QAction(make_nuke_icon(self.accent_color, 22), "Nuke", self)

        self.nuke_action.triggered.connect(self.nuke_all_data)

        menu.addSeparator()

        self.settings_action = menu.addAction(
            make_settings_icon(self.accent_color, 18),
            "Settings",
        )

        self.settings_action.triggered.connect(self.show_settings_dialog)

        self.back_action.triggered.connect(self.go_back)
        self.fwd_action.triggered.connect(self.go_fwd)
        self.reload_action.triggered.connect(self.reload)

        tb.addAction(self.back_action)
        tb.addAction(self.fwd_action)
        tb.addAction(self.reload_action)

        tb.addSeparator()
        self.addr = QLineEdit()
        self.addr.setContextMenuPolicy(Qt.CustomContextMenu)
        self.addr.customContextMenuRequested.connect(self.show_urlbar_context_menu)
        self.addr.setPlaceholderText("Search or enter URL")
        self.addr.returnPressed.connect(self.on_url_entered)

        # ADD LOCK ICON HERE
        self.lock_action = self.addr.addAction(
            self.make_outline_lock_icon("#ffffff", 24), QLineEdit.LeadingPosition
        )
        self.lock_action.setVisible(False)

        # Clear / X button — thin white X, no circle
        self.clear_action = self.addr.addAction(
            self._make_clear_x_icon(),
            QLineEdit.TrailingPosition,
        )
        
        self.clear_action.triggered.connect(self.addr.clear)

        # Hide until text exists
        self.clear_action.setVisible(False)

        # Auto show/hide
        self.addr.textChanged.connect(
            lambda text: self.clear_action.setVisible(bool(text))
        )

        self._update_urlbar_style()

        # ---- Hotkey button ----

        self.hotkey_action = QAction(
            make_keyboard_icon(self.accent_color, 18), "Hotkeys", self
        )

        self.hotkey_action.setToolTip("Keyboard Shortcuts")

        self.hotkey_action.triggered.connect(self.show_hotkey_help)

        self.java_action.setCheckable(True)
        self.java_action.setChecked(True)
        self.java_action.setToolTip("Enable/Disable JavaScript globally")

        tb.addWidget(self.addr)

        # --------------------------------
        # Bookmark Current Page
        # --------------------------------

        self.bookmark_btn = QToolButton()

        self.bookmark_btn.setIcon(make_bookmark_icon(self.accent_color, 20))

        self.bookmark_btn.setToolTip("Bookmark Current Page")

        self.bookmark_btn.setCursor(Qt.PointingHandCursor)

        self.bookmark_btn.setFixedSize(36, 36)

        self.bookmark_btn.setStyleSheet("""
        QToolButton {
            background: transparent;
            border: none;
            border-radius: 10px;
        }

        QToolButton:hover {
            background: rgba(255,255,255,.08);
        }

        QToolButton:pressed {
            background: rgba(255,255,255,.15);
        }
        """)

        self.bookmark_btn.clicked.connect(self.bookmark_current_page)

        tb.addWidget(self.bookmark_btn)

        tb.addWidget(self.menu_btn)

        def update_js_icon():
            enabled = self.java_action.isChecked()
            color = "#f89820" if enabled else "#bbbbbb"
            self.java_action.setIcon(make_java_icon(color, 18))
            self.java_action.setText("JavaScript" if enabled else "JS Off")
            self.toggle_javascript()

        self.java_action.triggered.connect(update_js_icon)

        tb.addSeparator()
        return tb

    # Toolbar UI Helpers

    def show_settings_dialog(self):
        dlg = DarkelfSettingsDialog(self)

        dlg.refresh()  # optional
        dlg.exec()

    def show_quantum_status(self):

        interceptor = getattr(
            self.shared_profile,
            "_darkelf_interceptor",
            None,
        )

        if interceptor is None or not hasattr(interceptor, "pq"):
            QMessageBox.warning(
                self,
                "Darkelf Quantum",
                "Quantum subsystem unavailable.",
            )
            return

        pq = interceptor.pq

        try:
            pq.status_info()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Darkelf Quantum",
                f"Quantum runtime unavailable:\n\n"
                f"{type(e).__name__}\n{e}",
            )
            return

        try:
            html = self._build_quantum_report_html(pq)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Darkelf Quantum",
                f"Failed to build Quantum Console:\n\n"
                f"{type(e).__name__}\n{e}",
            )
            return

        win = QDialog(self)
        win.setWindowTitle("Darkelf Quantum Console")
        win.resize(900, 600)

        layout = QVBoxLayout(win)
        layout.setContentsMargins(0, 0, 0, 0)

        view = QWebEngineView(win)

        page = QWebEnginePage(
            self.shared_profile,
            view,
        )

        view.setPage(page)

        try:
            view.setHtml(html)
    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Darkelf Quantum",
                f"Unable to display Quantum Console:\n\n"
                f"{type(e).__name__}\n{e}",
            )
            return

        layout.addWidget(view)

        win.exec()

    def show_hotkey_help(self):

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">

        <style>
        * {{
            box-sizing:border-box;
        }}

        html, body {{
            margin:0;
            padding:0;
            width:100%;
            height:100%;
            background:#07090f;
            color:white;
            font-family: Inter, system-ui, -apple-system, sans-serif;
            overflow:hidden;
        }}

        body {{
            padding:20px 22px;
        }}

        .header {{
            display:flex;
            align-items:flex-end;
            justify-content:space-between;
            margin-bottom:16px;
        }}

        h1 {{
            color:{self.accent_color};
            font-size:24px;
            margin:0;
            font-weight:900;
            letter-spacing:-.03em;
        }}

        .subtitle {{
            color:#8f99a6;
            font-size:12px;
            margin-top:4px;
        }}

        .badge {{
            color:{self.accent_color};
            border:1px solid {self.accent_color};
            background:rgba(168,85,247,.10);
            border-radius:999px;
            padding:5px 12px;
            font-size:11px;
            font-weight:800;
            letter-spacing:.08em;
        }}

        .grid {{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:12px;
        }}

        .group {{
            background:linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.025));
            border:1px solid rgba(255,255,255,.08);
            border-radius:16px;
            padding:13px 14px;
            min-height:118px;
        }}

        .title {{
            color:{self.accent_color};
            font-size:11px;
            letter-spacing:.20em;
            text-transform:uppercase;
            margin-bottom:9px;
            font-weight:900;
        }}

        .row {{
            display:grid;
            grid-template-columns:1fr auto;
            align-items:center;
            gap:12px;
            padding:7px 0;
            border-bottom:1px solid rgba(255,255,255,.055);
        }}

        .row:last-child {{
            border-bottom:none;
        }}

        .desc {{
            color:#dde3ea;
            font-size:13px;
            font-weight:600;
            white-space:nowrap;
        }}

        .keys {{
            display:flex;
            align-items:center;
            gap:4px;
            white-space:nowrap;
        }}

        .key {{
            color:{self.accent_color};
            background:rgba(168,85,247,.10);
            border:1px solid rgba(168,85,247,.55);
            border-bottom:2px solid rgba(168,85,247,.75);
            border-radius:7px;
            padding:3px 7px;
            font-size:11px;
            font-weight:900;
            line-height:1;
            min-width:22px;
            text-align:center;
        }}

        .plus {{
            color:#798291;
            font-size:11px;
            font-weight:900;
        }}

        .footer {{
            margin-top:14px;
            text-align:center;
            color:#667080;
            font-size:10px;
            font-weight:800;
            letter-spacing:.18em;
        }}
        </style>
        </head>

        <body>

            <div class="header">
                <div>
                    <h1>Keyboard Shortcuts</h1>
                    <div class="subtitle">Fast commands for Darkelf Shadow</div>
                </div>
                <div class="badge">HOTKEY ENGINE</div>
            </div>

            <div class="grid">

                <div class="group">
                    <div class="title">Tabs</div>
                    <div class="row"><div class="desc">New Tab</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">T</span></div></div>
                    <div class="row"><div class="desc">Close Tab</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">W</span></div></div>
                    <div class="row"><div class="desc">Focus URL</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">L</span></div></div>
                </div>

                <div class="group">
                    <div class="title">Navigation</div>
                    <div class="row"><div class="desc">Reload Page</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">R</span></div></div>
                    <div class="row"><div class="desc">Take Snapshot</div><div class="keys"><span class="key">Ctrl</span><span class="plus">+</span><span class="key">Shift</span><span class="plus">+</span><span class="key">S</span></div></div>
                </div>

                <div class="group">
                    <div class="title">Zoom</div>
                    <div class="row"><div class="desc">Zoom In</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">+</span></div></div>
                    <div class="row"><div class="desc">Zoom Out</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">-</span></div></div>
                    <div class="row"><div class="desc">Reset Zoom</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">0</span></div></div>
                </div>

                <div class="group">
                    <div class="title">Find</div>
                    <div class="row"><div class="desc">Find Page</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">F</span></div></div>
                    <div class="row"><div class="desc">Next Match</div><div class="keys"><span class="key">Ctrl/⌘</span><span class="plus">+</span><span class="key">G</span></div></div>
                </div>

                <div class="group">
                    <div class="title">Window</div>
                    <div class="row"><div class="desc">Fullscreen</div><div class="keys"><span class="key">F11</span><span class="plus">/</span><span class="key">Alt</span><span class="plus">+</span><span class="key">Enter</span></div></div>
                    <div class="row"><div class="desc">macOS Fullscreen</div><div class="keys"><span class="key">⌘</span><span class="plus">+</span><span class="key">Return</span></div></div>
                </div>

                <div class="group">
                    <div class="title">Notes</div>
                    <div class="row"><div class="desc">CapsLock</div><div class="keys"><span class="key">Shift</span><span class="plus">+</span><span class="key">Letter</span></div></div>
                </div>

            </div>

            <div class="footer">DARKELF SHADOW · PRIVATE BROWSER COMMANDS</div>

        </body>
        </html>
        """

        win = QDialog(self)
        win.setWindowTitle("Hotkeys")
        win.resize(900, 660)
        win.setMinimumSize(820, 600)

        layout = QVBoxLayout(win)
        layout.setContentsMargins(0, 0, 0, 0)

        view = QWebEngineView()
        view.setHtml(html)

        layout.addWidget(view)

        win.exec()

    def show_miniai_status(self):

        html = self._build_threat_report_html()

        win = QDialog(self)
        win.setWindowTitle("Darkelf MiniAI Threat Console")
        win.resize(900, 600)

        layout = QVBoxLayout(win)

        view = QWebEngineView()
        view.setHtml(html)

        layout.addWidget(view)

        win.exec()

    # Toolbar Styling

    def set_accent_color(self, color):

        self.accent_color = color.name()
        c = self.accent_color

        # update Qt highlight palette (text selection, menus, etc.)
        app = QApplication.instance()
        palette = app.palette()
        palette.setColor(QPalette.Highlight, QColor(c))
        palette.setColor(QPalette.HighlightedText, QColor("#0a0b10"))
        palette.setColor(QPalette.Link, QColor(c))
        palette.setColor(QPalette.LinkVisited, QColor(c))
        app.setPalette(palette)

        # update toolbar icons
        self.back_action.setIcon(make_nav_arrow_icon("left", c, 22))
        self.fwd_action.setIcon(make_nav_arrow_icon("right", c, 22))
        self.reload_action.setIcon(make_reload_icon(c, 22))

        if hasattr(self, "menu_btn"):

            self.menu_btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: white;
                border: none;

                font-size: 28px;
                font-weight: 900;
            }}

            QToolButton:hover {{
                color: {c};
            }}
            """)

        self._update_urlbar_style()

        # update diamond palette button
        self.color_btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            color: {c};
            border: none;
            font-size: 16px;
        }}

        QToolButton:hover {{
            color: white;
        }}
        """)

        if hasattr(self, "menu_btn") and self.menu_btn.menu():
            self.menu_btn.menu().setStyleSheet(f"""
            QMenu {{
                background: #0b0f14;
                border: 1px solid #222;
                border-radius: 14px;
                padding: 8px;
            }}

            QMenu::item {{
                color: white;
                padding: 10px 28px 10px 14px;
                margin: 2px;
                border-radius: 10px;
            }}

            QMenu::item:selected {{
                background: rgba({color.red()},{color.green()},{color.blue()},0.20);
                border: 1px solid {c};
                color: white;
            }}

            QMenu::separator {{
                height:1px;
                background:#222;
                margin:6px 8px;
            }}
            """)

        if hasattr(self, "bookmark_action"):
            self.bookmark_action.setIcon(make_bookmark_icon(c, 20))

        if hasattr(self, "find_action"):
            self.find_action.setIcon(make_find_icon(c, 20))

        if hasattr(self, "find_bar"):
            self._update_find_bar_style()

        if hasattr(self, "js_menu_action"):
            self.js_menu_action.setIcon(make_java_icon(c, 16))

        if hasattr(self, "quantum_menu_action"):
            self.quantum_menu_action.setIcon(make_quantum_icon(c, 18))

        if hasattr(self, "miniai_menu_action"):
            self.miniai_menu_action.setIcon(make_shield_icon(c, 16))

        if hasattr(self, "hotkeys_action"):
            self.hotkeys_action.setIcon(make_keyboard_icon(c, 22))

        if hasattr(self, "nuke_menu_action"):
            self.nuke_menu_action.setIcon(make_nuke_icon(c, 22))

        if hasattr(self, "settings_action"):
            self.settings_action.setIcon(make_settings_icon(c, 18))
        # Update bookmark toolbar icon
        if hasattr(self, "bookmark_btn"):
            browser = self.current_view()
            bookmarked = browser is not None and any(
                bm["url"] == browser.url().toString()
                for bm in getattr(self, "bookmarks", [])
            )

            self.bookmark_btn.setIcon(
                make_bookmark_filled_icon(c, 20)
                if bookmarked
                else make_bookmark_icon(c, 20)
            )

        if hasattr(self, "plus_btn"):
            self.plus_btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {c};
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

        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)

            js = f"""
            document.documentElement.style.setProperty('--accent', '{self.accent_color}');
            """

            try:
                view.page().runJavaScript(js)
            except Exception as e:
                print("Error:", e)
                
        self._set_tab_style()
        
    def _configure_tabbar_small(self):
        bar = self.tabs.tabBar()
        bar.setExpanding(False)
        bar.setMovable(True)
        bar.setElideMode(Qt.TextElideMode.ElideRight)
        bar.setIconSize(QSize(16, 16))
        bar.setUsesScrollButtons(True)
        bar.setStyleSheet("""
            QTabBar::tab { height: 22px; padding: 2px 8px; max-width: 140px; }
        """)
        
    def _apply_global_stylesheet(self):
        QApplication.instance().setStyleSheet("""
            QMainWindow {
                background-color: #0b0f14;
            }

            QWidget {
                background-color: #0b0f14;
                color: white;
            }

            QLineEdit {
                background-color: #111;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
            }

            QToolBar {
                background-color: #0b0f14;
                border-bottom: 1px solid #222;
            }

            QPushButton {
                background-color: #111;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
            }

            QMenu {
                background-color: #0b0f14;
                border: 1px solid #222;
                padding: 4px;
            }

            QMenu::item {
                color: #eafaf0;
                padding: 6px 18px;
            }

            QMenu::separator {
                height: 1px;
                background: #222;
                margin: 4px 6px;
            }
        """)
        
    def update_tab_icon(self, view):
        index = self.tabs.indexOf(view)

        if index == -1:
            return

        # Internal Darkelf Home page
        if getattr(view, "_is_homepage", False):
            icon_path = resources.files("shadow.assets").joinpath(
                "darkelf-mark-128.png"
            )

            self.tabs.setTabIcon(
                index,
                QIcon(str(icon_path))
            )
            return

        # Website favicon
        self.tabs.setTabIcon(index, view.icon())
            
    def _set_tab_style(self):

        if not hasattr(self, "tabs"):
            return

        c = QColor(self.accent_color)

        rgba20 = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.20)"
        rgba25 = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.25)"
        rgba35 = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.35)"

        self.tabs.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 0;
        }}

        QTabBar {{
            background: #0b0f14;
        }}

        QTabBar::tab {{
            background: transparent;
            color: #d6d9df;

            padding: 6px 14px;

            border-radius: 14px;
            border: 1px solid transparent;

            margin: 3px;
        }}

        QTabBar::tab:hover {{
            background: {rgba20};
            border: 1px solid {self.accent_color};
            color: white;
        }}

        QTabBar::tab:selected {{
            background: {rgba25};
            border: 1px solid {self.accent_color};

            color: white;
            font-weight: 700;
        }}

        QTabBar::tab:selected:hover {{
            background: {rgba35};
        }}
        
        QTabBar::close-button {{
            image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-close-16.png);
            width: 10px;
            height: 10px;
            padding: 2px;
            background: transparent;
            border: none;
        }}

        QTabBar::close-button:hover {{
            background: transparent;
        }}
        """)

    # ------------------------------------------------
    # BOOKMARK CURRENT PAGE
    # ------------------------------------------------

    def bookmark_current_page(self):

        if not hasattr(self, "bookmarks"):
            self.bookmarks = []

        browser = self.current_view()

        if browser is None:
            return

        title = browser.title().strip() or "Untitled"
        url = browser.url().toString().strip()

        if not url:
            return

        # Already bookmarked
        for bm in self.bookmarks:
            if bm["url"] == url:

                self.bookmark_btn.setIcon(
                    make_bookmark_filled_icon(self.accent_color, 20)
                )

                self.bookmark_btn.setToolTip("Already bookmarked")

                return

        # Add bookmark
        self.bookmarks.insert(
            0,
            {
                "title": title,
                "url": url,
                "icon": browser.icon(),
            },
        )

        self.update_bookmark_icon()

        if hasattr(self, "bookmark_manager"):
            self.refresh_bookmark_manager()

        if hasattr(self, "bookmark_bar"):
            self.refresh_bookmark_bar()

        if hasattr(self, "refresh_bookmark_manager"):
            self.refresh_bookmark_manager()

        # Update toolbar icon
        self.bookmark_btn.setIcon(make_bookmark_filled_icon(self.accent_color, 20))

        self.bookmark_btn.setToolTip("Bookmarked")

        if hasattr(self, "refresh_bookmark_manager"):
            self.refresh_bookmark_manager()

    # --------------------------------
    # UPDATE BOOKMARK BUTTON
    # --------------------------------

    def update_bookmark_icon(self):

        browser = self.current_view()

        if browser is None:
            return

        url = browser.url().toString()

        bookmarked = any(bm["url"] == url for bm in getattr(self, "bookmarks", []))

        if bookmarked:

            self.bookmark_btn.setIcon(make_bookmark_filled_icon(self.accent_color, 20))

            self.bookmark_btn.setToolTip("Bookmarked")

        else:

            self.bookmark_btn.setIcon(make_bookmark_icon(self.accent_color, 20))

            self.bookmark_btn.setToolTip("Bookmark this page")
