"""Data Studio 主界面组件。

包含品牌顶栏、横向模式导航、页面标题、首页统计组件和右侧数据概览。
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFormLayout, QComboBox,
    QSizePolicy, QVBoxLayout, QWidget,
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


class AnalysisLayout(QHBoxLayout):
    """Parameters remain accessible while results occupy the main canvas."""

    def __init__(self, owner):
        super().__init__(owner)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(16)
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(10)
        self.parameter_panel = QScrollArea()
        self.parameter_panel.setObjectName("parameterPanel")
        self.parameter_panel.setWidgetResizable(True)
        self.parameter_panel.setFixedWidth(280)
        self.parameter_panel.setMinimumHeight(400)
        self.parameter_panel.setFrameShape(QFrame.Shape.NoFrame)
        self.parameter_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        self.controls = QVBoxLayout(content)
        self.controls.setContentsMargins(0, 0, 0, 0)
        self.controls.setSpacing(12)
        self.parameter_panel.setWidget(content)
        self.sidebar_layout.addWidget(self.parameter_panel, 1)
        self.addWidget(sidebar)
        results = QWidget()
        self.results = QVBoxLayout(results)
        self.results.setContentsMargins(0, 0, 0, 0)
        self.results.setSpacing(12)
        self.addWidget(results, 1)

    def add_parameters(self, widget):
        for combo in widget.findChildren(QComboBox):
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(8)
        for form in widget.findChildren(QFormLayout):
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.controls.addWidget(widget)
        self.controls.addStretch(1)
        # Keep the actual execute action visible when long parameters scroll.
        primary = widget.findChild(QPushButton, "primary")
        if primary is not None:
            self.sidebar_layout.addWidget(primary)


def studio_label(text, name=None, wrap=True):
    widget = QLabel(str(text))
    widget.setWordWrap(bool(wrap))
    if name:
        widget.setObjectName(name)
    return widget


class ElidedLabel(QLabel):
    """Display a pixel-measured name while retaining the full text in a tooltip."""

    def __init__(self, text, name):
        super().__init__()
        self.setObjectName(name)
        self._full_text = ""
        self.setText(text)

    def setText(self, text):
        self._full_text = str(text)
        self.setToolTip(self._full_text)
        self._elide()

    def _elide(self):
        super().setText(self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight,
            max(0, self.contentsRect().width()),
        ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()


class StudioHeader(QFrame):
    """固定顶部品牌区；右侧只显示当前数据上下文和两个高频操作。"""

    def __init__(self, import_callback, result_callback, parent=None):
        super().__init__(parent)
        self.setObjectName("studioHeader")
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(12)

        mark = QLabel("高维")
        mark.setObjectName("studioMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(32, 32)
        layout.addWidget(mark)

        brand = QVBoxLayout()
        brand.setSpacing(3)
        self.brand_title = studio_label("高维数据降维与聚类分析系统", "studioBrand", wrap=False)
        self.brand_title.setMinimumWidth(300)
        brand.addWidget(self.brand_title)
        layout.addLayout(brand)
        layout.addStretch(1)

        context = QFrame()
        context.setObjectName("datasetCapsule")
        ctx = QHBoxLayout(context)
        ctx.setContentsMargins(12, 5, 12, 5)
        self.dataset_text = ElidedLabel("尚未导入数据", "datasetValue")
        self.dataset_text.setMinimumWidth(150)
        self.dataset_text.setMaximumWidth(330)
        self.dataset_text.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.dataset_text.setMinimumHeight(24)
        ctx.addWidget(self.dataset_text)
        self.dataset_context = context
        layout.addWidget(context, 1)

        self.import_button = QPushButton("＋  导入数据")
        self.import_button.setObjectName("headerPrimary")
        self.import_button.clicked.connect(import_callback)
        layout.addWidget(self.import_button)
        self.result_button = QPushButton("数据概览")
        self.result_button.setObjectName("headerGhost")
        self.result_button.setCheckable(True)
        self.result_button.clicked.connect(result_callback)
        layout.addWidget(self.result_button)

    def update_dataset(self, summary):
        if not summary or summary.get("rows", 0) == 0:
            self.dataset_text.setText("尚未导入数据")
            return
        name = summary.get("name") or "当前数据"
        self.dataset_text.setToolTip(str(name))
        self.dataset_text.setText(
            f"{name}  ·  {summary.get('rows', 0)} × {summary.get('columns', 0)}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep the full application title and actions readable at minimum width.
        compact = self.width() < 1400
        self.layout().setContentsMargins(16 if compact else 20, 8, 16 if compact else 20, 8)
        self.layout().setSpacing(10 if compact else 18)
        self.dataset_text.setMaximumWidth(180 if compact else 330)


class ModeStrip(QFrame):
    """横向模式导航组件。"""

    def __init__(self, page_names, change_callback, parent=None):
        super().__init__(parent)
        self.setObjectName("modeStrip")
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 2, 20, 2)
        layout.setSpacing(6)
        self.buttons = []
        for index, title in enumerate(page_names):
            button = QPushButton(title)
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
        row.setContentsMargins(0, 0, 0, 4)
        row.setSpacing(16)
        heading = studio_label(title, "pageTitle", wrap=False)
        heading.setToolTip(PAGE_HINTS[index])
        row.addWidget(heading, 1)


class MetricTile(QFrame):
    def __init__(self, caption, value="—", foot="", accent="violet", parent=None):
        super().__init__(parent)
        self.setObjectName("metricTile")
        self.setProperty("accent", accent)
        box = QVBoxLayout(self)
        box.setContentsMargins(16, 10, 16, 10)
        box.setSpacing(3)
        box.addWidget(studio_label(caption, "metricCaption"))
        self.value_label = studio_label(value, "metricValue")
        box.addWidget(self.value_label)
        self.setToolTip(foot)

    def set_value(self, value, foot=None):
        self.value_label.setText(str(value))
        if foot is not None:
            self.setToolTip(str(foot))


class PipelineStep(QFrame):
    def __init__(self, number, title, hint, jump, parent=None):
        super().__init__(parent)
        self.setObjectName("pipelineStep")
        self.setMinimumHeight(72)
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
    """右侧数据概览栏。内容不足时正常铺开，高 DPI 下可垂直滚动。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dataLensRail")
        self.setMinimumWidth(245)
        self.setMaximumWidth(285)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("lensScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)

        content = QWidget()
        content.setObjectName("lensContent")
        self.scroll.setWidget(content)
        box = QVBoxLayout(content)
        box.setContentsMargins(16, 14, 16, 14)
        box.setSpacing(8)

        self.title_label = studio_label("数据概览", "lensTitle", wrap=False)
        self.title_label.setMinimumHeight(30)
        box.addWidget(self.title_label)

        self.dataset_card = QFrame()
        self.dataset_card.setObjectName("lensDatasetCard")
        self.dataset_card.setMinimumHeight(88)
        card = QVBoxLayout(self.dataset_card)
        card.setContentsMargins(13, 11, 13, 11)
        card.setSpacing(4)
        self.dataset_caption = studio_label("当前数据集", "lensCardEyebrow", wrap=False)
        card.addWidget(self.dataset_caption)
        self.dataset_name = ElidedLabel("尚未导入", "lensDatasetName")
        self.dataset_name.setMinimumHeight(24)
        card.addWidget(self.dataset_name)
        self.dataset_shape = studio_label("等待数据", "lensDatasetShape", wrap=False)
        self.dataset_shape.setMinimumHeight(20)
        card.addWidget(self.dataset_shape)
        box.addWidget(self.dataset_card)

        self.quality_title = studio_label("数据质量", "lensSection", wrap=False)
        box.addWidget(self.quality_title)
        self.rows = self._metric("样本", "0")
        self.numeric = self._metric("数值变量", "0")
        self.missing = self._metric("缺失", "0")
        self.duplicates = self._metric("重复行", "0")
        for item in (self.rows, self.numeric, self.missing, self.duplicates):
            box.addWidget(item[0])

        self.records_title = studio_label("分析记录", "lensSection", wrap=False)
        box.addWidget(self.records_title)
        self.result_value = studio_label("0", "lensResultValue", wrap=False)
        self.result_caption = studio_label("尚无分析结果", "lensResultCaption", wrap=False)
        self.result_box = QFrame()
        self.result_box.setObjectName("lensResultCard")
        self.result_box.setMinimumHeight(72)
        result_layout = QVBoxLayout(self.result_box)
        result_layout.setContentsMargins(13, 10, 13, 10)
        result_layout.setSpacing(2)
        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.result_caption)
        box.addWidget(self.result_box)

        self.position_title = studio_label("当前位置", "lensSection", wrap=False)
        box.addWidget(self.position_title)
        self.mode_code = studio_label("01", "lensModeCode", wrap=False)
        self.mode_title = studio_label("分析首页", "lensModeTitle", wrap=False)
        self.mode_title.setMinimumHeight(24)
        box.addWidget(self.mode_code)
        box.addWidget(self.mode_title)

        box.addSpacing(12)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(270, hint.height())

    def _metric(self, title, value):
        frame = QFrame()
        frame.setObjectName("lensMetric")
        frame.setMinimumHeight(40)
        row = QHBoxLayout(frame)
        row.setContentsMargins(11, 7, 11, 7)
        row.setSpacing(8)
        caption = studio_label(title, "lensMetricCaption", wrap=False)
        number = studio_label(value, "lensMetricValue", wrap=False)
        number.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(caption, 1)
        row.addWidget(number)
        return frame, number

    def update_data(self, summary, result_count=0):
        summary = summary or {}
        imported = summary.get("rows", 0) > 0
        name = summary.get("name") if imported else "尚未导入"
        self.dataset_name.setToolTip(str(name or "当前数据"))
        self.dataset_name.setText(name or "当前数据")
        self.dataset_shape.setText(
            f"{summary.get('rows', 0)} 行 × {summary.get('columns', 0)} 列"
            if imported else "等待数据"
        )
        self.rows[1].setText(str(summary.get("rows", 0)))
        self.numeric[1].setText(str(summary.get("numeric", 0)))
        self.missing[1].setText(str(summary.get("missing", 0)))
        self.duplicates[1].setText(str(summary.get("duplicates", 0)))
        self.result_value.setText(str(result_count))
        self.result_caption.setText("当前数据版本" if result_count else "尚无分析结果")

    def update_mode(self, index, title):
        if not 0 <= index < len(PAGE_HINTS):
            return
        self.mode_code.setText(f"{index + 1:02d}")
        self.mode_title.setText(title)

