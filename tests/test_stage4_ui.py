"""第四阶段：主窗口、聚类真实计算、K 值扫描、数据更新的无头 UI 测试。"""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QMessageBox
from sklearn.datasets import make_blobs
from app.main_window import MainWindow


def _app():
    return QApplication.instance() or QApplication([])


def _wait(app, page, limit=30):
    cutoff = time.monotonic() + limit
    while page.busy and time.monotonic() < cutoff:
        app.processEvents()
        time.sleep(.015)
    app.processEvents()
    assert page.busy is False, "聚类分析超时或线程没有释放"


def _window(tmp_path, app):
    x, _ = make_blobs(n_samples=60, n_features=4, centers=3,
                      cluster_std=.45, random_state=25)
    frame = pd.DataFrame(x, columns=["x", "y", "z", "w"])
    path = tmp_path / "cluster.csv"
    frame.to_csv(path, index=False)
    window = MainWindow()
    window.session.load(str(path))
    return window


def test_three_algorithms_and_evaluation_graph(tmp_path, monkeypatch):
    app = _app()
    messages = []
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda _, title, detail: messages.append((title, detail)))
    window = _window(tmp_path, app)
    cluster = window.cluster_page
    eval_page = window.evaluation_page
    assert window.stack.count() == 8
    assert cluster.variables.count() == 4
    assert eval_page.variables.count() == 4
    assert cluster.method_combo.currentData() == "kmeans"
    cluster.run_button.click()
    _wait(app, cluster)
    assert messages == []
    assert cluster.current_result is not None
    assert cluster.current_result.n_clusters == 3
    assert cluster.models["labels"].rowCount() == 60
    assert cluster.models["counts"].rowCount() == 3
    assert cluster.models["centers"].rowCount() == 3
    assert len(window.session.cluster_results) == 1
    assert eval_page.history_model.rowCount() == 1
    assert cluster.scatter3d.axes.name == "3d"

    cluster.method_combo.setCurrentIndex(1)
    cluster.run_button.click()
    _wait(app, cluster)
    assert messages == []
    assert cluster.current_result.linkage_matrix is not None
    assert len(cluster.tree_canvas.figure.axes) == 1
    assert cluster.models["centers"].rowCount() == 0
    assert eval_page.history_model.rowCount() == 2

    cluster.method_combo.setCurrentIndex(2)
    cluster.eps.setValue(0.6)
    cluster.min_samples.setValue(4)
    cluster.standardize.setChecked(True)
    cluster.run_button.click()
    _wait(app, cluster)
    assert messages == []
    assert cluster.current_result.algorithm == "dbscan"
    assert len(window.session.cluster_results) == 3
    assert eval_page.history_model.rowCount() == 3
    window.close()


def test_k_search_and_data_refresh(tmp_path, monkeypatch):
    app = _app()
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda _, title, detail: warnings.append((title, detail)))
    window = _window(tmp_path, app)
    ev = window.evaluation_page
    ev.k_min.setValue(2)
    ev.k_max.setValue(5)
    ev.search_button.click()
    _wait(app, ev)
    assert not warnings, warnings
    assert window.session.k_search_result is not None
    assert ev.search_model.rowCount() == 4
    assert len(ev.k_canvas.figure.axes) == 2
    assert window.session.k_search_result.suggested_k is not None
    window.session.restore()
    assert ev.search_model.rowCount() == 0
    assert window.session.k_search_result is None
    assert len(window.session.cluster_results) == 0
    window.close()


def test_invalid_selection_has_no_ghost_result(tmp_path, monkeypatch):
    app = _app()
    failures = []
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda _, title, detail: failures.append(str(detail)))
    window = _window(tmp_path, app)
    page = window.cluster_page
    page.method_combo.setCurrentIndex(2)
    page.eps.setValue(.001)
    page.min_samples.setValue(5)
    page.start_analysis()
    _wait(app, page)
    assert not failures
    assert page.current_result.n_clusters == 0
    assert page.current_result.metrics["silhouette"] is None
    assert page.models["metrics"].rowCount() == 5
    window.session.restore()
    assert page.current_result is None
    assert page.models["labels"].rowCount() == 0
    window.close()


def test_revision_guards_running_clustering(tmp_path, monkeypatch):
    app = _app()
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    window = _window(tmp_path, app)
    page = window.cluster_page
    page.method_combo.setCurrentIndex(1)
    page.start_analysis()
    window.session.restore()
    _wait(app, page)
    assert page.current_result is None
    assert len(window.session.cluster_results) == 0
    window.close()
