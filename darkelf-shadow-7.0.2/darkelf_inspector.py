# darkelf_console.py

import math
import json
import time
import traceback
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QFont,
    QKeyEvent,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSplitter,
    QTabWidget,
    QPlainTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
)



# ------------------------------------------------------------
# Darkelf Console Theme
# ------------------------------------------------------------

DARKELF_BG = "#05070b"
DARKELF_PANEL = "#0b0f14"
DARKELF_PANEL_2 = "#0f1720"
DARKELF_CARD = "#111827"
DARKELF_BORDER = "#243244"

DARKELF_TEXT = "#e8f0ff"
DARKELF_MUTED = "#8f9bad"
DARKELF_DIM = "#5d6b7a"

DARKELF_ACCENT = "#A855F7"
DARKELF_ACCENT_2 = "#7C3AED"
DARKELF_SUCCESS = "#42d97d"
DARKELF_WARN = "#f6c453"
DARKELF_DANGER = "#ff365e"
DARKELF_INFO = "#38bdf8"

FONT_UI = '"Inter", "SF Pro Display", "Segoe UI", Arial'
FONT_MONO = '"Menlo", "Monaco", monospace'

def now_stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def safe_text(value) -> str:
    try:
        return str(value)
    except Exception:
        return "<unprintable>"


# ------------------------------------------------------------
# Small UI Helpers
# ------------------------------------------------------------

class PillLabel(QLabel):
    def __init__(self, text="", color=DARKELF_ACCENT, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: rgba(168, 85, 247, 0.10);
                border: 1px solid {color};
                border-radius: 12px;
                padding: 2px 10px;
                font-family: {FONT_UI};
                font-size: 11px;
                font-weight: 700;
            }}
        """)


class SectionTitle(QLabel):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        if subtitle:
            self.setText(f"{title}\n{subtitle}")
        else:
            self.setText(title)

        self.setStyleSheet(f"""
            QLabel {{
                color: {DARKELF_TEXT};
                font-family: {FONT_UI};
                font-size: 14px;
                font-weight: 800;
                padding: 4px 0;
            }}
        """)


class DarkelfCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DarkelfCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame#DarkelfCard {{
                background: {DARKELF_PANEL};
                border: 1px solid {DARKELF_BORDER};
                border-radius: 14px;
            }}
        """)


# ------------------------------------------------------------
# Console Output
# ------------------------------------------------------------

class ConsoleWidget(QPlainTextEdit):
    """
    Main console log area.

    This is safer than QTextEdit for log output and better suited for
    high-volume diagnostic messages.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.history = []
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setMaximumBlockCount(5000)

        self.setFont(QFont("Menlo", 11))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {DARKELF_BG};
                color: {DARKELF_TEXT};
                border: 1px solid {DARKELF_BORDER};
                border-radius: 12px;
                padding: 10px;
                selection-background-color: {DARKELF_ACCENT_2};
                font-family: {FONT_MONO};
                font-size: 12px;
            }}
        """)

        self.banner()

    def banner(self):
        self.log("Darkelf Inspector initialized.", level="system")

    def log(self, text: str, level: str = "log"):
        text = safe_text(str(text))
        stamp = now_stamp()

        prefixes = {
            "system":   "[SYSTEM]",
            "info":     "[INFO]",
            "warn":     "[WARN]",
            "error":    "[ERROR]",
            "security": "[SECURITY]",
            "quantum":  "[QUANTUM]",
            "miniai":   "[MINIAI]",
            "network":  "[NETWORK]",
            "js":       "[JS]",
            "cmd":      ">",
            "log":      "[LOG]",
        }

        prefix = prefixes.get(level.lower(), "[LOG]")
        line = f"{stamp} {prefix} {text}"

        self.appendPlainText(line)

        self.history.append(line)

        # Prevent unlimited history growth
        MAX_HISTORY = 2000

        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]

            self.setPlainText("\n".join(self.history))

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

        self.ensureCursorVisible()

    def clear_console(self):
        self.clear()
        self.history.clear()
        self.log("Console cleared.", level="system")


# ------------------------------------------------------------
# Command Input
# ------------------------------------------------------------

class InputLine(QLineEdit):
    """
    Command input with history navigation.

    Up/Down arrows cycle command history.
    Enter executes through the parent connection.
    """

    history_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.command_history = []
        self.history_index = -1

        self.setFont(QFont("Menlo", 11))
        self.setPlaceholderText(
            "Enter a Darkelf command..."
        )
        self.setMinimumHeight(34)

        self.setStyleSheet(f"""
            QLineEdit {{
                background: {DARKELF_PANEL_2};
                color: {DARKELF_TEXT};
                border: 1px solid {DARKELF_BORDER};
                border-radius: 10px;
                padding: 7px 10px;
                font-family: {FONT_MONO};
                font-size: 12px;
            }}

            QLineEdit:focus {{
                border: 1px solid {DARKELF_ACCENT};
                background: #0d1320;
            }}
        """)

    def remember(self, command: str):
        command = command.strip()
        if not command:
            return

        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)

        self.history_index = len(self.command_history)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            if self.command_history:
                self.history_index = max(0, self.history_index - 1)
                self.setText(self.command_history[self.history_index])
                self.setCursorPosition(len(self.text()))
            return

        if event.key() == Qt.Key.Key_Down:
            if self.command_history:
                self.history_index = min(len(self.command_history), self.history_index + 1)

                if self.history_index >= len(self.command_history):
                    self.clear()
                else:
                    self.setText(self.command_history[self.history_index])
                    self.setCursorPosition(len(self.text()))
            return

        super().keyPressEvent(event)
        
# ------------------------------------------------------------
# Main Darkelf Inspector
# ------------------------------------------------------------

class DarkelfInspector(QWidget):
    """
    Darkelf Inspector shell.

    This class owns the main UI:
    - Header
    - Tool tabs
    - Console input/output
    - Status strip

    Browser integration hooks will be added in later parts.
    """

    def __init__(
        self,
        browser=None,
        webview=None,
        mini_ai=None,
        quantum=None,
        accent_color=DARKELF_ACCENT,
        parent=None,
    ):
        super().__init__(parent)

        self.browser = browser
        self.webview = webview
        self.mini_ai = mini_ai
        self.quantum = quantum
        self.accent_color = accent_color or DARKELF_ACCENT

        self.setWindowTitle("Darkelf Inspector")
        self.resize(1180, 720)
        self.setMinimumSize(920, 560)

        self.locals = {
            "pi": math.pi,
            "e": math.e,
            "sqrt": math.sqrt,
            "json": json,
            "time": time,
            "__builtins__": {
                "abs": abs,
                "min": min,
                "max": max,
                "round": round,
                "len": len,
                "sum": sum,
            },
        }

        self._request_count = 0
        self._blocked_count = 0

        self.init_ui()
        self.init_theme()
        self.seed_console()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_runtime)
        self.refresh_timer.start(2000)
    
    def _refresh_runtime(self):
        """
        Silent periodic refresh.

        Stops refreshing Quantum after its runtime has been destroyed,
        while allowing MiniAI and the rest of the Inspector to remain usable.
        """

        if not self.isVisible():
            return

        try:
            self.refresh_quantum()
        except RuntimeError as e:
            if "destroyed" in str(e).lower():
                self.quantum_pill.setText("QUANTUM: DESTROYED")
                self.quantum_pill.setStyleSheet(
                    self._pill_style(DARKELF_WARN)
                )

                self.q_status.setText("DESTROYED")
                self.q_generation.setText("--")
                self.q_requests.setText("--")
                self.q_observed.setText("--")
                self.q_rekeys.setText("--")
                self.q_seed_age.setText("--")
                self.q_runtime.setText("STOPPED")
                self.q_health.setText("UNAVAILABLE")
                self.q_chain_short.setText("--")
                self.quantum_chain.setPlainText("Quantum runtime destroyed.")

            else:
                self.console.log(
                    f"Quantum refresh failed: {e}",
                    "error",
                )

        except Exception as e:
            self.console.log(
                f"Quantum refresh failed: {e}",
                "error",
            )

        try:
            self.refresh_miniai()
        except Exception as e:
            self.console.log(
                f"MiniAI refresh failed: {e}",
                "error",
            )

        self.status_label.setText("Status: Monitoring")
    
    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # -------------------------
        # Header
        # -------------------------
        header = QFrame()
        header.setObjectName("DevToolsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)

        self.title_label = QLabel("Darkelf Inspector")
        self.title_label.setObjectName("DevToolsTitle")

        self.subtitle_label = QLabel(
            "Console • Network • Quantum • MiniAI"
        )
        self.subtitle_label.setObjectName("DevToolsSubtitle")

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)

        header_layout.addLayout(title_box)
        header_layout.addStretch(1)

        self.status_pill = PillLabel("READY", self.accent_color)
        self.quantum_pill = PillLabel("QUANTUM: STANDBY", DARKELF_INFO)
        self.miniai_pill = PillLabel("MINIAI: MONITORING", DARKELF_SUCCESS)

        header_layout.addWidget(self.status_pill)
        header_layout.addWidget(self.quantum_pill)
        header_layout.addWidget(self.miniai_pill)

        root.addWidget(header)

        # -------------------------
        # Main Tabs
        # -------------------------

        self.tabs = QTabWidget()
        self.tabs.setObjectName("DevToolsTabs")

        root.addWidget(self.tabs, 1)

        self.console_tab = QWidget()
        self.network_tab = QWidget()
        self.quantum_tab = QWidget()
        self.miniai_tab = QWidget()
        self.shortcuts_tab = QWidget()
        self.help_tab = QWidget()

        self.tabs.addTab(self.console_tab, "Console")
        self.tabs.addTab(self.network_tab, "Network")
        self.tabs.addTab(self.quantum_tab, "Quantum")
        self.tabs.addTab(self.miniai_tab, "MiniAI")
        self.tabs.addTab(self.shortcuts_tab, "Shortcuts")
        self.tabs.addTab(self.help_tab, "Help")

        self._build_console_tab()
        self._build_placeholder_tabs()
        
        for editor in self.findChildren(QPlainTextEdit):
            editor.setContextMenuPolicy(Qt.NoContextMenu)
        # -------------------------
        # Status Strip
        # -------------------------
        self.status_strip = QFrame()
        self.status_strip.setObjectName("StatusStrip")
        status_layout = QHBoxLayout(self.status_strip)
        status_layout.setContentsMargins(10, 4, 10, 4)
        status_layout.setSpacing(16)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setObjectName("StatusText")

        self.request_label = QLabel("Requests: 0")
        self.blocked_label = QLabel("Blocked: 0")
        self.renderer_label = QLabel("Renderer: Attached" if self.webview else "Renderer: Detached")

        for label in (
            self.status_label,
            self.request_label,
            self.blocked_label,
            self.renderer_label,
        ):
            label.setObjectName("StatusText")
            status_layout.addWidget(label)

        status_layout.addStretch(1)

        root.addWidget(self.status_strip)

    def _build_console_tab(self):
        layout = QVBoxLayout(self.console_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setObjectName("ConsoleSplitter")

        self.console = ConsoleWidget()
        self.console.setContextMenuPolicy(Qt.NoContextMenu)
        splitter.addWidget(self.console)

        input_card = DarkelfCard()
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        self.input_line = InputLine()

        self.run_button = QPushButton("Run")
        self.clear_button = QPushButton("Clear")

        for btn in (
            self.run_button,
            self.clear_button,
        ):
            btn.setMinimumHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.run_button.setObjectName("AccentButton")
        input_layout.addWidget(self.input_line, 1)
        input_layout.addWidget(self.run_button)
        input_layout.addWidget(self.clear_button)

        splitter.addWidget(input_card)
        splitter.setStretchFactor(0, 8)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self.run_button.clicked.connect(self.execute_command)
        self.clear_button.clicked.connect(self.console.clear_console)
        self.input_line.returnPressed.connect(self.execute_command)
        
    def _build_placeholder_tabs(self):
        self._build_network_tab()
        self._build_quantum_tab()
        self._build_miniai_tab()
        self._build_shortcuts_tab()
        self._build_help_tab()
        
    def _clear_network_log(self):
        self.network_log.clear()

        self._request_count = 0
        self._blocked_count = 0

        self.net_total.setText("Requests: 0")
        self.net_blocked.setText("Blocked: 0")
        self.net_active.setText("Events: 0")
        
    # --------------------------------------------------------
    # Network
    # --------------------------------------------------------

    def _build_network_tab(self):
        layout = QVBoxLayout(self.network_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(
            SectionTitle(
                "Network Monitor",
                "Live Security / Network Events"
            )
        )

        toolbar = QHBoxLayout()

        self.net_total = QLabel("Requests: 0")
        self.net_blocked = QLabel("Blocked: 0")
        self.net_active = QLabel("Events: 0")

        toolbar.addWidget(self.net_total)
        toolbar.addSpacing(20)
        toolbar.addWidget(self.net_blocked)
        toolbar.addSpacing(20)
        toolbar.addWidget(self.net_active)
        toolbar.addStretch()

        self.net_clear = QPushButton("Clear")
        toolbar.addWidget(self.net_clear)

        layout.addLayout(toolbar)

        self.network_log = QPlainTextEdit()
        self.network_log.setReadOnly(True)
        self.network_log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(self.network_log, 1)

        self.net_clear.clicked.connect(self._clear_network_log)
            
    # --------------------------------------------------------
    # Quantum
    # --------------------------------------------------------

    def _build_quantum_tab(self):
        layout = QVBoxLayout(self.quantum_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            SectionTitle(
                "Darkelf Quantum",
                "Runtime Telemetry Dashboard"
            )
        )

        dashboard = DarkelfCard()

        grid = QGridLayout(dashboard)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        def create_stat_card(title):

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {DARKELF_CARD};
                    border: 1px solid {DARKELF_BORDER};
                    border-radius: 10px;
                }}
            """)

            v = QVBoxLayout(card)
            v.setContentsMargins(10, 8, 10, 8)
            v.setSpacing(4)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                color:{DARKELF_MUTED};
                font-size:11px;
                font-weight:600;
                border:none;
            """)

            value_lbl = QLabel("--")
            value_lbl.setStyleSheet(f"""
                color:{DARKELF_TEXT};
                font-size:18px;
                font-weight:700;
                border:none;
            """)

            v.addWidget(title_lbl)
            v.addWidget(value_lbl)
            v.addStretch()

            return card, value_lbl

        labels = [
            ("Status", "q_status"),
            ("Generation", "q_generation"),
            ("Requests", "q_requests"),

            ("Observed", "q_observed"),
            ("Rekeys", "q_rekeys"),
            ("Seed Age", "q_seed_age"),

            ("Runtime", "q_runtime"),
            ("Health", "q_health"),
            ("Chain", "q_chain_short"),
        ]

        index = 0

        for row in range(3):
            for col in range(3):

                title, attr = labels[index]

                card, value = create_stat_card(title)

                setattr(self, attr, value)

                grid.addWidget(card, row, col)

                index += 1

        layout.addWidget(dashboard)

        chain_card = DarkelfCard()

        chain_layout = QVBoxLayout(chain_card)
        chain_layout.setContentsMargins(12, 12, 12, 12)
        chain_layout.setSpacing(8)

        chain_layout.addWidget(
            SectionTitle(
                "Quantum Chain",
                "Current post-quantum chain"
            )
        )

        self.quantum_chain = QPlainTextEdit()
        self.quantum_chain.setReadOnly(True)
        self.quantum_chain.setMaximumHeight(90)
        self.quantum_chain.setPlainText("Unavailable")

        self.quantum_chain.setStyleSheet(f"""
            QPlainTextEdit {{
                background:{DARKELF_PANEL};
                border:1px solid {DARKELF_BORDER};
                border-radius:8px;
                color:{DARKELF_TEXT};
                font-family:Menlo, Consolas, monospace;
                font-size:11px;
                padding:8px;
            }}
        """)

        chain_layout.addWidget(self.quantum_chain)

        layout.addWidget(chain_card)

        layout.addStretch()

    # --------------------------------------------------------
    # MiniAI
    # --------------------------------------------------------

    def _build_miniai_tab(self):
        layout = QVBoxLayout(self.miniai_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            SectionTitle(
                "MiniAI",
                "Threat Intelligence Dashboard"
            )
        )

        dashboard = DarkelfCard()
        grid = QGridLayout(dashboard)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        def create_stat_card(title):

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {DARKELF_CARD};
                    border: 1px solid {DARKELF_BORDER};
                    border-radius: 10px;
                }}
            """)

            v = QVBoxLayout(card)
            v.setContentsMargins(10, 8, 10, 8)
            v.setSpacing(4)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                color: {DARKELF_MUTED};
                font-size: 11px;
                font-weight: 600;
                border: none;
            """)

            value_lbl = QLabel("0")
            value_lbl.setStyleSheet(f"""
                color: {DARKELF_TEXT};
                font-size: 18px;
                font-weight: 700;
                border: none;
            """)

            v.addWidget(title_lbl)
            v.addWidget(value_lbl)
            v.addStretch()

            return card, value_lbl

        labels = [
            ("State", "ai_state"),
            ("Threat Score", "ai_threat"),
            ("Trackers", "ai_trackers"),

            ("Intrusions", "ai_intrusions"),
            ("Fingerprinting", "ai_fingerprint"),
            ("HTTP Blocks", "ai_blocks"),

            ("Malware", "ai_malware"),
            ("Exploits", "ai_exploits"),
            ("Unique Domains", "ai_domains"),

            ("Lockdown", "ai_lockdown"),
            ("Panic Mode", "ai_panic"),
            ("Uptime", "ai_uptime"),
        ]

        index = 0

        for row in range(4):
            for col in range(3):

                title, attr = labels[index]

                card, value = create_stat_card(title)

                setattr(self, attr, value)

                grid.addWidget(card, row, col)

                index += 1

        layout.addWidget(dashboard)
        layout.addStretch()
        
    def _build_shortcuts_tab(self):
        layout = QVBoxLayout(self.shortcuts_tab)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(
            SectionTitle(
                "Keyboard Shortcuts",
                "Darkelf Shadow Browser Hotkeys"
            )
        )

        shortcuts = QPlainTextEdit()
        shortcuts.setReadOnly(True)

        shortcuts.setPlainText("""
    Darkelf Shadow Keyboard Shortcuts
    ══════════════════════════════════════════════

    Tabs
    ──────────────────────────────────────────────

    ⌘ T
        Open New Tab

    ⌘ W
        Close Current Tab

    ⌘ Tab
    ⌘ Page Down
    ⌥ →
        Next Tab

    ⌘ Page Up
    ⌥ ←
        Previous Tab

    ──────────────────────────────────────────────

    Navigation
    ──────────────────────────────────────────────

    ⌘ L
        Focus Address Bar

    ⌘ R
        Reload Current Page

    ──────────────────────────────────────────────

    Find
    ──────────────────────────────────────────────

    ⌘ F
        Open Find Bar

    ⌘ G
        Find Next Match

    ──────────────────────────────────────────────

    Zoom
    ──────────────────────────────────────────────

    ⌘ +
        Zoom In

    ⌘ –
        Zoom Out

    ⌘ 0
        Reset Zoom

    ──────────────────────────────────────────────

    Snapshots
    ──────────────────────────────────────────────

    ⌘ ⇧ S
        Take Snapshot

    ──────────────────────────────────────────────

    Window
    ──────────────────────────────────────────────

    F11
    ⌥ Return
    ⌥ Enter
    ⌘ Return
        Toggle Fullscreen

    ══════════════════════════════════════════════

    Darkelf Shadow
    macOS Keyboard Shortcuts
    """)

        shortcuts.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {DARKELF_PANEL};
                border: 1px solid {DARKELF_BORDER};
                border-radius: 10px;
                color: {DARKELF_TEXT};
                font-family: "Menlo";
                font-size: 12px;
                padding: 10px;
            }}
        """)

        layout.addWidget(shortcuts)
        
    def _build_help_tab(self):
        layout = QVBoxLayout(self.help_tab)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(
            SectionTitle(
                "Darkelf Inspector",
                "Integrated Runtime Diagnostics"
            )
        )

        help_text = QPlainTextEdit()
        help_text.setReadOnly(True)

        help_text.setPlainText("""
    Darkelf Inspector
    ════════════════════════════════════════════

    Darkelf Inspector is the integrated runtime
    diagnostic environment for Darkelf Shadow.

    It provides live visibility into browser
    activity, network security, post-quantum
    telemetry and the MiniAI defensive engine.

    ════════════════════════════════════════════
    Console
    ════════════════════════════════════════════

    The Console executes JavaScript inside the
    currently active browser tab.

    Available commands

    • help
        Open this Help page.

    • clear
        Clear the Inspector console.

    • history
        Display recent console history.

    • info
        Display current runtime information.

    Any other text entered into the Console is
    executed as JavaScript in the active page.

    ════════════════════════════════════════════
    Network
    ════════════════════════════════════════════

    The Network tab displays live events received
    from the Darkelf Interceptor.

    Examples include

    • HTTP / HTTPS requests
    • Blocked trackers
    • Blocked scripts
    • Privacy protection events
    • HTTPS upgrades
    • MiniAI protection events
    • Runtime security notifications

    Use the Clear button to reset the log.

    ════════════════════════════════════════════
    Darkelf Quantum
    ════════════════════════════════════════════

    Darkelf Quantum continuously monitors the
    browser's post-quantum runtime.

    Dashboard information includes

    • Runtime status
    • Generation
    • Request count
    • Observed requests
    • Rekey operations
    • Seed age
    • Runtime health
    • Active chain identifier

    The Quantum Chain panel displays the current
    post-quantum chain maintained during the
    browser session.

    ════════════════════════════════════════════
    MiniAI
    ════════════════════════════════════════════

    MiniAI continuously monitors browser activity
    for suspicious behavior and privacy threats.

    Dashboard information includes

    • Monitoring state
    • Threat score
    • Tracker detections
    • Fingerprinting detections
    • HTTP blocks
    • Malware detections
    • Exploit detections
    • Unique domains observed
    • Lockdown status
    • Panic Mode
    • Runtime uptime

    MiniAI automatically escalates from
    Monitoring → Lockdown → Panic Mode when
    configured threat thresholds are reached.

    ════════════════════════════════════════════
    Inspector Overview
    ════════════════════════════════════════════

    Console
        Execute JavaScript and inspect results.

    Network
        View live browser and security events.

    Darkelf Quantum
        Monitor runtime health and post-quantum
        telemetry.

    MiniAI
        Monitor live browser protection and
        defensive statistics.

    Help
        View Inspector documentation.

    ════════════════════════════════════════════

    Darkelf Shadow

    Darkelf Inspector
    Version 6.0

    Integrated Runtime Diagnostics
    """)

        help_text.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {DARKELF_PANEL};
                border: 1px solid {DARKELF_BORDER};
                border-radius: 10px;
                color: {DARKELF_TEXT};
                font-family: "Menlo";
                font-size: 12px;
                padding: 10px;
            }}
        """)

        layout.addWidget(help_text)
    # --------------------------------------------------------
    # Command Engine
    # --------------------------------------------------------

    def seed_console(self):
        self.console.log("Darkelf Console online.", "system")

    def execute_command(self):
        cmd = self.input_line.text().strip()

        if not cmd:
            return

        self.input_line.remember(cmd)
        self.input_line.clear()

        self.console.log(cmd, "cmd")
        self.status_label.setText("Status: Running command")

        lower = cmd.lower()

        try:
            if lower in ("help", "?"):
                self.show_help()

            elif lower == "clear":
                self.console.clear_console()

            elif lower == "history":
                self.show_history()

            elif lower == "info":
                self.show_runtime_info()

            else:
                # Default behavior: treat unknown input as JavaScript first
                self.run_javascript(cmd)

        except Exception as e:
            self.console.log(f"{e}", "error")
            self.console.log(traceback.format_exc(), "error")

        self.status_label.setText("Status: Idle")
        
    def show_help(self):
        self.tabs.setCurrentWidget(self.help_tab)
        
    def show_history(self):
        if not self.console.history:
            self.console.log("No history yet.", "info")
            return

        for index, line in enumerate(self.console.history[-50:], 1):
            self.console.log(f"{index}: {line}", "log")


    def show_runtime_info(self):
        self.console.log("Runtime information:", "system")
        self.console.log(f"Browser attached: {bool(self.browser)}", "info")
        self.console.log(f"WebView attached: {bool(self.webview)}", "info")
        self.console.log(f"MiniAI attached: {bool(self.mini_ai)}", "info")
        self.console.log(f"Quantum attached: {bool(self.quantum)}", "info")

        if self.webview:
            try:
                url = self.webview.url().toString()
                self.console.log(f"Current URL: {url}", "info")
            except Exception as e:
                self.console.log(f"Unable to read page URL: {e}", "warn")

    def run_javascript(self, code: str):
        code = code.strip()

        if not code:
            return

        view = self._active_webview()

        if view is None:
            self.console.log("No active browser tab available.", "warn")
            return

        page = view.page()

        if page is None:
            self.console.log("Active browser tab has no page.", "error")
            return

        self.console.log(code, "cmd")

        def _finished(result):
            try:
                if result is None:
                    self.console.log("undefined", "js")
                elif isinstance(result, (dict, list)):
                    self.console.log(
                        json.dumps(result, indent=2, ensure_ascii=False),
                        "js",
                    )
                else:
                    self.console.log(str(result), "js")
            except Exception:
                self.console.log(safe_text(result), "js")

        try:
            page.runJavaScript(code, _finished)
        except Exception as e:
            self.console.log(
                f"JavaScript execution failed: {e}",
                "error",
            )

    def _active_webview(self):
        if self.webview:
            return self.webview

        if self.browser and hasattr(self.browser, "current_view"):
            try:
                return self.browser.current_view()
            except Exception:
                return None

        return None
        
    # --------------------------------------------------------
    # Darkelf Runtime Integration
    # --------------------------------------------------------

    def refresh_quantum(self):
        """
        Refresh the Darkelf Quantum dashboard safely.
        """

        pq = self._resolve_quantum()

        if pq is None:
            self._set_quantum_unavailable("UNAVAILABLE")
            return

        try:
            if hasattr(pq, "status_info"):
                stats = pq.status_info()
            elif hasattr(pq, "status"):
                stats = {"status": pq.status()}
            else:
                self._set_quantum_unavailable("UNAVAILABLE")
                return

            status = str(stats.get("status", "UNKNOWN")).upper()
            chain = stats.get("chain") or getattr(pq, "chain", "")

            self.q_status.setText(status)
            self.q_generation.setText(str(stats.get("generation", 0)))
            self.q_requests.setText(str(stats.get("requests", 0)))
            self.q_observed.setText(str(stats.get("observed", 0)))
            self.q_rekeys.setText(str(stats.get("rekeys", 0)))
            self.q_seed_age.setText(str(stats.get("seed_age", 0)))

            runtime = "HEALTHY" if status == "ACTIVE" else "STANDBY"

            self.q_runtime.setText(runtime)
            self.q_health.setText(runtime)
            self.q_chain_short.setText(self._short_chain(chain))
            self.quantum_chain.setPlainText(
                chain if chain else "Unavailable"
            )

            if status == "ACTIVE":
                self.quantum_pill.setText("QUANTUM: ACTIVE")
                self.quantum_pill.setStyleSheet(
                self._pill_style(DARKELF_SUCCESS)
                )
            else:
                self.quantum_pill.setText(f"QUANTUM: {status}")
                self.quantum_pill.setStyleSheet(
                    self._pill_style(DARKELF_INFO)
                )

        except RuntimeError as e:
            if "destroyed" in str(e).lower():
                self._set_quantum_unavailable("DESTROYED")
                return
            raise
            
    def _set_quantum_unavailable(self, state="UNAVAILABLE"):
        self.quantum_pill.setText(f"QUANTUM: {state}")
        self.quantum_pill.setStyleSheet(
            self._pill_style(DARKELF_WARN)
        )

        self.q_status.setText(state)
        self.q_generation.setText("--")
        self.q_requests.setText("--")
        self.q_observed.setText("--")
        self.q_rekeys.setText("--")
        self.q_seed_age.setText("--")
        self.q_runtime.setText("STOPPED")
        self.q_health.setText("UNAVAILABLE")
        self.q_chain_short.setText("--")
        self.quantum_chain.setPlainText(
            "Quantum runtime is unavailable."
        )
        
    def refresh_miniai(self):

        ai = self._resolve_miniai()

        if not ai:
            self.miniai_pill.setText("MINIAI: UNAVAILABLE")
            self.miniai_pill.setStyleSheet(self._pill_style(DARKELF_WARN))
            return

        try:
            stats = ai.get_statistics()
            panic = bool(getattr(ai, "panic_mode_active", False))
            lockdown = bool(getattr(ai, "lockdown_active", False))
            threshold = getattr(ai, "threshold", "unknown")

            if panic:
                state = "PANIC"
                color = DARKELF_DANGER
            elif lockdown:
                state = "LOCKDOWN"
                color = DARKELF_DANGER
            else:
                state = "MONITORING"
                color = DARKELF_SUCCESS

            self.miniai_pill.setText(f"MINIAI: {state}")
            self.miniai_pill.setStyleSheet(self._pill_style(color))

            # Update dashboard labels

            stats = ai.get_statistics()

            self.ai_state.setText(state)

            self.ai_threat.setText(str(stats["threat_score"]))

            self.ai_trackers.setText(
                str(stats["threats"]["trackers"])
            )

            self.ai_intrusions.setText(
                str(stats["threats"]["intrusions"])
            )

            self.ai_fingerprint.setText(
                str(stats["threats"]["fingerprinting"])
            )

            self.ai_blocks.setText(
                str(stats["threats"]["http_blocks"])
            )

            self.ai_malware.setText(
                str(stats["threats"]["malware"])
            )

            self.ai_exploits.setText(
                str(stats["threats"]["exploits"])
            )

            self.ai_domains.setText(
                str(stats["unique_domains"])
            )

            self.ai_lockdown.setText(
                "ON" if stats["lockdown"]["active"] else "OFF"
            )

            self.ai_panic.setText(
                "ON" if stats["panic"]["active"] else "OFF"
            )

            self.ai_uptime.setText(
                f"{int(stats['uptime_seconds'])} s"
            )

            # Log one summary line

            self.status_label.setText("Status: MiniAI refreshed")

        except Exception as e:
            self.console.log(f"MiniAI refresh failed: {e}", "error")

    def log_network_event(self, message):
        if not message:
            return

        self.network_log.appendPlainText(message)

        self._request_count += 1

        self.request_label.setText(f"Requests: {self._request_count}")
        self.net_total.setText(f"Requests: {self._request_count}")
        self.net_active.setText(f"Events: {self._request_count}")
        
    def log_security_event(self, message, level="security"):
        self.console.log(message, level)
        
    def log_blocked_event(self, url="", reason="Blocked by Darkelf"):
        self._blocked_count += 1
    
        self.blocked_label.setText(f"Blocked: {self._blocked_count}")
        self.net_blocked.setText(f"Blocked: {self._blocked_count}")

        self.log_network_event(f"{reason}: {url}")
        
    def update_status(self, message="Idle"):
        self.status_label.setText(f"Status: {message}")
        self.status_pill.setText(message.upper()[:18])


    # --------------------------------------------------------
    # Runtime Resolution Helpers
    # --------------------------------------------------------

    def _resolve_quantum(self):
        if self.quantum:
            return self.quantum

        if self.browser:
            try:
                profile = getattr(self.browser, "shared_profile", None)
                interceptor = getattr(profile, "_darkelf_interceptor", None)

                if interceptor and hasattr(interceptor, "pq"):
                    return interceptor.pq
            except Exception as e:
                self.console.log(
                    f"Unable to resolve Quantum interceptor: {e}",
                    "warn",
                )

            try:
                easy = getattr(self.browser, "easy", None)
                if easy and hasattr(easy, "pq"):
                    return easy.pq
            except Exception as e:
                self.console.log(
                    f"Unable to resolve EasyList Quantum runtime: {e}",
                    "warn",
                )

        return None


    def _resolve_miniai(self):
        if self.mini_ai:
            return self.mini_ai

        if self.browser:
            try:
                ai = getattr(self.browser, "mini_ai", None)
                if ai:
                    return ai
            except Exception as e:
                self.console.log(
                    f"Unable to resolve MiniAI runtime: {e}",
                    "warn",
                )

        return None


    def _short_chain(self, chain):
        chain = safe_text(chain)

        if not chain or chain.lower() == "none":
            return "Unavailable"

        if len(chain) > 42:
            return chain[:42] + "..."

        return chain

    def _pill_style(self, color):
        return f"""
            QLabel {{
                color: {color};
                background: rgba(168, 85, 247, 0.10);
                border: 1px solid {color};
                border-radius: 12px;
                padding: 2px 10px;
                font-family: {FONT_UI};
                font-size: 11px;
                font-weight: 700;
            }}
        """
    # --------------------------------------------------------
    # Theme / Styling
    # --------------------------------------------------------

    def init_theme(self):
        self.setStyleSheet(f"""

        QWidget {{
            background: {DARKELF_BG};
            color: {DARKELF_TEXT};
            font-family: {FONT_UI};
            font-size: 12px;
        }}

        /* =====================================================
        Header
        ===================================================== */

        QFrame#DevToolsHeader {{
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:0,
                stop:0 #0b1017,
                stop:1 #121923
            );

            border: 1px solid {DARKELF_BORDER};
            border-radius: 14px;
        }}

    QLabel#DevToolsTitle {{
            color: white;
            font-size: 20px;
            font-weight: 800;
        }}

        QLabel#DevToolsSubtitle {{
            color: {DARKELF_MUTED};
            font-size: 11px;
        }}

        /* =====================================================
        Tabs
        ===================================================== */

        QTabWidget::pane {{
            border: 1px solid {DARKELF_BORDER};
            background: {DARKELF_PANEL};
            border-radius: 12px;
            top: -1px;
        }}

        QTabBar::tab {{

            background: transparent;

            color: {DARKELF_MUTED};

            min-width: 105px;

            padding: 9px 18px;

            margin-right: 4px;

            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}

        QTabBar::tab:selected {{

            color: white;

            background: rgba(168,85,247,.14);

            border-bottom: 2px solid {self.accent_color};
        }}

        QTabBar::tab:hover {{

            color: white;

            background: rgba(255,255,255,.05);
        }}

        /* =====================================================
        Console
        ===================================================== */

        QPlainTextEdit,
        QTextEdit {{

            background: #070a0f;

            color: {DARKELF_TEXT};

            border: 1px solid {DARKELF_BORDER};

            border-radius: 12px;

            selection-background-color: {self.accent_color};

            padding: 8px;

            font-family: {FONT_MONO};

            font-size: 12px;
        }}

        /* =====================================================
        Tree
        ===================================================== */

        QTreeWidget {{

            background: #090d13;

            border: 1px solid {DARKELF_BORDER};

            border-radius: 10px;

            outline: none;
        }}

        QTreeWidget::item {{

            padding: 4px;
        }}

        QTreeWidget::item:selected {{

            background: rgba(168,85,247,.18);

            color: white;
        }}

        /* =====================================================
        Tables
        ===================================================== */

        QTableWidget {{

            background: #090d13;

            alternate-background-color: #0e131b;

            border: 1px solid {DARKELF_BORDER};

            border-radius: 10px;

            gridline-color: #1d2d40;

            selection-background-color: rgba(168,85,247,.20);
        }}

        QHeaderView::section {{

            background: #10161f;

            color: white;

            padding: 6px;

            border: none;

            border-bottom: 1px solid {DARKELF_BORDER};
        }}

        /* =====================================================
        Lists
        ===================================================== */

        QListWidget {{

            background: #090d13;

            border: 1px solid {DARKELF_BORDER};

            border-radius: 10px;
        }}

        QListWidget::item {{

            padding: 8px;
        }}

        QListWidget::item:selected {{

            background: rgba(168,85,247,.16);
        }}

        /* =====================================================
        Input
        ===================================================== */

        QLineEdit {{

            background: #10161f;

            color: white;
    
            border: 1px solid {DARKELF_BORDER};
    
            border-radius: 10px;

            padding: 7px 10px;

            selection-background-color: {self.accent_color};

            font-family: {FONT_MONO};
        }}

        QLineEdit:focus {{

            border: 1px solid {self.accent_color};
        }}

        /* =====================================================
        Buttons
        ===================================================== */

        QPushButton {{

            background: #161d28;

            color: white;

            border: 1px solid {DARKELF_BORDER};

            border-radius: 10px;

            padding: 7px 14px;
        }}

        QPushButton:hover {{

            background: #202938;
        }}

        QPushButton:pressed {{

            background: #111722;
        }}

        QPushButton#AccentButton {{

            background: {self.accent_color};

            color: white;

            border: none;

            font-weight: 700;
        }}

        QPushButton#AccentButton:hover {{
    
            background: {DARKELF_ACCENT_2};
        }}

        /* =====================================================
        Splitters
        ===================================================== */

        QSplitter::handle {{

            background: #151c26;
        }}

        QSplitter::handle:horizontal {{

            width: 2px;
        }}

        QSplitter::handle:vertical {{

            height: 2px;
        }}

        /* =====================================================
        Status Strip
        ===================================================== */

        QFrame#StatusStrip {{

            background: #0b1017;

            border: 1px solid {DARKELF_BORDER};

            border-radius: 10px;
        }}

        QLabel#StatusText {{

            color: {DARKELF_MUTED};

            padding-left: 4px;
        }}

        /* =====================================================
        Scrollbars
        ===================================================== */

        QScrollBar:vertical {{

            background: transparent;

            width: 10px;
        }}

        QScrollBar::handle:vertical {{

            background: #2d3748;

            border-radius: 5px;

            min-height: 28px;
        }}

        QScrollBar::handle:vertical:hover {{

            background: {self.accent_color};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{

            height: 0px;
        }}

        QScrollBar:horizontal {{

            background: transparent;

            height: 10px;
        }}

        QScrollBar::handle:horizontal {{

            background: #2d3748;

            border-radius: 5px;

            min-width: 28px;
        }}

        QScrollBar::handle:horizontal:hover {{

            background: {self.accent_color};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{

            width: 0px;
        }}

        """)
