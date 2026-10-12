"""八页中文界面：统计、PCA、降维、聚类与评价均接入真实计算。"""
from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLayout, QListWidget, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QTableView, QVBoxLayout, QWidget, QComboBox, QTabWidget,
)
from core import preprocessing, statistics
from app.diagnostics import record_fatal_context
from app.plot_canvas import PlotCanvas
from app.pca_page import PCAPage
from app.dimension_page import ReductionPage
from app.clustering_page import ClusterPage
from app.evaluation_page import EvaluationPage
from app.results_page import ResultsPage
from app.session import Session
from app.table_model import FrameTableModel
from app.studio_components import (
    DataLensRail, MetricGrid, MetricTile, ModeStrip, PageBanner, StudioHeader, AnalysisLayout,
)

PAGES = [
    "分析首页", "数据管理与预处理", "特征统计分析", "主成分分析（PCA）",
    "多方法降维", "聚类分析", "聚类评价与模型对比", "结果中心",
]
NAV_TITLES = [
    "概览", "数据准备", "特征探索", "PCA",
    "多方法降维", "聚类", "模型评价", "结果中心",
]


def resource_path(*parts):
    """兼容源码运行和 PyInstaller onedir 的只读资源路径。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base.joinpath(*parts)


def label(text, kind=None):
    widget = QLabel(str(text))
    widget.setWordWrap(True)
    if kind:
        widget.setObjectName(kind)
    return widget


def button(text, fn, primary=False):
    widget = QPushButton(text)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(fn)
    return widget


def card(title=None):
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(10)
    if title:
        lay.addWidget(label(title, "cardTitle"))
    return frame, lay


def table():
    view = QTableView()
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    view.setSortingEnabled(False)
    view.setMinimumHeight(220)
    view.horizontalHeader().setStretchLastSection(True)
    return view


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高维数据降维与聚类分析系统 V1.0")
        self.resize(1600, 940)
        self.setMinimumSize(1180, 760)
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            self.resize(max(1180, min(1600, available.width() - 40)),
                        max(760, min(940, available.height() - 48)))
        self.session = Session(self)
        self.views = []
        self.feature_figure_ready = False
        self.refreshers = []
        self.setStatusBar(self.statusBar())

        root = QWidget()
        root.setObjectName("studioWorkspace")
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # Data Studio 主界面：品牌顶栏、横向模式导航、分析画布和数据概览。
        self.studio_header = StudioHeader(
            self.open_file,
            self.toggle_data_lens,
            self,
        )
        shell.addWidget(self.studio_header)

        self.mode_strip = ModeStrip(NAV_TITLES, self.goto, self)
        self.nav_buttons = self.mode_strip.buttons  # 保留公共接口，方便自动化测试和快捷导航。
        shell.addWidget(self.mode_strip)

        self.stack = QStackedWidget()
        self.stack.setObjectName("studioCanvas")
        self.data_lens = DataLensRail(self)
        self.data_lens.setVisible(False)
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        content_row.addWidget(self.stack, 1)
        content_row.addWidget(self.data_lens, 0)
        content_row.setStretch(0, 1)
        content_row.setStretch(1, 0)
        shell.addLayout(content_row, 1)

        makers = [
            self.make_home, self.make_data_page, self.make_feature_page,
            self.make_pca_page, self.make_dimension_page, self.make_cluster_page,
            self.make_evaluation_page, self.make_results_page
        ]
        for index, (name, maker) in enumerate(zip(PAGES, makers)):
            scroll = QScrollArea()
            scroll.setObjectName("studioScroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            page = QWidget()
            page.setObjectName("studioPage")
            page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            lay = QVBoxLayout(page)
            lay.setContentsMargins(20, 16, 20, 20)
            lay.setSpacing(12)
            lay.setAlignment(Qt.AlignmentFlag.AlignTop)
            lay.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
            lay.addWidget(PageBanner(index, name))
            maker(lay)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        self.session.data_changed.connect(self.refresh_all)
        self.goto(0)
        self.refresh_all()

    def toggle_data_lens(self, checked=False):
        self.data_lens.setVisible(bool(checked))
        self.studio_header.result_button.setChecked(bool(checked))

    def goto(self, number):
        if not 0 <= number < self.stack.count():
            return
        self.stack.setCurrentIndex(number)
        self.mode_strip.select(number)
        self.data_lens.update_mode(number, PAGES[number])
        record_fatal_context(f"页面切换: {number + 1:02d} {PAGES[number]}")
        self.statusBar().showMessage(
            f"当前位置：{number + 1:02d}  ·  {PAGES[number]}", 4000
        )

    def _result_count(self):
        return (
            (1 if self.session.feature_result is not None else 0)
            + (1 if self.session.latest_pca is not None else 0)
            + len(self.session.reduction_results)
            + len(self.session.cluster_results)
            + (1 if self.session.k_search_result is not None else 0)
        )

    def _refresh_data_lens(self):
        summary = self.session.data.summary()
        self.data_lens.update_data(summary, self._result_count())
        self.studio_header.update_dataset(summary)

    def inform(self, message):
        QMessageBox.information(self, "提示", message)

    def fail(self, error):
        QMessageBox.warning(self, "操作未完成", str(error))

    def guarded(self, operation):
        try:
            operation()
        except (ValueError, TypeError, OSError, KeyError) as exc:
            self.fail(exc)
        except Exception:
            self.fail("操作发生意外错误，请检查数据文件与输入参数。")

    def make_home(self, layout):
        actions = QHBoxLayout()
        self.home_dataset_name = label("选择一个数据集，开始分析", "homeHeading")
        actions.addWidget(self.home_dataset_name, 1)
        actions.addWidget(button("导入数据", self.open_file, True))
        actions.addWidget(button("使用示例", self.load_demo_data))
        layout.addLayout(actions)

        self.metric_tiles = {
            "rows": MetricTile("样本", "0"),
            "numeric": MetricTile("数值变量", "0"),
            "missing": MetricTile("缺失", "0"),
            "results": MetricTile("分析结果", "0"),
        }
        metrics = MetricGrid()
        metrics.add_tiles(list(self.metric_tiles.values()))
        layout.addWidget(metrics)

        self.home_pipeline = QFrame()
        self.home_pipeline.setObjectName("quickActions")
        row = QHBoxLayout(self.home_pipeline)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self.home_pipeline_steps = []
        for title, target, hint in [
            ("PCA", 3, "主成分分析"),
            ("降维", 4, "因子分析 / MDS / t-SNE"),
            ("聚类", 5, "K-means / 层次聚类 / DBSCAN"),
            ("评价", 6, "聚类指标 / K 值选择"),
        ]:
            action = button(title + "  →", lambda checked=False, page=target: self.goto(page))
            action.setObjectName("quickAction")
            action.setToolTip(hint)
            row.addWidget(action, 1)
            self.home_pipeline_steps.append(action)
        layout.addWidget(self.home_pipeline)

        panel, content = card("数据预览")
        self.home_preview = table()
        self.home_preview.setMinimumHeight(280)
        self.home_preview_model = FrameTableModel(self.home_preview)
        self.home_preview.setModel(self.home_preview_model)
        content.addWidget(self.home_preview)
        layout.addWidget(panel, 1)
        self.home_dataset_hint = label("尚未导入数据", "muted")
        layout.addWidget(self.home_dataset_hint)

        def update():
            summary = self.session.data.summary()
            imported = summary["rows"] > 0
            self.home_dataset_name.setText(summary["name"] if imported else "选择一个数据集，开始分析")
            self.home_dataset_hint.setText(
                f"{summary['rows']} 行 · {summary['columns']} 列 · 当前工作数据"
                if imported else "支持 CSV、XLSX 和 XLS"
            )
            self.home_preview_model.set_frame(self.session.data.current_data)
            for key, value in (("rows", summary["rows"]), ("numeric", summary["numeric"]),
                               ("missing", summary["missing"]), ("results", self._result_count())):
                self.metric_tiles[key].set_value(value)
        self.refreshers.append(update)
        self.session.results_changed.connect(update)
        self.session.results_changed.connect(self._refresh_data_lens)

    def make_data_page(self, layout):
        panel, pane = card()
        actions = QHBoxLayout()
        actions.addWidget(button("导入数据", self.open_file, True))
        actions.addWidget(button("使用示例", self.load_demo_data))
        actions.addWidget(button("恢复原始数据", lambda: self.guarded(self.session.restore)))
        actions.addStretch(1)
        pane.addLayout(actions)
        processing = QHBoxLayout()
        processing.addWidget(label("预处理"))
        self.preprocess_selector = QComboBox()
        self.preprocessing_operations = [
            ("删除缺失行", lambda f: preprocessing.drop_missing(f)),
            ("均值填补", lambda f: preprocessing.fill_missing(f, "mean")),
            ("中位数填补", lambda f: preprocessing.fill_missing(f, "median")),
            ("删除重复行", lambda f: preprocessing.remove_duplicates(f)),
            ("Z-score 标准化", lambda f: preprocessing.scale_numeric(f, "zscore")),
            ("Min-Max 归一化", lambda f: preprocessing.scale_numeric(f, "minmax")),
        ]
        self.preprocess_selector.addItems([name for name, _ in self.preprocessing_operations])
        processing.addWidget(self.preprocess_selector)
        self.preprocess_apply_button = button("应用", self.apply_preprocessing)
        processing.addWidget(self.preprocess_apply_button)
        processing.addStretch(1)
        self.data_summary = label("尚未导入数据", "muted")
        processing.addWidget(self.data_summary)
        pane.addLayout(processing)
        layout.addWidget(panel)

        self.data_tabs = QTabWidget()
        self.data_table = table()
        self.data_table.setMinimumHeight(380)
        self.data_model = FrameTableModel(self.data_table)
        self.data_table.setModel(self.data_model)
        self.data_tabs.addTab(self.data_table, "数据")
        self.column_table = table()
        self.column_model = FrameTableModel(self.column_table)
        self.column_table.setModel(self.column_model)
        self.data_tabs.addTab(self.column_table, "变量概况")
        layout.addWidget(self.data_tabs, 1)

        def update():
            frame = self.session.data.current_data
            self.data_model.set_frame(frame)
            self.home_preview_model.set_frame(frame)
            if frame is None:
                self.column_model.set_frame(None)
                self.data_summary.setText("尚未导入数据")
                self.preprocess_apply_button.setEnabled(False)
                return
            stats = self.session.data.summary()
            self.data_summary.setText(
                f"{stats['rows']} 行 · {stats['columns']} 列 · 缺失 {stats['missing']} · 重复 {stats['duplicates']}")
            self.data_summary.setToolTip(f"{stats['name']}\n数值变量 {stats['numeric']} · 非数值变量 {stats['non_numeric']}")
            self.column_model.set_frame(self.session.data.column_summary())
            self.preprocess_apply_button.setEnabled(True)
        self.refreshers.append(update)

    def apply_preprocessing(self):
        name, operation = self.preprocessing_operations[self.preprocess_selector.currentIndex()]
        self.preprocess(name, operation)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "", "表格文件 (*.csv *.xlsx *.xls)")
        if file:
            self.guarded(lambda: self.session.load(file))

    def load_demo_data(self):
        """载入内置 90 样本 × 8 数值特征示例数据，便于直接体验完整流程。"""
        path = resource_path("data", "demo_high_dimensional.csv")
        if not path.is_file():
            self.fail("内置示例数据文件缺失，请重新下载完整软件包。")
            return
        self.guarded(lambda: self.session.load(str(path)))
        if self.session.data.current_data is not None:
            self.statusBar().showMessage(
                "已加载示例数据：90 个样本、8 个数值特征、3 个已知分组。", 9000
            )
            self.goto(1)

    def preprocess(self, name, operation):
        def run():
            before = self.session.data.get_data()
            after = operation(before)
            if after.empty:
                self.inform("该操作将删除全部样本，已取消；工作数据保持不变。")
                return
            self.session.apply(after)
            self.statusBar().showMessage(f"完成：{name}（{len(before)} → {len(after)} 行）", 8000)
        self.guarded(run)

    def make_feature_page(self, layout):
        workspace = QWidget()
        split = AnalysisLayout(workspace)
        panel, pane = card("变量 · 默认全部")
        self.feature_vars = QListWidget()
        self.feature_vars.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.feature_vars.setMaximumHeight(160)
        pane.addWidget(self.feature_vars)
        actions = QGridLayout()
        feature_actions = [
            ("描述性统计", lambda: self.calculate_stats("describe")),
            ("Pearson 相关性", lambda: self.calculate_stats("corr")),
            ("协方差矩阵", lambda: self.calculate_stats("cov")),
            ("相关热力图", self.draw_heatmap),
            ("变量直方图", lambda: self.plot_feature("hist")),
            ("多变量箱线图", lambda: self.plot_feature("box")),
            ("双变量散点图", lambda: self.plot_feature("scatter")),
        ]
        self.feature_action_buttons = {}
        for i, (caption, fn) in enumerate(feature_actions):
            action_button = button(caption, fn, i == 0)
            self.feature_action_buttons[caption] = action_button
            actions.addWidget(action_button, i, 0)
        pane.addLayout(actions)
        split.add_parameters(panel)
        self.feature_tabs = QTabWidget()
        self.stats_table = table()
        self.stats_model = FrameTableModel(self.stats_table)
        self.stats_table.setModel(self.stats_model)
        self.stats_table.setMinimumHeight(400)
        self.feature_tabs.addTab(self.stats_table, "统计表")
        self.statistics_canvas = PlotCanvas()
        self.statistics_canvas.setMinimumHeight(400)
        self.feature_tabs.addTab(self.statistics_canvas, "图表")
        split.results.addWidget(self.feature_tabs, 1)
        layout.addWidget(workspace, 1)

        def update():
            self.feature_vars.clear()
            self.feature_vars.addItems([str(x) for x in self.session.data.get_numeric_columns()])
            self.stats_model.set_frame(None)
            self.statistics_canvas.clear_message("选择数值变量并执行统计分析")
            self.feature_figure_ready = False
        self.refreshers.append(update)

    def selected_columns(self, widget):
        selected = [item.text() for item in widget.selectedItems()]
        return selected or None

    def calculate_stats(self, kind):
        def work():
            df = self.session.data.get_data()
            cols = self.selected_columns(self.feature_vars)
            if kind == "describe":
                output = statistics.describe(df, cols)
            elif kind == "corr":
                output = statistics.correlation(df, cols).rename_axis("变量").reset_index()
            else:
                output = statistics.covariance(df, cols).rename_axis("变量").reset_index()
            self.stats_model.set_frame(output)
            self.feature_tabs.setCurrentIndex(0)
            names = {"describe": "描述性统计", "corr": "Pearson 相关性", "cov": "协方差"}
            self.session.feature_result = (names[kind], output.copy(deep=True))
            self.session.results_changed.emit()
            self.statusBar().showMessage("统计计算已完成。", 5000)
        self.guarded(work)

    def draw_heatmap(self):
        def work():
            matrix = statistics.correlation(
                self.session.data.get_data(), self.selected_columns(self.feature_vars))

            def build(axes):
                from mpl_toolkits.axes_grid1 import make_axes_locatable
                pic = axes.imshow(matrix.to_numpy(), cmap="Blues", vmin=-1, vmax=1)
                axes.set_xticks(
                    range(len(matrix.columns)),
                    [str(x) for x in matrix.columns],
                    rotation=45, ha="right",
                )
                axes.set_yticks(range(len(matrix.index)), [str(x) for x in matrix.index])
                axes.set_title("Pearson 相关热力图")
                color_axis = make_axes_locatable(axes).append_axes("right", size="4%", pad=.18)
                self.statistics_canvas.figure.colorbar(pic, cax=color_axis)
                self.statistics_canvas.figure.subplots_adjust(bottom=.24, top=.90)

            if self.statistics_canvas.safe_update(
                "Pearson 相关热力图", build, force_draw=True
            ):
                self.feature_figure_ready = True
                self.feature_tabs.setCurrentIndex(1)
                self.session.results_changed.emit()
        self.guarded(work)

    def plot_feature(self, kind):
        """基于当前数据和已选数值列进行分布与散点可视化。"""
        import numpy as np

        def work():
            frame = statistics.numeric_data(
                self.session.data.get_data(), self.selected_columns(self.feature_vars))
            canvas = self.statistics_canvas

            def build(ax):
                if kind == "hist":
                    col = frame.columns[0]
                    clean = frame[col].replace([np.inf, -np.inf], np.nan).dropna()
                    if clean.empty:
                        raise ValueError("该变量没有可用的有限数值。")
                    ax.hist(
                        clean, bins="auto", color="#3b82b8",
                        edgecolor="white", alpha=.8
                    )
                    ax.set_title(f"{col} 分布（n={len(clean)}）")
                    ax.set_xlabel(str(col))
                    ax.set_ylabel("频数")
                elif kind == "box":
                    chart = frame.iloc[:, :12].replace([np.inf, -np.inf], np.nan)
                    series = [chart[c].dropna().to_numpy() for c in chart.columns]
                    valid = [
                        (str(c), v)
                        for c, v in zip(chart.columns, series)
                        if len(v)
                    ]
                    if not valid:
                        raise ValueError("所选变量没有可用于箱线图的有限数值。")
                    ax.boxplot(
                        [v for _, v in valid],
                        tick_labels=[c for c, _ in valid],
                        patch_artist=False,
                    )
                    ax.tick_params(axis="x", rotation=35)
                    ax.set_title("多变量箱线图（最多 12 个变量）")
                    ax.set_ylabel("数值")
                elif kind == "scatter":
                    if len(frame.columns) < 2:
                        raise ValueError("双变量散点图至少需要两个数值变量。")
                    left, right = frame.columns[:2]
                    finite = frame.loc[:, [left, right]].replace(
                        [np.inf, -np.inf], np.nan
                    ).dropna()
                    if finite.empty:
                        raise ValueError("两变量没有共同的有效样本。")
                    ax.scatter(
                        finite[left], finite[right], alpha=.7, s=25,
                        edgecolors="white", linewidths=.4,
                    )
                    ax.set_xlabel(str(left))
                    ax.set_ylabel(str(right))
                    ax.set_title(
                        f"{left} 与 {right} 散点图（n={len(finite)}）"
                    )
                else:
                    raise ValueError("未知图表类型。")
                ax.grid(alpha=.15)

            title = {
                "hist": "变量直方图",
                "box": "多变量箱线图",
                "scatter": "双变量散点图",
            }.get(kind, "特征统计图")
            if canvas.safe_update(title, build, force_draw=True):
                self.feature_figure_ready = True
                self.feature_tabs.setCurrentIndex(1)
                self.session.results_changed.emit()
        self.guarded(work)

    def make_pca_page(self, layout):
        self.pca_page = PCAPage(self.session)
        layout.addWidget(self.pca_page)

    def make_dimension_page(self, layout):
        self.dimension_page = ReductionPage(self.session)
        layout.addWidget(self.dimension_page)

    def make_cluster_page(self, layout):
        self.cluster_page = ClusterPage(self.session)
        layout.addWidget(self.cluster_page)

    def make_evaluation_page(self, layout):
        self.evaluation_page = EvaluationPage(self.session)
        layout.addWidget(self.evaluation_page)

    def make_results_page(self, layout):
        self.results_page = ResultsPage(self.session, self)
        layout.addWidget(self.results_page)

    def closeEvent(self, event):
        busy = [
            p for p in (
                getattr(self, "dimension_page", None),
                getattr(self, "cluster_page", None),
                getattr(self, "evaluation_page", None),
            ) if p is not None and p.busy
        ]
        if busy:
            QMessageBox.information(self, "计算进行中",
                "计算线程仍在运行，请等待分析完成后再关闭窗口。")
            event.ignore()
            return
        super().closeEvent(event)

    def refresh_all(self):
        for refresh in self.refreshers:
            refresh()
        self._refresh_data_lens()
