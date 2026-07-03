# shadow/browser_features.py

import gc
import html
import os
import shutil
import time

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtGui import (
    QColor,
)

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)

from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)

from shadow.browser_icons import (
    make_shield_icon,
)

from shadow.utils import (
    _randomized_filename,
)

# --------------------------------------------------
# Browser Features Mixin
# --------------------------------------------------


class BrowserFeaturesMixin:
    """
    Browser feature implementations for DarkelfBrowser.

    This mixin contains optional browser capabilities:
    - Bookmarks
    - Find in Page
    - MiniAI
    - Downloads
    - Memory cleanup
    - Snapshots
    - JavaScript
    - Nuke Browser
    """

    # ------------------------------------------------
    # BOOKMARK CARD
    # ------------------------------------------------

    def _create_bookmark_card(self, bookmark):

        title = bookmark["title"]
        url = bookmark["url"]

        card = QFrame()

        card.setStyleSheet(f"""
        QFrame {{
            background:#11161d;
            border:1px solid #242b36;
            border-radius:16px;
        }}

        QLabel {{
            background:transparent;
            color:white;
        }}

        QPushButton {{
            background:#1a2028;
            border:1px solid #313b48;
            border-radius:10px;
            color:white;
            padding:6px 16px;
        }}

        QPushButton:hover {{
            border:1px solid {self.accent_color};
        }}
        """)

        outer = QVBoxLayout(card)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(10)

        top = QHBoxLayout()

        icon = QLabel()
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignCenter)

        fav = bookmark.get("icon")

        if fav and not fav.isNull():
            icon.setPixmap(fav.pixmap(32, 32))
        else:
            icon.setText("🌐")
            icon.setStyleSheet(f"""
                background:{self.accent_color};
                color:black;
                border-radius:21px;
                font-size:18px;
                font-weight:bold;
            """)

        labels = QVBoxLayout()

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            font-size:16px;
            font-weight:700;
            color:white;
        """)

        url_lbl = QLabel(url)
        url_lbl.setStyleSheet("""
            color:#8f99a6;
            font-size:12px;
        """)

        labels.addWidget(title_lbl)
        labels.addWidget(url_lbl)

        top.addWidget(icon)
        top.addSpacing(12)
        top.addLayout(labels)
        top.addStretch()

        outer.addLayout(top)

        buttons = QHBoxLayout()
        buttons.addStretch()

        open_btn = QPushButton("Open")
        remove_btn = QPushButton("Remove")

        buttons.addWidget(open_btn)
        buttons.addWidget(remove_btn)

        outer.addLayout(buttons)

        open_btn.clicked.connect(lambda: self.navigate_to(url))

        remove_btn.clicked.connect(lambda: self.remove_bookmark(card, title, url))

        return card

        # ------------------------------------------------
        # REFRESH BOOKMARK LIST
        # ------------------------------------------------

    def refresh_bookmark_manager(self):

        if getattr(self, "bookmark_cards", None) is None:
            return

        if not hasattr(self, "bookmarks"):
            self.bookmarks = []

        while self.bookmark_cards.count() > 1:

            item = self.bookmark_cards.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

        if not getattr(self, "bookmarks", None):

            empty = QLabel("No bookmarks yet.\n\nSave your favorite websites here.")

            empty.setAlignment(Qt.AlignCenter)

            empty.setStyleSheet("""
                color:#7b8592;
                font-size:15px;
                padding:50px;
            """)

            self.bookmark_cards.insertWidget(0, empty)

            return

        for bm in self.bookmarks:

            card = self._create_bookmark_card(bm)

            self.bookmark_cards.insertWidget(0, card)

    # ------------------------------------------------
    # BOOKMARK MANAGER (Darkelf Style)
    # ------------------------------------------------

    def show_bookmark_manager(self):
        if hasattr(self, "_bookmark_dialog"):
            try:
                self._bookmark_dialog.close()
            except Exception as e:
                print(f"Unable to close bookmark dialog: {e}")

        dlg = QDialog(self)
        self._bookmark_dialog = dlg
        dlg.resize(820, 700)
        dlg.setWindowTitle("Bookmarks")

        dlg.setStyleSheet(f"""
        QDialog {{
            background:#0b0e14;
        }}

        QLabel {{
            color:#e8edf5;
            background:transparent;
        }}

        QFrame#panel {{
            background:#111722;
            border:1px solid #242e3b;
            border-radius:14px;
        }}

        QFrame#listCard {{
            background:#0f1520;
            border:1px solid #212a36;
            border-radius:12px;
        }}

        QPushButton {{
            background:#141b27;
            color:#e8edf5;
            border:1px solid #2b3646;
            border-radius:10px;
            padding:8px 14px;
        }}

        QPushButton:hover {{
            border:1px solid {self.accent_color};
        }}

        QPushButton#accent {{
            background:{self.accent_color};
            color:#05070b;
            font-weight:700;
            border:none;
        }}

        QScrollArea {{
            border:none;
            background:transparent;
        }}
        """)

        root = QVBoxLayout(dlg)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)

        # Header
        title = QLabel("Bookmarks")
        title.setStyleSheet(f"font-size:26px;font-weight:800;color:{self.accent_color};")
        subtitle = QLabel("Save, open, and manage your current page bookmarks.")
        subtitle.setStyleSheet("color:#9aa6b4;font-size:13px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Current page panel
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(10)

        view = self.current_view()
        if view:
            page_title = view.title() or "Untitled Page"
            page_url = view.url().toString()
        else:
            page_title = "No Active Page"
            page_url = ""

        title_lbl = QLabel(page_title)
        title_lbl.setStyleSheet("font-size:16px;font-weight:700;color:white;")

        url_lbl = QLabel(page_url or "No URL available")
        url_lbl.setWordWrap(True)
        url_lbl.setStyleSheet("color:#90a0b2;font-size:12px;")

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 2, 0, 0)
        btn_row.setSpacing(8)

        save_btn = QPushButton("Save Current Page")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self.add_bookmark)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)

        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addWidget(save_btn)

        panel_layout.addWidget(title_lbl)
        panel_layout.addWidget(url_lbl)
        panel_layout.addLayout(btn_row)
        root.addWidget(panel)

        # Saved list title
        list_title = QLabel("Saved Bookmarks")
        list_title.setStyleSheet("font-size:14px;font-weight:700;color:#c9d4e0;padding-top:2px;")
        root.addWidget(list_title)

        # Scroll list
        self.bookmark_scroll = QScrollArea()
        self.bookmark_scroll.setWidgetResizable(True)

        holder = QWidget()
        self.bookmark_cards = QVBoxLayout(holder)
        self.bookmark_cards.setContentsMargins(0, 0, 0, 0)
        self.bookmark_cards.setSpacing(10)
        self.bookmark_cards.setAlignment(Qt.AlignTop)

        self.bookmark_scroll.setWidget(holder)
        root.addWidget(self.bookmark_scroll, 1)

        self.refresh_bookmark_manager()
        dlg.exec()

    # ------------------------------------------------
    # ADD BOOKMARK
    # ------------------------------------------------

    def add_bookmark(self):

        if not hasattr(self, "bookmarks"):
            self.bookmarks = []

        view = self.current_view()

        if view is None:
            QMessageBox.warning(
                self,
                "Bookmark",
                "No active page to bookmark."
            )
            return

        url = view.url().toString().strip()

        if not url or url == "about:blank":
            QMessageBox.warning(
                self,
                "Bookmark",
                "Nothing to bookmark."
            )
            return

        title = view.title().strip() or url
        icon = view.icon()

        #
        # Prevent duplicates
        #

        for bm in self.bookmarks:
            if bm["url"] == url:
                QMessageBox.information(
                    self,
                    "Bookmark",
                    "That bookmark already exists.\n\nSession-Only Bookmarks"
                )
                return

        self.bookmarks.insert(0, {
            "title": title,
            "url": url,
            "icon": icon,
        })

        self.refresh_bookmark_manager()

        self.update_bookmark_icon()

        if hasattr(self, "bookmark_bar"):
            self.refresh_bookmark_bar()

    # ------------------------------------------------
    # REMOVE BOOKMARK
    # ------------------------------------------------

    def remove_bookmark(self, card, title, url):

        # Session-only bookmark list
        if not hasattr(self, "bookmarks"):
            self.bookmarks = []
            return

        self.bookmarks = [
            bm
            for bm in self.bookmarks
            if not (bm["title"] == title and bm["url"] == url)
        ]

        if card is not None:
            card.deleteLater()

        self.refresh_bookmark_manager()

        self.update_bookmark_icon()

        if hasattr(self, "bookmark_bar"):
            self.refresh_bookmark_bar()

    # ------------------------------------------------
    # OPEN BOOKMARK
    # ------------------------------------------------

    def navigate_to(self, url):

        self._add_tab(url=url)

    # Find in Page

    def _create_find_bar(self):
        self.find_bar = QFrame()
        self.find_bar.hide()
        self.find_bar.setFixedHeight(42)

        self._update_find_bar_style()

        layout = QHBoxLayout(self.find_bar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        title = QLabel("Find")

        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Find in page")
        self.find_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.find_count = QLabel("")

        self.find_prev_btn = QToolButton()
        self.find_prev_btn.setText("‹")

        self.find_next_btn = QToolButton()
        self.find_next_btn.setText("›")

        self.find_close_btn = QToolButton()
        self.find_close_btn.setText("✕")

        for btn in (
            self.find_prev_btn,
            self.find_next_btn,
            self.find_close_btn,
        ):
            btn.setFixedSize(34, 34)
            btn.setStyleSheet("""
                QToolButton {{
                    font-size: 24px;
                    font-weight: 300;
                }}
            """)

        layout.addWidget(title)
        layout.addWidget(self.find_edit)
        layout.addWidget(self.find_count)
        layout.addWidget(self.find_prev_btn)
        layout.addWidget(self.find_next_btn)

        layout.addStretch()

        layout.addWidget(self.find_close_btn)

        self.find_edit.textChanged.connect(self.find_text)
        self.find_edit.returnPressed.connect(self.find_next)

        self.find_prev_btn.clicked.connect(self.find_previous)
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_close_btn.clicked.connect(self.hide_find_bar)

    def _update_find_bar_style(self):
        c = self.accent_color

        self.find_bar.setStyleSheet(f"""
        QFrame {{
            background:#10131a;
            border-top:1px solid #20242d;
            border-bottom:1px solid #20242d;
        }}

        QLineEdit {{
            background:#161b24;
            color:white;
            border:1px solid #252b36;
            border-radius:8px;
            padding:5px 10px;
            selection-background-color:{c};
            selection-color:black;
        }}

        QLineEdit:focus {{
            border:1px solid {c};
        }}

        QLabel {{
            color:#8f99a6;
            background:transparent;
            font-size:12px;
        }}

        QToolButton {{
            background: transparent;
            border: none;
            color: #cfd8e3;
            border-radius: 8px;

            min-width: 36px;
            min-height: 36px;
            max-width: 36px;
            max-height: 36px;

            font-size: 24px;
            font-weight: 600;
        }}

        QToolButton:hover {{
            color:{c};
            background:rgba(255,255,255,.08);
        }}

        QToolButton:pressed {{
            background: rgba(255,255,255,.15);
        }}
        """)

    def show_find_bar(self):
        self.find_bar.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def hide_find_bar(self):
        self.find_bar.hide()

        view = self.current_view()

        if view:
            view.page().findText("")
            view.setFocus()

        self.find_edit.clear()
        self.find_count.clear()

    def find_text(self, text):
        view = self.current_view()

        if not view:
            return

        self._last_find_text = text

        view.page().findText("")

        if text:
            view.page().findText(text)

    def find_next(self):
        if not getattr(self, "_last_find_text", ""):
            return

        view = self.current_view()

        if view:
            view.page().findText(self._last_find_text, QWebEnginePage.FindFlag(0))

    def find_previous(self):
        if not getattr(self, "_last_find_text", ""):
            return

        view = self.current_view()

        if view:
            view.page().findText(self._last_find_text, QWebEnginePage.FindBackward)

    # MiniAI

    def update_miniai_icon(self):

        if self.mini_ai.panic_mode_active:
            color = "#8B0000"  # panic

        elif self.mini_ai.lockdown_active:
            color = "#ff0033"  # lockdown

        else:
            color = self.accent_color  # normal

        self.miniai_action.setIcon(make_shield_icon(color, 18))

    def _build_threat_report_html(self):
        stats = self.mini_ai.get_statistics()

        base = QColor(self.accent_color)

        accent = base.name()
        accent2 = base.lighter(130).name()
        accent3 = base.darker(130).name()

        accent_rgba = f"rgba({base.red()}, {base.green()}, {base.blue()}, .45)"

        accent2_rgba = (
            f"rgba({base.lighter(130).red()}, "
            f"{base.lighter(130).green()}, "
            f"{base.lighter(130).blue()}, .40)"
        )

        accent3_rgba = (
            f"rgba({base.darker(130).red()}, "
            f"{base.darker(130).green()}, "
            f"{base.darker(130).blue()}, .45)"
        )

        grid_rgba = f"rgba({base.red()}, {base.green()}, {base.blue()}, .18)"

        return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

    <meta http-equiv="Content-Security-Policy"
    content="
    default-src 'none';
    style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
    font-src https://cdn.jsdelivr.net;
    img-src 'self' data:;
    connect-src 'none';
    script-src 'none';
    object-src 'none';
    frame-ancestors 'none';
    base-uri 'none';
    form-action 'none';
    ">

    <title>Darkelf Threat Console</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">

    <style>

    :root {{
    --bg:#05060a;
    --accent:{accent};
    --accent2:{accent2};
    --accent3:{accent3};
    --danger:#ff3b30;
    --warn:#ffd36b;
    --muted:#9db0be;
    --card:rgba(255,255,255,.05);
    }}

    *{{box-sizing:border-box}}
    html,body{{margin:0;height:100%;font-family:ui-sans-serif,system-ui,-apple-system;}}

    body{{
    background:
    radial-gradient(1200px 800px at 15% -10%,
    {accent_rgba},
    transparent 70%),

    radial-gradient(900px 600px at 110% 0%,
    {accent2_rgba},
    transparent 70%),

    radial-gradient(1200px 700px at 50% 120%,
    {accent3_rgba},
    transparent 70%),

    var(--bg);

    color:#eef2f6;
    }}

    body::before {{
    content:"";
    position:fixed;
    inset:0;

    background:
    linear-gradient(
    {grid_rgba} 1px,
    transparent 1px
    ),

    linear-gradient(
    90deg,
    {grid_rgba} 1px,
    transparent 1px
    );

    background-size:40px 40px;
    pointer-events:none;
    opacity:.22;
    }}

    .scanline {{
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:2px;
    background:linear-gradient(90deg,transparent,var(--accent2),transparent);
    animation:scan 5s linear infinite;
    opacity:.5;
    }}

    @keyframes scan {{
    0%{{transform:translateY(-20px)}}
    100%{{transform:translateY(100vh)}}
    }}

    .container {{
    max-width:1100px;
    margin:auto;
    padding:90px 24px;
    }}

    .title {{
    font-size:1.8rem;
    font-weight:900;
    letter-spacing:.15em;
    background:linear-gradient(90deg,var(--accent),var(--accent2),var(--accent3));
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    }}

    .status-lights {{
    margin-top:18px;
    display:flex;
    gap:10px;
    }}

    .light {{
    width:10px;
    height:10px;
    border-radius:50%;
    }}

    .green {{background:var(--accent)}}
    .cyan {{background:var(--accent2)}}
    .purple {{background:var(--accent3)}}

    .badge {{
    display:inline-flex;
    align-items:center;
    gap:10px;
    margin-top:20px;
    padding:8px 16px;
    border-radius:999px;
    font-size:.7rem;
    font-weight:800;
    letter-spacing:.15em;
    background:{"#ff3b30" if stats['lockdown']['active'] else "#36ff9a"};
    color:#000;
    }}

    .badge::before {{
    content:"";
    width:8px;
    height:8px;
    border-radius:50%;
    background:#fff;
    animation:pulse 1.5s infinite;
    }}

    @keyframes pulse {{
    0%{{transform:scale(.7);opacity:.6}}
    50%{{transform:scale(1.4);opacity:1}}
    100%{{transform:scale(.7);opacity:.6}}
    }}

    .cards {{
    margin-top:60px;
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:50px;
    }}

    .card {{
    background:var(--card);
    backdrop-filter:blur(20px);
    padding:40px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,.08);
    box-shadow:0 0 40px {accent2_rgba};
    }}

    .section-title {{
    font-size:.75rem;
    letter-spacing:.25em;
    text-transform:uppercase;
    color:var(--muted);
    margin-bottom:24px;
    }}

    .line {{
    display:grid;
    grid-template-columns:28px auto max-content;
    align-items:center;
    column-gap:14px;
    margin:16px 0;
    }}

    .icon {{
    font-size:1.2rem;
    color:var(--accent2);
    }}

    .stat-label {{color:#c3d2dd}}

    .stat-value {{
    font-weight:900;
    font-size:1.15rem;
    }}

    .footer {{
    margin-top:80px;
    text-align:center;
    font-size:.8rem;
    color:var(--muted);
    opacity:.7;
    }}

    </style>
    </head>

    <body>

    <div class="scanline"></div>
    
    <div class="container">

    <div class="title">Darkelf MiniAI Threat Console</div>

    <div class="status-lights">
    <div class="light green"></div>
    <div class="light cyan"></div>
    <div class="light purple"></div>
    </div>

    <div class="badge">
    {"LOCKDOWN ACTIVE" if stats['lockdown']['active'] else "SYSTEM MONITORING"}
    </div>

    <div class="cards">

    <div class="card">
    <div class="section-title">Session Metrics</div>

    <div class="line"><i class="bi bi-clock-history icon"></i><span class="stat-label">Session Uptime</span><span class="stat-value">{stats['uptime_seconds']:.1f}s</span></div>
    <div class="line"><i class="bi bi-activity icon"></i><span class="stat-label">Total Events</span><span class="stat-value">{stats['total_events']}</span></div>
    <div class="line"><i class="bi bi-globe2 icon"></i><span class="stat-label">Unique Domains</span><span class="stat-value">{stats['unique_domains']}</span></div>

    <div class="line">
    <i class="bi bi-shield-exclamation icon"></i>
    <span class="stat-label">Threat Score</span>
    <span class="stat-value">{stats['threat_score']}</span>
    </div>

    </div>

    <div class="card">
    <div class="section-title">Threat Analysis</div>

    <div class="line"><i class="bi bi-crosshair icon"></i><span class="stat-label">Trackers</span><span class="stat-value">{stats['threats']['trackers']}</span></div>
    <div class="line"><i class="bi bi-bullseye icon"></i><span class="stat-label">Intrusions</span><span class="stat-value">{stats['threats']['intrusions']}</span></div>
    <div class="line"><i class="bi bi-bug-fill icon"></i><span class="stat-label">Malware</span><span class="stat-value">{stats['threats']['malware']}</span></div>
    <div class="line"><i class="bi bi-lightning-charge-fill icon"></i><span class="stat-label">Exploits</span><span class="stat-value">{stats['threats']['exploits']}</span></div>
    <div class="line"><i class="bi bi-fingerprint icon"></i><span class="stat-label">Fingerprinting</span><span class="stat-value">{stats['threats']['fingerprinting']}</span></div>
    <div class="line"><i class="bi bi-arrow-left-right icon"></i><span class="stat-label">HTTP Blocks</span><span class="stat-value">{stats['threats']['http_blocks']}</span></div>

    </div>

    </div>

    <div class="footer">
    Darkelf Browser • MiniAI Sentinel • Hardened Runtime
    </div>

    </div>
    </body>
    </html>
    """
    
    
    """
    This file contains a drop-in replacement helper for building a Quantum
    HTML dashboard modeled after the MiniAI Threat Console.
    """

    def _build_quantum_report_html(self, pq):
        stats = pq.status_info()

        base = QColor(self.accent_color)
        accent = base.name()
        accent2 = base.lighter(130).name()
        accent3 = base.darker(130).name()

        accent_rgba = f"rgba({base.red()}, {base.green()}, {base.blue()}, .45)"
        accent2_rgba = (
            f"rgba({base.lighter(130).red()}, "
            f"{base.lighter(130).green()}, "
            f"{base.lighter(130).blue()}, .40)"
        )
        accent3_rgba = (
            f"rgba({base.darker(130).red()}, "
            f"{base.darker(130).green()}, "
            f"{base.darker(130).blue()}, .45)"
        )
        grid_rgba = f"rgba({base.red()}, {base.green()}, {base.blue()}, .18)"

        badge = "QUANTUM ACTIVE" if stats["status"] == "active" else "STANDBY"

        chain = pq.chain or "Unavailable"
        chain_short = chain[:96] + "..." if len(chain) > 96 else chain

        return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <style>
    :root{{
    --bg:#05060a;
    --accent:{accent};
    --accent2:{accent2};
    --accent3:{accent3};
    --card:rgba(255,255,255,.05);
    --muted:#9db0be;
    }}
    *{{box-sizing:border-box}}
    html,body{{margin:0;height:100%;font-family:ui-sans-serif,system-ui,-apple-system}}
    body{{
    background:
    radial-gradient(1200px 800px at 15% -10%,{accent_rgba},transparent 70%),
    radial-gradient(900px 600px at 110% 0%,{accent2_rgba},transparent 70%),
    radial-gradient(1200px 700px at 50% 120%,{accent3_rgba},transparent 70%),
    var(--bg);
    color:#eef2f6;
    }}
    body:before{{content:"";position:fixed;inset:0;background:
    linear-gradient({grid_rgba} 1px,transparent 1px),
    linear-gradient(90deg,{grid_rgba} 1px,transparent 1px);
    background-size:40px 40px;opacity:.22;pointer-events:none;}}
    .scanline{{position:fixed;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,var(--accent2),transparent);animation:scan 5s linear infinite}}
    @keyframes scan {{ from {{ transform: translateY(-20px); }} to {{ transform: translateY(100vh); }} }}
    .container{{max-width:1100px;margin:auto;padding:90px 24px}}
    .title{{font-size:1.8rem;font-weight:900;letter-spacing:.15em;background:linear-gradient(90deg,var(--accent),var(--accent2),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}

    .status-lights{{display:flex;gap:10px;margin:18px 0}}
    .light{{width:10px;height:10px;border-radius:50%}}
    .green{{background:var(--accent)}}
    .cyan{{background:var(--accent2)}}
    .purple{{background:var(--accent3)}}

    .badge{{display:inline-flex;align-items:center;gap:10px;padding:8px 16px;border-radius:999px;background:var(--accent);color:#000;font-weight:800}}
    .cards{{margin-top:40px;display:grid;grid-template-columns:1fr 1fr;gap:40px}}
    .card{{background:var(--card);backdrop-filter:blur(20px);padding:36px;border-radius:18px;border:1px solid rgba(255,255,255,.08);box-shadow:0 0 40px {accent2_rgba};}}
    .section-title{{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.2em;margin-bottom:22px}}
    .line{{display:grid;grid-template-columns:28px auto max-content;gap:14px;align-items:center;margin:14px 0}}
    .icon{{color:var(--accent2);font-size:1.2rem}}.stat-value{{font-weight:900}}
    .chain{{margin-top:40px;background:#10131a;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px;font-family:Menlo,monospace;word-break:break-all}}
    .footer{{text-align:center;margin-top:60px;color:var(--muted)}}
    </style>
    </head>
    <body>
    <div class="scanline"></div>
    <div class="container">
    <div class="title">Darkelf Quantum Console</div>
    <div class="status-lights"><div class="light green"></div><div class="light cyan"></div><div class="light purple"></div></div>
    <div class="badge"><i class="bi bi-shield-lock-fill"></i> {badge}</div>

    <div class="cards">

    <div class="card">
    <div class="section-title"><i class="bi bi-cpu-fill icon"></i>Session Metrics</div>
    <div class="line"><i class="bi bi-layers-fill icon"></i><span>Generation</span><span class="stat-value">{stats['generation']}</span></div>
    <div class="line"><i class="bi bi-arrow-repeat icon"></i><span>Rekeys</span><span class="stat-value">{stats['rekeys']}</span></div>
    <div class="line"><i class="bi bi-clock-history icon"></i><span>Seed Age</span><span class="stat-value">{stats['seed_age']} s</span></div>
    <div class="line"><i class="bi bi-activity icon"></i><span>Last Update</span><span class="stat-value">{stats['last_update']} s</span></div>
    </div>

    <div class="card">
    <div class="section-title"><i class="bi bi-diagram-3-fill icon"></i>Quantum Runtime</div>
    <div class="line"><i class="bi bi-shield-check icon"></i><span>Status</span><span class="stat-value">{stats['status'].upper()}</span></div>
    <div class="line"><i class="bi bi-arrow-left-right icon"></i><span>Requests</span><span class="stat-value">{stats['requests']}</span></div>
    <div class="line"><i class="bi bi-eye-fill icon"></i><span>Observed</span><span class="stat-value">{stats['observed']}</span></div>
    <div class="line"><i class="bi bi-collection-fill icon"></i><span>Tabs</span><span class="stat-value">{stats['tabs']}</span></div>
    </div>

    </div>

    <div class="chain">
    <div class="section-title"><i class="bi bi-link-45deg icon"></i>Chain Integrity</div>
    {html.escape(chain_short, quote=True)}
    </div>

    <div class="footer">Darkelf Browser • Quantum Runtime • Post‑Quantum Cryptography</div>
    </div>
    </body>
    </html>
    """

    # Downloads

    def _darkelf_library_dir(self):
        """
        Parent folder for Darkelf user-created artifacts.

        This folder is intentionally created lazily so it does not appear
        unless the user downloads a file or takes a snapshot.
        """
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "Darkelf Library")

    def _ensure_private_dir(self, path):
        """
        Create a folder with user-only permissions where the OS supports it.
        """
        os.makedirs(path, mode=0o700, exist_ok=True)

        try:
            os.chmod(path, 0o700)
        except OSError:
            # Ignore permission or filesystem limitations.
            pass

        return path

    def _ensure_download_dir(self):
        """
        Create the temporary download folder only when a download starts.
        """
        library_dir = self._ensure_private_dir(self._darkelf_library_dir())

        download_dir = self._ensure_private_dir(
            os.path.join(library_dir, "Darkelf Temp Folder")
        )

        self._download_dir = download_dir
        return download_dir

    def _ensure_snapshot_dir(self):
        """
        Create the snapshot folder only when the user takes a snapshot.
        """
        library_dir = self._ensure_private_dir(self._darkelf_library_dir())

        return self._ensure_private_dir(
            os.path.join(library_dir, "Darkelf Snap Folder")
        )

    def _hook_secure_downloads(self):

        signal = self.shared_profile.downloadRequested

        if getattr(self, "_download_signal_connected", False):
            return

        signal.connect(self._handle_download_requested)
        self._download_signal_connected = True

    def _handle_download_requested(self, item):

        filename = _randomized_filename(item.downloadFileName())
        filename = os.path.basename(filename)

        # Create Darkelf Library/Temp Folder lazily only when a download starts.
        download_dir = self._ensure_download_dir()

        item.setDownloadDirectory(download_dir)
        item.setDownloadFileName(filename)

        self._downloaded_files.append(os.path.join(download_dir, filename))

        item.accept()

        # show shelf
        self.download_shelf.show()

        # add item to shelf
        self.download_shelf.add_download(item)

    def _wipe_download_traces(self):
        """
        Deletes the per-session temp download directory (best-effort).
        """
        try:
            if getattr(self, "_download_dir", None) and os.path.isdir(
                self._download_dir
            ):
                shutil.rmtree(self._download_dir, ignore_errors=True)
        except Exception as e:
            print(e)
            pass

    # Cleanup

    def debounce_cleanup(self, delay=5000):
        # Restart timer every time
        self.cleanup_timer.start(delay)

    def memory_cleanup(self):
        try:
            gc.collect()
            print("[Darkelf] GC complete")

        except Exception as e:
            print("[Darkelf] Cleanup error:", e)

    def release_renderer_memory(self):
        try:
            for i in range(self.tabs.count()):
                view = self.tabs.widget(i)
                if not isinstance(view, QWebEngineView):
                    continue

                page = view.page()
                if page is None:
                    continue

                if i != self.tabs.currentIndex():
                    try:
                        page.triggerAction(QWebEnginePage.Stop)
                    except RuntimeError:
                        continue
        except Exception as e:
            print("[Darkelf] Renderer cleanup error:", e)

    # Browser Utilities

    def take_snapshot(self):
        view = self.tabs.currentWidget()
        if not view:
            return

        # Grab screenshot of current tab
        pixmap = view.grab()

        # Create Darkelf Library/Snap Folder lazily only when a snapshot is taken.
        snap_dir = self._ensure_snapshot_dir()

        # Filename
        filename = f"darkelf_snapshot_{int(time.time())}.png"
        path = os.path.join(snap_dir, filename)

        # Save image
        pixmap.save(path, "PNG")

        self.debounce_cleanup()

        print(f"[Darkelf] Snapshot saved → {path}")

    def toggle_javascript(self):
        enabled = self.java_action.isChecked()
        settings = self.shared_profile.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, enabled)
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if isinstance(view, QWebEngineView):
                view.reload()

    def confirm_nuke_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Delete browsing data")
        dlg.setModal(True)
        dlg.setFixedSize(560, 220)

        dlg.setStyleSheet(f"""
        QDialog {{
            background:#0d1017;
            border:1px solid #24293a;
            border-radius:24px;
        }}

        QLabel#title {{
            color:white;
            font-size:22px;
            font-weight:700;
        }}

        QLabel#text {{
            color:#9aa5b1;
            font-size:14px;
        }}

        QPushButton {{
            background:#171b27;
            color:white;
            border:1px solid #262d42;
            border-radius:14px;
            min-height:40px;
            padding:0 28px;
            font-size:15px;
        }}

        QPushButton:hover {{
            border:1px solid {self.accent_color};
        }}

        QPushButton#danger {{
            color:#ff6666;
            border:1px solid #5a2b34;
        }}

        QPushButton#danger:hover {{
            background:#30161a;
            border:1px solid #ff6666;
        }}
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Delete browsing data")
        title.setObjectName("title")

        text = QLabel(
            "This wipes all cookies, cache and visited links, "
            "then closes the browser."
        )
        text.setWordWrap(True)
        text.setObjectName("text")

        layout.addWidget(title)
        layout.addWidget(text)
        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Cancel")
        delete = QPushButton("Delete and Quit")
        delete.setObjectName("danger")

        buttons.addWidget(cancel)
        buttons.addSpacing(12)
        buttons.addWidget(delete)

        layout.addLayout(buttons)

        cancel.clicked.connect(dlg.reject)
        delete.clicked.connect(dlg.accept)

        return dlg.exec() == QDialog.Accepted

    def nuke_all_data(self):

        self._destroy_quantum_state()

        if not self.confirm_nuke_dialog():
            return

        try:
            # Stop all pages first
            for i in range(self.tabs.count()):
                view = self.tabs.widget(i)
                if isinstance(view, QWebEngineView):
                    try:
                        view.page().triggerAction(QWebEnginePage.Stop)
                    except Exception as e:
                        print("Error stopping page:", e)

            profile = QWebEngineProfile.defaultProfile()

            # Wipe browser data
            profile.cookieStore().deleteAllCookies()
            profile.clearHttpCache()
            profile.clearAllVisitedLinks()

        except Exception as e:
            print("NUKE ERROR:", e)

        # Close every tab
        self.tabs.clear()

        # Force cleanup
        gc.collect()

        # Quit shortly after cleanup
        QTimer.singleShot(150, QApplication.quit)

    def _destroy_quantum_state(self):
        interceptor = getattr(self.shared_profile, "_darkelf_interceptor", None)

        if interceptor and hasattr(interceptor, "pq"):
            interceptor.pq.destroy()

    def authenticate_cookie(self, controller, cookie_path):
        try:
            with open(cookie_path, "rb") as f:
                cookie = f.read()
            controller.authenticate(cookie)
        except Exception as e:
            print(f"[Darkelf] Tor cookie authentication failed: {e}")
