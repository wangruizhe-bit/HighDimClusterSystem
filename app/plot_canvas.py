"""Matplotlib 绘图组件。

二维图使用 QtAgg 交互画布；三维图使用 Agg 离屏渲染后转为 Qt 静态图像，
避免 mplot3d 在 Windows Qt PaintEvent 中触发 native 崩溃。
"""
from __future__ import annotations

import os

from matplotlib import font_manager, rcParams
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # 冻结程序显式收集 3D toolkit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QLabel, QMessageBox, QSizePolicy, QVBoxLayout, QWidget,
)

from app.diagnostics import log_plot_exception


def _choose_chinese_matplotlib_font():
    """优先使用实际已安装的中文字体。"""
    installed = {face.name for face in font_manager.fontManager.ttflist}
    candidates = (
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans CJK JP",
        "Noto Sans SC", "WenQuanYi Zen Hei", "PingFang SC", "Arial Unicode MS",
    )
    chosen = next((name for name in candidates if name in installed), "DejaVu Sans")
    rcParams["font.sans-serif"] = [chosen, "DejaVu Sans"]
    rcParams["axes.unicode_minus"] = False
    rcParams["font.size"] = 11
    rcParams["axes.titlesize"] = 13
    rcParams["axes.labelsize"] = 12
    rcParams["xtick.labelsize"] = 11
    rcParams["ytick.labelsize"] = 11
    rcParams["legend.fontsize"] = 11


_choose_chinese_matplotlib_font()


def _report_draw_error(owner, title, exc):
    log_path = log_plot_exception(title, exc)
    if os.environ.get("HIGHDIM_SELF_CHECK") == "1":
        raise exc
    try:
        QMessageBox.critical(
            owner.window(),
            "图形绘制失败",
            f"{title}绘制失败：\n{exc}\n\n错误日志：{log_path}",
        )
    except Exception:
        pass
    return False


class QtPlotCanvas(FigureCanvasQTAgg):
    """保留的 QtAgg 画布实现，仅用于兼容性诊断，不用于正式界面。"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(6, 4))
        self.figure.subplots_adjust(left=.12, right=.95, bottom=.14, top=.90)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        if parent is not None:
            self.setParent(parent)
        self._last_plot_title = "图形"
        self.clear_message("等待分析结果", request_draw=False)

    def new_axes(self, three_d=None):
        if three_d:
            raise ValueError("二维 QtAgg 画布不能创建三维坐标轴。")
        self.figure.clear()
        self.figure.subplots_adjust(left=.12, right=.95, bottom=.14, top=.90)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_axis_on()
        return self.axes

    def clear_message(self, message, *, request_draw=True):
        ax = self.new_axes()
        ax.text(
            .5, .5, message, ha="center", va="center",
            transform=ax.transAxes, color="#75899e",
        )
        ax.set_axis_off()
        if request_draw and self.isVisible():
            self.draw_idle()

    def safe_update(self, title, callback, *, three_d=None, force_draw=True):
        self._last_plot_title = str(title)
        try:
            axes = self.new_axes(three_d=three_d)
            callback(axes)
            if force_draw:
                self.draw()
            elif self.isVisible():
                self.draw_idle()
            return True
        except Exception as exc:
            return _report_draw_error(self, self._last_plot_title, exc)

    def safe_figure_update(self, title, callback, *, force_draw=True):
        self._last_plot_title = str(title)
        try:
            self.figure.clear()
            self.figure.subplots_adjust(
                left=.10, right=.96, bottom=.14, top=.88, wspace=.28
            )
            callback(self.figure)
            if force_draw:
                self.draw()
            elif self.isVisible():
                self.draw_idle()
            return True
        except Exception as exc:
            return _report_draw_error(self, self._last_plot_title, exc)

    def draw(self, *args, **kwargs):
        """捕获普通 Python 绘制异常；native fatal crash 由 faulthandler 记录。"""
        try:
            return super().draw(*args, **kwargs)
        except Exception as exc:
            _report_draw_error(self, self._last_plot_title, exc)
            return None


class StaticPlotCanvas(QWidget):
    """Agg 离屏渲染画布。

    专门用于三维科研图。Matplotlib 完成 mplot3d 渲染后，将 RGBA 缓冲区复制为
    QImage/QPixmap 交给 QLabel 显示；Qt 不再直接 paint mplot3d Canvas。
    """

    def __init__(self, parent=None, *, three_d=False):
        super().__init__(parent)
        self._three_d = bool(three_d)
        self.figure = Figure(figsize=(6, 4))
        self.figure.subplots_adjust(left=.10, right=.96, bottom=.12, top=.90)
        self._agg = FigureCanvasAgg(self.figure)
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        self._last_plot_title = "三维图形"
        self._image = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.image_label.setMinimumSize(100, 100)
        layout.addWidget(self.image_label)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.draw)
        self.clear_message("等待分析结果", request_draw=False)

    def new_axes(self, three_d=None):
        if three_d is not None:
            self._three_d = bool(three_d)
        self.figure.clear()
        self.figure.subplots_adjust(left=.10, right=.96, bottom=.12, top=.90)
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        self.axes.set_axis_on()
        return self.axes

    def _update_pixmap(self):
        if self._image is None:
            self.image_label.clear()
            return
        pixmap = QPixmap.fromImage(self._image)
        target = self.image_label.size()
        if target.width() > 10 and target.height() > 10:
            pixmap = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.image_label.setPixmap(pixmap)

    def draw(self, *args, **kwargs):
        del args, kwargs
        try:
            # Render at actual physical pixels, including Windows display scale.
            # Ignored QLabel size hints prevent the pixmap inflating its own layout.
            ratio = self.devicePixelRatioF()
            width = max(100, self.image_label.width()) * ratio
            height = max(100, self.image_label.height()) * ratio
            self.figure.set_size_inches(width / self.figure.dpi, height / self.figure.dpi, forward=False)
            self._agg.draw()
            rgba = self._agg.buffer_rgba()
            width, height = self._agg.get_width_height()
            image = QImage(
                rgba, width, height, width * 4,
                QImage.Format.Format_RGBA8888,
            )
            # Matplotlib owns the renderer buffer; copy before it can be reused.
            self._image = image.copy()
            self._update_pixmap()
            return None
        except Exception as exc:
            _report_draw_error(self, self._last_plot_title, exc)
            return None

    def draw_idle(self):
        if self.isVisible():
            self.draw()

    def clear_message(self, message, *, request_draw=True):
        ax = self.new_axes()
        if self._three_d:
            ax.text2D(
                .5, .5, message, ha="center", va="center",
                transform=ax.transAxes, color="#75899e",
            )
        else:
            ax.text(
                .5, .5, message, ha="center", va="center",
                transform=ax.transAxes, color="#75899e",
            )
        ax.set_axis_off()
        if request_draw:
            self.draw()

    def safe_update(self, title, callback, *, three_d=None, force_draw=True):
        self._last_plot_title = str(title)
        try:
            axes = self.new_axes(three_d=three_d)
            callback(axes)
            # StaticPlotCanvas 使用纯 Agg 离屏渲染；即使控件当前隐藏也可以安全生成
            # QImage 缓存，用户首次切换到该 Tab 时不会出现空白或旧占位图。
            self.draw()
            return True
        except Exception as exc:
            return _report_draw_error(self, self._last_plot_title, exc)

    def safe_figure_update(self, title, callback, *, force_draw=True):
        self._last_plot_title = str(title)
        try:
            self.figure.clear()
            self.figure.subplots_adjust(
                left=.10, right=.96, bottom=.12, top=.90, wspace=.28
            )
            callback(self.figure)
            # 纯 Agg 渲染不依赖 Qt PaintEvent，隐藏状态下生成缓存是安全的。
            self.draw()
            return True
        except Exception as exc:
            return _report_draw_error(self, self._last_plot_title, exc)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()
        if self._image is not None:
            self._resize_timer.start(80)


# 正式界面统一使用离屏 Agg 渲染。保留 PlotCanvas 名称，避免页面层代码改动。
PlotCanvas = StaticPlotCanvas
