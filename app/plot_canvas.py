"""可复用 Matplotlib 画布，支持二维、三维轴与重复绘图清理。"""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


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
