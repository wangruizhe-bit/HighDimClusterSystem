"""八页中文界面：统计、PCA、降维、聚类与评价均接入真实计算。"""
from functools import partial

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QDoubleSpinBox, QStackedWidget,
    QTableView, QVBoxLayout, QWidget,
)
from core import preprocessing, statistics
from app.plot_canvas import PlotCanvas
from app.pca_page import PCAPage
from app.dimension_page import ReductionPage
from app.clustering_page import ClusterPage
from app.evaluation_page import EvaluationPage
from app.results_page import ResultsPage
from app.session import Session
from app.table_model import FrameTableModel
from app.studio_components import (
    DataLensRail, MetricGrid, MetricTile, ModeStrip, PageBanner, PipelineStep, StudioHeader,
)

PAGES = [
    "分析首页", "数据管理与预处理", "特征统计分析", "主成分分析（PCA）",
    "多方法降维", "聚类分析", "聚类评价与模型对比", "结果中心",
]
NAV_TITLES = [
    "概览", "数据准备", "特征探索", "PCA",
    "多方法降维", "聚类", "模型评价", "结果中心",
]


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
    lay.setContentsMargins(20, 17, 20, 17)
    lay.setSpacing(12)
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
        self.resize(1480, 920)
        self.setMinimumSize(1080, 720)
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

        # 第三个软著采用独立的 Data Studio 结构：
        # 深色品牌顶栏 + 横向模式导航 + 全宽分析画布。
        self.studio_header = StudioHeader(
            self.open_file,
            lambda: self.goto(7),
            self,
        )
        shell.addWidget(self.studio_header)

        self.mode_strip = ModeStrip(NAV_TITLES, self.goto, self)
        self.nav_buttons = self.mode_strip.buttons  # 保留公共接口，方便自动化测试和快捷导航。
        shell.addWidget(self.mode_strip)

        self.stack = QStackedWidget()
        self.stack.setObjectName("studioCanvas")
        self.data_lens = DataLensRail(self)
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        content_row.addWidget(self.stack, 1)
        content_row.addWidget(self.data_lens)
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
            lay = QVBoxLayout(page)
            lay.setContentsMargins(30, 24, 30, 30)
            lay.setSpacing(16)
            lay.addWidget(PageBanner(index, name))
            maker(lay)
            lay.addStretch(1)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        self.session.data_changed.connect(self.refresh_all)
        self.goto(0)
        self.refresh_all()

    def goto(self, number):
        if not 0 <= number < self.stack.count():
            return
        self.stack.setCurrentIndex(number)
        self.mode_strip.select(number)
        self.data_lens.update_mode(number, PAGES[number])
        self.statusBar().showMessage(
            f"DATA STUDIO  ·  {number + 1:02d}  ·  {PAGES[number]}", 4000
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
        hero = QFrame()
        hero.setObjectName("homeHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(24)

        copy = QVBoxLayout()
        copy.setSpacing(9)
        copy.addWidget(label("DATA DISCOVERY / DIMENSION REDUCTION / CLUSTERING", "heroEyebrow"))
        copy.addWidget(label("从高维数据中发现结构", "heroTitle"))
        copy.addWidget(label(
            "以真实数据为起点，完成清洗、统计探索、PCA、多方法降维、聚类与模型评价，"
            "在统一工作区中追踪数据状态、分析过程与可导出结果。",
            "heroSubtitle"
        ))
        hero_actions = QHBoxLayout()
        hero_actions.setSpacing(10)
        hero_actions.addWidget(button("＋  导入数据", self.open_file, True))
        hero_actions.addWidget(button("探索变量", lambda: self.goto(2)))
        hero_actions.addWidget(button("开始聚类", lambda: self.goto(5)))
        hero_actions.addStretch(1)
        copy.addLayout(hero_actions)
        hero_layout.addLayout(copy, 3)

        context = QFrame()
        context.setObjectName("homeContext")
        ctx = QVBoxLayout(context)
        ctx.setContentsMargins(18, 16, 18, 16)
        ctx.setSpacing(6)
        ctx.addWidget(label("WORKSPACE STATUS", "contextEyebrow"))
        self.home_dataset_name = label("尚未导入数据", "contextTitle")
        ctx.addWidget(self.home_dataset_name)
        self.home_dataset_hint = label("导入 CSV 或 Excel 后开始分析", "contextHint")
        ctx.addWidget(self.home_dataset_hint)
        ctx.addStretch(1)
        self.home_result_count = label("0 个分析结果", "contextBadge")
        ctx.addWidget(self.home_result_count)
        hero_layout.addWidget(context, 1)
        layout.addWidget(hero)

        self.metric_tiles = {
            "rows": MetricTile("样本数量", "0", "当前工作数据", "violet"),
            "numeric": MetricTile("数值变量", "0", "可参与降维与聚类", "amber"),
            "missing": MetricTile("缺失单元格", "0", "建议在建模前处理", "rose"),
            "results": MetricTile("分析结果", "0", "当前数据版本结果快照", "mint"),
        }
        metrics = MetricGrid()
        metrics.add_tiles(list(self.metric_tiles.values()))
        layout.addWidget(metrics)

        body = QHBoxLayout()
        body.setSpacing(14)

        pipeline = QFrame()
        pipeline.setObjectName("studioPanel")
        pipeline_layout = QVBoxLayout(pipeline)
        pipeline_layout.setContentsMargins(20, 18, 20, 18)
        pipeline_layout.setSpacing(10)
        pipeline_layout.addWidget(label("分析路径", "panelTitle"))
        pipeline_layout.addWidget(label(
            "不是固定向导，可按研究任务跳转；下列四步覆盖最常见的数据分析流程。",
            "panelHint"
        ))
        steps = [
            (1, "准备数据", "导入 · 清洗 · 缺失值 · 标准化", 1),
            (2, "理解结构", "描述统计 · 相关性 · PCA · 嵌入", 2),
            (3, "识别类别", "K-means · 层次聚类 · DBSCAN", 5),
            (4, "评价与交付", "质量指标 · K 值 · 结果导出", 6),
        ]
        for number, title, hint, target in steps:
            pipeline_layout.addWidget(PipelineStep(
                number, title, hint,
                lambda checked=False, page=target: self.goto(page)
            ))
        pipeline_layout.addStretch(1)
        body.addWidget(pipeline, 3)

        capability = QFrame()
        capability.setObjectName("studioPanel")
        cap = QVBoxLayout(capability)
        cap.setContentsMargins(20, 18, 20, 18)
        cap.setSpacing(10)
        cap.addWidget(label("分析能力矩阵", "panelTitle"))
        cap.addWidget(label("已完成并接入真实计算的模块", "panelHint"))
        capabilities = [
            ("PCA", "特征值 / 载荷 / 得分 / 2D-3D"),
            ("FA · MDS · t-SNE", "解释型降维与非线性嵌入"),
            ("K-means · HC · DBSCAN", "三类互补聚类方法"),
            ("Silhouette · CH · DB", "聚类质量与 K 值辅助判断"),
            ("CSV · Excel · HTML", "表格、报告与图像本地导出"),
        ]
        for name, hint in capabilities:
            line = QFrame()
            line.setObjectName("capabilityRow")
            row = QHBoxLayout(line)
            row.setContentsMargins(12, 9, 12, 9)
            row.addWidget(label(name, "capabilityName"))
            row.addStretch(1)
            row.addWidget(label(hint, "capabilityHint"))
            cap.addWidget(line)
        cap.addStretch(1)
        body.addWidget(capability, 2)
        layout.addLayout(body)

        def update():
            summary = self.session.data.summary()
            self.studio_header.update_dataset(summary)
            imported = summary["rows"] > 0
            self.home_dataset_name.setText(summary["name"] if imported else "尚未导入数据")
            self.home_dataset_hint.setText(
                f"{summary['rows']} 行 × {summary['columns']} 列 · "
                f"{summary['numeric']} 个数值变量"
                if imported else "导入 CSV 或 Excel 后开始分析"
            )
            result_count = self._result_count()
            self.home_result_count.setText(f"{result_count} 个分析结果")
            self.metric_tiles["rows"].set_value(summary["rows"], "当前工作数据")
            self.metric_tiles["numeric"].set_value(summary["numeric"], "可参与降维与聚类")
            self.metric_tiles["missing"].set_value(summary["missing"], "建议在建模前处理")
            self.metric_tiles["results"].set_value(result_count, "当前数据版本结果快照")
        self.refreshers.append(update)
        self.session.results_changed.connect(update)
        self.session.results_changed.connect(self._refresh_data_lens)

    def make_data_page(self, layout):
        info, pane = card("导入与预处理")
        actions = QHBoxLayout()
        actions.addWidget(button("导入 CSV / Excel", self.open_file, True))
        actions.addWidget(button("恢复原始数据", lambda: self.guarded(self.session.restore)))
        actions.addStretch()
        pane.addLayout(actions)
        grid = QGridLayout()
        items = [
            ("删除含缺失值的样本", lambda f: preprocessing.drop_missing(f)),
            ("均值填补数值缺失", lambda f: preprocessing.fill_missing(f, "mean")),
            ("中位数填补数值缺失", lambda f: preprocessing.fill_missing(f, "median")),
            ("删除重复样本", lambda f: preprocessing.remove_duplicates(f)),
            ("Z-score 标准化", lambda f: preprocessing.scale_numeric(f, "zscore")),
            ("Min-Max 归一化", lambda f: preprocessing.scale_numeric(f, "minmax")),
        ]
        for i, (title, operation) in enumerate(items):
            grid.addWidget(button(title, partial(self.preprocess, title, operation)), i // 3, i % 3)
        pane.addLayout(grid)
        layout.addWidget(info)
        panel, pane = card("数据基本信息")
        self.data_summary = label("尚未导入数据。")
        pane.addWidget(self.data_summary)
        layout.addWidget(panel)
        panel, pane = card("数据预览（最多显示前 500 行）")
        self.data_table = table()
        self.data_model = FrameTableModel(self.data_table)
        self.data_table.setModel(self.data_model)
        pane.addWidget(self.data_table)
        layout.addWidget(panel)
        panel, pane = card("逐列数据概况")
        self.column_table = table()
        self.column_model = FrameTableModel(self.column_table)
        self.column_table.setModel(self.column_model)
        pane.addWidget(self.column_table)
        layout.addWidget(panel)

        def update():
            if self.session.data.current_data is None:
                self.data_model.set_frame(None)
                self.column_model.set_frame(None)
                self.data_summary.setText("尚未导入数据。")
                return
            stats = self.session.data.summary()
            self.data_summary.setText(
                f"文件：{stats['name']}    行数：{stats['rows']}    列数：{stats['columns']}\n"
                f"数值变量：{stats['numeric']}    非数值变量：{stats['non_numeric']}    "
                f"缺失值：{stats['missing']}    重复行：{stats['duplicates']}")
            self.data_model.set_frame(self.session.data.current_data)
            self.column_model.set_frame(self.session.data.column_summary())
        self.refreshers.append(update)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "", "表格文件 (*.csv *.xlsx *.xls)")
        if file:
            self.guarded(lambda: self.session.load(file))

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
        panel, pane = card("数值变量选择")
        pane.addWidget(label("可多选变量；未选择时默认分析全部数值列。"))
        self.feature_vars = QListWidget()
        self.feature_vars.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.feature_vars.setMaximumHeight(145)
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
        for i, (caption, fn) in enumerate(feature_actions):
            actions.addWidget(button(caption, fn, i == 0), i // 4, i % 4)
        pane.addLayout(actions)
        layout.addWidget(panel)
        panel, pane = card("真实统计计算结果")
        self.stats_table = table()
        self.stats_model = FrameTableModel(self.stats_table)
        self.stats_table.setModel(self.stats_model)
        pane.addWidget(self.stats_table)
        self.statistics_canvas = PlotCanvas()
        self.statistics_canvas.setMinimumHeight(310)
        pane.addWidget(self.statistics_canvas)
        layout.addWidget(panel)

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
            names = {"describe": "描述性统计", "corr": "Pearson 相关性", "cov": "协方差"}
            self.session.feature_result = (names[kind], output.copy(deep=True))
            self.session.results_changed.emit()
            self.statusBar().showMessage("统计计算已完成。", 5000)
        self.guarded(work)

    def draw_heatmap(self):
        def work():
            matrix = statistics.correlation(
                self.session.data.get_data(), self.selected_columns(self.feature_vars))
            axes = self.statistics_canvas.new_axes()
            pic = axes.imshow(matrix.to_numpy(), cmap="Blues", vmin=-1, vmax=1)
            axes.set_xticks(range(len(matrix.columns)),
                           [str(x) for x in matrix.columns], rotation=45, ha="right")
            axes.set_yticks(range(len(matrix.index)), [str(x) for x in matrix.index])
            axes.set_title("Pearson correlation")
            # 重新绘图前移除此前的颜色条，防止重复堆积。
            for other in list(self.statistics_canvas.figure.axes):
                if other is not axes:
                    other.remove()
            self.statistics_canvas.figure.colorbar(pic, ax=axes, fraction=.045, pad=.035)
            self.statistics_canvas.draw_idle()
            self.feature_figure_ready = True
            self.session.results_changed.emit()
        self.guarded(work)

    def plot_feature(self, kind):
        """基于当前数据和已选数值列进行真实分布与散点可视化。"""
        import numpy as np
        def work():
            frame = statistics.numeric_data(
                self.session.data.get_data(), self.selected_columns(self.feature_vars))
            canvas = self.statistics_canvas
            ax = canvas.new_axes()
            if kind == "hist":
                col = frame.columns[0]
                clean = frame[col].replace([np.inf, -np.inf], np.nan).dropna()
                if clean.empty:
                    raise ValueError("该变量没有可用的有限数值。")
                ax.hist(clean, bins="auto", color="#3b82b8", edgecolor="white", alpha=.8)
                ax.set_title(f"Distribution: {col} (n={len(clean)})")
                ax.set_xlabel(str(col))
                ax.set_ylabel("Frequency")
            elif kind == "box":
                # 对多变量图形的显示数量设上限，不影响统计结果本身。
                chart = frame.iloc[:, :12].replace([np.inf, -np.inf], np.nan)
                series = [chart[c].dropna().to_numpy() for c in chart.columns]
                valid = [(str(c), v) for c, v in zip(chart.columns, series) if len(v)]
                if not valid:
                    raise ValueError("所选变量没有可用于箱线图的有限数值。")
                ax.boxplot([v for _, v in valid], tick_labels=[c for c, _ in valid],
                           patch_artist=False)
                ax.tick_params(axis="x", rotation=35)
                ax.set_title("Box plot (up to 12 variables)")
                ax.set_ylabel("Value")
            elif kind == "scatter":
                if len(frame.columns) < 2:
                    raise ValueError("双变量散点图至少需要两个数值变量。")
                left, right = frame.columns[:2]
                finite = frame.loc[:, [left, right]].replace(
                    [np.inf, -np.inf], np.nan).dropna()
                if finite.empty:
                    raise ValueError("两变量没有共同的有效样本。")
                ax.scatter(finite[left], finite[right], alpha=.7, s=25,
                           edgecolors="white", linewidths=.4)
                ax.set_xlabel(str(left))
                ax.set_ylabel(str(right))
                ax.set_title(f"Scatter: {left} vs {right} (n={len(finite)})")
            else:
                raise ValueError("未知图表类型。")
            ax.grid(alpha=.15)
            canvas.draw_idle()
            self.feature_figure_ready = True
            self.session.results_changed.emit()
        self.guarded(work)

    def settings_box(self, title, fields):
        group = QGroupBox(title)
        lay = QGridLayout(group)
        for row, (name, typ, values) in enumerate(fields):
            lay.addWidget(label(name), row, 0)
            if typ == "choice":
                widget = QComboBox()
                widget.addItems(values)
            elif typ == "float":
                widget = QDoubleSpinBox()
                widget.setRange(0.001, 100000)
                widget.setDecimals(3)
                widget.setValue(float(values))
            elif typ == "check":
                widget = QCheckBox()
                widget.setChecked(bool(values))
            else:
                widget = QSpinBox()
                widget.setRange(1, 100000)
                widget.setValue(int(values))
            lay.addWidget(widget, row, 1)
        return group

    def placeholder(self, layout, title, fields, result_title):
        panel, pane = card(title)
        pane.addWidget(self.settings_box("参数设置（第二阶段以后接入计算）", fields))
        pane.addWidget(button("执行分析", self.not_ready, True))
        layout.addWidget(panel)
        panel, pane = card(result_title)
        pane.addWidget(label("尚无分析结果。本模块将在后续开发阶段接入真实算法。", "subtitle"))
        canvas = PlotCanvas()
        canvas.setMinimumHeight(300)
        pane.addWidget(canvas)
        layout.addWidget(panel)

    def not_ready(self):
        self.inform("该分析功能将在后续开发阶段完成；目前没有生成任何模拟计算结果。")

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
