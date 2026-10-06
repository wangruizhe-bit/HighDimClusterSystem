"""集中管理当前数据和跨页面信号。"""
from PySide6.QtCore import QObject, Signal
from core.data_manager import DataManager

class Session(QObject):
    data_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = DataManager()
        self.results = []
        self.latest_pca = None

    def load(self, path):
        self.data.load_file(path)
        self.results.clear()
        self.latest_pca = None
        self.data_changed.emit()

    def apply(self, frame):
        self.data.set_data(frame)
        self.results.clear()
        self.latest_pca = None
        self.data_changed.emit()

    def restore(self):
        self.data.restore_original()
        self.results.clear()
        self.latest_pca = None
        self.data_changed.emit()
