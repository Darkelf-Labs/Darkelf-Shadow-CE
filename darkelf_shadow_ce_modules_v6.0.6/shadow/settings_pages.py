# shadow/settings_pages.py

from PySide6.QtCore import (
    Qt,
    Signal,
    Property,
    QRectF,
    QUrl,
    QEasingCurve,
    QPropertyAnimation,
)

from PySide6.QtGui import (
    QColor,
    QPainter,
    QPixmap,
    QDesktopServices,
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QAbstractButton,
)

from importlib.resources import files

def accent(browser):
    return browser.accent_color if hasattr(browser, "accent_color") else "#A855F7"
    
# ============================================================
# Reusable Settings Widgets
# Paste below ThemeCard
# ============================================================

class SettingsLabel(QLabel):

    def __init__(self, text):
        super().__init__(text)

        self.setStyleSheet("""
        QLabel{
            color:white;
            font-size:16px;
            font-weight:600;
            background:transparent;
        }
        """)


class DescriptionLabel(QLabel):

    def __init__(self, text):
        super().__init__(text)

        self.setWordWrap(True)

        self.setStyleSheet("""
        QLabel{
            color:#98A2B3;
            font-size:13px;
            background:transparent;
        }
        """)


class SettingsChip(QFrame):

    def __init__(self, text, color="#A855F7"):
        super().__init__()

        self.setStyleSheet(f"""
        QFrame{{
            background:rgba(168,85,247,.15);
            border:1px solid {color};
            border-radius:10px;
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10,4,10,4)

        lbl = QLabel(text)

        lbl.setStyleSheet(f"""
        color:{color};
        font-weight:700;
        font-size:12px;
        """)

        layout.addWidget(lbl)


class Divider(QFrame):

    def __init__(self):
        super().__init__()

        self.setFrameShape(QFrame.HLine)

        self.setStyleSheet("""
        color:#252C37;
        background:#252C37;
        min-height:1px;
        max-height:1px;
        """)


class StatusBadge(QFrame):

    def __init__(self, text=""):

        super().__init__()

        self._color = "#A855F7"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(8)

        self.dot = QLabel()
        self.dot.setFixedSize(8, 8)

        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

        self.setMinimumWidth(120)
        self.setMaximumHeight(34)

        self.setColor("#A855F7")

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.label.text()

    def setColor(self, color):

        self._color = color

        self.setStyleSheet(f"""
        QFrame {{
            background:rgba(168,85,247,.08);
            border:1px solid {color};
            border-radius:17px;
        }}

        QLabel {{
            background:transparent;
            color:{color};
            font-size:12px;
            font-weight:700;
        }}
        """)

        self.dot.setStyleSheet(f"""
        background:{color};
        border-radius:4px;
        min-width:8px;
        max-width:8px;
        min-height:8px;
        max-height:8px;
        """)


class SettingsRow(QFrame):

    """
    Reusable:

    Label.....................Widget
    """

    def __init__(
        self,
        title,
        description="",
        widget=None
    ):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 18, 8, 18)
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(4)

        title_lbl = SettingsLabel(title)
        left.addWidget(title_lbl)

        if description:
            desc = DescriptionLabel(description)
            desc.setWordWrap(True)
            left.addWidget(desc)

        #
        # Give the text column all remaining space
        #
        layout.addLayout(left, 1)

        #
        # Keep the badge aligned on the right
        #
        if widget:
            widget.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed
            )

            layout.addWidget(
                widget,
                0,
                Qt.AlignRight | Qt.AlignVCenter
            )


# ============================================================
# Animated Switch
# ============================================================

class ToggleSwitch(QAbstractButton):

    toggledAnimated = Signal(bool)

    def __init__(self):

        super().__init__()

        self.setCursor(Qt.PointingHandCursor)

        self.setCheckable(True)

        self.setFixedSize(58,32)

        self._offset = 3

        self.anim = QPropertyAnimation(
            self,
            b"offset"
        )

        self.anim.setDuration(140)

        self.anim.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.clicked.connect(
            self.startAnimation
        )

    #
    # Property
    #

    def getOffset(self):
        return self._offset

    def setOffset(self,value):
        self._offset=value
        self.update()

    offset = Property(
        float,
        getOffset,
        setOffset
    )

    #
    #

    def startAnimation(self):

        self.anim.stop()

        self.anim.setStartValue(self._offset)

        if self.isChecked():

            self.anim.setEndValue(29)

        else:

            self.anim.setEndValue(3)

        self.anim.start()

        self.toggledAnimated.emit(
            self.isChecked()
        )

    #
    #

    def paintEvent(self,event):

        p = QPainter(self)

        p.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        bg = QColor(
            "#A855F7"
            if self.isChecked()
            else "#394150"
        )

        p.setBrush(bg)

        p.setPen(Qt.NoPen)

        p.drawRoundedRect(
            rect,
            16,
            16
        )

        p.setBrush(Qt.white)

        p.drawEllipse(
            QRectF(
                self._offset,
                3,
                26,
                26
            )
        )


# ============================================================
# Section Header
# ============================================================

class SectionHeader(QWidget):

    def __init__(
        self,
        title,
        subtitle=""
    ):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0,0,0,0)

        lbl = QLabel(title)

        lbl.setStyleSheet("""
        color:white;
        font-size:34px;
        font-weight:800;
        """)

        layout.addWidget(lbl)

        if subtitle:

            sub = QLabel(subtitle)

            sub.setStyleSheet("""
            color:#97A3B5;
            font-size:15px;
            """)

            layout.addWidget(sub)
            
# ============================================================
# Privacy & Security
# ============================================================

class PrivacyPage(QWidget):

    def __init__(self, browser):

        super().__init__()

        self.browser = browser

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setStyleSheet("""
        QScrollArea{
            border:none;
            background:transparent;
        }
        """)

        container = QWidget()

        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(22, 12, 22, 32)
        self.layout.setSpacing(32)

        scroll.setWidget(container)
        root.addWidget(scroll)

        # =====================================================
        # Header
        # =====================================================

        self.layout.addWidget(
            SectionHeader(
                "Privacy & Security",
                "Darkelf permanently enforces the protections below."
            )
        )

        # =====================================================
        # Browser Security
        # =====================================================

        security = SettingsCard("Browser Security")

        self.javascript_badge = StatusBadge("Enabled")

        security.layout.addWidget(
            SettingsRow(
                "JavaScript",
                "Secure JavaScript engine.",
                self.javascript_badge
            )
        )

        security.layout.addWidget(Divider())

        self.fp_badge = StatusBadge("Active")

        security.layout.addWidget(
            SettingsRow(
                "Fingerprint Defense",
                "Canvas, WebGL, AudioContext and Navigator protection.",
                self.fp_badge
            )
        )

        security.layout.addWidget(Divider())

        self.https_badge = StatusBadge("Always On")

        security.layout.addWidget(
            SettingsRow(
                "HTTPS Upgrade",
                "Automatically upgrade insecure requests.",
                self.https_badge
            )
        )

        security.layout.addWidget(Divider())

        self.webrtc_badge = StatusBadge("Blocked")

        security.layout.addWidget(
            SettingsRow(
                "WebRTC",
                "Prevent local and public IP address leaks.",
                self.webrtc_badge
            )
        )

        self.layout.addWidget(security)

        # =====================================================
        # Private Browsing
        # =====================================================

        private = SettingsCard("Private Browsing")

        self.cookies_badge = StatusBadge("Memory")

        private.layout.addWidget(
            SettingsRow(
                "Cookies",
                "Stored only for the current session.",
                self.cookies_badge
            )
        )

        private.layout.addWidget(Divider())

        self.cache_badge = StatusBadge("Memory")

        private.layout.addWidget(
            SettingsRow(
                "Disk Cache",
                "Ephemeral in-memory cache.",
                self.cache_badge
            )
        )

        private.layout.addWidget(Divider())

        self.history_badge = StatusBadge("Disabled")

        private.layout.addWidget(
            SettingsRow(
                "Browsing History",
                "Never written to disk.",
                self.history_badge
            )
        )

        private.layout.addWidget(Divider())

        self.profile_badge = StatusBadge("Private")

        private.layout.addWidget(
            SettingsRow(
                "Browser Profile",
                "Off-the-record profile.",
                self.profile_badge
            )
        )

        self.layout.addWidget(private)
        
        private.layout.addWidget(Divider())

        # -------------------------------------------------
        # Session-only Bookmarks
        # -------------------------------------------------

        self.bookmarks_badge = StatusBadge("Session")

        private.layout.addWidget(
            SettingsRow(
                "Bookmarks",
                "Session-only bookmarks stored in memory.",
                self.bookmarks_badge
            )
        )

        private.layout.addWidget(Divider())

        # -------------------------------------------------
        # Darkelf Quantum
        # -------------------------------------------------

        self.quantum_badge = StatusBadge("Active")

        private.layout.addWidget(
            SettingsRow(
                "Darkelf Quantum",
                "PQ chaining provides session hardening and enhanced memory tokens.",
                self.quantum_badge
            )
        )

        self.layout.addWidget(private)
        
        # =====================================================
        # Network Protection
        # =====================================================

        network = SettingsCard("Network Protection")

        self.tracker_badge = StatusBadge("Active")

        network.layout.addWidget(
            SettingsRow(
                "Tracker Blocking",
                "EasyList and heuristic filtering.",
                self.tracker_badge
            )
        )

        network.layout.addWidget(Divider())

        self.referrer_badge = StatusBadge("Protected")

        network.layout.addWidget(
            SettingsRow(
                "Referrer Protection",
                "Limit cross-site information leakage.",
                self.referrer_badge
            )
        )

        network.layout.addWidget(Divider())

        self.miniai_badge = StatusBadge("Monitoring")

        network.layout.addWidget(
            SettingsRow(
                "MiniAI Sentinel",
                "Real-time network monitoring.",
                self.miniai_badge
            )
        )

        self.layout.addWidget(network)

        # =====================================================
        # Content Filtering
        # =====================================================

        filtering = SettingsCard("Content Filtering")

        self.rules_badge = StatusBadge("Loaded")

        filtering.layout.addWidget(
            SettingsRow(
                "Network Rules",
                "Tracker and advertising filter lists.",
                self.rules_badge
            )
        )

        filtering.layout.addWidget(Divider())

        self.rule_count_badge = StatusBadge("0")

        filtering.layout.addWidget(
            SettingsRow(
                "Rules Loaded",
                "Current active filter rules.",
                self.rule_count_badge
            )
        )

        self.layout.addWidget(filtering)
        
    # ---------------------------------------------------------
    # Accent Synchronization
    # ---------------------------------------------------------

    def applyAccent(self):

        c = (
            self.browser.accent_color.name()
            if isinstance(self.browser.accent_color, QColor)
            else str(self.browser.accent_color)
        )

        badges = (

            self.javascript_badge,
            self.fp_badge,
            self.https_badge,
            self.webrtc_badge,

            self.cookies_badge,
            self.cache_badge,
            self.history_badge,
            self.profile_badge,
            self.bookmarks_badge,
            self.quantum_badge,

            self.tracker_badge,
            self.referrer_badge,
            self.miniai_badge,

            self.rules_badge,
            self.rule_count_badge,

        )

        for badge in badges:
            badge.setColor(c)

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):

        #
        # JavaScript
        #

        enabled = True

        if hasattr(self.browser, "java_action"):
            enabled = self.browser.java_action.isChecked()

        self.javascript_badge.setText(
            "Enabled" if enabled else "Disabled"
        )

        #
        # Browser Profile
        #

        try:

            private = self.browser.shared_profile.isOffTheRecord()

        except Exception:

            private = False

        if private:

            self.cookies_badge.setText("Memory")
            self.cache_badge.setText("Memory")
            self.profile_badge.setText("Private")
            self.history_badge.setText("Disabled")
            self.bookmarks_badge.setText("Session")
            self.quantum_badge.setText("Active")
            
        else:

            self.cookies_badge.setText("Persistent")
            self.cache_badge.setText("Persistent")
            self.profile_badge.setText("Standard")
            self.history_badge.setText("Enabled")
            self.bookmarks_badge.setText("Session")
            self.quantum_badge.setText("Active")
        #
        # Browser protections
        #

        self.fp_badge.setText("Active")
        self.https_badge.setText("Always On")
        self.webrtc_badge.setText("Blocked")
        self.tracker_badge.setText("Active")
        self.referrer_badge.setText("Protected")
        self.miniai_badge.setText("Monitoring")
        self.rules_badge.setText("Loaded")

        # Rule Count
        count = None

        for attr in (
            "network_rule_count",
            "rule_count",
            "rules_loaded",
            "filter_rule_count",
        ):
            value = getattr(self.browser, attr, None)

            if value is not None:
                count = value
                break
        
        count = None

        if hasattr(self.browser, "easy") and hasattr(self.browser.easy, "network_rules"):
            count = len(self.browser.easy.network_rules)

        elif hasattr(self.browser, "easy") and hasattr(self.browser.easy, "rules"):
            count = len(self.browser.easy.rules)

        else:
            count = 0

        self.rule_count_badge.setText(f"{count:,}")

        self.applyAccent()
        
# ============================================================
# Darkelf Quantum
# Place directly ABOVE class AboutPage(QWidget)
# ============================================================

class QuantumPage(QWidget):

    def __init__(self, browser):

        super().__init__()

        self.browser = browser

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setStyleSheet("""
        QScrollArea{
            border:none;
            background:transparent;
        }
        """)

        container = QWidget()

        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(22, 12, 22, 32)
        self.layout.setSpacing(32)

        scroll.setWidget(container)
        root.addWidget(scroll)

        # =====================================================
        # Header
        # =====================================================

        self.layout.addWidget(
            SectionHeader(
                "Darkelf Quantum",
                "Runtime health, watchdog monitoring and post-quantum session integrity."
            )
        )

        # =====================================================
        # Runtime Health
        # =====================================================

        runtime = SettingsCard("Runtime Health")

        self.status_badge = StatusBadge("Active")
        self.watchdog_badge = StatusBadge("Healthy")
        self.integrity_badge = StatusBadge("Verified")
        self.session_badge = StatusBadge("Secure")

        runtime.layout.addWidget(
            SettingsRow(
                "Quantum Engine",
                "Current Quantum runtime status.",
                self.status_badge
            )
        )

        runtime.layout.addWidget(Divider())

        runtime.layout.addWidget(
            SettingsRow(
                "Watchdog",
                "Continuously monitors Quantum runtime health.",
                self.watchdog_badge
            )
        )

        runtime.layout.addWidget(Divider())

        runtime.layout.addWidget(
            SettingsRow(
                "Integrity",
                "Validates Quantum runtime integrity.",
                self.integrity_badge
            )
        )

        runtime.layout.addWidget(Divider())

        runtime.layout.addWidget(
            SettingsRow(
                "Session",
                "Current Quantum session state.",
                self.session_badge
            )
        )

        self.layout.addWidget(runtime)

        # =====================================================
        # Session Statistics
        # =====================================================

        stats = SettingsCard("Session Statistics")

        self.generation_badge = StatusBadge("0")
        self.rekeys_badge = StatusBadge("0")
        self.requests_badge = StatusBadge("0")
        self.tabs_badge = StatusBadge("0")
        self.seed_age_badge = StatusBadge("0s")

        stats.layout.addWidget(
            SettingsRow(
                "Generation",
                "Current Quantum generation.",
                self.generation_badge
            )
        )

        stats.layout.addWidget(Divider())

        stats.layout.addWidget(
            SettingsRow(
                "Rekeys",
                "Quantum runtime resets.",
                self.rekeys_badge
            )
        )

        stats.layout.addWidget(Divider())

        stats.layout.addWidget(
            SettingsRow(
                "Protected Requests",
                "Observed protected requests.",
                self.requests_badge
            )
        )

        stats.layout.addWidget(Divider())

        stats.layout.addWidget(
            SettingsRow(
                "Protected Tabs",
                "Tabs protected by Quantum.",
                self.tabs_badge
            )
        )

        stats.layout.addWidget(Divider())

        stats.layout.addWidget(
            SettingsRow(
                "Session Age",
                "Age of the active Quantum seed.",
                self.seed_age_badge
            )
        )

        self.layout.addWidget(stats)

        # =====================================================
        # Runtime Monitoring
        # =====================================================

        monitor = SettingsCard("Runtime Monitoring")

        monitor.layout.addWidget(
            SettingsRow(
                "Watchdog Monitoring",
                "Continuously validates Quantum runtime.",
                StatusBadge("Enabled")
            )
        )

        monitor.layout.addWidget(Divider())

        monitor.layout.addWidget(
            SettingsRow(
                "Automatic Recovery",
                "Automatically restores runtime integrity when possible.",
                StatusBadge("Enabled")
            )
        )

        monitor.layout.addWidget(Divider())

        monitor.layout.addWidget(
            SettingsRow(
                "Chain Monitoring",
                "Monitors Quantum chain consistency.",
                StatusBadge("Enabled")
            )
        )

        monitor.layout.addWidget(Divider())

        monitor.layout.addWidget(
            SettingsRow(
                "Bounded Memory",
                "Session-only bounded Quantum memory.",
                StatusBadge("Enabled")
            )
        )

        self.layout.addWidget(monitor)

        # =====================================================
        # Quantum Defenses
        # =====================================================

        defenses = SettingsCard("Quantum Defenses")

        defenses.layout.addWidget(
            DescriptionLabel(
                "Darkelf Quantum continuously protects browser sessions using "
                "post-quantum chain evolution, per-tab seeds, bounded session "
                "memory, runtime integrity validation and automatic watchdog "
                "monitoring. All Quantum state remains session-only and is "
                "securely destroyed when the browsing session ends."
            )
        )

        self.layout.addWidget(defenses)

        self.layout.addStretch()

    # ---------------------------------------------------------
    # Accent
    # ---------------------------------------------------------

    def applyAccent(self):

        c = (
            self.browser.accent_color.name()
            if isinstance(self.browser.accent_color, QColor)
            else str(self.browser.accent_color)
        )

        badges = (
            self.status_badge,
            self.watchdog_badge,
            self.integrity_badge,
            self.session_badge,
            self.generation_badge,
            self.rekeys_badge,
            self.requests_badge,
            self.tabs_badge,
            self.seed_age_badge,
        )

        for badge in badges:
            badge.setColor(c)

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):

        interceptor = getattr(
            self.browser.shared_profile,
            "_darkelf_interceptor",
            None
        )

        if interceptor and hasattr(interceptor, "pq"):

            pq = interceptor.pq

            info = pq.status_info()
            health = pq.watchdog()

            self.status_badge.setText(
                info["status"].title()
            )

            self.watchdog_badge.setText(
                "Healthy" if health["healthy"] else "Warning"
            )

            self.integrity_badge.setText(
                "Verified" if health["healthy"] else "Recovered"
            )

            self.session_badge.setText("Secure")

            self.generation_badge.setText(
                str(info["generation"])
            )

            self.rekeys_badge.setText(
                str(info["rekeys"])
            )

            self.requests_badge.setText(
                f'{info["requests"]:,}'
            )

            self.tabs_badge.setText(
                str(info["tabs"])
            )

            self.seed_age_badge.setText(
                f'{info["seed_age"]}s'
            )

        self.applyAccent()
        
class AboutPage(QWidget):

    def __init__(self, browser):
        super().__init__()

        self.browser = browser

        accent = (
            browser.accent_color.name()
            if isinstance(browser.accent_color, QColor)
            else str(browser.accent_color)
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
        QScrollArea{
            border:none;
            background:transparent;
        }
        """)

        container = QWidget()

        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setMaximumWidth(800)
        content.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        outer.addWidget(content, 0, Qt.AlignHCenter | Qt.AlignTop)

        scroll.setWidget(container)
        root.addWidget(scroll)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        layout.addWidget(
            SectionHeader(
                "About",
                "Darkelf Shadow Privacy Browser"
            )
        )

        # -------------------------------------------------
        # About Card
        # -------------------------------------------------

        about = SettingsCard()

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)

        try:
            logo_path = files("shadow").joinpath("assets/darkelf-256.png")
            pixmap = QPixmap(str(logo_path))

            if pixmap.isNull():
                raise RuntimeError(f"Unable to load logo: {logo_path}")

            logo.setPixmap(
                pixmap.scaled(
                    88,
                    88,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

        except Exception as e:
            print("Logo load failed:", e)

            logo.setText("Darkelf")
            logo.setStyleSheet("""
                color:white;
                font-size:30px;
                font-weight:700;
            """)

        title = QLabel("Darkelf Shadow")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
        color:white;
        font-size:30px;
        font-weight:800;
        """)

        version = SettingsChip("Version 6.0", accent)
        license_chip = SettingsChip("LGPL-3.0", accent)

        badges = QHBoxLayout()
        badges.addStretch()
        badges.addWidget(version)
        badges.addWidget(license_chip)
        badges.addStretch()

        description = QLabel(
            "Darkelf Shadow is a hardened privacy browser built on Qt "
            "WebEngine. It runs entirely in memory, blocks trackers, "
            "upgrades HTTP connections to HTTPS, defends against browser "
            "fingerprinting, blocks WebRTC IP leaks and includes the "
            "MiniAI Sentinel for real-time protection."
        )

        description.setWordWrap(True)

        description.setStyleSheet("""
        color:#98A2B3;
        font-size:15px;
        line-height:24px;
        """)

        about.layout.addWidget(logo)
        about.layout.addWidget(title)
        about.layout.addLayout(badges)
        about.layout.addSpacing(8)
        about.layout.addWidget(description)

        layout.addWidget(about)

        # -------------------------------------------------
        # Features
        # -------------------------------------------------

        features = SettingsCard("Protection Features")

        flow = QHBoxLayout()
        flow.setSpacing(10)

        for text in (
            "Private Mode",
            "Tracker Block",
            "HTTPS",
            "Fingerprints",
            "WebRTC Block",
            "MiniAI Sentinel",
        ):
            flow.addWidget(SettingsChip(text, accent))

        flow.addStretch()

        features.layout.addLayout(flow)

        layout.addWidget(features)

        # -------------------------------------------------
        # Resources
        # -------------------------------------------------

        resources = SettingsCard("Resources")

        github = QPushButton("GitHub")
        pypi = QPushButton("PyPI")
        issues = QPushButton("Report Issue")
        license_btn = QPushButton("License")

        buttons = (github, pypi, issues, license_btn)

        for btn in buttons:

            btn.setCursor(Qt.PointingHandCursor)

            btn.setStyleSheet(f"""
            QPushButton{{
                background:#171d27;
                color:white;
                border:1px solid #2c3443;
                border-radius:12px;
                padding:10px 20px;
                font-weight:600;
            }}

            QPushButton:hover{{
                border:1px solid {accent};
                background:#1d2430;
            }}
            """)

        github.clicked.connect(
            lambda: self.open_url(
                QUrl("https://github.com/Darkelf2024/Darkelf-Shadow")
            )
        )

        pypi.clicked.connect(
            lambda: self.open_url(
                QUrl("https://pypi.org/project/darkelf-shadow/")
            )
        )

        issues.clicked.connect(
            lambda: self.open_url(
                QUrl("https://github.com/Darkelf2024/Darkelf-Shadow/issues")
            )
        )

        license_btn.clicked.connect(
            lambda: self.open_url(
                QUrl("https://www.gnu.org/licenses/lgpl-3.0.html")
            )
        )

        row = QHBoxLayout()

        row.addWidget(github)
        row.addWidget(pypi)
        row.addWidget(issues)
        row.addWidget(license_btn)
        row.addStretch()

        resources.layout.addLayout(row)

        layout.addWidget(resources)

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

        footer = QLabel(
            "© 2025 Dr. Kevin Moore • TeeM • Darkelf Project • Shadow Edition"
        )

        footer.setAlignment(Qt.AlignCenter)

        footer.setStyleSheet("""
        QLabel{
            color:#697586;
            font-size:12px;
            padding:20px;
        }
        """)

        layout.addWidget(footer)

        layout.addStretch()

    # ---------------------------------------------------------
    # Open links inside Darkelf
    # ---------------------------------------------------------

    def open_url(self, url: QUrl):

        try:
            # Open in a new Darkelf tab
            if hasattr(self.browser, "navigate_to"):
                self.browser.navigate_to(url.toString())
                return

            # Alternative browser implementations
            if hasattr(self.browser, "add_new_tab"):
                self.browser.add_new_tab(url)
                return

            # Fallback: open blank tab then load URL
            if hasattr(self.browser, "new_tab"):
                self.browser.new_tab()

                view = self.browser.current_view()
                if view:
                    view.load(url)

                return

        except Exception as e:
            print("open_url:", e)

        # Final fallback
        QDesktopServices.openUrl(url)

    # ---------------------------------------------------------

    def refresh(self):
        pass
# ------------------------------------------------------------
# Section Card
# ------------------------------------------------------------

class SettingsCard(QFrame):

    def __init__(self, title="", parent=None):
        super().__init__(parent)

        self.setObjectName("SettingsCard")

        self.setStyleSheet("""
        QFrame#SettingsCard{

            background:qlineargradient(
                x1:0,y1:0,
                x2:0,y2:1,

                stop:0 #121821,
                stop:1 #0D1219
            );

            border:1px solid rgba(168,85,247,.18);

            border-radius:22px;
        }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24,24,24,24)
        self.layout.setSpacing(18)

        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("""
                color:white;
                font-size:22px;
                font-weight:700;
            """)
            self.layout.addWidget(lbl)


# ------------------------------------------------------------
# Accent Color Button
# ------------------------------------------------------------

class AccentButton(QPushButton):

    clickedColor = Signal(str)

    def __init__(self, color):
        super().__init__()

        self.color = color

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(42,42)

        self.setStyleSheet(f"""
        QPushButton{{
            background:{color};
            border:none;
            border-radius:21px;
        }}

        QPushButton:hover{{
            border:3px solid white;
        }}

        QPushButton:pressed{{
            border:3px solid black;
        }}
        """)

        self.clicked.connect(
            lambda: self.clickedColor.emit(color)
        )

# ------------------------------------------------------------
# Theme Preview Card
# ------------------------------------------------------------

class ThemeCard(QFrame):

    selected = Signal(str)

    def __init__(self, name, colors):
        super().__init__()

        self.themeName = name

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(220, 150)

        self.setStyleSheet("""
        QFrame{
            background:#10131a;
            border:1px solid #2a3140;
            border-radius:18px;
        }

        QFrame:hover{
            border:2px solid #A855F7;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        preview = QFrame()
        preview.setMinimumHeight(70)

        preview.setStyleSheet(f"""
        background:qlineargradient(
            x1:0,y1:0,
            x2:1,y2:1,
            stop:0 {colors[0]},
            stop:.5 {colors[1]},
            stop:1 {colors[2]}
        );
        border-radius:14px;
        """)

        layout.addWidget(preview)

        label = QLabel(name)
        label.setStyleSheet("""
        color:white;
        font-size:16px;
        font-weight:600;
        """)
        layout.addWidget(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.themeName)

        super().mousePressEvent(event)

    def selectTheme(self, name):
        # Save the selected theme
        self.browser.homepage_theme = name
        
        self.browser.refresh_homepage()

        # If the browser has a method to rebuild the homepage, use it
        if hasattr(self.browser, "refresh_homepage"):
            self.browser.refresh_homepage()
            return

        # Otherwise refresh the currently displayed homepage tab
        try:
            view = self.browser.current_view()

            if view is not None:
                url = view.url().toString().lower()

                # Adjust these conditions to match your homepage URL if needed
                if (
                    url == ""
                    or url == "about:blank"
                    or url.startswith("darkelf:")
                    or "homepage" in url
                ):
                    view.reload()
        except Exception as e:
            print("Theme refresh:", e)
        
# ------------------------------------------------------------
# Appearance
# ------------------------------------------------------------

class AppearancePage(QWidget):

    def __init__(self,browser):

        super().__init__()

        self.browser = browser

        root = QVBoxLayout(self)

        root.setContentsMargins(0,0,0,0)

        root.setSpacing(24)

        title = QLabel("Appearance")

        title.setStyleSheet("""
        font-size:34px;
        color:white;
        font-weight:800;
        """)

        subtitle = QLabel(
            "Customize Darkelf's appearance."
        )

        subtitle.setStyleSheet("""
        color:#9aa5b2;
        font-size:15px;
        """)

        root.addWidget(title)
        root.addWidget(subtitle)

        #
        # Accent Colors
        #

        accentCard = SettingsCard("Accent Color")

        colors = [
            "#A855F7",
            "#3B82F6",
            "#10B981",
            "#EF4444",
            "#F97316",
            "#06B6D4",
            "#EC4899",
            "#EAB308",
            "#8B5CF6",
            "#14B8A6",
        ]

        row = QHBoxLayout()

        row.setSpacing(12)

        for color in colors:

            btn = AccentButton(color)

            btn.clickedColor.connect(
                self.changeAccent
            )

            row.addWidget(btn)

        row.addStretch()

        accentCard.layout.addLayout(row)

        root.addWidget(accentCard)

        #
        # Themes
        #

        themeCard = SettingsCard("Background")

        grid = QGridLayout()

        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        themes = [

            ("Aurora",
             ["#2E026D","#A855F7","#34D399"]),

            ("Nebula",
             ["#000428","#004e92","#8E2DE2"]),

            ("Void",
             ["#050505","#111111","#2b2b2b"]),

            ("Matrix",
             ["#031403","#0B6E4F","#00ff66"]),

            ("Circuit",
             ["#07131F","#0F4C81","#4ADEDE"]),

            ("Graded",
             ["#1f2937","#374151","#9ca3af"])
        ]

        r=0
        c=0

        for name,cols in themes:

            card = ThemeCard(name,cols)

            card.selected.connect(
                self.selectTheme
            )

            grid.addWidget(card,r,c)

            c+=1

            if c==3:
                c=0
                r+=1

        themeCard.layout.addLayout(grid)

        root.addWidget(themeCard)

        root.addStretch()
        
    def applyAccent(self):

        c = accent(self.browser)

        self.setStyleSheet(f"""
        QLabel {{
            color:white;
        }}

        QFrame#SettingsCard {{
            background:#11161d;
            border:1px solid #252c37;
            border-radius:20px;
        }}

        QPushButton:hover {{
            border:1px solid {c};
        }}
        """)
        
    # -------------------------------------------------

    def changeAccent(self, color):

        self.browser.set_accent_color(QColor(color))

        dlg = self.window()

        if hasattr(dlg, "applyAccent"):
            dlg.applyAccent()

    # -------------------------------------------------

    def selectTheme(self, name):

        # Save selected homepage theme
        self.browser.homepage_theme = name

        # Persist if using QSettings
        if hasattr(self.browser, "settings"):
            try:
                self.browser.settings.setValue(
                    "homepage_theme",
                    name
                )
            except Exception as e:
                print(f"Unable to save homepage theme: {e}")
                
        # Rebuild homepage immediately
        if hasattr(self.browser, "refresh_homepage"):
            self.browser.refresh_homepage()

    # -------------------------------------------------

    def refresh(self):
        pass
