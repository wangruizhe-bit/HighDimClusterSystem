"""集中管理当前数据和跨页面信号。"""
from PySide6.QtCore import QObject, Signal
from core.data_manager import DataManager

class Session(QObject):
    data_changed = Signal()
    cluster_changed = Signal()
    k_search_changed = Signal()
    results_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = DataManager()
        self.results = []
        self.feature_result = None
        self.latest_pca = None
        self.reduction_results = []
        self.data_revision = 0
        self.cluster_results = []
        self.k_search_result = None

    def _invalidate(self):
        self.results.clear()
        self.feature_result = None
        self.latest_pca = None
        self.reduction_results.clear()
        self.cluster_results.clear()
        self.k_search_result = None
        self.data_revision += 1
        self.data_changed.emit()
        self.cluster_changed.emit()
        self.k_search_changed.emit()
        self.results_changed.emit()

    def load(self, path):
        self.data.load_file(path)
        self._invalidate()

    def apply(self, frame):
        self.data.set_data(frame)
        self._invalidate()

    def restore(self):
        self.data.restore_original()
        self._invalidate()

    def clear_results(self):
        """清空分析快照但不改变原始数据或当前工作数据。"""
        self._invalidate()
