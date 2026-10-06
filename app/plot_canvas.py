"""复用 matplotlib Qt 画布。"""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, three_d=False):
        self.figure = Figure(figsize=(6,4), tight_layout=True)
        self.axes = self.figure.add_subplot(111, projection="3d" if three_d else None)
        super().__init__(self.figure)
        if parent is not None:
            self.setParent(parent)
        self.clear_message("等待分析结果")

    def clear_message(self, message):
        self.axes.clear()
        self.axes.text(0.5, 0.5, message, ha="center", va="center",
                       transform=self.axes.transAxes, color="#75899e")
        self.axes.set_axis_off()
        self.draw_idle()

    def new_axes(self):
        self.axes.clear()
        self.axes.set_axis_on()
        return self.axes
