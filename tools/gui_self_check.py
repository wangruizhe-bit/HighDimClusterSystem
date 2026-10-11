"""打包前 GUI 绘图自检。

这些检查走真实 Qt Widget、Tab 切换、Matplotlib QtAgg draw() 与窗口 grab()。
用于源码和 PyInstaller EXE；失败时必须以非零退出码结束。
"""
from __future__ import annotations

import os
import time

from PySide6.QtWidgets import QApplication


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("GUI 自检必须在 QApplication 创建后运行。")
    return app


def _events(seconds: float = 0.08) -> None:
    app = _app()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()


def _wait(predicate, *, timeout: float, name: str) -> None:
    app = _app()
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if predicate():
            app.processEvents()
            return
        time.sleep(0.01)
    raise RuntimeError(f"GUI 自检超时：{name}")


def _grab(window, label: str) -> None:
    _events()
    pixmap = window.grab()
    if pixmap.isNull() or pixmap.width() < 200 or pixmap.height() < 200:
        raise RuntimeError(f"窗口 PaintEvent 自检失败：{label}")


def _show_tab(tab_widget, index: int, canvas, window, label: str) -> None:
    tab_widget.setCurrentIndex(index)
    _events()
    canvas.draw()
    _events()
    _grab(window, label)


def run_pca_gui_self_check(window, *, cycles: int = 20) -> dict:
    """重复真实用户路径：计算 PCA + 表格/2D/3D Tab 切换 + draw + grab。"""
    os.environ["HIGHDIM_SELF_CHECK"] = "1"
    app = _app()

    window.show()
    window.load_demo_data()
    window.goto(3)
    _events()

    page = window.pca_page
    page.mode.setCurrentIndex(1)  # 指定 k
    page.count.setValue(3)

    plot_by_tab = {
        page.VARIANCE_TAB: page.variance_canvas,
        page.SCATTER_2D_TAB: page.scatter2d_canvas,
        page.SCATTER_3D_TAB: page.scatter3d_canvas,
    }
    sequence = [
        0, 1, 2, 3,
        page.VARIANCE_TAB,
        page.SCATTER_2D_TAB,
        page.SCATTER_3D_TAB,
        3,
        page.SCATTER_3D_TAB,
    ]

    for cycle in range(cycles):
        page.run_button.click()
        app.processEvents()
        if page.result is None or page.result.chosen_components != 3:
            raise RuntimeError(f"PCA 第 {cycle + 1} 轮没有产生 k=3 结果。")
        for index in sequence:
            print(f"PCA_TRACE cycle={cycle + 1} tab={index} phase=before_set", flush=True)
            page.tabs.setCurrentIndex(index)
            print(f"PCA_TRACE cycle={cycle + 1} tab={index} phase=after_set", flush=True)
            app.processEvents()
            print(f"PCA_TRACE cycle={cycle + 1} tab={index} phase=after_events", flush=True)
            canvas = plot_by_tab.get(index)
            if canvas is not None:
                canvas.draw()
                print(f"PCA_TRACE cycle={cycle + 1} tab={index} phase=after_draw", flush=True)
            app.processEvents()
            _grab(window, f"PCA cycle {cycle + 1} tab {index}")
            print(f"PCA_TRACE cycle={cycle + 1} tab={index} phase=after_draw_events", flush=True)

    # 额外快速切换 20 轮，模拟用户快速点击标签。
    for cycle in range(20):
        for index in range(page.tabs.count()):
            print(f"PCA_RAPID cycle={cycle + 1} tab={index} phase=before_set", flush=True)
            page.tabs.setCurrentIndex(index)
            app.processEvents()
            print(f"PCA_RAPID cycle={cycle + 1} tab={index} phase=after_events", flush=True)
            canvas = plot_by_tab.get(index)
            if canvas is not None:
                canvas.draw()
                print(f"PCA_RAPID cycle={cycle + 1} tab={index} phase=after_draw", flush=True)
            _grab(window, f"PCA rapid {cycle + 1} tab {index}")
        _events(0.02)

    page.tabs.setCurrentIndex(page.SCATTER_3D_TAB)
    app.processEvents()
    page.scatter3d_canvas.draw()
    app.processEvents()

    return {
        "pca_cycles": cycles,
        "rapid_tab_cycles": 20,
        "backend": __import__("matplotlib").get_backend(),
    }


def _run_reduction(window, *, method_index: int, dimensions: int, label: str) -> None:
    page = window.dimension_page
    window.goto(4)
    page.method_combo.setCurrentIndex(method_index)
    page.dimension_combo.setCurrentIndex(1 if dimensions == 3 else 0)
    if page.method_combo.currentData() == "tsne":
        page.perplexity.setValue(15.0)
        page.tsne_max_iter.setValue(300)
    if page.method_combo.currentData() == "mds":
        page.mds_max_iter.setValue(120)
        page.mds_n_init.setValue(1)

    page.run_button.click()
    _wait(lambda: not page.busy, timeout=180, name=label)
    if page.current_result is None:
        raise RuntimeError(f"{label}没有产生结果。")
    if page.current_result.dimensions != dimensions:
        raise RuntimeError(f"{label}目标维度不正确。")

    _show_tab(page.result_tabs, 4, page.canvas2d, window, f"{label} 2D")
    if dimensions == 3:
        _show_tab(page.result_tabs, 5, page.canvas3d, window, f"{label} 3D")


def _run_cluster(window, *, method_index: int, label: str) -> None:
    page = window.cluster_page
    window.goto(5)
    page.method_combo.setCurrentIndex(method_index)
    if page.method_combo.currentData() == "dbscan":
        # 示例数据在标准化空间内使用较宽 eps，避免自检只得到全噪声。
        page.eps.setValue(1.5)
        page.min_samples.setValue(4)
    page.run_button.click()
    _wait(lambda: not page.busy, timeout=120, name=label)
    if page.current_result is None:
        raise RuntimeError(f"{label}没有产生结果。")

    _show_tab(page.tabs, 5, page.scatter2d, window, f"{label} 2D")
    if "PC3" in page.current_result.coords.columns:
        _show_tab(page.tabs, 6, page.scatter3d, window, f"{label} 3D")
    if page.current_result.linkage_matrix is not None:
        _show_tab(page.tabs, 7, page.tree_canvas, window, f"{label} tree")


def run_all_graphics_gui_self_check(window) -> dict:
    """逐个走共享 PlotCanvas 的全部主要绘图入口。"""
    os.environ["HIGHDIM_SELF_CHECK"] = "1"
    window.show()
    window.load_demo_data()
    _events()

    # 特征统计：热力图、直方图、箱线图、散点图。
    window.goto(2)
    for label, caption in [
        ("heatmap", "相关热力图"),
        ("histogram", "变量直方图"),
        ("boxplot", "多变量箱线图"),
        ("scatter", "双变量散点图"),
    ]:
        window.feature_action_buttons[caption].click()
        _events()
        window.statistics_canvas.draw()
        _events()
        _grab(window, f"feature plot {label}")

    # PCA 自检使用 3 轮；完整 20 轮由专用 --pca-gui-self-check 执行。
    pca_result = run_pca_gui_self_check(window, cycles=3)

    # FA / MDS / t-SNE：二维与三维。
    for method_index, method_name in enumerate(("FA", "MDS", "t-SNE")):
        _run_reduction(
            window, method_index=method_index, dimensions=2,
            label=f"{method_name} 2D",
        )
        _run_reduction(
            window, method_index=method_index, dimensions=3,
            label=f"{method_name} 3D",
        )

    # 降维方法对比图：选择 MDS-3D 与 t-SNE-3D，两者输入条件与目标维度一致。
    reduction = window.dimension_page
    if reduction.compare_a.count() >= 6:
        reduction.compare_a.setCurrentIndex(3)
        reduction.compare_b.setCurrentIndex(5)
        reduction.draw_comparison()
        if not reduction.comparison_ready:
            raise RuntimeError("同条件降维方法对比图没有成功绘制。")
        reduction.comparison_canvas.draw()
        _events()

    # 聚类：K-means、层次聚类、DBSCAN；层次聚类额外验证树状图。
    _run_cluster(window, method_index=0, label="K-means")
    _run_cluster(window, method_index=1, label="Hierarchical")
    _run_cluster(window, method_index=2, label="DBSCAN")

    # 模型评价页：聚类记录轮廓系数图 + K 值曲线。
    window.goto(6)
    evaluation = window.evaluation_page
    evaluation.refresh_cluster_comparison()
    evaluation.score_canvas.draw()
    _events()

    evaluation.k_min.setValue(2)
    evaluation.k_max.setValue(6)
    evaluation.search_button.click()
    _wait(lambda: not evaluation.busy, timeout=120, name="K search")
    if window.session.k_search_result is None:
        raise RuntimeError("K 值扫描没有产生结果。")
    evaluation.k_canvas.draw()
    _events()

    return {
        "feature_plots": 4,
        "pca": pca_result,
        "reduction_runs": 6,
        "cluster_runs": 3,
        "evaluation_plots": 2,
    }
