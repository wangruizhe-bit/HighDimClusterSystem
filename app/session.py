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
        self.reduction_results = []
        self.data_revision = 0

    def _invalidate(self):
        self.results.clear()
        self.latest_pca = None
        self.reduction_results.clear()
        self.data_revision += 1
        self.data_changed.emit()

    def load(self, path):
        self.data.load_file(path)
        self._invalidate()

    def apply(self, frame):
        self.data.set_data(frame)
        self._invalidate()

    def restore(self):
        self.data.restore_original()
        self._invalidate()
