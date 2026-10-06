"""八页中文界面：数据处理真实执行，后续算法入口明确标识未实现。"""
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
from app.session import Session
from app.table_model import FrameTableModel

PAGES = [
    "分析首页", "数据管理与预处理", "特征统计分析", "主成分分析（PCA）",
    "多方法降维", "聚类分析", "聚类评价与模型对比", "结果中心",
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
        lay.addWidget(label(title, "heading" if False else "subtitle"))
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
        self.resize(1440, 900)
        self.setMinimumSize(1020, 680)
        self.session = Session(self)
        self.views = []
        self.refreshers = []
        self.setStatusBar(self.statusBar())
        root = QWidget()
        root.setObjectName("workspace")
        self.setCentralWidget(root)
        horizontal = QHBoxLayout(root)
        horizontal.setContentsMargins(0, 0, 0, 0)
        horizontal.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(16, 24, 16, 18)
        nav.setSpacing(7)
        nav.addWidget(label("◈  数理数据工作台"))
        nav.addWidget(label("HighDimCluster · V1.0"))
        nav.addSpacing(24)
        self.nav_buttons = []
        self.stack = QStackedWidget()
        for index, name in enumerate(PAGES):
            b = QPushButton(name)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(partial(self.goto, index))
            nav.addWidget(b)
            self.nav_buttons.append(b)
        nav.addStretch(1)
        nav.addWidget(label("本地分析 · 无需联网"))
        horizontal.addWidget(sidebar)
        horizontal.addWidget(self.stack, 1)

        makers = [
            self.make_home, self.make_data_page, self.make_feature_page,
            self.make_pca_page, self.make_dimension_page, self.make_cluster_page,
            self.make_evaluation_page, self.make_results_page
        ]
        for name, maker in zip(PAGES, makers):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            page = QWidget()
            page.setObjectName("workspace")
            lay = QVBoxLayout(page)
            lay.setContentsMargins(28, 24, 28, 24)
            lay.setSpacing(16)
            lay.addWidget(label(name, "heading"))
            maker(lay)
            lay.addStretch(1)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)
        self.session.data_changed.connect(self.refresh_all)
        self.goto(0)
        self.refresh_all()

    def goto(self, number):
        self.stack.setCurrentIndex(number)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == number)
        self.statusBar().showMessage("当前页面：" + PAGES[number], 4000)

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
        panel, pane = card()
        pane.addWidget(label("高维数据降维与聚类分析系统", "heading"))
        pane.addWidget(label("面向高维数值数据的预处理、统计分析、降维与聚类工作台。", "subtitle"))
        shortcuts = QHBoxLayout()
        shortcuts.addWidget(button("导入数据", lambda: self.goto(1), True))
        shortcuts.addWidget(button("特征分析", lambda: self.goto(2)))
        shortcuts.addWidget(button("主成分分析", lambda: self.goto(3)))
        shortcuts.addWidget(button("聚类分析", lambda: self.goto(5)))
        shortcuts.addStretch()
        pane.addLayout(shortcuts)
        layout.addWidget(panel)
        panel, pane = card("当前数据集")
        self.home_summary = label("尚未导入数据")
        pane.addWidget(self.home_summary)
        layout.addWidget(panel)
        panel, pane = card("工作流程")
        pane.addWidget(label(
            "数据导入 → 数据清洗与标准化 → 特征统计 → 主成分分析 → 多方法降维 → 聚类分析 → "
            "模型评价 → 结果导出\n\n当前第一阶段：数据管理、预处理和基础统计可真实运行；"
            "高级降维与聚类算法将在后续阶段实现。"))
        layout.addWidget(panel)

        def update():
            s = self.session.data.summary()
            self.home_summary.setText(
                f"数据集：{s['name']}\n样本：{s['rows']}    特征：{s['columns']}    "
                f"数值变量：{s['numeric']}    非数值变量：{s['non_numeric']}\n"
                f"缺失单元格：{s['missing']}    重复样本：{s['duplicates']}")
        self.refreshers.append(update)

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
        actions = QHBoxLayout()
        actions.addWidget(button("描述性统计", lambda: self.calculate_stats("describe"), True))
        actions.addWidget(button("Pearson 相关性", lambda: self.calculate_stats("corr")))
        actions.addWidget(button("协方差矩阵", lambda: self.calculate_stats("cov")))
        actions.addWidget(button("相关热力图", self.draw_heatmap))
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
        self.placeholder(layout, "主成分分析 · PCA", [
            ("变量选择", "choice", ["自动选择数值变量"]),
            ("是否标准化", "check", True),
            ("主成分数量方式", "choice", ["自动确定", "指定数量", "按累计贡献率"]),
            ("主成分数量", "int", 2),
            ("目标累计贡献率（%）", "float", 85),
        ], "特征值、贡献率、载荷矩阵、主成分得分与二维/三维结果")

    def make_dimension_page(self, layout):
        self.placeholder(layout, "因子分析 / MDS / t-SNE", [
            ("方法", "choice", ["因子分析", "MDS 多维尺度分析", "t-SNE"]),
            ("目标维度", "choice", ["2", "3"]),
            ("因子数量", "int", 2),
            ("距离度量", "choice", ["euclidean", "manhattan"]),
            ("perplexity", "float", 30),
            ("learning rate", "float", 200),
            ("最大迭代次数", "int", 1000),
            ("随机种子", "int", 42),
        ], "降维结果与方法对比")

    def make_cluster_page(self, layout):
        self.placeholder(layout, "K-means / 层次聚类 / DBSCAN", [
            ("算法", "choice", ["K-means", "层次聚类", "DBSCAN"]),
            ("聚类数 K", "int", 3),
            ("最大迭代次数", "int", 300),
            ("随机种子", "int", 42),
            ("linkage", "choice", ["ward", "complete", "average", "single"]),
            ("距离度量", "choice", ["euclidean", "manhattan"]),
            ("eps", "float", 0.5),
            ("min_samples", "int", 5),
        ], "类别标签、类别统计、二维/三维聚类图与树状图")

    def make_evaluation_page(self, layout):
        self.placeholder(layout, "聚类质量评价与模型对比", [
            ("评价指标", "choice", ["Silhouette", "Calinski-Harabasz", "Davies-Bouldin"]),
            ("K 值辅助选择", "choice", ["肘部法", "轮廓系数法"]),
            ("最小 K", "int", 2),
            ("最大 K", "int", 10),
        ], "待实现：多模型评分、运行时间、肘部曲线与轮廓系数曲线")

    def make_results_page(self, layout):
        panel, pane = card("结果中心")
        pane.addWidget(label("真实分析结果记录和报表将在第五阶段统一接入。"
                            "基础统计结果目前可在“特征统计分析”页面查看。"))
        action = QHBoxLayout()
        for title in ["导出数据", "导出结果表", "保存图像", "清空结果"]:
            action.addWidget(button(title, self.not_ready))
        pane.addLayout(action)
        layout.addWidget(panel)

    def refresh_all(self):
        for refresh in self.refreshers:
            refresh()
