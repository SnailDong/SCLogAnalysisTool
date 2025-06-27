from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.workspace_panel.log_panel.log_viewer import SCLogViewer
from src.ui.workspace_panel.mark_panel.mark_log import SCMarkLogViewer

class SCMarkPanel(QWidget):
    markClicked = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.log_viewer = SCLogViewer()
        self.log_viewer.set_filter_type("original")
        self.mark_viewer = SCMarkLogViewer()
        self.splitter.addWidget(self.log_viewer)
        self.splitter.addWidget(self.mark_viewer)
        self.splitter.setSizes([300, 200])
        layout.addWidget(self.splitter)
        self.mark_viewer.markClicked.connect(self.markClicked.emit)

    def set_filepath(self, filepath: str):
        self.mark_viewer.set_filepath(filepath)

    def get_mark_viewer(self):
        return self.mark_viewer
    def get_log_viewer(self):
        return self.log_viewer 