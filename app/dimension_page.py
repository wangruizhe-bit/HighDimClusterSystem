"""阶段三：可运行的因子分析、MDS、t-SNE 页面和可比性明确的方法对照。"""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QMessageBox,
    QPushButton, QSpinBox, QStackedWidget, QTabWidget, QTableView,
    QVBoxLayout, QWidget,
)
import pandas as pd

from app.plot_canvas import PlotCanvas
from app.table_model import FrameTableModel
from core.dimension_reduction import METHOD_LABELS, fit_reduction


class ReductionWorker(QThread):
    """在工作线程执行耗时数学运算，禁止在此线程直接操作 QWidget。"""
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, frame, params, parent=None):
        super().__init__(parent)
        self._frame = frame
        self._params = params

    def run(self):
        try:
            answer = fit_reduction(self._frame, **self._params)
            self.succeeded.emit(answer)
        except (ValueError, TypeError) as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("降维计算未能完成，请检查参数和输入数据。")


class ReductionPage(QWidget):
    MAX_HISTORY = 12

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.current_result = None
        self.worker = None
        self.busy = False
        self._submitted_revision = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        form = QGroupBox("分析方法与变量")
        form_layout = QHBoxLayout(form)
        select_panel = QVBoxLayout()
        select_panel.addWidget(QLabel("参与分析的数值变量（不选择则使用所有数值变量）"))
        self.variables = QListWidget()
        self.variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.variables.setMaximumHeight(180)
        select_panel.addWidget(self.variables)
        form_layout.addLayout(select_panel, 3)

        settings = QVBoxLayout()
        basic = QFormLayout()
        self.method_combo = QComboBox()
        for key, name in METHOD_LABELS.items():
            self.method_combo.addItem(name, key)
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        basic.addRow("选择算法", self.method_combo)

        self.dimension_combo = QComboBox()
        self.dimension_combo.addItem("二维", 2)
        self.dimension_combo.addItem("三维", 3)
        basic.addRow("目标空间维度", self.dimension_combo)
        self.standardize = QCheckBox("Z-score 标准化数值变量")
        self.standardize.setChecked(True)
        basic.addRow("数据预处理", self.standardize)
        self.random_state = QSpinBox()
        self.random_state.setRange(0, 2147483647)
        self.random_state.setValue(42)
        basic.addRow("随机种子", self.random_state)
        settings.addLayout(basic)

        self.algorithm_options = QStackedWidget()
        self.factor_form = QWidget()
        factor_controls = QFormLayout(self.factor_form)
        self.rotation = QComboBox()
        self.rotation.addItem("正交旋转（varimax）", "varimax")
        self.rotation.addItem("正交旋转（quartimax）", "quartimax")
        self.rotation.addItem("不旋转", "none")
        factor_controls.addRow("因子旋转", self.rotation)
        factor_controls.addRow(QLabel("因子数量等于目标维度；如变量数量不足，会阻止计算。"))
        self.algorithm_options.addWidget(self.factor_form)

        self.mds_form = QWidget()
        mds_controls = QFormLayout(self.mds_form)
        self.mds_distance = QComboBox()
        self.mds_distance.addItem("欧氏距离", "euclidean")
        self.mds_distance.addItem("曼哈顿距离", "manhattan")
        mds_controls.addRow("原始样本距离", self.mds_distance)
        self.mds_max_iter = QSpinBox()
        self.mds_max_iter.setRange(30, 3000)
        self.mds_max_iter.setValue(300)
        mds_controls.addRow("最大迭代次数", self.mds_max_iter)
        self.mds_n_init = QSpinBox()
        self.mds_n_init.setRange(1, 8)
        self.mds_n_init.setValue(2)
        mds_controls.addRow("初始化次数", self.mds_n_init)
        self.algorithm_options.addWidget(self.mds_form)

        self.tsne_form = QWidget()
        tsne_controls = QFormLayout(self.tsne_form)
        self.perplexity = QDoubleSpinBox()
        self.perplexity.setDecimals(1)
        self.perplexity.setRange(.1, 100000)
        self.perplexity.setValue(30)
        tsne_controls.addRow("perplexity", self.perplexity)
        self.tsne_lr_mode = QComboBox()
        self.tsne_lr_mode.addItem("自动选择", "auto")
        self.tsne_lr_mode.addItem("手动输入", "manual")
        self.tsne_lr_mode.currentIndexChanged.connect(self.on_learning_rate_changed)
        tsne_controls.addRow("学习率模式", self.tsne_lr_mode)
        self.tsne_learning_rate = QDoubleSpinBox()
        self.tsne_learning_rate.setRange(.1, 100000)
        self.tsne_learning_rate.setValue(200)
        tsne_controls.addRow("手动学习率", self.tsne_learning_rate)
        self.tsne_max_iter = QSpinBox()
        self.tsne_max_iter.setRange(250, 5000)
        self.tsne_max_iter.setValue(1000)
        tsne_controls.addRow("最大迭代次数", self.tsne_max_iter)
        self.algorithm_options.addWidget(self.tsne_form)
        settings.addWidget(self.algorithm_options)
        self.run_button = QPushButton("执行降维分析")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self.start_analysis)
        settings.addWidget(self.run_button)
        form_layout.addLayout(settings, 2)
        root.addWidget(form)

        self.summary = QLabel("请先导入数据。")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.result_tabs = QTabWidget()
        self.coordinate_view = QTableView()
        self.coordinate_model = FrameTableModel(self.coordinate_view)
        self.coordinate_view.setModel(self.coordinate_model)
        self.coordinate_view.horizontalHeader().setStretchLastSection(True)
        self.result_tabs.addTab(self.coordinate_view, "降维样本坐标")
        self.loading_view = QTableView()
        self.loading_model = FrameTableModel(self.loading_view)
        self.loading_view.setModel(self.loading_model)
        self.loading_view.horizontalHeader().setStretchLastSection(True)
        self.result_tabs.addTab(self.loading_view, "因子载荷")
        self.unique_view = QTableView()
        self.unique_model = FrameTableModel(self.unique_view)
        self.unique_view.setModel(self.unique_model)
        self.unique_view.horizontalHeader().setStretchLastSection(True)
        self.result_tabs.addTab(self.unique_view, "因子独特方差")
        self.metric_view = QTableView()
        self.metric_model = FrameTableModel(self.metric_view)
        self.metric_view.setModel(self.metric_model)
        self.metric_view.horizontalHeader().setStretchLastSection(True)
        self.result_tabs.addTab(self.metric_view, "计算指标")
        self.canvas2d = PlotCanvas()
        self.canvas3d = PlotCanvas(three_d=True)
        self.canvas2d.setMinimumHeight(380)
        self.canvas3d.setMinimumHeight(380)
        self.result_tabs.addTab(self.canvas2d, "二维降维结果")
        self.result_tabs.addTab(self.canvas3d, "三维降维结果")
        root.addWidget(self.result_tabs)

        group = QGroupBox("分析记录与方法对比")
        record_layout = QVBoxLayout(group)
        record_layout.addWidget(QLabel(
            "同一数据版本、相同变量及标准化方式、相同输出维度下，可用局部邻域保持度作辅助对比；"
            "不同方法的载荷、距离残差、KL 散度不可直接互相排名。"))
        self.history_view = QTableView()
        self.history_model = FrameTableModel(self.history_view)
        self.history_view.setModel(self.history_model)
        self.history_view.horizontalHeader().setStretchLastSection(True)
        self.history_view.setMinimumHeight(170)
        record_layout.addWidget(self.history_view)
        compare_choices = QHBoxLayout()
        self.compare_a = QComboBox()
        self.compare_b = QComboBox()
        compare_choices.addWidget(QLabel("对比 A"))
        compare_choices.addWidget(self.compare_a, 1)
        compare_choices.addWidget(QLabel("对比 B"))
        compare_choices.addWidget(self.compare_b, 1)
        self.compare_button = QPushButton("并排对比")
        self.compare_button.clicked.connect(self.draw_comparison)
        compare_choices.addWidget(self.compare_button)
        record_layout.addLayout(compare_choices)
        self.compare_summary = QLabel("至少运行两次分析后，可进行并排对比。")
        self.compare_summary.setWordWrap(True)
        record_layout.addWidget(self.compare_summary)
        self.comparison_canvas = PlotCanvas()
        self.comparison_canvas.setMinimumHeight(360)
        record_layout.addWidget(self.comparison_canvas)
        root.addWidget(group)

        self.session.data_changed.connect(self.on_data_changed)
        self.on_method_changed()
        self.on_learning_rate_changed()
        self.on_data_changed()

    def on_method_changed(self, *_):
        self.algorithm_options.setCurrentIndex(self.method_combo.currentIndex())

    def on_learning_rate_changed(self, *_):
        self.tsne_learning_rate.setEnabled(self.tsne_lr_mode.currentData() == "manual")

    def on_data_changed(self):
        # Session 已同步清空旧历史；异步结束时仍需再次校验提交版本。
        self.current_result = None
        self.variables.clear()
        self.variables.addItems([str(c) for c in self.session.data.get_numeric_columns()])
        self.coordinate_model.set_frame(None)
        self.loading_model.set_frame(None)
        self.unique_model.set_frame(None)
        self.metric_model.set_frame(None)
        self.canvas2d.clear_message("执行降维后显示二维结果")
        self.canvas3d.clear_message("三维可视化需要选择三维目标空间")
        self.comparison_canvas.clear_message("至少两项同条件结果可并排对比")
        self.compare_summary.setText("至少运行两次分析后，可进行并排对比。")
        self.summary.setText("已导入数据，可选择算法及参数执行分析。" if self.variables.count()
                             else "尚无可分析的数值变量，请先导入数据。")
        n = len(self.session.data.current_data) if self.session.data.current_data is not None else 0
        if n > 1:
            self.perplexity.setMaximum(max(.1, n - .1))
            if self.perplexity.value() >= n:
                self.perplexity.setValue(min(30., max(.5, n / 3)))
        else:
            self.perplexity.setMaximum(100000)
        self.update_history()

    def _params(self):
        selected = [item.text() for item in self.variables.selectedItems()] or None
        base = dict(
            method=self.method_combo.currentData(),
            columns=selected,
            n_components=self.dimension_combo.currentData(),
            standardize=self.standardize.isChecked(),
            random_state=self.random_state.value(),
        )
        match base["method"]:
            case "factor":
                base["rotation"] = self.rotation.currentData()
            case "mds":
                base.update(mds_distance=self.mds_distance.currentData(),
                            mds_max_iter=self.mds_max_iter.value(),
                            mds_n_init=self.mds_n_init.value())
            case "tsne":
                base.update(tsne_perplexity=self.perplexity.value(),
                            tsne_learning_rate=(
                                self.tsne_learning_rate.value()
                                if self.tsne_lr_mode.currentData() == "manual" else "auto"
                            ), tsne_max_iter=self.tsne_max_iter.value())
        return base

    def start_analysis(self):
        if self.busy:
            return
        try:
            frame = self.session.data.get_data()
        except ValueError as exc:
            QMessageBox.warning(self, "未导入数据", str(exc))
            return
        self.busy = True
        self._submitted_revision = self.session.data_revision
        self.run_button.setEnabled(False)
        self.summary.setText("正在执行降维计算，完成后自动显示真实结果……")
        self.worker = ReductionWorker(frame, self._params(), self)
        self.worker.succeeded.connect(self._succeeded)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self._finished)
        self.worker.start()

    def _succeeded(self, result):
        if self._submitted_revision != self.session.data_revision:
            self.summary.setText("数据已发生变化，本次过期的计算结果未保存。")
            return
        self.current_result = result
        self.session.reduction_results.append(result)
        if len(self.session.reduction_results) > self.MAX_HISTORY:
            del self.session.reduction_results[:-self.MAX_HISTORY]
        trust = result.metrics.get("trustworthiness")
        trust_text = f"{trust:.4f}" if trust is not None else "未计算（样本过多）"
        self.summary.setText(
            f"已完成：{result.method_label}；{result.sample_count} 行样本 × "
            f"{len(result.columns)} 个变量 → {result.dimensions} 维；"
            f"{'标准化' if result.standardized else '未标准化'}；"
            f"局部邻域保持度={trust_text}；用时 {result.elapsed_seconds:.2f} 秒。"
        )
        self.coordinate_model.set_frame(result.coordinates)
        self.loading_model.set_frame(result.factor_loadings)
        self.unique_model.set_frame(result.uniqueness)
        explanations = {
            "trustworthiness": "共同局部邻域保持度（0–1，较大较好；只用于同条件辅助比较）",
            "log_likelihood": "因子分析的每样本平均对数似然",
            "raw_stress": "MDS 原始距离平方残差总和",
            "stress_ratio": "MDS 标准化距离残差比例（较小较好）",
            "kl_divergence": "t-SNE 的 KL 散度（仅在可比 t-SNE 参数下解释）",
        }
        metrics = []
        for name, value in result.metrics.items():
            metrics.append({
                "指标": name,
                "数值": "未计算" if value is None else float(value),
                "说明": explanations.get(name, name),
            })
        self.metric_model.set_frame(pd.DataFrame(metrics))
        self._draw_embedding(result)
        self.update_history()
        self.result_tabs.setCurrentIndex(0)

    def _failed(self, message):
        if self._submitted_revision == self.session.data_revision:
            self.summary.setText("本次分析未完成；未保存任何新的结果。")
            QMessageBox.warning(self, "降维计算失败", message)

    def _finished(self):
        self.busy = False
        self.run_button.setEnabled(True)
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def _draw_embedding(self, result):
        vals = result.coordinates
        canvas = self.canvas2d
        ax = canvas.new_axes()
        ax.scatter(vals["维度1"], vals["维度2"], s=29, alpha=.72,
                   edgecolors="white", linewidths=.45)
        ax.set_xlabel("Dimension 1")
        ax.set_ylabel("Dimension 2")
        ax.set_title(f"{result.method_label} · 2D projection")
        ax.grid(alpha=.15)
        canvas.draw_idle()
        if result.dimensions == 3:
            three = self.canvas3d
            ax = three.new_axes(three_d=True)
            ax.scatter(vals["维度1"], vals["维度2"], vals["维度3"],
                       s=29, alpha=.74, depthshade=True)
            ax.set_xlabel("Dimension 1")
            ax.set_ylabel("Dimension 2")
            ax.set_zlabel("Dimension 3")
            ax.set_title(f"{result.method_label} · 3D embedding")
            three.draw_idle()
        else:
            self.canvas3d.clear_message("本次保留二维坐标；选择三维目标空间可绘制三维图")

    def update_history(self):
        records = self.session.reduction_results
        latest = self.current_result
        items = []
        for idx, rec in enumerate(records):
            common = rec.metrics.get("trustworthiness")
            specialized = {
                "factor": ("平均对数似然", "log_likelihood"),
                "mds": ("标准化距离残差", "stress_ratio"),
                "tsne": ("KL 散度", "kl_divergence"),
            }[rec.method]
            items.append({
                "序号": idx + 1,
                "算法": rec.method_label,
                "维度": rec.dimensions,
                "变量数量": len(rec.columns),
                "标准化": "是" if rec.standardized else "否",
                "邻域保持度": "" if common is None else round(common, 4),
                "专属指标": specialized[0],
                "指标值": rec.metrics.get(specialized[1]),
                "用时(s)": rec.elapsed_seconds,
                "与当前结果可比": (
                    "是" if latest is not None and
                    rec.comparability_key == latest.comparability_key else "否"
                ),
            })
        self.history_model.set_frame(pd.DataFrame(items))
        self.compare_a.clear()
        self.compare_b.clear()
        for i, rec in enumerate(records):
            caption = f"#{i+1} {rec.method_label} · {rec.dimensions}D"
            self.compare_a.addItem(caption, i)
            self.compare_b.addItem(caption, i)
        if len(records) > 1:
            self.compare_a.setCurrentIndex(len(records)-2)
            self.compare_b.setCurrentIndex(len(records)-1)

    def draw_comparison(self):
        records = self.session.reduction_results
        ia, ib = self.compare_a.currentData(), self.compare_b.currentData()
        if ia is None or ib is None or len(records) < 2 or ia == ib:
            QMessageBox.information(self, "方法对比", "请先运行至少两次分析，并选择不同的记录。")
            return
        left, right = records[ia], records[ib]
        if left.comparability_key != right.comparability_key:
            QMessageBox.warning(self, "对比条件不一致",
                "只有使用同一数据版本、相同变量、相同标准化方式和相同目标维度的结果"
                "才能作为公平的辅助比较。")
            return
        figure = self.comparison_canvas.figure
        figure.clear()
        for i, result in enumerate((left, right)):
            ax = figure.add_subplot(1, 2, i+1)
            coords = result.coordinates
            ax.scatter(coords["维度1"], coords["维度2"], s=15, alpha=.7)
            ax.set_aspect("equal", adjustable="datalim")
            ax.set_title(f"{result.method_label} · #{(ia, ib)[i]+1}", fontsize=10)
            ax.set_xlabel("Dimension 1")
            ax.set_ylabel("Dimension 2")
            ax.grid(alpha=.15)
        self.comparison_canvas.draw_idle()
        ta, tb = left.metrics.get("trustworthiness"), right.metrics.get("trustworthiness")
        format_score = lambda x: "未计算" if x is None else f"{x:.4f}"
        self.compare_summary.setText(
            f"相同条件下的局部邻域保持度：A={format_score(ta)}，"
            f"B={format_score(tb)}（较大通常代表局部邻域保留更好）。"
            "因子模型对数似然、MDS stress 和 t-SNE KL 散度不是同一种损失，"
            "不能据此直接得出整体算法优劣；左右坐标轴均为各自嵌入空间。"
        )
