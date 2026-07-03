# shadow/settings_dialog.py

from PySide6.QtCore import (
    Qt,
    QEasingCurve,
    QPropertyAnimation,
)

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QDialog,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QStackedWidget,
)

from shadow.settings_pages import (
    AppearancePage,
    PrivacyPage,
    QuantumPage,
    AboutPage,
)



class SidebarButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setFixedWidth(200)
        
        self.setStyleSheet("""
        QPushButton{
            background:transparent;
            color:white;
            border:none;
            border-radius:12px;
            text-align:left;
            padding-left:18px;
            font-size:17px;
            font-weight:500;
        }

        QPushButton:hover{
            background:#141925;
        }

        QPushButton:checked{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:0,
                stop:0 #b14cff,
                stop:1 #a855f7
            );
            color:black;
            font-weight:700;
        }
        """)


class DarkelfSettingsDialog(QDialog):

    WIDTH = 1280
    HEIGHT = 820

    def __init__(self, browser):
        super().__init__(browser)

        self.browser = browser

        self.setWindowTitle("Settings")
        self.resize(self.WIDTH, self.HEIGHT)

        self.setModal(True)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setStyleSheet("""
        QDialog{
            background:#090b12;
            border:1px solid #22283a;
            border-radius:28px;
        }

        QLabel{
            color:white;
            background:transparent;
        }

        QFrame#Sidebar{
            background:#070910;
            border-right:1px solid #1b2130;
            border-top-left-radius:28px;
            border-bottom-left-radius:28px;
        }

        QFrame#Content{
            background:#090b12;
            border-top-right-radius:28px;
            border-bottom-right-radius:28px;
        }
        """)

        self._build_ui()

        self._animate_open()
        
        self.applyAccent()
        
    def applyAccent(self):

        c = self.browser.accent_color

        if isinstance(c, QColor):
            color = c
            c = c.name()
        else:
            color = QColor(c)

        # ----------------
        # Sidebar buttons
        # ----------------

        for btn in self.buttons:

            btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #cfd6e4;

                border: 1px solid transparent;
                border-radius: 16px;

                padding: 10px 22px;
                text-align: left;

                font-size: 17px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: rgba({color.red()},{color.green()},{color.blue()}, 0.12);
                border: 1px solid {c};
                color: white;
            }}

            QPushButton:checked {{
                background: rgba({color.red()},{color.green()},{color.blue()}, 0.20);
                border: 1px solid {c};
                color: white;
                font-weight: 700;
            }}

            QPushButton:checked:hover {{
                background: rgba({color.red()},{color.green()},{color.blue()}, 0.30);
            }}
            """)

        # ---------------
        # Refresh pages
        # ---------------

        for page in self.pages:

            if hasattr(page, "applyAccent"):
                page.applyAccent()
            
    ######################################################################
    # UI
    ######################################################################

    def _build_ui(self):

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --------
        # Sidebar
        # --------

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(330)

        side_layout = QVBoxLayout(sidebar)

        side_layout.setContentsMargins(24, 22, 24, 22)
        side_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet("""
        font-size:28px;
        font-weight:800;
        margin-bottom:8px;
        """)

        side_layout.addWidget(title)

        # ----------------
        # Sidebar Buttons
        # ----------------

        self.appearance_btn = SidebarButton("Appearance")
        self.privacy_btn = SidebarButton("Privacy && Security")
        self.quantum_btn = SidebarButton("Darkelf Quantum")
        self.about_btn = SidebarButton("About Darkelf")

        side_layout.addWidget(self.appearance_btn)
        side_layout.addWidget(self.privacy_btn)
        side_layout.addWidget(self.quantum_btn)
        side_layout.addWidget(self.about_btn)
        
        side_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(200, 48)

        self.close_btn.setStyleSheet("""
        QPushButton{
            background:#131723;
            color:white;
            border:1px solid #252c3d;
            border-radius:16px;
            font-size:18px;
            font-weight:600;
        }

        QPushButton:hover{
            border:1px solid #a855f7;
        }

        QPushButton:pressed{
            background:#1a2030;
        }
        """)

        side_layout.addWidget(self.close_btn, 0, Qt.AlignHCenter)

        root.addWidget(sidebar)

        # ------------
        # Content
        # ------------

        content = QFrame()
        content.setObjectName("Content")

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(40, 34, 40, 34)

        self.stack = QStackedWidget()

        self.appearance_page = AppearancePage(self.browser)
        self.privacy_page = PrivacyPage(self.browser)
        self.quantum_page = QuantumPage(self.browser)
        self.about_page = AboutPage(self.browser)

        self.stack.addWidget(self.appearance_page)
        self.stack.addWidget(self.privacy_page)
        self.stack.addWidget(self.quantum_page)
        self.stack.addWidget(self.about_page)

        content_layout.addWidget(self.stack)

        root.addWidget(content)

        # ------------
        # Navigation
        # ------------

        self.buttons = [
            self.appearance_btn,
            self.privacy_btn,
            self.quantum_btn,
            self.about_btn,
        ]

        self.pages = [
            self.appearance_page,
            self.privacy_page,
            self.quantum_page,
            self.about_page,
        ]

        for i, button in enumerate(self.buttons):
            button.clicked.connect(
                lambda checked=False, index=i:
                    self.set_page(index)
            )

        self.close_btn.clicked.connect(self.accept)

        self.set_page(0)

    ######################################################################
    # Navigation
    ######################################################################

    def set_page(self, index):

        self.stack.setCurrentIndex(index)

        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

    ######################################################################
    # Public helpers
    ######################################################################

    def refresh(self):
        """
        Called before showing the dialog.
        Allows pages to synchronize with the browser state.
        """

        for page in self.pages:
            if hasattr(page, "refresh"):
                page.refresh()

    ######################################################################
    # Animation
    ######################################################################

    def _animate_open(self):

        self.anim = QPropertyAnimation(self, b"windowOpacity")

        self.anim.setDuration(220)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim.start()
