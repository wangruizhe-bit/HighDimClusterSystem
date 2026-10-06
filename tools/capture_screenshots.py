"""生成软件真实界面截图，用于功能核查和操作说明（仅使用人工示例数据）。

Windows CI 在 offscreen Qt 平台运行。截图由实际 QWidget.grab() 产生，不是美化合成图。
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.main_window import MainWindow
from app.styles import STYLE


def pump(app, condition=None, timeout=25.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if condition is None or condition():
            break
        time.sleep(0.02)
    app.processEvents()
    if condition is not None and not condition():
        raise RuntimeError("截图示例计算未在时限内完成。")


def snapshot(app, window, section, name, destination):
    window.goto(section)
    pump(app)
    target = destination / name
    result = window.grab().save(str(target), "PNG")
    if not result or target.stat().st_size < 10000:
        raise RuntimeError(f"截图无效或文件过小：{target}")
    print(f'Screenshot saved: page {section}, size={target.stat().st_size} bytes')


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "screenshots"
    output.mkdir(exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.resize(1440, 900)
    window.show()
    pump(app)
    window.session.load(str(root / "data" / "sample_data.csv"))
    snapshot(app, window, 0, "01_分析首页.png", output)
    snapshot(app, window, 1, "02_数据管理.png", output)
    window.calculate_stats("describe")
    window.draw_heatmap()
    snapshot(app, window, 2, "03_特征统计.png", output)

    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(3)
    window.pca_page.run_analysis()
    if window.pca_page.result is None:
        raise RuntimeError("PCA 实际运行失败。")
    window.pca_page.tabs.setCurrentIndex(4)
    snapshot(app, window, 3, "04_PCA可视化.png", output)

    window.cluster_page.method_combo.setCurrentIndex(0)
    window.cluster_page.start_analysis()
    pump(app, lambda: not window.cluster_page.busy)
    if window.cluster_page.current_result is None:
        raise RuntimeError("K-means 实际运行失败。")
    window.cluster_page.tabs.setCurrentIndex(5)
    snapshot(app, window, 5, "05_聚类可视化.png", output)
    snapshot(app, window, 6, "06_聚类评价.png", output)
    snapshot(app, window, 7, "07_结果中心.png", output)
    window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
