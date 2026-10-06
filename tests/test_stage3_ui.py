"""真实 Qt 异步计算、跨页结果清理与方法对比的集成测试。"""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QMessageBox
from app.main_window import MainWindow


def qt_app():
    return QApplication.instance() or QApplication([])


def until_completed(app, page, seconds=25):
    end = time.monotonic() + seconds
    while page.busy and time.monotonic() < end:
        app.processEvents()
        time.sleep(.02)
    app.processEvents()
    assert not page.busy, "后台分析线程超时"


def test_method_comparison_and_stale_results(tmp_path, monkeypatch):
    app = qt_app()
    msgs = []
    monkeypatch.setattr(QMessageBox, "warning", lambda _, title, info: msgs.append((title, info)))
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    rng = np.random.default_rng(14)
    frame = pd.DataFrame(rng.normal(size=(36, 4)), columns=["A", "B", "C", "D"])
    path = tmp_path / "reduction.csv"
    frame.to_csv(path, index=False)
    window = MainWindow()
    window.session.load(str(path))
    page = window.dimension_page

    assert page.variables.count() == 4
    assert page.method_combo.currentData() == "factor"
    page.dimension_combo.setCurrentIndex(1)  # three dimensions
    page.start_analysis()
    until_completed(app, page)
    assert not msgs, msgs
    assert page.current_result is not None
    assert page.current_result.dimensions == 3
    assert page.coordinate_model.rowCount() == 36
    assert page.loading_model.rowCount() == 4
    assert page.unique_model.rowCount() == 4
    assert page.canvas3d.axes.name == "3d"
    assert len(window.session.reduction_results) == 1

    page.method_combo.setCurrentIndex(1)  # MDS
    page.mds_n_init.setValue(1)
    page.mds_max_iter.setValue(70)
    page.start_analysis()
    until_completed(app, page)
    assert not msgs, msgs
    assert len(window.session.reduction_results) == 2
    assert page.loading_model.rowCount() == 0
    page.draw_comparison()
    assert len(page.comparison_canvas.figure.axes) == 2
    assert "局部邻域保持度" in page.compare_summary.text()

    page.method_combo.setCurrentIndex(2)  # t-SNE
    page.perplexity.setValue(8)
    page.tsne_max_iter.setValue(300)
    page.start_analysis()
    until_completed(app, page)
    assert not msgs, msgs
    assert len(window.session.reduction_results) == 3
    assert page.history_model.rowCount() == 3

    window.session.restore()
    assert len(window.session.reduction_results) == 0
    assert page.current_result is None
    assert page.coordinate_model.rowCount() == 0
    assert page.history_model.rowCount() == 0
    window.close()


def test_invalid_perplexity_does_not_add_fake_output(tmp_path, monkeypatch):
    app = qt_app()
    msgs = []
    monkeypatch.setattr(QMessageBox, "warning", lambda _, title, info: msgs.append(str(info)))
    rng = np.random.default_rng(101)
    frame = pd.DataFrame(rng.normal(size=(12, 3)))
    path = tmp_path / "small.csv"
    frame.to_csv(path, index=False)
    window = MainWindow()
    window.session.load(str(path))
    page = window.dimension_page
    page.method_combo.setCurrentIndex(2)
    page.perplexity.setMaximum(100)
    page.perplexity.setValue(30)  # greater than number of samples
    page.tsne_max_iter.setValue(300)
    page.start_analysis()
    until_completed(app, page)
    assert msgs and "perplexity" in msgs[-1]
    assert page.current_result is None
    assert not window.session.reduction_results
    window.close()


def test_data_revision_prevents_stale_background_results(tmp_path, monkeypatch):
    app = qt_app()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    rng = np.random.default_rng(17)
    frame = pd.DataFrame(rng.normal(size=(90, 4)))
    path = tmp_path / "revision.csv"
    frame.to_csv(path, index=False)
    window = MainWindow()
    window.session.load(str(path))
    page = window.dimension_page
    page.method_combo.setCurrentIndex(2)
    page.tsne_max_iter.setValue(300)
    page.perplexity.setValue(10)
    page.start_analysis()
    window.session.restore()
    until_completed(app, page)
    assert page.current_result is None
    assert len(window.session.reduction_results) == 0
    window.close()
