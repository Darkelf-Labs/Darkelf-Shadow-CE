"""Darkelf Shadow: frameless traffic lights and visual window arrangement menu."""
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer, QRectF
from PySide6.QtGui import QCursor, QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QMenu, QWidgetAction, QApplication, QFrame,
)


class _TrafficLight(QPushButton):
    """Paint native-style circles without Qt stylesheet parsing warnings."""
    def __init__(self, color, glyph, tooltip, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._glyph = glyph
        self._hovered = False
        self.setObjectName("ShadowTrafficLight")
        self.setFixedSize(14, 14)
        self.setToolTip(tooltip)
        self.setCursor(Qt.ArrowCursor)
        self.setFlat(True)
        self.setStyleSheet("border: none; background: transparent; padding: 0;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self._color.darker(135), 0.8))
        painter.setBrush(self._color)
        painter.drawEllipse(QRectF(0.8, 0.8, 12.4, 12.4))
        if self._hovered:
            painter.setPen(QPen(QColor("#343039"), 1.4))
            if self._glyph == "×":
                painter.drawLine(5, 5, 9, 9)
                painter.drawLine(9, 5, 5, 9)
            elif self._glyph == "−":
                painter.drawLine(4, 7, 10, 7)
            else:
                painter.drawLine(4, 7, 10, 7)
                painter.drawLine(7, 4, 7, 10)
        painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)


class _LayoutPreview(QWidget):
    def __init__(self, layout_id, accent, parent=None):
        super().__init__(parent)
        self.layout_id, self.accent = layout_id, accent
        self.setFixedSize(100, 54)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        frame = QRectF(3, 3, 94, 48)
        p.setPen(QPen(QColor('#536071'), 1))
        p.setBrush(QColor('#151b26'))
        p.drawRoundedRect(frame, 5, 5)
        x, y, w, h = 6.0, 6.0, 88.0, 42.0
        cells = []
        key = self.layout_id
        if key in ('left', 'right'):
            cells = [(x, y, w/2-1, h, key == 'left'), (x+w/2+1, y, w/2-1, h, key == 'right')]
        elif key in ('third_left', 'third_center', 'third_right'):
            active = {'third_left': 0, 'third_center': 1, 'third_right': 2}[key]
            cells = [(x+i*w/3+1, y, w/3-2, h, i == active) for i in range(3)]
        elif key.startswith('quarter_'):
            active = {'quarter_tl': 0, 'quarter_tr': 1, 'quarter_bl': 2, 'quarter_br': 3}[key]
            cells = [(x+(i%2)*w/2+1, y+(i//2)*h/2+1, w/2-2, h/2-2, i == active) for i in range(4)]
        elif key == 'maximize':
            cells = [(x, y, w, h, True)]
        else:
            cells = [(x+12, y+2, w-24, h-4, True)]
        for cx, cy, cw, ch, selected in cells:
            c = QColor(self.accent) if selected else QColor('#343c4e')
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c))
            p.drawRoundedRect(QRectF(cx, cy, cw, ch), 3, 3)
        p.end()


class _LayoutTile(QPushButton):
    def __init__(self, label, layout_id, accent, callback, parent=None):
        super().__init__(parent)
        self.setObjectName('ShadowLayoutTile')
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(126, 95)
        self.setStyleSheet(
            'QPushButton#ShadowLayoutTile {background:#111722; border:1px solid #30394b; border-radius:10px;}'
            f'QPushButton#ShadowLayoutTile:hover {{background:#1a2130; border:1px solid {accent};}}'
            'QPushButton#ShadowLayoutTile:pressed {background:#252d3d;}'
        )
        box = QVBoxLayout(self)
        box.setContentsMargins(5, 6, 5, 7)
        box.setSpacing(3)
        preview = _LayoutPreview(layout_id, accent, self)
        box.addWidget(preview, alignment=Qt.AlignHCenter)
        title = QLabel(label, self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color:#e8edf6; background:transparent; font-size:11px; font-weight:600;')
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        box.addWidget(title)
        self.clicked.connect(callback)


class ShadowTitleBar(QWidget):
    """Black draggable title bar; click green for fullscreen, hover for tiling."""
    def __init__(self, window):
        super().__init__(window)
        self._window = window
        self.setObjectName('ShadowTitleBar')
        self.setFixedHeight(32)
        self.setStyleSheet('QWidget#ShadowTitleBar {background:#050609;}')
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(8)
        self.close_button = _TrafficLight('#ff5f57', '×', 'Close', self)
        self.min_button = _TrafficLight('#febc2e', '−', 'Minimize', self)
        self.green_button = _TrafficLight('#28c840', '+', 'Click: fullscreen · Hover: arrange', self)
        for button in (self.close_button, self.min_button, self.green_button):
            row.addWidget(button)
        row.addStretch(1)
        self.close_button.clicked.connect(window.close)
        self.min_button.clicked.connect(window.showMinimized)
        self.green_button.clicked.connect(self._green_clicked)
        self.green_button.installEventFilter(self)
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(1800)
        self._hover_timer.timeout.connect(self._open_if_hovered)
        self.menu = QMenu(self)
        self.menu.setObjectName('ShadowArrangeMenu')
        self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.aboutToShow.connect(self._rebuild_menu)
        self._rebuild_menu()

    def _accent(self):
        value = getattr(self._window, 'accent_color', '#A855F7')
        color = QColor(value)
        return color.name() if color.isValid() else '#A855F7'

    def _green_clicked(self):
        self._hover_timer.stop()
        if self.menu.isVisible():
            self.menu.hide()
        self._window.toggle_fullscreen()

    def eventFilter(self, watched, event):
        if watched is self.green_button:
            if event.type() == QEvent.Enter:
                self._hover_timer.start()
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonPress):
                self._hover_timer.stop()
        return super().eventFilter(watched, event)

    def _open_if_hovered(self):
        if self.green_button.rect().contains(self.green_button.mapFromGlobal(QCursor.pos())):
            self.show_arrangement_menu()

    def show_arrangement_menu(self):
        self._hover_timer.stop()
        if not self.menu.isVisible():
            self.menu.popup(self.green_button.mapToGlobal(QPoint(0, self.green_button.height() + 8)))

    def _rebuild_menu(self):
        accent = self._accent()
        self.menu.clear()
        self.menu.setStyleSheet(
            'QMenu#ShadowArrangeMenu {background:#080b11; color:#e8edf6; '
            'border:1px solid #333c4c; border-radius:14px; padding:8px;}'
        )
        content = QWidget(self.menu)
        content.setObjectName('ShadowArrangementContent')
        content.setStyleSheet('QWidget#ShadowArrangementContent {background:#080b11; border-radius:12px;}')
        outer = QVBoxLayout(content)
        outer.setContentsMargins(10, 9, 10, 10)
        outer.setSpacing(10)
        heading = QLabel('Window Arrangement', content)
        heading.setStyleSheet('color:#f5f6fb; font-size:14px; font-weight:700;')
        outer.addWidget(heading)
        hint = QLabel('Click green for fullscreen · Choose a layout below', content)
        hint.setStyleSheet('color:#9ca8ba; font-size:10px;')
        outer.addWidget(hint)
        grid = QGridLayout()
        grid.setSpacing(7)
        items = [
            ('Left Half', 'left', lambda: self.tile(0, 0, 1, 2)),
            ('Right Half', 'right', lambda: self.tile(1, 0, 1, 2)),
            ('Left Third', 'third_left', lambda: self.tile(0, 0, 1, 3)),
            ('Center Third', 'third_center', lambda: self.tile(1, 0, 1, 3)),
            ('Right Third', 'third_right', lambda: self.tile(2, 0, 1, 3)),
            ('Maximize', 'maximize', self.toggle_maximized),
            ('Top Left', 'quarter_tl', lambda: self.tile(0, 0, 1, 2, rows=2)),
            ('Top Right', 'quarter_tr', lambda: self.tile(1, 0, 1, 2, rows=2)),
            ('Bottom Left', 'quarter_bl', lambda: self.tile(0, 1, 1, 2, rows=2)),
            ('Bottom Right', 'quarter_br', lambda: self.tile(1, 1, 1, 2, rows=2)),
        ]
        for i, (label, layout_id, callback) in enumerate(items):
            def select(checked=False, cb=callback):
                # QPushButton.clicked supplies a bool. Without the explicit
                # checked parameter it overwrites cb and crashes singleShot.
                self.menu.hide()
                QTimer.singleShot(0, cb)
            grid.addWidget(_LayoutTile(label, layout_id, accent, select, content), i // 2, i % 2)
        outer.addLayout(grid)
        fullscreen = QPushButton('⛶   Enter / Exit Fullscreen', content)
        fullscreen.setCursor(Qt.PointingHandCursor)
        fullscreen.setStyleSheet(
            'QPushButton {color:#f2f4fa; background:#161c27; border:1px solid #384255; '
            'border-radius:9px; padding:10px; font-weight:600; text-align:left;}'
            f'QPushButton:hover {{border-color:{accent}; background:#252b39;}}'
        )
        fullscreen.clicked.connect(lambda: (self.menu.hide(), QTimer.singleShot(0, self._window.toggle_fullscreen)))
        outer.addWidget(fullscreen)
        action = QWidgetAction(self.menu)
        action.setDefaultWidget(content)
        self.menu.addAction(action)

    def toggle_maximized(self):
        if self._window.isMaximized() or self._window.isFullScreen():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def tile(self, column, row, width_columns, columns, rows=1):
        window = self._window
        if window.isFullScreen() or window.isMaximized():
            window.showNormal()
        screen = window.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        left = area.x() + round(area.width() * column / columns)
        right = area.x() + round(area.width() * (column + width_columns) / columns)
        top = area.y() + round(area.height() * row / rows)
        bottom = area.y() + round(area.height() * (row + 1) / rows)
        window.setGeometry(left, top, max(1, right - left), max(1, bottom - top))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._window.isFullScreen():
            handle = self._window.windowHandle()
            if handle and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)
