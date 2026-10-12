"""聚类页面：真实 K-means/层次聚类/DBSCAN、标签、评分及图表。"""
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QTabWidget, QTableView, QVBoxLayout, QWidget,
)
import pandas as pd
from scipy.cluster.hierarchy import dendrogram

from app.plot_canvas import PlotCanvas, StaticPlotCanvas
from app.table_model import FrameTableModel
from app.studio_components import AnalysisLayout
from core.clustering import ALGORITHMS, fit_clustering


class ClusterWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, frame, params, parent=None):
        super().__init__(parent)
        self.frame = frame
        self.params = params

    def run(self):
        try:
            self.succeeded.emit(fit_clustering(self.frame, **self.params))
        except (ValueError, TypeError) as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("聚类分析失败，请检查数据范围和算法参数。")


class ClusterPage(QWidget):
    MAX_HISTORY = 12

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.current_result = None
        self.worker = None
        self.busy = False
        self._submitted_revision = -1

        workspace = AnalysisLayout(self)
        self.parameter_panel = workspace.parameter_panel
        root = workspace.results
        root.setSpacing(14)

        options = QGroupBox("聚类算法与特征选择")
        horizontal = QVBoxLayout(options)
        variable_layout = QVBoxLayout()
        variable_layout.addWidget(QLabel("变量 · 默认全部"))
        self.variables = QListWidget()
        self.variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.variables.setMaximumHeight(115)
        variable_layout.addWidget(self.variables)
        horizontal.addLayout(variable_layout)

        right = QVBoxLayout()
        general = QFormLayout()
        self.method_combo = QComboBox()
        for key, title in ALGORITHMS.items():
            self.method_combo.addItem(title, key)
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        general.addRow("算法", self.method_combo)
        self.standardize = QCheckBox("Z-score 标准化输入数据")
        self.standardize.setChecked(True)
        general.addRow("数据预处理", self.standardize)
        right.addLayout(general)

        self.methods = QStackedWidget()
        kmeans_form = QWidget()
        kform = QFormLayout(kmeans_form)
        self.kmeans_k = QSpinBox()
        self.kmeans_k.setRange(2, 10000)
        self.kmeans_k.setValue(3)
        kform.addRow("聚类数量 K", self.kmeans_k)
        self.max_iter = QSpinBox()
        self.max_iter.setRange(10, 3000)
        self.max_iter.setValue(300)
        kform.addRow("最大迭代次数", self.max_iter)
        self.random_state = QSpinBox()
        self.random_state.setRange(0, 2147483647)
        self.random_state.setValue(42)
        kform.addRow("随机种子", self.random_state)
        self.methods.addWidget(kmeans_form)

        hierarchical_form = QWidget()
        hform = QFormLayout(hierarchical_form)
        self.hierarchical_k = QSpinBox()
        self.hierarchical_k.setRange(2, 10000)
        self.hierarchical_k.setValue(3)
        hform.addRow("聚类数量 K", self.hierarchical_k)
        self.linkage = QComboBox()
        for value in ("ward", "complete", "average", "single"):
            self.linkage.addItem(value, value)
        self.linkage.currentIndexChanged.connect(self.on_linkage_changed)
        hform.addRow("linkage 方法", self.linkage)
        self.hierarchical_metric = QComboBox()
        self.hierarchical_metric.addItem("欧氏距离", "euclidean")
        self.hierarchical_metric.addItem("曼哈顿距离", "manhattan")
        hform.addRow("样本距离", self.hierarchical_metric)
        self.methods.addWidget(hierarchical_form)

        dbscan_form = QWidget()
        dform = QFormLayout(dbscan_form)
        self.eps = QDoubleSpinBox()
        self.eps.setRange(.001, 100000.)
        self.eps.setDecimals(3)
        self.eps.setSingleStep(.1)
        self.eps.setValue(.5)
        dform.addRow("邻域半径 eps", self.eps)
        self.min_samples = QSpinBox()
        self.min_samples.setRange(2, 100000)
        self.min_samples.setValue(5)
        dform.addRow("核心点 min_samples", self.min_samples)
        self.dbscan_metric = QComboBox()
        self.dbscan_metric.addItem("欧氏距离", "euclidean")
        self.dbscan_metric.addItem("曼哈顿距离", "manhattan")
        dform.addRow("样本距离", self.dbscan_metric)
        self.methods.addWidget(dbscan_form)

        right.addWidget(self.methods)
        self.run_button = QPushButton("执行聚类分析")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self.start_analysis)
        right.addWidget(self.run_button)
        horizontal.addLayout(right)
        workspace.add_parameters(options)

        self.summary = QLabel("请先导入数据。")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.models = {}
        for label, attr in [
            ("样本聚类标签", "labels"),
            ("类别样本数", "counts"),
            ("类别特征均值", "cluster_profile"),
            ("K-means 聚类中心", "centers"),
            ("聚类评价指标", "metrics"),
        ]:
            view = QTableView()
            view.setAlternatingRowColors(True)
            view.horizontalHeader().setStretchLastSection(True)
            view.setMinimumHeight(330)
            model = FrameTableModel(view)
            view.setModel(model)
            self.models[attr] = model
            self.tabs.addTab(view, label)

        self.scatter2d = PlotCanvas()
        self.scatter3d = StaticPlotCanvas(three_d=True)
        self.tree_canvas = PlotCanvas()
        for name, canvas in [
            ("二维 PCA 投影聚类图", self.scatter2d),
            ("三维 PCA 投影聚类图", self.scatter3d),
            ("层次聚类树状图", self.tree_canvas),
        ]:
            canvas.setMinimumHeight(360)
            self.tabs.addTab(canvas, name)
        root.addWidget(self.tabs, 1)

        self.notes = QLabel("PCA 投影仅用于绘图；DBSCAN 中 -1 表示噪声，不计入有效簇。")
        self.notes.setWordWrap(True)
        root.addWidget(self.notes)
        self.session.data_changed.connect(self.on_data_changed)
        self.on_data_changed()
        self.on_method_changed()

    def on_linkage_changed(self, *_):
        if self.linkage.currentData() == "ward":
            self.hierarchical_metric.setCurrentIndex(0)
            self.hierarchical_metric.setEnabled(False)
        else:
            self.hierarchical_metric.setEnabled(True)

    def on_method_changed(self, *_):
        self.methods.setCurrentIndex(self.method_combo.currentIndex())

    def on_data_changed(self):
        self.current_result = None
        self.variables.clear()
        self.variables.addItems([str(c) for c in self.session.data.get_numeric_columns()])
        n = len(self.session.data.current_data) if self.session.data.current_data is not None else 0
        for widget in (self.kmeans_k, self.hierarchical_k):
            widget.setMaximum(max(2, n-1))
            widget.setValue(min(3, max(2, n-1)))
        self.min_samples.setMaximum(max(2, n))
        self.min_samples.setValue(min(5, max(2, n)))
        for model in self.models.values():
            model.set_frame(None)
        self.scatter2d.clear_message("请执行聚类分析")
        self.scatter3d.clear_message("三维绘图需要至少 3 个数值变量")
        self.tree_canvas.clear_message("请选择层次聚类以生成树状图")
        self.summary.setText("数据已准备就绪，请选择变量和聚类算法。" if n else "请先导入数据。")

    def parameters(self):
        selected = [item.text() for item in self.variables.selectedItems()] or None
        method = self.method_combo.currentData()
        params = {"method": method, "columns": selected,
                  "standardize": self.standardize.isChecked()}
        if method == "kmeans":
            params.update(n_clusters=self.kmeans_k.value(),
                          max_iter=self.max_iter.value(),
                          random_state=self.random_state.value())
        elif method == "hierarchical":
            params.update(n_clusters=self.hierarchical_k.value(),
                          linkage=self.linkage.currentData(),
                          metric=self.hierarchical_metric.currentData())
        else:
            params.update(eps=self.eps.value(), min_samples=self.min_samples.value(),
                          metric=self.dbscan_metric.currentData())
        return params

    def start_analysis(self):
        if self.busy:
            return
        try:
            frame = self.session.data.get_data()
        except ValueError as exc:
            QMessageBox.warning(self, "无法开始", str(exc))
            return
        self.busy = True
        self._submitted_revision = self.session.data_revision
        self.run_button.setEnabled(False)
        self.summary.setText("正在计算真实聚类结果，请查看计算完成后的类别与评价……")
        self.worker = ClusterWorker(frame, self.parameters(), self)
        self.worker.succeeded.connect(self._success)
        self.worker.failed.connect(self._error)
        self.worker.finished.connect(self._done)
        self.worker.start()

    def _success(self, result):
        if self._submitted_revision != self.session.data_revision:
            self.summary.setText("数据集已变化；本次计算的过期结果未保存。")
            return
        self.current_result = result
        self.session.cluster_results.append(result)
        if len(self.session.cluster_results) > self.MAX_HISTORY:
            del self.session.cluster_results[:-self.MAX_HISTORY]
        self.summary.setText(
            f"{result.label} · {result.n_samples} 个样本 · {result.n_clusters} 个簇 · "
            f"噪声 {result.n_noise} · {result.elapsed_seconds:.2f} 秒"
            + (" · 评价不含噪声" if result.algorithm == "dbscan" else "")
        )
        self.summary.setToolTip(result.score_note +
            ("\n已标准化" if result.standardized else "\n未标准化"))
        for key in ("labels", "counts", "cluster_profile", "centers"):
            self.models[key].set_frame(getattr(result, key))
        definitions = {
            "silhouette": "轮廓系数（高更好；需要至少两个有效簇）",
            "calinski_harabasz": "Calinski–Harabasz 指数（较高通常更好）",
            "davies_bouldin": "Davies–Bouldin 指数（较低通常更好）",
            "inertia": "K-means 惯性 SSE（仅适用于 K-means）",
            "noise_ratio": "DBSCAN 噪声比例（其他算法为 0）",
        }
        self.models["metrics"].set_frame(pd.DataFrame([
            {"指标": definitions.get(k, k), "数值": "不适用" if v is None else v}
            for k, v in result.metrics.items()
        ]))
        self._plot(result)
        self.tabs.setCurrentIndex(0)
        self.session.cluster_changed.emit()
        self.session.results_changed.emit()

    def _error(self, message):
        if self._submitted_revision == self.session.data_revision:
            self.summary.setText("聚类未完成；未生成或保存错误结果。")
            QMessageBox.warning(self, "聚类参数或数据错误", message)

    def _done(self):
        self.busy = False
        self.run_button.setEnabled(True)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    @staticmethod
    def _scatter(ax, frame, dims):
        labels = frame["簇标签"].to_numpy(dtype=int)
        ids = sorted(set(labels))
        for i, cluster in enumerate(ids):
            mask = labels == cluster
            if cluster == -1:
                color, marker = "#596579", "x"
                name = "噪声"
            else:
                color, marker = None, "o"
                name = f"第{cluster+1}类"
            coords = [frame[f"PC{j}"].to_numpy()[mask] for j in range(1, dims+1)]
            ax.scatter(*coords, color=color, marker=marker, alpha=.77, s=27, label=name)
        if len(ids) <= 16:
            ax.legend(fontsize=8)

    def _plot(self, result):
        ratios = result.projection_ratios

        def build_2d(a):
            self._scatter(a, result.coords, 2)
            a.set_xlabel(f"PC1 ({ratios[0]*100:.1f}%)")
            a.set_ylabel(f"PC2 ({ratios[1]*100:.1f}%)")
            a.set_title(f"{result.label} · 二维 PCA 投影")
            a.grid(alpha=.15)

        self.scatter2d.safe_update(
            f"{result.label}二维聚类图", build_2d,
            force_draw=self.scatter2d.isVisible(),
        )

        if "PC3" in result.coords:
            def build_3d(a):
                self._scatter(a, result.coords, 3)
                a.set_xlabel("PC1")
                a.set_ylabel("PC2")
                a.set_zlabel("PC3")
                a.set_title(f"{result.label} · 三维 PCA 投影")

            self.scatter3d.safe_update(
                f"{result.label}三维聚类图", build_3d, three_d=True,
                force_draw=self.scatter3d.isVisible(),
            )
        else:
            self.scatter3d.clear_message(
                "所选变量少于三列，不能生成三维 PCA 投影。",
                request_draw=self.scatter3d.isVisible(),
            )

        if result.linkage_matrix is not None:
            if result.n_samples <= 160:
                def build_tree(a):
                    dendrogram(
                        result.linkage_matrix, ax=a, no_labels=True,
                        color_threshold=0,
                    )
                    a.set_title("层次聚类树状图")
                    a.set_ylabel("合并距离")

                self.tree_canvas.safe_update(
                    "层次聚类树状图", build_tree,
                    force_draw=self.tree_canvas.isVisible(),
                )
            else:
                self.tree_canvas.clear_message(
                    "样本数超过 160：保留层次聚类结果，不显示拥挤的树状图。",
                    request_draw=self.tree_canvas.isVisible(),
                )
        else:
            self.tree_canvas.clear_message(
                "本次不是层次聚类；树状图不适用。",
                request_draw=self.tree_canvas.isVisible(),
            )
