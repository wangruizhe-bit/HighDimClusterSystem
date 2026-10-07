"""P0 回归：PCA 图形不得重新接回 QtAgg Tab Canvas。"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.plot_canvas import PlotCanvas, StaticPlotCanvas


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


def test_all_application_plot_widgets_use_static_agg():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert PlotCanvas is StaticPlotCanvas
    canvases = [
        window.statistics_canvas,
        window.pca_page.variance_canvas,
        window.pca_page.scatter2d_canvas,
        window.pca_page.scatter3d_canvas,
        window.dimension_page.canvas2d,
        window.dimension_page.canvas3d,
        window.dimension_page.comparison_canvas,
        window.cluster_page.scatter2d,
        window.cluster_page.scatter3d,
        window.cluster_page.tree_canvas,
        window.evaluation_page.score_canvas,
        window.evaluation_page.k_canvas,
    ]
    assert all(isinstance(canvas, StaticPlotCanvas) for canvas in canvases)
    window.close()
    app.processEvents()


def test_hidden_static_canvas_prerenders_image_cache():
    app = QApplication.instance() or QApplication([])
    canvas = StaticPlotCanvas(three_d=True)
    assert not canvas.isVisible()

    def build(ax):
        ax.scatter([0, 1], [0, 1], [0, 1])
        ax.set_title("hidden 3D")

    assert canvas.safe_update("hidden 3D", build, three_d=True, force_draw=False)
    assert canvas._image is not None
    assert not canvas._image.isNull()
    canvas.close()
    app.processEvents()
