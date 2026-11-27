# main.py

# --- Qt ---
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

# --- Standard ---
import sys

# --- Local modules ---
from shadow.splash import BootSplash
from shadow.boot import BootWorker, update_progress, boot_done
from shadow.utils import apply_chromium_flags


def main():
    # --- Chromium flags MUST be before Qt ---
    apply_chromium_flags()

    # --- Create app ---
    app = QApplication(sys.argv)

    # 🔥 CRITICAL: prevent app from quitting when splash closes
    app.setQuitOnLastWindowClosed(False)

    # 🔥 CRITICAL: FORCE CONSISTENT STYLE ENGINE
    app.setStyle("Fusion")

    # 🔥 GLOBAL DARK THEME
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor("#0d0f12"))
    palette.setColor(QPalette.Base, QColor("#0d0f12"))
    palette.setColor(QPalette.AlternateBase, QColor("#0d0f12"))

    palette.setColor(QPalette.Text, QColor("#A855F7"))
    palette.setColor(QPalette.ButtonText, QColor("#A855F7"))

    palette.setColor(QPalette.Button, QColor("#0d0f12"))

    palette.setColor(QPalette.Highlight, QColor("#A855F7"))
    palette.setColor(QPalette.HighlightedText, QColor("#000000"))

    app.setPalette(palette)

    # 🔥 OPTIONAL: Global stylesheet
    app.setStyleSheet("""
    QTabWidget::pane {
        border: none;
    }

    QTabBar::tab {
        background: #0d0f12;
        color: #A855F7;
        padding: 6px 14px;
        border-radius: 8px;
        margin: 2px;
    }

    QTabBar::tab:selected {
        background: #A855F7;
        color: #000000;
    }

    QToolBar {
        background: #0d0f12;
        border: none;
    }

    QToolButton {
        color: #A855F7;
        padding: 6px;
    }

    QToolButton:hover {
        background: #003322;
    }
    """)

    # --- Splash screen ---
    splash = BootSplash()
    splash.show()

    # --- Boot worker ---
    worker = BootWorker()

    # --- Connect progress updates ---
    worker.progress.connect(lambda v, t: update_progress(splash, v, t))

    # --- Connect completion ---
    worker.finished.connect(
        lambda engine, ai: boot_done(splash, app, engine, ai)
    )

    # --- Start boot process ---
    worker.start()

    # --- Run app ---
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
