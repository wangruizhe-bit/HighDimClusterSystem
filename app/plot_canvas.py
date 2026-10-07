"""可复用 Matplotlib 画布，支持二维、三维轴与重复绘图清理。"""
from matplotlib import rcParams, font_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


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
    def __init__(self, parent=None, three_d=False):
        self.figure = Figure(figsize=(6, 4), tight_layout=True)
        self._three_d = bool(three_d)
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        super().__init__(self.figure)
        if parent is not None:
            self.setParent(parent)
        self.clear_message("等待分析结果")

    def new_axes(self, three_d=None):
        if three_d is not None:
            self._three_d = bool(three_d)
        # 新建画布会移除历史 colorbar / twin axes，避免重复绘图层叠。
        self.figure.clear()
        self.axes = self.figure.add_subplot(
            111, projection="3d" if self._three_d else None
        )
        self.axes.set_axis_on()
        return self.axes

    def clear_message(self, message):
        ax = self.new_axes()
        if self._three_d:
            ax.text2D(.5, .5, message, ha="center", va="center",
                      transform=ax.transAxes, color="#75899e")
        else:
            ax.text(.5, .5, message, ha="center", va="center",
                    transform=ax.transAxes, color="#75899e")
        ax.set_axis_off()
        self.draw_idle()
