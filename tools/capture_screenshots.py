"""生成软件真实界面截图，用于功能核查和操作说明（仅使用人工示例数据）。

Windows CI 在 offscreen Qt 平台运行。截图由实际 QWidget.grab() 产生，不是美化合成图。
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QImage, QPainter
from app.main_window import MainWindow
from app.styles import STYLE


def pump(app, condition=None, timeout=25.0):
    end = time.monotonic() + timeout
    if condition is None:
        # 给布局、字体与 Matplotlib 至少 250ms 完成一次真实事件循环。
        settle = time.monotonic() + 0.25
        while time.monotonic() < settle:
            app.processEvents()
            time.sleep(0.01)
        return
    while time.monotonic() < end:
        app.processEvents()
        if condition():
            app.processEvents()
            return
        time.sleep(0.02)
    raise RuntimeError("截图示例计算未在时限内完成。")


def snapshot(app, window, section, name, destination):
    window.goto(section)
    pump(app)
    target = destination / name
    # Windows Server 没有真实桌面。使用纯内存 QImage + QPainter 渲染 QWidget，
    # 避免 QPixmap 依赖原生窗口缓冲区导致 headless 环境退出。
    image = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    try:
        window.render(painter)
    finally:
        painter.end()
    result = image.save(str(target), "PNG")
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
    window.resize(1600, 900)
    window.show()
    pump(app)
    window.session.load(str(root / "data" / "sample_data.csv"))
    snapshot(app, window, 0, "01_home.png", output)
    snapshot(app, window, 1, "02_data.png", output)
    window.calculate_stats("describe")
    window.draw_heatmap()
    snapshot(app, window, 2, "03_statistics.png", output)

    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(3)
    window.pca_page.run_analysis()
    if window.pca_page.result is None:
        raise RuntimeError("PCA 实际运行失败。")
    window.pca_page.tabs.setCurrentIndex(4)
    snapshot(app, window, 3, "04_pca.png", output)

    window.cluster_page.method_combo.setCurrentIndex(0)
    window.cluster_page.start_analysis()
    pump(app, lambda: not window.cluster_page.busy)
    if window.cluster_page.current_result is None:
        raise RuntimeError("K-means 实际运行失败。")
    window.cluster_page.tabs.setCurrentIndex(5)
    snapshot(app, window, 5, "05_clustering.png", output)
    snapshot(app, window, 6, "06_evaluation.png", output)
    snapshot(app, window, 7, "07_results.png", output)
    window.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        # GitHub Windows 控制台编码并不总能输出中文异常文本。
        # 使用 ASCII backslash 转义保证诊断信息一定能进入 Actions 日志。
        message = traceback.format_exc().encode("ascii", "backslashreplace").decode("ascii")
        print(message, file=sys.stderr, flush=True)
        raise
