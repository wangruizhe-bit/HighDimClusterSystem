"""PCA 真实 GUI 绘图回归：覆盖用户点击所有表格/图形 Tab 的路径。"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "QtAgg")
os.environ.setdefault("QT_API", "pyside6")
os.environ["HIGHDIM_SELF_CHECK"] = "1"

import numpy as np
import pandas as pd


def test_pca_all_tabs_real_qt_draw(tmp_path):
    from PySide6.QtWidgets import QApplication
    from app.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    rng = np.random.default_rng(2026)
    frame = pd.DataFrame(
        rng.normal(size=(40, 5)),
        columns=["A", "B", "C", "D", "E"],
    )
    path = tmp_path / "pca_gui.csv"
    frame.to_csv(path, index=False)

    window = MainWindow()
    window.resize(1400, 900)
    window.show()
    app.processEvents()
    window.session.load(str(path))
    window.goto(3)
    app.processEvents()

    page = window.pca_page
    page.mode.setCurrentIndex(1)
    page.count.setValue(3)
    page.run_analysis()
    app.processEvents()

    assert page.result is not None
    assert page.result.chosen_components == 3

    canvas_by_tab = {
        page.VARIANCE_TAB: page.variance_canvas,
        page.SCATTER_2D_TAB: page.scatter2d_canvas,
        page.SCATTER_3D_TAB: page.scatter3d_canvas,
    }

    for index in range(page.tabs.count()):
        page.tabs.setCurrentIndex(index)
        QApplication.processEvents()
        canvas = canvas_by_tab.get(index)
        if canvas is not None:
            canvas.draw()
        QApplication.processEvents()
        pixmap = window.grab()
        assert not pixmap.isNull()

    # 模拟用户从表格回到三维，再回二维，再回三维。
    for index in (3, page.SCATTER_3D_TAB, page.SCATTER_2D_TAB, page.SCATTER_3D_TAB):
        page.tabs.setCurrentIndex(index)
        QApplication.processEvents()
        canvas = canvas_by_tab.get(index)
        if canvas is not None:
            canvas.draw()
        QApplication.processEvents()

    assert page.scatter3d_canvas.axes.name == "3d"
    window.close()
    QApplication.processEvents()
