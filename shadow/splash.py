# ============================================================
# Darkelf Browser
# Premium Splash Screen
# Part 1
# ============================================================

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QSize,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar,
)


# ============================================================
# Splash
# ============================================================

class BootSplash(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            False,
        )

        self.setFixedSize(640, 420)

        #
        # Root
        #

        root = QVBoxLayout(self)

        root.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        #
        # Card
        #

        self.card = QFrame()

        self.card.setObjectName("SplashCard")

        root.addWidget(self.card)

        layout = QVBoxLayout(self.card)

        layout.setContentsMargins(
            40,
            34,
            40,
            34,
        )

        layout.setSpacing(14)

        # -----------------------------------------------------
        # Logo
        # -----------------------------------------------------

        self.logo = QLabel()

        self.logo.setAlignment(Qt.AlignCenter)

        logo_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "darkelf-256.png"
        )

        pix = QPixmap(str(logo_path))

        if not pix.isNull():

            self.logo.setPixmap(

                pix.scaled(

                    QSize(50, 50),

                    Qt.KeepAspectRatio,

                    Qt.SmoothTransformation,
                )
            )

        else:

            self.logo.setText("Darkelf")

            self.logo.setStyleSheet("""
                color:#A855F7;
                font-size:34px;
                font-weight:800;
            """)

        layout.addWidget(self.logo)

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        self.title = QLabel(
            "Darkelf Browser"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )

        self.title.setFont(
            QFont(
                "Arial",
                28,
                QFont.Bold,
            )
        )

        layout.addWidget(
            self.title
        )

        # -----------------------------------------------------
        # Subtitle
        # -----------------------------------------------------

        self.subtitle = QLabel(
            "SHADOW • PRIVATE • HARDENED"
        )

        self.subtitle.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.subtitle
        )

        layout.addSpacing(10)

        # -----------------------------------------------------
        # Feature Chips
        # -----------------------------------------------------

        chips = QHBoxLayout()

        chips.setSpacing(10)

        for text in (

            "Private",

            "Tracker Blocking",

            "HTTPS",

            "MiniAI",

        ):

            chip = QLabel(text)

            chip.setAlignment(
                Qt.AlignCenter
            )

            chip.setStyleSheet("""
            QLabel{

                background:#171d27;

                border:1px solid #A855F7;

                border-radius:11px;

                color:#A855F7;

                padding:6px 14px;

                font-size:11px;

                font-weight:700;
            }
            """)

            chips.addWidget(chip)

        layout.addLayout(chips)

        layout.addSpacing(12)

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        self.status = QLabel(
            "Initializing..."
        )

        self.status.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.status
        )

        # -----------------------------------------------------
        # Progress Bar
        # -----------------------------------------------------

        self.bar = QProgressBar()

        self.bar.setRange(
            0,
            100,
        )

        self.bar.setValue(0)

        self.bar.setTextVisible(True)

        self.bar.setFormat("%p%")

        layout.addWidget(
            self.bar
        )

        # =====================================================
        # Part 2
        # =====================================================
        
        #
        # Progress spacing
        #

        layout.addSpacing(18)

        # -----------------------------------------------------
        # Footer
        # -----------------------------------------------------

        footer = QHBoxLayout()

        self.version = QLabel("Version 7.0.4")

        self.version.setObjectName("VersionLabel")

        footer.addWidget(self.version)

        footer.addStretch()

        self.miniai = QLabel("Darkelf MiniAI Sentinel")

        self.miniai.setObjectName("MiniAILabel")

        footer.addWidget(self.miniai)

        layout.addLayout(footer)

        #
        # Stretch
        #

        layout.addStretch()

        # -----------------------------------------------------
        # Style
        # -----------------------------------------------------

        self.setStyleSheet("""
        QWidget{
            background:#050505;
        }

        QFrame#SplashCard{

            background:qlineargradient(
                x1:0,y1:0,
                x2:0,y2:1,

                stop:0 #10141b,
                stop:.45 #0c1016,
                stop:1 #08090d
            );

            border:1px solid #252c37;

            border-radius:24px;
        }

        QLabel{

            background:transparent;
        }

        QLabel#VersionLabel{

            color:#6e7988;

            font-size:11px;
        }

        QLabel#MiniAILabel{

            color:#A855F7;

            font-size:11px;

            font-weight:700;

            letter-spacing:1px;
        }

        QProgressBar{

            background:#11161d;

            border:1px solid #252c37;

            border-radius:8px;

            height:16px;

            text-align:center;

            color:white;

            font-weight:700;
        }

        QProgressBar::chunk{

            border-radius:7px;

            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:0,

                stop:0 #8B5CF6,
                stop:.5 #A855F7,
                stop:1 #C084FC
            );
        }
        """)

        #
        # Title
        #

        self.title.setStyleSheet("""
        color:#ffffff;

        font-size:34px;

        font-weight:800;
        """)

        #
        # Subtitle
        #

        self.subtitle.setStyleSheet("""
        color:#A8B3C2;

        font-size:13px;

        letter-spacing:3px;
        """)

        #
        # Status
        #

        self.status.setStyleSheet("""
        color:#9AA5B2;

        font-size:14px;

        padding-top:6px;
        """)
        
        # -----------------------------------------------------
        # Fade-in Animation
        # -----------------------------------------------------

        from PySide6.QtCore import (
            QPropertyAnimation,
            QEasingCurve,
            QTimer,
        )

        from PySide6.QtWidgets import (
            QGraphicsDropShadowEffect,
        )

        shadow = QGraphicsDropShadowEffect(self)

        shadow.setBlurRadius(48)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(168, 85, 247, 120))

        self.card.setGraphicsEffect(shadow)

        #
        # Window fade
        #

        self.setWindowOpacity(0)

        self.fadeAnim = QPropertyAnimation(
            self,
            b"windowOpacity",
        )

        self.fadeAnim.setDuration(700)

        self.fadeAnim.setStartValue(0)

        self.fadeAnim.setEndValue(1)

        self.fadeAnim.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.fadeAnim.start()

        #
        # Logo breathing animation
        #

        self._grow = True

        self._logoSize = 50

        self.logoTimer = QTimer(self)

        self.logoTimer.timeout.connect(
            self._animate_logo
        )

        self.logoTimer.start(55)

        #
        # MiniAI pulse
        #

        self._miniPulse = True

        self.miniTimer = QTimer(self)

        self.miniTimer.timeout.connect(
            self._animate_miniai
        )

        self.miniTimer.start(600)
        
    # ---------------------------------------------------------
    # Logo Animation
    # ---------------------------------------------------------

    def _animate_logo(self):

        if self._grow:

            self._logoSize += 1

            if self._logoSize >= 60:
                self._grow = False

        else:

            self._logoSize -= 1

            if self._logoSize <= 50:
                self._grow = True

        logo_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "darkelf.png"
        )

        pix = QPixmap(str(logo_path))

        if pix.isNull():
            return

        self.logo.setPixmap(

            pix.scaled(

                self._logoSize,

                self._logoSize,

                Qt.KeepAspectRatio,

                Qt.SmoothTransformation,

            )
        )

    # ---------------------------------------------------------
    # MiniAI Pulse
    # ---------------------------------------------------------

    def _animate_miniai(self):

        if self._miniPulse:

            self.miniai.setStyleSheet("""
                color:#C084FC;
                font-size:11px;
                font-weight:700;
                letter-spacing:1px;
            """)

        else:

            self.miniai.setStyleSheet("""
                color:#A855F7;
                font-size:11px;
                font-weight:700;
                letter-spacing:1px;
            """)

        self._miniPulse = not self._miniPulse
