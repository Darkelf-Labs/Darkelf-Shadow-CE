"""Darkelf Shadow Cocoa-inspired floating utility panels.

Drop into shadow/shadow_panels.py. Existing browser_ui.py calls remain unchanged.
No native QDialog window chrome, no QDockWidget and no webpage resizing.
"""
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QApplication,
)

from shadow.settings_dialog import DarkelfSettingsDialog
from shadow.darkelf_inspector import DarkelfInspector


class _DragHeader(QFrame):
    def __init__(self, window, title):
        super().__init__(window)
        self._window = window
        self._drag_origin = None
        self.setObjectName("DarkelfFloatingHeader")
        self.setFixedHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 12, 0)
        label = QLabel(title)
        label.setObjectName("DarkelfFloatingTitle")
        layout.addWidget(label)
        layout.addStretch(1)
        close = QPushButton("×")
        close.setObjectName("DarkelfFloatingClose")
        close.setFixedSize(30, 30)
        close.setToolTip("Close panel")
        close.clicked.connect(window.hide)
        layout.addWidget(close)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self._window.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_origin)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin = None
        super().mouseReleaseEvent(event)


class ShadowFloatingPanel(QWidget):
    """Separate, nonmodal frameless macOS tool window with a black surface."""

    def __init__(self, browser, title, width, height):
        super().__init__(browser, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.browser = browser
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setMinimumSize(460, 340)
        self.resize(width, height)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.surface = QFrame(self)
        self.surface.setObjectName("DarkelfFloatingSurface")
        # One visible surface only: no inset glass gutter or shadow layer.
        outer.addWidget(self.surface)

        content = QVBoxLayout(self.surface)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        self.header = _DragHeader(self, title)
        content.addWidget(self.header)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)
        content.addLayout(self.body, 1)
        self.setStyleSheet("""
            QFrame#DarkelfFloatingSurface {
                background-color: #08090D;
                border: 1px solid #292B35;
                border-radius: 18px;
            }
            QFrame#DarkelfFloatingHeader {
                background-color: #08090D;
                border: none;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
            QLabel#DarkelfFloatingTitle {
                background: transparent;
                border: none;
                color: #F4F4F7;
                font-size: 14px;
                font-weight: 650;
            }
            QPushButton#DarkelfFloatingClose {
                color: #C9CBD4;
                background: #191B23;
                border: 1px solid #30333D;
                border-radius: 9px;
                font-size: 19px;
            }
            QPushButton#DarkelfFloatingClose:hover {
                color: white;
                background: #333642;
            }
        """)

    def show_panel(self):
        if not self.isVisible():
            # Center over the browser, constrained to the available display.
            screen = self.browser.screen() or QApplication.primaryScreen()
            available = screen.availableGeometry() if screen else self.browser.geometry()
            w = min(self.width(), max(460, available.width() - 32))
            h = min(self.height(), max(340, available.height() - 32))
            self.resize(w, h)
            frame = self.browser.frameGeometry()
            x = frame.center().x() - w // 2
            y = frame.center().y() - h // 2
            x = max(available.left(), min(x, available.right() - w + 1))
            y = max(available.top(), min(y, available.bottom() - h + 1))
            self.move(QPoint(x, y))
        self.show()
        self.raise_()
        self.activateWindow()


def open_settings_panel(browser):
    panel = getattr(browser, "_shadow_settings_floating", None)
    if panel is None:
        panel = ShadowFloatingPanel(browser, "Settings", 1120, 760)
        settings = DarkelfSettingsDialog(browser)
        # Reparent before embedding: QDialog is used as a child widget, not a dialog.
        settings.setParent(panel.surface)
        settings.setWindowFlags(Qt.WindowType.Widget)
        settings.setModal(False)
        settings.setMinimumSize(0, 0)
        settings.setMaximumSize(16777215, 16777215)
        settings.setStyleSheet(settings.styleSheet() + """
            QDialog { background: #08090D; border: 0; border-radius: 12px; }
            QFrame#Sidebar { background: #08090D; border-right: 1px solid #20232B; }
            QFrame#Content { background: #08090D; }
        """)
        if hasattr(settings, "close_btn"):
            try:
                settings.close_btn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            settings.close_btn.clicked.connect(panel.hide)
        panel.body.addWidget(settings)
        browser._shadow_settings_floating = panel
        browser._shadow_settings_widget = settings
    browser._shadow_settings_widget.refresh()
    browser._shadow_settings_widget.applyAccent()
    panel.show_panel()


def open_inspector_panel(browser):
    panel = getattr(browser, "_shadow_inspector_floating", None)
    if panel is None:
        panel = ShadowFloatingPanel(browser, "Darkelf Inspector", 1120, 730)
        inspector = DarkelfInspector(
            browser=browser,
            webview=browser.current_view(),
            mini_ai=browser.mini_ai,
            parent=panel.surface,
        )
        panel.body.addWidget(inspector)
        browser._shadow_inspector_floating = panel
        browser.darkelf_inspector = inspector
        browser.dev_console = inspector
        browser.tabs.currentChanged.connect(browser._sync_inspector_webview)
    browser._sync_inspector_webview()
    panel.show_panel()
