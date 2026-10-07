"""P0 回归：PCA 图形不得重新接回 QtAgg Tab Canvas。"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.plot_canvas import StaticPlotCanvas


def test_pca_plot_tabs_use_static_agg_widgets():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    page = window.pca_page
    assert isinstance(page.variance_canvas, StaticPlotCanvas)
    assert isinstance(page.scatter2d_canvas, StaticPlotCanvas)
    assert isinstance(page.scatter3d_canvas, StaticPlotCanvas)
    assert page.scatter3d_canvas.axes.name == "3d"
    window.close()
    app.processEvents()


def test_all_three_dimensional_views_use_static_agg_widgets():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert isinstance(window.pca_page.scatter3d_canvas, StaticPlotCanvas)
    assert isinstance(window.dimension_page.canvas3d, StaticPlotCanvas)
    assert isinstance(window.cluster_page.scatter3d, StaticPlotCanvas)
    window.close()
    app.processEvents()
