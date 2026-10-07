"""第三软著专用 Data Studio 组件。

视觉与结构目标：
- 不采用 Pareto 系统的左侧白色导航；
- 不采用可靠性系统的顶部模块下拉控制台；
- 使用“深色 Studio Header + 横向 Mode Strip + 全宽分析画布”。
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)


PAGE_HINTS = [
    "查看当前数据状态并进入各分析模块",
    "导入数据，处理缺失值、重复样本和变量尺度",
    "计算描述统计、相关性并查看变量分布",
    "计算主成分、载荷、得分及方差贡献率",
    "执行因子分析、MDS 和 t-SNE 降维",
    "执行 K-means、层次聚类和 DBSCAN",
    "比较聚类指标并辅助选择 K 值",
    "浏览、导出并保存当前分析结果",
]


def studio_label(text, name=None):
    widget = QLabel(str(text))
    widget.setWordWrap(True)
    if name:
        widget.setObjectName(name)
    return widget


class StudioHeader(QFrame):
    """固定顶部品牌区；右侧只显示当前数据上下文和两个高频操作。"""

    def __init__(self, import_callback, result_callback, parent=None):
        super().__init__(parent)
        self.setObjectName("studioHeader")
        self.setFixedHeight(104)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 14, 28, 14)
        layout.setSpacing(18)

        mark = QLabel("高维")
        mark.setObjectName("studioMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(58, 58)
        layout.addWidget(mark)

        brand = QVBoxLayout()
        brand.setSpacing(3)
        self.brand_title = studio_label("高维数据降维与聚类分析系统", "studioBrand")
        self.brand_subtitle = studio_label("V1.0  ·  High-Dimensional Data Analysis", "studioBrandSub")
        brand.addWidget(self.brand_title)
        brand.addWidget(self.brand_subtitle)
        layout.addLayout(brand)
        layout.addStretch(1)

        context = QFrame()
        context.setObjectName("datasetCapsule")
        ctx = QVBoxLayout(context)
        ctx.setContentsMargins(16, 9, 16, 9)
        ctx.setSpacing(2)
        self.dataset_caption = studio_label("当前数据集", "datasetEyebrow")
        ctx.addWidget(self.dataset_caption)
        self.dataset_text = studio_label("尚未导入数据", "datasetValue")
        self.dataset_text.setMinimumWidth(280)
        ctx.addWidget(self.dataset_text)
        layout.addWidget(context)

        self.import_button = QPushButton("＋  导入数据")
        self.import_button.setObjectName("headerPrimary")
        self.import_button.clicked.connect(import_callback)
        layout.addWidget(self.import_button)
        self.result_button = QPushButton("结果中心  ↗")
        self.result_button.setObjectName("headerGhost")
        self.result_button.clicked.connect(result_callback)
        layout.addWidget(self.result_button)

    def update_dataset(self, summary):
        if not summary or summary.get("rows", 0) == 0:
            self.dataset_text.setText("尚未导入数据")
            return
        name = summary.get("name") or "当前数据"
        self.dataset_text.setText(
            f"{name}   ·   {summary.get('rows', 0)} × {summary.get('columns', 0)}"
        )


class ModeStrip(QFrame):
    """横向模式带，是第三个软著的主要导航，而非侧栏或下拉导航。"""

    def __init__(self, page_names, change_callback, parent=None):
        super().__init__(parent)
        self.setObjectName("modeStrip")
        self.setFixedHeight(82)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 9, 24, 9)
        layout.setSpacing(8)
        self.buttons = []
        for index, title in enumerate(page_names):
            button = QPushButton(f"{index + 1:02d}\n{title}")
            button.setObjectName("modeButton")
            button.setProperty("active", False)
            button.setCheckable(True)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.clicked.connect(lambda checked=False, target=index: change_callback(target))
            layout.addWidget(button, 1)
            self.buttons.append(button)

    def select(self, index):
        for number, button in enumerate(self.buttons):
            active = number == index
            button.setChecked(active)
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)


class PageBanner(QFrame):
    """每页的轻量标题栏，避免传统大卡片首页风格。"""

    def __init__(self, index, title, parent=None):
        super().__init__(parent)
        self.setObjectName("pageBanner")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 16)
        row.setSpacing(16)
        code = QLabel(f"{index + 1:02d}")
        code.setObjectName("pageCode")
        code.setFixedWidth(52)
        row.addWidget(code)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(studio_label(title, "pageTitle"))
        text.addWidget(studio_label(PAGE_HINTS[index], "pageHint"))
        row.addLayout(text, 1)


class MetricTile(QFrame):
    def __init__(self, caption, value="—", foot="", accent="violet", parent=None):
        super().__init__(parent)
        self.setObjectName("metricTile")
        self.setProperty("accent", accent)
        box = QVBoxLayout(self)
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(7)
        box.addWidget(studio_label(caption, "metricCaption"))
        self.value_label = studio_label(value, "metricValue")
        box.addWidget(self.value_label)
        self.foot_label = studio_label(foot, "metricFoot")
        box.addWidget(self.foot_label)

    def set_value(self, value, foot=None):
        self.value_label.setText(str(value))
        if foot is not None:
            self.foot_label.setText(str(foot))


class PipelineStep(QFrame):
    def __init__(self, number, title, hint, jump, parent=None):
        super().__init__(parent)
        self.setObjectName("pipelineStep")
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 13, 16, 13)
        row.setSpacing(14)
        badge = QLabel(f"{number:02d}")
        badge.setObjectName("pipelineNumber")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(40, 40)
        row.addWidget(badge)
        copy = QVBoxLayout()
        copy.setSpacing(3)
        copy.addWidget(studio_label(title, "pipelineTitle"))
        copy.addWidget(studio_label(hint, "pipelineHint"))
        row.addLayout(copy, 1)
        button = QPushButton("进入  →")
        button.setObjectName("pipelineJump")
        button.clicked.connect(jump)
        row.addWidget(button)


class MetricGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_grid = QGridLayout(self)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.setHorizontalSpacing(12)
        self.layout_grid.setVerticalSpacing(12)

    def add_tiles(self, tiles):
        for index, tile in enumerate(tiles):
            self.layout_grid.addWidget(tile, index // 4, index % 4)


class DataLensRail(QFrame):
    """第三软著的持久数据上下文栏。

    它不是导航栏：页面切换仍由顶部 Mode Strip 完成。
    右侧仅展示数据质量、分析进度和当前页面提示，从结构上区别于前两个软著。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dataLensRail")
        self.setFixedWidth(292)
        box = QVBoxLayout(self)
        box.setContentsMargins(20, 20, 20, 20)
        box.setSpacing(13)

        self.title_label = studio_label("数据概览", "lensTitle")
        box.addWidget(self.title_label)

        self.dataset_card = QFrame()
        self.dataset_card.setObjectName("lensDatasetCard")
        card = QVBoxLayout(self.dataset_card)
        card.setContentsMargins(15, 14, 15, 14)
        card.setSpacing(5)
        card.addWidget(studio_label("当前数据集", "lensCardEyebrow"))
        self.dataset_name = studio_label("尚未导入", "lensDatasetName")
        card.addWidget(self.dataset_name)
        self.dataset_shape = studio_label("0 × 0", "lensDatasetShape")
        card.addWidget(self.dataset_shape)
        box.addWidget(self.dataset_card)

        box.addWidget(studio_label("数据质量", "lensSection"))
        self.rows = self._metric("样本", "0")
        self.numeric = self._metric("数值变量", "0")
        self.missing = self._metric("缺失", "0")
        self.duplicates = self._metric("重复行", "0")
        for item in (self.rows, self.numeric, self.missing, self.duplicates):
            box.addWidget(item[0])

        box.addWidget(studio_label("分析记录", "lensSection"))
        self.result_value = studio_label("0", "lensResultValue")
        self.result_caption = studio_label("当前数据版本尚无分析结果", "lensResultCaption")
        result_box = QFrame()
        result_box.setObjectName("lensResultCard")
        result_layout = QVBoxLayout(result_box)
        result_layout.setContentsMargins(15, 13, 15, 13)
        result_layout.setSpacing(4)
        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.result_caption)
        box.addWidget(result_box)

        box.addWidget(studio_label("当前位置", "lensSection"))
        self.mode_code = studio_label("01", "lensModeCode")
        self.mode_title = studio_label("分析首页", "lensModeTitle")
        self.mode_hint = studio_label(PAGE_HINTS[0], "lensModeHint")
        box.addWidget(self.mode_code)
        box.addWidget(self.mode_title)
        box.addWidget(self.mode_hint)
        box.addStretch(1)

        offline = QFrame()
        offline.setObjectName("lensOffline")
        offline_layout = QVBoxLayout(offline)
        offline_layout.setContentsMargins(14, 12, 14, 12)
        offline_layout.setSpacing(3)
        offline_layout.addWidget(studio_label("本地计算", "lensOfflineTitle"))
        offline_layout.addWidget(studio_label("数据仅在本机处理，不上传。", "lensOfflineHint"))
        box.addWidget(offline)

    def _metric(self, title, value):
        frame = QFrame()
        frame.setObjectName("lensMetric")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(8)
        caption = studio_label(title, "lensMetricCaption")
        number = studio_label(value, "lensMetricValue")
        number.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(caption, 1)
        row.addWidget(number)
        return frame, number

    def update_data(self, summary, result_count=0):
        summary = summary or {}
        imported = summary.get("rows", 0) > 0
        self.dataset_name.setText(summary.get("name") if imported else "尚未导入")
        self.dataset_shape.setText(
            f"{summary.get('rows', 0)} × {summary.get('columns', 0)}"
            if imported else "等待数据"
        )
        self.rows[1].setText(str(summary.get("rows", 0)))
        self.numeric[1].setText(str(summary.get("numeric", 0)))
        self.missing[1].setText(str(summary.get("missing", 0)))
        self.duplicates[1].setText(str(summary.get("duplicates", 0)))
        self.result_value.setText(str(result_count))
        self.result_caption.setText(
            "当前数据版本的分析结果"
            if result_count else "尚无分析结果"
        )

    def update_mode(self, index, title):
        if not 0 <= index < len(PAGE_HINTS):
            return
        self.mode_code.setText(f"{index + 1:02d}")
        self.mode_title.setText(title)
        self.mode_hint.setText(PAGE_HINTS[index])
