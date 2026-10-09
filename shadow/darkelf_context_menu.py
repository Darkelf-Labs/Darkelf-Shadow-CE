from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QColor

class DarkelfContextMenu(QMenu):

    def __init__(self, browser, parent=None):
        super().__init__(parent)

        self.browser = browser

        self.setAttribute(Qt.WA_TranslucentBackground)

        accent = QColor(browser.accent_color)

        r = accent.red()
        g = accent.green()
        b = accent.blue()

        self.setStyleSheet(f"""
        QMenu {{
            background:#0d1118;
            border:1px solid #252c39;
            border-radius:14px;
            padding:8px;
            color:white;
        }}

        QMenu::item {{
            padding:10px 18px;
            border-radius:9px;
            margin:2px;
            color:white;
            background:transparent;
        }}

        QMenu::item:selected {{
            background: rgba({r}, {g}, {b}, .20);
            border:1px solid {browser.accent_color};
            color:white;
        }}

        QMenu::separator {{
            height:1px;
            background:#242b38;
            margin:8px 10px;
        }}
        """)
        
    def section(self):
        self.addSeparator()







