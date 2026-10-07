"""可复用 Matplotlib Qt 画布，支持二维/三维轴与稳定重复绘图。"""
from __future__ import annotations

import os

from matplotlib import rcParams, font_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # PyInstaller 显式收集 3D toolkit
from PySide6.QtWidgets import QMessageBox

from app.diagnostics import log_plot_exception


def _choose_chinese_matplotlib_font():
    """优先使用实际已安装的字体，避免中文标题/坐标标签显示为方块。"""
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


class PlotCanvas(FigureCanvasQTAgg):
    """QtAgg FigureCanvas。

    不使用 Figure(tight_layout=True)，避免隐藏/显示与 3D Axes 重建时触发
    不稳定的自动布局路径。每次重建轴后使用固定边距。
    """

    def __init__(self, parent=None, three_d=False):
        self.figure = Figure(figsize=(6, 4))
        self.figure.subplots_adjust(left=.12, right=.95, bottom=.14, top=.90)
        self._three_d = bool(three_d)
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        super().__init__(self.figure)
        if parent is not None:
            self.setParent(parent)
        self._last_plot_title = "图形"
        self.clear_message("等待分析结果", request_draw=False)

    def new_axes(self, three_d=None):
        if three_d is not None:
            self._three_d = bool(three_d)
        self.figure.clear()
        self.figure.subplots_adjust(left=.12, right=.95, bottom=.14, top=.90)
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        self.axes.set_axis_on()
        return self.axes

    def clear_message(self, message, *, request_draw=True):
        ax = self.new_axes()
        if self._three_d:
            ax.text2D(.5, .5, message, ha="center", va="center",
                      transform=ax.transAxes, color="#75899e")
        else:
            ax.text(.5, .5, message, ha="center", va="center",
                    transform=ax.transAxes, color="#75899e")
        ax.set_axis_off()
        if request_draw and self.isVisible():
            self.draw_idle()

    def safe_update(self, title, callback, *, three_d=None, force_draw=True):
        """在 Python 层保护“重建轴 + 绘制 + Qt Canvas draw”完整过程。"""
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
            log_path = log_plot_exception(self._last_plot_title, exc)
            # 自动化/EXE 自检中必须把错误抛给调用者，不能被模态框吞掉。
            if os.environ.get("HIGHDIM_SELF_CHECK") == "1":
                raise
            try:
                QMessageBox.critical(
                    self.window(),
                    "图形绘制失败",
                    f"{self._last_plot_title}绘制失败：\n{exc}\n\n"
                    f"错误日志：{log_path}",
                )
            except Exception:
                pass
            return False

    def draw(self, *args, **kwargs):
        """捕获普通 Python 绘制异常；native fatal crash 由 faulthandler 记录。"""
        try:
            return super().draw(*args, **kwargs)
        except Exception as exc:
            log_path = log_plot_exception(self._last_plot_title, exc)
            if os.environ.get("HIGHDIM_SELF_CHECK") == "1":
                raise
            try:
                QMessageBox.critical(
                    self.window(),
                    "图形绘制失败",
                    f"{self._last_plot_title}绘制失败：\n{exc}\n\n"
                    f"错误日志：{log_path}",
                )
            except Exception:
                pass
            return None
