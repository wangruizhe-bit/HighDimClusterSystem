"""PCA 专业分析页：变量与模式设置、结果表、谱图、二维/三维得分图。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QPushButton, QSpinBox, QTabWidget, QTableView,
    QVBoxLayout, QWidget,
)
from app.plot_canvas import PlotCanvas
from app.table_model import FrameTableModel
from core.pca import fit_pca


class PCAPage(QWidget):
    """显示完整 PCA 输出，数据变化时清理当前计算结果。"""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.result = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        parameters = QGroupBox("主成分分析设置")
        grid = QGridLayout(parameters)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        grid.addWidget(QLabel("参与分析的数值变量（可多选，不选择则使用全部数值变量）"), 0, 0, 1, 2)
        self.variables = QListWidget()
        self.variables.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.variables.setMaximumHeight(148)
        grid.addWidget(self.variables, 1, 0, 5, 2)

        self.standardize = QCheckBox("进行 Z-score 标准化")
        self.standardize.setChecked(True)
        grid.addWidget(self.standardize, 1, 2, 1, 2)

        grid.addWidget(QLabel("主成分数量选择方式"), 2, 2)
        self.mode = QComboBox()
        self.mode.addItem("自动推荐（累计贡献率 ≥85%）", "auto")
        self.mode.addItem("指定保留主成分数量", "manual")
        self.mode.addItem("按累计贡献率阈值", "threshold")
        self.mode.currentIndexChanged.connect(self.update_controls)
        grid.addWidget(self.mode, 2, 3)

        grid.addWidget(QLabel("主成分数量 k"), 3, 2)
        self.count = QSpinBox()
        self.count.setRange(1, 99999)
        self.count.setValue(2)
        grid.addWidget(self.count, 3, 3)

        grid.addWidget(QLabel("累计贡献率阈值（%）"), 4, 2)
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(1., 100.)
        self.threshold.setDecimals(1)
        self.threshold.setSingleStep(1.)
        self.threshold.setValue(85.)
        grid.addWidget(self.threshold, 4, 3)

        self.run_button = QPushButton("执行主成分分析")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self.run_analysis)
        grid.addWidget(self.run_button, 5, 2, 1, 2)
        root.addWidget(parameters)

        self.summary = QLabel("尚无 PCA 结果。请先导入数据。")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.tabs = QTabWidget()
        self.tables = {}
        for title, attr in [
            ("特征值与贡献率", "eigen_table"),
            ("主成分载荷", "loading_table"),
            ("主成分系数", "coefficient_table"),
            ("样本主成分得分", "score_table"),
        ]:
            view = QTableView()
            view.setAlternatingRowColors(True)
            view.horizontalHeader().setStretchLastSection(True)
            model = FrameTableModel(view)
            view.setModel(model)
            view.setMinimumHeight(360)
            self.tables[attr] = model
            self.tabs.addTab(view, title)

        self.variance_canvas = PlotCanvas()
        self.scatter2d_canvas = PlotCanvas()
        self.scatter3d_canvas = PlotCanvas(three_d=True)
        for title, canvas in [
            ("方差贡献率与碎石图", self.variance_canvas),
            ("二维主成分得分图", self.scatter2d_canvas),
            ("三维主成分得分图", self.scatter3d_canvas),
        ]:
            canvas.setMinimumHeight(400)
            self.tabs.addTab(canvas, title)
        root.addWidget(self.tabs)
        self.notes = QLabel("说明：载荷 = 原始输入变量与主成分得分的 Pearson 相关系数；"
                            "主成分系数 = 特征向量。各分析结果均来自当前工作数据。")
        self.notes.setWordWrap(True)
        root.addWidget(self.notes)

        self.session.data_changed.connect(self.on_data_changed)
        self.on_data_changed()
        self.update_controls()

    def update_controls(self, *_):
        current = self.mode.currentData()
        self.count.setEnabled(current == "manual")
        self.threshold.setEnabled(current == "threshold")

    def on_data_changed(self):
        self.result = None
        self.session.latest_pca = None
        self.variables.clear()
        numeric = self.session.data.get_numeric_columns()
        self.variables.addItems([str(name) for name in numeric])
        frame = self.session.data.current_data
        upper = min(len(frame), len(numeric)) if frame is not None else 1
        self.count.setMaximum(max(1, upper))
        if self.count.value() > upper:
            self.count.setValue(max(1, upper))
        for model in self.tables.values():
            model.set_frame(None)
        self.variance_canvas.clear_message("执行 PCA 后显示贡献率与累计贡献率")
        self.scatter2d_canvas.clear_message("需要至少 2 个已保留主成分")
        self.scatter3d_canvas.clear_message("需要至少 3 个已保留主成分")
        self.summary.setText("已载入数值变量，可以执行分析。" if numeric else
                             "尚无可分析的数值变量，请先导入数据。")

    def run_analysis(self):
        try:
            chosen = [item.text() for item in self.variables.selectedItems()] or None
            result = fit_pca(
                self.session.data.get_data(),
                columns=chosen,
                standardize=self.standardize.isChecked(),
                selection=self.mode.currentData(),
                component_count=self.count.value(),
                variance_threshold=self.threshold.value() / 100,
            )
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "PCA 参数或数据错误", str(exc))
            return
        except Exception:
            QMessageBox.warning(self, "PCA 分析失败", "计算失败，请检查数据内容和参数设置。")
            return
        self.result = result
        self.session.latest_pca = result
        self.summary.setText(
            f"本次分析：{result.sample_count} 个样本，{len(result.columns)} 个变量；"
            f"保留 {result.chosen_components} / {result.total_components} 个主成分；"
            f"累计方差贡献率 {result.retained_variance * 100:.2f}%；"
            f"{'已标准化' if result.standardized else '未标准化'}。"
        )
        for attr, model in self.tables.items():
            model.set_frame(getattr(result, attr))
        self.draw_variance(result)
        self.draw_scores2d(result)
        self.draw_scores3d(result)
        self.tabs.setCurrentIndex(0)
        self.session.results_changed.emit()

    def draw_variance(self, result):
        canvas = self.variance_canvas
        axes = canvas.new_axes()
        frame = result.eigen_table
        xs = list(range(1, result.total_components + 1))
        contribution = frame["方差贡献率(%)"].to_numpy()
        cumulative = frame["累计贡献率(%)"].to_numpy()
        axes.bar(xs, contribution, alpha=.85, label="Individual")
        axes.set_xlabel("Principal component")
        axes.set_ylabel("Explained variance (%)")
        axes.set_xticks(xs)
        axes.set_ylim(bottom=0)
        right = axes.twinx()
        right.plot(xs, cumulative, "o-", linewidth=1.6, label="Cumulative")
        right.axhline(85, color="#9aaec3", linestyle="--", alpha=.8)
        right.axvline(result.chosen_components, color="#577fa3",
                      linestyle=":", alpha=.75)
        right.set_ylabel("Cumulative variance (%)")
        right.set_ylim(0, 105)
        axes.set_title("PCA explained variance and cumulative contribution")
        canvas.draw_idle()

    def draw_scores2d(self, result):
        if result.chosen_components < 2:
            self.scatter2d_canvas.clear_message("只保留了一个主成分；请将 k 设为至少 2")
            return
        canvas = self.scatter2d_canvas
        ax = canvas.new_axes()
        x = result.score_table["PC1"]
        y = result.score_table["PC2"]
        ax.scatter(x, y, s=27, alpha=.75, edgecolor="white", linewidth=.4)
        ax.axhline(0, color="#bdc9d7", lw=.8)
        ax.axvline(0, color="#bdc9d7", lw=.8)
        ax.set_xlabel(f"PC1 ({result.eigen_table['方差贡献率(%)'].iat[0]:.1f}%)")
        ax.set_ylabel(f"PC2 ({result.eigen_table['方差贡献率(%)'].iat[1]:.1f}%)")
        ax.set_title("PCA score plot (2D)")
        ax.grid(alpha=.15)
        canvas.draw_idle()

    def draw_scores3d(self, result):
        if result.chosen_components < 3:
            self.scatter3d_canvas.clear_message("需要至少三个保留主成分；请将 k 设为至少 3")
            return
        canvas = self.scatter3d_canvas
        ax = canvas.new_axes(three_d=True)
        score = result.score_table
        ax.scatter(score["PC1"], score["PC2"], score["PC3"],
                   s=24, alpha=.77, depthshade=True)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_zlabel("PC3")
        ax.set_title("PCA score plot (3D)")
        canvas.draw_idle()
