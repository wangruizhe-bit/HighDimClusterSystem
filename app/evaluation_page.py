"""聚类评价与 K 值辅助选择：真实指标展示、方法对比与曲线。"""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QMessageBox, QPushButton, QSpinBox, QTableView, QVBoxLayout, QWidget,
)
import pandas as pd

from app.plot_canvas import PlotCanvas
from app.table_model import FrameTableModel
from core.clustering import search_k


class KSearchWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, frame, kwargs, parent=None):
        super().__init__(parent)
        self.frame = frame
        self.kwargs = kwargs

    def run(self):
        try:
            self.succeeded.emit(search_k(self.frame, **self.kwargs))
        except (ValueError, TypeError) as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("K 值扫描失败，请检查数据、样本数量与参数。")


class EvaluationPage(QWidget):
    """不能将噪声、不同特征集或不同预处理下的指标直接视为同条件排序。"""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.worker = None
        self.busy = False
        self.score_plot_ready = False
        self._submitted_revision = -1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(13)
        self.heading = QLabel("Silhouette、CH 越高通常越好，DB 越低通常越好；DBSCAN 评分不含噪声。")
        self.heading.setWordWrap(True)
        root.addWidget(self.heading)

        history = QGroupBox("当前数据版本的聚类运行记录")
        history_lay = QVBoxLayout(history)
        self.history_view = QTableView()
        self.history_model = FrameTableModel(self.history_view)
        self.history_view.setModel(self.history_model)
        self.history_view.horizontalHeader().setStretchLastSection(True)
        self.history_view.setMinimumHeight(200)
        history_lay.addWidget(self.history_view)
        self.record_summary = QLabel("请先进入“聚类分析”运行至少一个算法。")
        self.record_summary.setWordWrap(True)
        history_lay.addWidget(self.record_summary)
        self.score_canvas = PlotCanvas()
        self.score_canvas.setMinimumHeight(330)
        history_lay.addWidget(self.score_canvas)
        root.addWidget(history)

        selection = QGroupBox("K-means K 值辅助选择：肘部法与轮廓系数法")
        s_lay = QHBoxLayout(selection)
        left = QVBoxLayout()
        left.addWidget(QLabel("参与 K 扫描的数值变量（不选默认全部）"))
        self.variables = QListWidget()
        self.variables.setMaximumHeight(190)
        self.variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        left.addWidget(self.variables)
        s_lay.addLayout(left, 3)
        controls = QFormLayout()
        self.standardize = QCheckBox("Z-score 标准化")
        self.standardize.setChecked(True)
        controls.addRow("预处理", self.standardize)
        self.k_min = QSpinBox()
        self.k_min.setRange(2, 30)
        self.k_min.setValue(2)
        self.k_max = QSpinBox()
        self.k_max.setRange(2, 30)
        self.k_max.setValue(8)
        controls.addRow("最小 K", self.k_min)
        controls.addRow("最大 K", self.k_max)
        self.max_iter = QSpinBox()
        self.max_iter.setRange(10, 3000)
        self.max_iter.setValue(300)
        controls.addRow("每个 K 的最大迭代次数", self.max_iter)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(42)
        controls.addRow("固定随机种子", self.seed)
        right = QVBoxLayout()
        right.addLayout(controls)
        self.search_button = QPushButton("执行 K 值扫描")
        self.search_button.setObjectName("primary")
        self.search_button.clicked.connect(self.start_search)
        right.addWidget(self.search_button)
        s_lay.addLayout(right, 2)
        root.addWidget(selection)

        self.search_summary = QLabel("SSE 肘部曲线与轮廓系数用于辅助选择 K 值。")
        self.search_summary.setWordWrap(True)
        root.addWidget(self.search_summary)
        self.search_table = QTableView()
        self.search_model = FrameTableModel(self.search_table)
        self.search_table.setModel(self.search_model)
        self.search_table.horizontalHeader().setStretchLastSection(True)
        self.search_table.setMinimumHeight(180)
        root.addWidget(self.search_table)
        self.k_canvas = PlotCanvas()
        self.k_canvas.setMinimumHeight(400)
        root.addWidget(self.k_canvas)

        self.session.data_changed.connect(self.on_data_changed)
        self.session.cluster_changed.connect(self.refresh_cluster_comparison)
        self.on_data_changed()

    def on_data_changed(self):
        self.variables.clear()
        self.variables.addItems([str(c) for c in self.session.data.get_numeric_columns()])
        n = len(self.session.data.current_data) if self.session.data.current_data is not None else 0
        maximum = max(2, min(30, n-1))
        self.k_min.setMaximum(maximum)
        self.k_max.setMaximum(maximum)
        self.k_min.setValue(2)
        self.k_max.setValue(min(8, maximum))
        self.search_model.set_frame(None)
        self.score_plot_ready = False
        self.k_canvas.clear_message("导入有效数据后可执行 K 值扫描")
        self.search_summary.setText("尚无 K 值扫描结果。")
        self.refresh_cluster_comparison()

    def refresh_cluster_comparison(self):
        records = self.session.cluster_results
        newest = records[-1] if records else None
        rows = []
        for i, r in enumerate(records, start=1):
            comparable = newest is not None and r.comparability_key == newest.comparability_key
            rows.append({
                "序号": i, "算法": r.label,
                "有效簇数": r.n_clusters, "噪声点数": r.n_noise,
                "轮廓系数": r.metrics["silhouette"],
                "CH": r.metrics["calinski_harabasz"],
                "DB": r.metrics["davies_bouldin"],
                "K-means SSE": r.metrics["inertia"],
                "用时(s)": r.elapsed_seconds,
                "同条件对比": "是" if comparable else "否",
            })
        self.history_model.set_frame(pd.DataFrame(rows))
        if not records:
            self.score_plot_ready = False
            self.score_canvas.clear_message("暂无有效聚类记录")
            self.record_summary.setText("暂无记录。请先到聚类页面执行分析。")
            return
        same = [(i, r) for i, r in enumerate(records, start=1)
                if newest is not None and r.comparability_key == newest.comparability_key]
        valid = [(i, r) for i, r in same if r.metrics["silhouette"] is not None]
        self.record_summary.setText(
            f"当前共有 {len(records)} 次运行记录；与最新运行同输入条件的结果 {len(same)} 个，"
            f"其中可计算轮廓系数的 {len(valid)} 个。不同特征或标准化方式不能公平排名；"
            "DBSCAN 的评分仅基于非噪声样本，请同时观察噪声比例。"
        )
        if not valid:
            self.score_plot_ready = False
            self.score_canvas.clear_message("无同条件、可计算轮廓系数的模型结果")
            return
        ax = self.score_canvas.new_axes()
        titles = [f"#{i} {r.label}" for i, r in valid]
        scores = [r.metrics["silhouette"] for _, r in valid]
        bars = ax.bar(range(len(valid)), scores)
        ax.set_xticks(range(len(valid)), titles, rotation=20, ha="right")
        ax.axhline(0, linewidth=.8, color="#94a3b8")
        ax.set_ylabel("轮廓系数")
        ax.set_title("同条件结果轮廓系数对比（DBSCAN 不含噪声）")
        ax.grid(axis="y", alpha=.15)
        self.score_canvas.draw_idle()
        self.score_plot_ready = True

    def start_search(self):
        if self.busy:
            return
        try:
            frame = self.session.data.get_data()
        except ValueError as exc:
            QMessageBox.warning(self, "尚未导入数据", str(exc))
            return
        kwargs = {
            "columns": [item.text() for item in self.variables.selectedItems()] or None,
            "standardize": self.standardize.isChecked(),
            "k_min": self.k_min.value(), "k_max": self.k_max.value(),
            "max_iter": self.max_iter.value(), "random_state": self.seed.value()
        }
        self.busy = True
        self._submitted_revision = self.session.data_revision
        self.search_button.setEnabled(False)
        self.search_summary.setText("正在对不同 K 运行真实 K-means 并计算评价指标……")
        self.worker = KSearchWorker(frame, kwargs, self)
        self.worker.succeeded.connect(self._success)
        self.worker.failed.connect(self._error)
        self.worker.finished.connect(self._done)
        self.worker.start()

    def _success(self, result):
        if self._submitted_revision != self.session.data_revision:
            self.search_summary.setText("数据已变化，已丢弃过期的 K 扫描结果。")
            return
        self.session.k_search_result = result
        self.search_model.set_frame(result.scores)
        recommendation = (
            f"最大轮廓系数对应 K={result.suggested_k}（仅作为辅助参考）"
            if result.suggested_k is not None else "当前数据没有可计算的轮廓系数"
        )
        self.search_summary.setText(
            f"已扫描 {len(result.scores)} 个 K 值；{recommendation}；"
            f"耗时 {result.elapsed_seconds:.2f} 秒。肘部位置应结合左侧曲线由用户判断。"
        )
        self._plot_k(result)
        self.session.k_search_changed.emit()
        self.session.results_changed.emit()

    def _error(self, message):
        if self._submitted_revision == self.session.data_revision:
            self.search_summary.setText("K 值扫描未完成；未保存任何模拟结果。")
            QMessageBox.warning(self, "扫描错误", message)

    def _done(self):
        self.busy = False
        self.search_button.setEnabled(True)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def _plot_k(self, result):
        fig = self.k_canvas.figure
        fig.clear()
        data = result.scores
        a = fig.add_subplot(1, 2, 1)
        a.plot(data["K"], data["惯性(SSE)"], "o-")
        a.set_xlabel("K")
        a.set_ylabel("惯性 / SSE")
        a.set_title("SSE 肘部曲线")
        a.set_xticks(data["K"])
        a.grid(alpha=.15)
        b = fig.add_subplot(1, 2, 2)
        b.plot(data["K"], data["轮廓系数"], "o-")
        if result.suggested_k is not None:
            b.axvline(result.suggested_k, linestyle="--", color="#879db4")
        b.set_xlabel("K")
        b.set_ylabel("轮廓系数")
        b.set_title("不同 K 的轮廓系数")
        b.set_xticks(data["K"])
        b.grid(alpha=.15)
        self.k_canvas.draw_idle()
