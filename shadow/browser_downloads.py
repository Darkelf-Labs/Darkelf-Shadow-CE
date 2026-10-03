from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
    QWidgetAction,
    QGridLayout
)

from PySide6.QtGui import QColor

from PySide6.QtWebEngineCore import (
    QWebEngineDownloadRequest
)


class DownloadItem(QWidget):

    def __init__(self, download):
        super().__init__()

        self.download = download

        layout = QHBoxLayout(self)

        self.label = QLabel(download.downloadFileName())
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.cancel = QPushButton("Cancel")

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.cancel)

        self.cancel.clicked.connect(self._handle_click)

        download.receivedBytesChanged.connect(self.update_progress)
        download.totalBytesChanged.connect(self.update_progress)
        download.stateChanged.connect(self.handle_state)

    def update_progress(self):
        total = self.download.totalBytes()
        received = self.download.receivedBytes()

        if total <= 0:
            # Unknown file size → show animated busy bar
            self.progress.setRange(0, 0)
        else:
            percent = int((received / total) * 100)
            self.progress.setRange(0, 100)
            self.progress.setValue(percent)

    def handle_state(self, state):

        if state == QWebEngineDownloadRequest.DownloadCompleted:
            self.progress.setValue(100)
            self.cancel.setText("Done")

        elif state == QWebEngineDownloadRequest.DownloadCancelled:
            self.cancel.setText("Remove")

        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            self.cancel.setText("Failed")
            
    def _handle_click(self):

        state = self.download.state()

        if state == QWebEngineDownloadRequest.DownloadInProgress:
            self.download.cancel()
        else:
            self.setParent(None)
            self.deleteLater()

class DownloadShelf(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

    def add_download(self, download):

        item = DownloadItem(download)
        self.layout.addWidget(item)

        item.destroyed.connect(self._check_empty)

    def _check_empty(self):

        if self.layout.count() == 0:
            self.hide()
            
def create_color_palette_menu(parent, callback):

    menu = QMenu(parent)

    # palette widget INSIDE the menu
    palette = QWidget(menu)

    grid = QGridLayout(palette)
    grid.setSpacing(2)
    grid.setContentsMargins(4,4,4,4)

    colors = [
        "#34C759",
        "#444444","#666666","#999999",
        "#ff4d4f","#ff7a45","#ffa940",
        "#ffd666","#73d13d","#36cfc9","#40a9ff",
        "#597ef7","#9254de","#f759ab","#bfbfbf",
        "#FFFFFF",   # white
        "#FFC0CB",   # baby pink
        "#00BFA6",   # teal
        "#FF6F61",   # coral
        "#8BC34A",   # light green
        "#FFB6C1",   # light pink
        "#FFD700",   # gold
        "#7B68EE",   # medium purple
        "#20B2AA"    # light sea green
    ]

    row = 0
    col = 0

    for color_hex in colors:

        btn = QPushButton()
        btn.setFixedSize(20,20)

        btn.setStyleSheet(
            f"""
            QPushButton {{
                background:{color_hex};
                border:1px solid #555;
            }}
            QPushButton:hover {{
                border:2px solid white;
            }}
            """
        )

        # important: capture color safely
        btn.clicked.connect(lambda _, c=color_hex: callback(QColor(c)))

        grid.addWidget(btn, row, col)

        col += 1
        if col == 8:
            col = 0
            row += 1

    action = QWidgetAction(menu)
    action.setDefaultWidget(palette)

    menu.addAction(action)

    return menu
