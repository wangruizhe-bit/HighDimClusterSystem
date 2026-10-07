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
    "数据工作区概览 · 从数据进入降维与聚类分析",
    "文件导入 · 缺失处理 · 标准化 · 数据质量检查",
    "分布特征 · 相关结构 · 描述统计 · 探索性图形",
    "主成分谱 · 载荷解释 · 得分空间 · 方差压缩",
    "因子分析 · MDS · t-SNE · 低维嵌入对比",
    "K-means · 层次聚类 · DBSCAN · 类别结构发现",
    "聚类质量 · K 值搜索 · 指标对照 · 模型判断",
    "统一结果库 · CSV / Excel / HTML / 图像导出",
]

PAGE_CODES = ["HOME", "DATA", "EDA", "PCA", "EMBED", "CLUSTER", "SCORE", "EXPORT"]


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
        self.setFixedHeight(86)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(26, 12, 26, 12)
        layout.setSpacing(14)

        mark = QLabel("HD")
        mark.setObjectName("studioMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(48, 48)
        layout.addWidget(mark)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        brand.addWidget(studio_label("HIGH-DIMENSIONAL DATA STUDIO", "studioBrand"))
        brand.addWidget(studio_label("高维数据降维与聚类分析系统  ·  V1.0", "studioBrandSub"))
        layout.addLayout(brand)
        layout.addStretch(1)

        context = QFrame()
        context.setObjectName("datasetCapsule")
        ctx = QVBoxLayout(context)
        ctx.setContentsMargins(14, 6, 14, 6)
        ctx.setSpacing(0)
        ctx.addWidget(studio_label("CURRENT DATASET", "datasetEyebrow"))
        self.dataset_text = studio_label("尚未导入数据", "datasetValue")
        self.dataset_text.setMinimumWidth(250)
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
        self.setFixedHeight(66)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 8, 22, 8)
        layout.setSpacing(7)
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
        row.setContentsMargins(0, 0, 0, 12)
        row.setSpacing(14)
        code = QLabel(f"{index + 1:02d} / {PAGE_CODES[index]}")
        code.setObjectName("pageCode")
        code.setFixedWidth(90)
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
        box.setContentsMargins(18, 15, 18, 15)
        box.setSpacing(5)
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
        row.setContentsMargins(14, 11, 14, 11)
        row.setSpacing(12)
        badge = QLabel(f"{number:02d}")
        badge.setObjectName("pipelineNumber")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(36, 36)
        row.addWidget(badge)
        copy = QVBoxLayout()
        copy.setSpacing(1)
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
