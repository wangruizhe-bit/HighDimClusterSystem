"""第五阶段 GUI：从真实计算结果导出文件、图像并清空记录。"""
import os
import time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from app.main_window import MainWindow


def app_instance():
    return QApplication.instance() or QApplication([])


def fixture_window(tmp_path):
    rng = np.random.default_rng(717)
    data = pd.DataFrame(rng.normal(size=(35, 4)), columns=list("ABCD"))
    data["group"] = ["test"] * 35
    path = tmp_path / "true_samples.csv"
    data.to_csv(path, index=False)
    window = MainWindow()
    window.session.load(str(path))
    return window, data


def until_done(app, page, timeout=30):
    deadline = time.monotonic() + timeout
    while page.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.012)
    app.processEvents()
    assert not page.busy


def test_results_page_csv_excel_report_and_png(tmp_path, monkeypatch):
    app = app_instance()
    window, data = fixture_window(tmp_path)
    page = window.results_page
    assert len(page.catalog) == 2
    assert page.figure_combo.count() == 0
    window.calculate_stats("describe")
    assert window.session.feature_result is not None
    assert len(page.catalog) == 3
    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(3)
    window.pca_page.run_analysis()
    assert window.session.latest_pca is not None
    assert any(item.key == "pca_scores" for item in page.catalog)
    assert page.figure_combo.count() >= 3

    output = tmp_path / "PCA_samples.csv"
    page.result_combo.setCurrentIndex(page.result_combo.findData("pca_scores"))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(output), "CSV"))
    page.save_csv()
    loaded = pd.read_csv(output)
    assert loaded.shape == (35, 4)
    assert "PC3" in loaded.columns

    workbook = tmp_path / "all_results.xlsx"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(workbook), "XLSX"))
    page.save_excel()
    sheets = pd.read_excel(workbook, sheet_name=None)
    assert len(sheets) == len(page.catalog)
    assert any("PC3" in frame.columns for frame in sheets.values())

    report = tmp_path / "summary.html"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(report), "HTML"))
    page.save_report()
    html = report.read_text(encoding="utf-8")
    assert "PCA" in html and "PC3" in html
    assert "样本数" in html

    picture = tmp_path / "projection.png"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(picture), "PNG"))
    page.figure_combo.setCurrentIndex(page.figure_combo.findText("PCA 二维得分图"))
    page.save_figure()
    assert picture.read_bytes().startswith(b"\x89PNG")
    window.close()


def test_result_refresh_and_clear_preserve_data(tmp_path, monkeypatch):
    app = app_instance()
    window, original = fixture_window(tmp_path)
    page = window.results_page
    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(2)
    window.pca_page.run_analysis()
    window.cluster_page.method_combo.setCurrentIndex(0)
    window.cluster_page.start_analysis()
    until_done(app, window.cluster_page)
    assert len(window.session.cluster_results) == 1
    assert any(item.key == "cluster_1_labels" for item in page.catalog)

    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *args: QMessageBox.StandardButton.Yes,
    )
    snapshot = window.session.data.get_data()
    page.clear_results()
    assert window.session.latest_pca is None
    assert not window.session.cluster_results
    # 清空的是分析快照，内存中的工作数据必须逐值完全不变。
    pd.testing.assert_frame_equal(window.session.data.get_data(), snapshot)
    # CSV 存取允许浮点数最后几位的正常舍入误差。
    pd.testing.assert_frame_equal(window.session.data.get_data(), original,
                                  rtol=1e-12, atol=1e-12)
    assert len(page.catalog) == 2
    assert page.figure_combo.count() == 0

    window.pca_page.run_analysis()
    assert window.session.latest_pca is not None
    window.session.restore()
    assert window.session.latest_pca is None
    assert len(page.catalog) == 2
    window.close()


def test_feature_plots_only_after_real_draw_and_no_import(tmp_path):
    app = app_instance()
    window = MainWindow()
    assert not window.results_page.catalog
    assert window.results_page.figure_combo.count() == 0
    window.close()

    win, _ = fixture_window(tmp_path)
    assert win.results_page.figure_combo.count() == 0
    win.plot_feature("hist")
    assert win.results_page.figure_combo.findText("特征统计图") >= 0
    win.session.restore()
    assert win.results_page.figure_combo.count() == 0
    win.close()
