# shadow/browser_features.py

import gc
import os
import shutil
import sys
import tempfile
from pathlib import Path
import time

from PySide6.QtCore import (
    Qt,
    QProcess,
    QTimer,
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
    QWebEngineSettings,
)


from shadow.utils import (
    _randomized_filename,
)

# Delete only Chromium website stores after the owning application exits.
# The named-profile WebAuthn secret and macOS Keychain are deliberately retained.
_PROFILE_WIPE_SCRIPT = r"""
set -eu
parent_pid=$1
root=$2
status=$3
umask 077
work=$(/usr/bin/mktemp -d /tmp/darkelf-wipe.XXXXXXXX)
trap '/bin/rm -rf "$work"' EXIT
attempt=0
while /bin/kill -0 "$parent_pid" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 90 ]; then
        printf '%s\n' 'FAILED: browser did not exit; storage retained.' > "$status"
        exit 1
    fi
    /bin/sleep 1
done
attempt=0
while :; do
    # lsof returns 1 with empty output when there are no open files.
    result=0
    /usr/sbin/lsof -nP +D "$root" > "$work/open" 2> "$work/error" || result=$?
    if [ -s "$work/error" ] || [ "$result" -gt 1 ]; then
        printf '%s\n' 'FAILED: could not verify storage is closed; storage retained.' > "$status"
        exit 1
    fi
    if [ ! -s "$work/open" ]; then
        break
    fi
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 90 ]; then
        printf '%s\n' 'FAILED: storage still in use; storage retained.' > "$status"
        exit 1
    fi
    /bin/sleep 1
done
for name in 'Local Storage' IndexedDB 'Session Storage' 'Service Worker' \
    'File System' WebStorage Storage databases blob_storage \
    Cookies Cookies-journal 'Visited Links' Network \
    QuotaManager QuotaManager-journal SharedStorage SharedStorage-wal \
    SharedStorage-shm 'Shared Dictionary' Cache 'Code Cache' GPUCache \
    DawnCache GrShaderCache 'VideoDecodeStats' 'Network Persistent State' \
    TransportSecurity 'Trust Tokens' 'Trust Tokens-journal' 'Reporting and NEL' \
    DIPS DIPS-wal DIPS-shm 'BrowsingTopicsSiteData' 'BrowsingTopicsState'; do
    if ! /bin/rm -rf "$root/$name"; then
        printf '%s\n' 'FAILED: one or more website stores could not be removed.' > "$status"
        exit 1
    fi
done
printf '%s\n' 'COMPLETE: website stores removed; authentication files retained.' > "$status"
"""


def _schedule_profile_storage_wipe(profile):
    """Schedule macOS named-profile cleanup; return its status-file path.

    Never remove files from a live Qt profile. Off-the-record profiles disappear
    with the process and need no disk cleanup. Do not relaunch during cleanup.
    """
    if profile.isOffTheRecord():
        return None
    if sys.platform != 'darwin' or profile.storageName() != 'Darkelf':
        raise RuntimeError('Disk cleanup supports only the macOS Darkelf profile.')
    raw_path = profile.persistentStoragePath()
    root = Path(raw_path).expanduser()
    home = Path.home().resolve()
    if (
        not raw_path
        or not root.is_absolute()
        or root.resolve() != root
        or root.name != 'Darkelf'
        or root.parent.name != 'QtWebEngine'
        or home not in root.parents
        or not root.is_dir()
    ):
        raise RuntimeError('Refusing cleanup of an unexpected profile storage path.')
    if not Path('/usr/sbin/lsof').is_file():
        raise RuntimeError('macOS lsof is required to check that profile files are closed.')
    descriptor, status = tempfile.mkstemp(prefix='.darkelf-wipe-', suffix='.status', dir=root)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        stream.write('SCHEDULED: waiting for browser exit and closed profile files.\n')
    try:
        started, _ = QProcess.startDetached(
            '/bin/sh', ['-c', _PROFILE_WIPE_SCRIPT, 'darkelf-wipe', str(os.getpid()), str(root), status]
        )
        if not started:
            raise RuntimeError('Could not start the post-exit website-storage cleanup.')
    except Exception:
        Path(status).unlink(missing_ok=True)
        raise
    return status


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
        Shared application-exit hook, connected to QApplication.aboutToQuit.

        Schedule named-profile website-store cleanup on every normal exit,
        including the last-window close, Cmd+Q, and Delete and Quit. Preserve
        authentication files. Also remove the per-session download directory.
        """
        try:
            self._ensure_profile_wipe_scheduled()
        except (OSError, RuntimeError) as error:
            # Shutdown is already in progress. Report failure accurately rather
            # than claiming that website storage was removed.
            print(f'[Darkelf] Website-storage cleanup could not be scheduled: {error}')
        try:
            if getattr(self, "_download_dir", None) and os.path.isdir(
                self._download_dir
            ):
                shutil.rmtree(self._download_dir, ignore_errors=True)
        except Exception as e:
            print(e)
            pass

    def _ensure_profile_wipe_scheduled(self):
        """Arm a single post-exit cleanup worker for this browser session."""
        if getattr(self, '_profile_wipe_scheduled', False):
            return getattr(self, '_profile_wipe_status', None)

        status = _schedule_profile_storage_wipe(self.shared_profile)
        self._profile_wipe_status = status
        self._profile_wipe_scheduled = True
        if status:
            print(f'[Darkelf] Post-exit website cleanup status: {status}')
        return status

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
        dlg.setFixedSize(560, 280)

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
            "Deletes cookies, cache and visited links, then closes the browser. "
            "The macOS named profile also clears website storage after every normal exit. "
            "Passkey authentication files are retained. Wait for cleanup before reopening."
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
        if getattr(self, '_nuke_in_progress', False):
            return
        if not self.confirm_nuke_dialog():
            return

        profile = self.shared_profile
        try:
            self._ensure_profile_wipe_scheduled()
        except (OSError, RuntimeError) as error:
            QMessageBox.warning(self, 'Delete browsing data', str(error))
            return

        self._nuke_in_progress = True
        self._destroy_quantum_state()

        # Detach and destroy pages/views, rather than leaving parented widgets
        # alive after QTabWidget.clear(). The profile remains alive until exit.
        for index in range(self.tabs.count() - 1, -1, -1):
            view = self.tabs.widget(index)
            self.tabs.removeTab(index)
            if isinstance(view, QWebEngineView):
                try:
                    page = view.page()
                    page.triggerAction(QWebEnginePage.Stop)
                    page.deleteLater()
                except RuntimeError:
                    pass  # A previously closed tab may already be deleted.
            if view is not None:
                try:
                    view.deleteLater()
                except RuntimeError:
                    pass

        # Let asynchronous HTTP-cache clearing finish, with a bounded fallback.
        # Named-profile disk deletion happens only in the post-exit helper.
        self._nuke_quit_timer = QTimer(self)
        self._nuke_quit_timer.setSingleShot(True)
        self._nuke_quit_timer.timeout.connect(QApplication.quit)
        self._nuke_quit_timer.start(5000)
        profile.clearHttpCacheCompleted.connect(QApplication.quit)
        try:
            profile.cookieStore().deleteAllCookies()
            profile.clearAllVisitedLinks()
            profile.clearHttpCache()
        except RuntimeError as error:
            print(f'[Darkelf] In-process browsing cleanup: {error}')
            QTimer.singleShot(0, QApplication.quit)
        gc.collect()

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
