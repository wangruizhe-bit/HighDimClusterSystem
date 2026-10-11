"""Run real GUI analyses and exports; collect platform-specific evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
from PySide6 import __version__ as qt_binding_version
from PySide6.QtWidgets import QApplication

from app.fonts import chinese_font_family
from app.main_window import resource_path
from tools.gui_self_check import _events, _wait


def run_release_acceptance(window, output):
    """Never fabricate result objects: use the application's buttons and session."""
    started = time.perf_counter()
    app = QApplication.instance()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ["HIGHDIM_SELF_CHECK"] = "1"
    native = os.name == "nt" and app.platformName() == "windows"
    available = window.screen().availableGeometry()
    max_width, max_height = available.width() - 40, available.height() - 48
    if native:
        if max_width < window.minimumWidth() or max_height < window.minimumHeight():
            raise RuntimeError("Screen is too small for native acceptance; use at least 1920x1080 at 125%.")
        window.resize(min(1600, max_width), min(940, max_height))
        window.move(available.x() + 12, available.y() + 5)
    window.show()
    _events()
    source = resource_path("data", "demo_high_dimensional.csv")
    window.session.load(str(source))
    original = pd.read_csv(source)
    pd.testing.assert_frame_equal(window.session.data.current_data, original)
    captures = []
    analyses = []

    def capture(name, page, focus=None):
        window.goto(page)
        _events()
        scroll = window.stack.currentWidget()
        if focus is None:
            scroll.verticalScrollBar().setValue(0)
        else:
            scroll.ensureWidgetVisible(focus, 12, 12)
        _events()
        # Windows uses the real screen, including native titlebar. Offscreen
        # captures are explicitly identified in evidence.json, never Windows proof.
        if os.name == "nt" and app.platformName() == "windows":
            rect = window.frameGeometry()
            screen = window.screen()
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        else:
            pixmap = window.grab()
        target = output / f"{name}.png"
        if pixmap.isNull() or not pixmap.save(str(target), "PNG"):
            raise RuntimeError(f"Screenshot failed: {target}")
        captures.append(target.name)

    capture("01_import", 1)
    capture("02_home", 0)
    window.goto(2)
    window.feature_action_buttons["相关热力图"].click()
    window.statistics_canvas.draw()
    if not window.feature_figure_ready:
        raise RuntimeError("Statistics plot was not generated")
    capture("03_statistics", 2, window.statistics_canvas)

    window.goto(3)
    pca = window.pca_page
    pca.mode.setCurrentIndex(1)
    pca.count.setValue(3)
    pca.run_button.click()
    if pca.result is None or pca.result.chosen_components != 3:
        raise RuntimeError("PCA did not produce the requested components")
    capture("04_pca_parameters", 3)
    for tab, title, canvas in (
        (4, "05_pca_variance", pca.variance_canvas),
        (5, "06_pca_2d", pca.scatter2d_canvas),
        (6, "07_pca_3d", pca.scatter3d_canvas),
    ):
        pca.tabs.setCurrentIndex(tab)
        _events()
        canvas.draw()
        capture(title, 3, pca.tabs)
    analyses.append({"method": "pca", "retained_variance": pca.result.retained_variance})

    reduction = window.dimension_page
    for index, method in enumerate(("factor", "mds", "tsne")):
        window.goto(4)
        reduction.method_combo.setCurrentIndex(index)
        reduction.dimension_combo.setCurrentIndex(0)
        reduction.perplexity.setValue(15)
        reduction.tsne_max_iter.setValue(500)
        reduction.run_button.click()
        _wait(lambda: not reduction.busy, timeout=180, name=method)
        result = reduction.current_result
        if result is None or result.method != method:
            raise RuntimeError(f"{method} did not produce results")
        if not np.isfinite(result.coordinates.to_numpy()).all():
            raise RuntimeError(f"{method} produced nonfinite coordinates")
        analyses.append({"method": method, "metrics": result.metrics, "parameters": result.parameters})
        capture(f"08_{method}_parameters", 4)
        reduction.result_tabs.setCurrentIndex(3)
        capture(f"09_{method}_metrics", 4, reduction.result_tabs)
        reduction.result_tabs.setCurrentIndex(4)
        reduction.canvas2d.draw()
        capture(f"10_{method}_plot", 4, reduction.result_tabs)

    cluster = window.cluster_page
    for index, method in enumerate(("kmeans", "hierarchical", "dbscan")):
        window.goto(5)
        cluster.method_combo.setCurrentIndex(index)
        cluster.eps.setValue(1.5)
        cluster.min_samples.setValue(4)
        cluster.run_button.click()
        _wait(lambda: not cluster.busy, timeout=180, name=method)
        result = cluster.current_result
        if result is None or result.algorithm != method or len(result.labels) != len(original):
            raise RuntimeError(f"{method} did not produce sample labels")
        analyses.append({"method": method, "metrics": result.metrics,
                         "n_clusters": result.n_clusters, "n_noise": result.n_noise})
        capture(f"11_{method}_parameters", 5)
        cluster.tabs.setCurrentIndex(4)
        capture(f"12_{method}_metrics", 5, cluster.tabs)
        cluster.tabs.setCurrentIndex(5)
        cluster.scatter2d.draw()
        capture(f"13_{method}_plot", 5, cluster.tabs)
        if method == "hierarchical":
            cluster.tabs.setCurrentIndex(7)
            cluster.tree_canvas.draw()
            capture("14_hierarchical_tree", 5, cluster.tabs)

    window.goto(6)
    evaluation = window.evaluation_page
    evaluation.k_min.setValue(2)
    evaluation.k_max.setValue(6)
    evaluation.search_button.click()
    _wait(lambda: not evaluation.busy, timeout=180, name="K search")
    if window.session.k_search_result is None:
        raise RuntimeError("K search did not produce results")
    capture("15_evaluation", 6, evaluation.history_view)
    capture("16_k_search", 6, evaluation.k_canvas)

    window.goto(7)
    results = window.results_page
    results.refresh()
    if len(results.catalog) < 30 or not results.plots:
        raise RuntimeError("Results center is missing analysis tables/plots")

    def save_using_ui(callback, filename):
        path = output / filename
        chooser = results._choose
        try:
            results._choose = lambda *args: str(path)
            callback()
        finally:
            results._choose = chooser
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Export failed: {filename}")
        return path

    xlsx = save_using_ui(results.save_excel, "analysis.xlsx")
    workbook = pd.ExcelFile(xlsx)
    try:
        if len(workbook.sheet_names) != len(results.catalog):
            raise RuntimeError("Excel sheet count does not match actual results")
        pd.testing.assert_frame_equal(pd.read_excel(workbook, sheet_name=0), original)
    finally:
        workbook.close()
    capture("17_excel_export", 7, results.notice)
    csv = save_using_ui(results.save_csv, "working_data.csv")
    pd.testing.assert_frame_equal(pd.read_csv(csv), original)
    save_using_ui(results.save_report, "analysis.html")
    for index in range(len(results.plots)):
        results.figure_combo.setCurrentIndex(index)
        save_using_ui(results.save_figure, f"plot_{index + 1:02d}.png")
    save_using_ui(results.save_figure, "plot.svg")
    capture("18_image_export", 7, results.notice)
    for width, height in ((1600, 940), (1180, 760)):
        window.resize(min(width, max_width) if native else width,
                      min(height, max_height) if native else height)
        for page in (0, 3, 4, 5, 7):
            capture(f"layout_{window.width()}x{window.height()}_{page}", page)
    screen = window.screen()
    evidence = {
        "status": "passed", "platform": platform.platform(),
        "windows_build": platform.win32_ver(), "qt_platform": app.platformName(),
        "pyside6": qt_binding_version, "qt_font": chinese_font_family(),
        "device_pixel_ratio": window.devicePixelRatioF(),
        "logical_dpi": screen.logicalDotsPerInch(), "physical_dpi": screen.physicalDotsPerInch(),
        "native_windows_capture": os.name == "nt" and app.platformName() == "windows",
        "dataset": source.name, "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rows": len(original), "analyses": analyses, "screenshots": captures,
        "result_tables": len(results.catalog), "exported_plots": len(results.plots),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "visual_review": "pending: inspect actual screenshots for glyphs, truncation and overflow",
    }
    (output / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    return evidence
