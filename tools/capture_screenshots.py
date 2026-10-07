"""生成真实 Qt 界面截图，用于 Windows 1080p / 125% 视觉验收。

不合成界面，不修改截图内容。100% 使用 1920×1080 逻辑窗口；
125% 用等效 1536×864 逻辑工作区，并输出为 1920×1080 图片。
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QImage, QPainter
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.styles import STYLE


def pump(app, condition=None, timeout=30.0):
    end = time.monotonic() + timeout
    settle = time.monotonic() + 0.30
    while time.monotonic() < end:
        app.processEvents()
        if condition is not None and condition():
            app.processEvents()
            return
        if condition is None and time.monotonic() >= settle:
            return
        time.sleep(0.015)
    raise RuntimeError("界面或示例计算未在时限内完成。")


def render_window(window, target: Path, scale: float):
    width = round(window.width() * scale)
    height = round(window.height() * scale)
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    try:
        painter.scale(scale, scale)
        window.render(painter)
    finally:
        painter.end()
    if not image.save(str(target), "PNG"):
        raise RuntimeError(f"无法保存界面截图：{target}")
    if target.stat().st_size < 15000:
        raise RuntimeError(f"界面截图异常，文件过小：{target}")


def snapshot(app, window, section, name, destination, scale):
    window.goto(section)
    pump(app)
    target = destination / name
    render_window(window, target, scale)
    print(f"Screenshot page={section}, bytes={target.stat().st_size}", flush=True)


def validate_key_geometry(window, app):
    """在截图前检查容易因字号放大产生的截断位置。"""
    app.processEvents()
    for button in window.nav_buttons:
        metrics = button.fontMetrics()
        lines = button.text().splitlines()
        max_width = max(metrics.horizontalAdvance(line) for line in lines)
        required_height = metrics.lineSpacing() * len(lines)
        if max_width > button.width() - 14:
            raise RuntimeError(f"顶部导航文字横向截断：{button.text()}")
        if required_height > button.height() - 8:
            raise RuntimeError(f"顶部导航文字纵向截断：{button.text()}")
    labels = [
        window.studio_header.dataset_text,
        window.data_lens.dataset_name,
        window.data_lens.dataset_shape,
        window.data_lens.mode_title,
        window.data_lens.mode_hint,
    ]
    for widget in labels:
        if widget.width() <= 20 or widget.height() <= 12:
            raise RuntimeError(f"关键文字控件尺寸异常：{widget.objectName()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, choices=(1.0, 1.25), default=1.0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    profile = "100" if args.scale == 1.0 else "125"
    output = root / "screenshots" / profile
    output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 11))
    app.setStyleSheet(STYLE)

    window = MainWindow()
    # 1920×1080 在 125% 缩放下的常见等效逻辑工作区约为 1536×864。
    if args.scale == 1.0:
        window.resize(1920, 1080)
    else:
        window.resize(1536, 864)
    window.show()
    pump(app)

    window.session.load(str(root / "data" / "sample_data.csv"))
    validate_key_geometry(window, app)
    snapshot(app, window, 0, "01_home.png", output, args.scale)
    snapshot(app, window, 1, "02_data.png", output, args.scale)

    window.calculate_stats("describe")
    window.draw_heatmap()
    snapshot(app, window, 2, "03_statistics.png", output, args.scale)

    window.pca_page.mode.setCurrentIndex(1)
    window.pca_page.count.setValue(3)
    window.pca_page.run_analysis()
    if window.pca_page.result is None:
        raise RuntimeError("PCA 示例计算失败。")
    window.pca_page.tabs.setCurrentIndex(4)
    snapshot(app, window, 3, "04_pca.png", output, args.scale)

    window.cluster_page.method_combo.setCurrentIndex(0)
    window.cluster_page.start_analysis()
    pump(app, lambda: not window.cluster_page.busy)
    if window.cluster_page.current_result is None:
        raise RuntimeError("K-means 示例计算失败。")
    window.cluster_page.tabs.setCurrentIndex(5)
    snapshot(app, window, 5, "05_clustering.png", output, args.scale)
    snapshot(app, window, 6, "06_evaluation.png", output, args.scale)
    snapshot(app, window, 7, "07_results.png", output, args.scale)

    window.close()
    print(f"Visual profile {profile}% passed: {len(list(output.glob('*.png')))} screenshots.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        message = traceback.format_exc().encode("ascii", "backslashreplace").decode("ascii")
        print(message, file=sys.stderr, flush=True)
        raise
