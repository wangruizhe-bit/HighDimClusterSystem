"""第二阶段 GUI 联调：PCA 表格与二维三维结果、重置、特征绘图。"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd


def test_pca_page_real_execution_and_reset(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    rng = np.random.default_rng(52)
    frame = pd.DataFrame(rng.normal(size=(25, 4)), columns=["A", "B", "C", "D"])
    path = tmp_path / "data.csv"
    frame.to_csv(path, index=False)
    window = MainWindow()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: (_ for _ in ()).throw(
        AssertionError("计算不应出现弹窗错误")
    ))
    window.session.load(str(path))
    page = window.pca_page
    assert page.variables.count() == 4
    page.mode.setCurrentIndex(1)
    page.count.setValue(3)
    page.run_analysis()
    assert page.result is not None
    assert window.session.latest_pca is page.result
    assert page.result.chosen_components == 3
    assert page.tables["eigen_table"].rowCount() == 4
    assert page.tables["loading_table"].rowCount() == 4
    assert page.tables["score_table"].rowCount() == 25
    assert page.scatter3d_canvas.axes.name == "3d"
    page.mode.setCurrentIndex(2)
    page.threshold.setValue(90)
    page.run_analysis()
    assert page.result.retained_variance >= 0.9
    window.session.restore()
    assert page.result is None
    assert window.session.latest_pca is None
    assert page.tables["score_table"].rowCount() == 0
    window.close()


def test_feature_plots_and_pca_single_component(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    data = pd.DataFrame({
        "x": [1., 2., 3., 4., 5., 6.],
        "y": [7., 4., 6., 9., 4., 8.],
        "z": [3., 7., 2., 8., 6., 5.],
    })
    path = tmp_path / "dataset.csv"
    data.to_csv(path, index=False)
    window = MainWindow()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: (_ for _ in ()).throw(
        AssertionError("分析未通过验证")
    ))
    window.session.load(str(path))
    window.plot_feature("hist")
    window.plot_feature("box")
    window.plot_feature("scatter")
    window.draw_heatmap()
    assert len(window.statistics_canvas.figure.axes) == 2
    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(1)
    window.pca_page.run_analysis()
    assert window.pca_page.result.chosen_components == 1
    assert window.pca_page.scatter3d_canvas.axes.name == "3d"
    window.close()
