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

from PySide6.QtCore import QPoint, Qt
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
        window.render(painter, QPoint())
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
    ]
    for widget in labels:
        if widget.width() <= 20 or widget.height() <= 12:
            raise RuntimeError(f"关键文字控件尺寸异常：{widget.objectName()}")

    # 品牌名称不得因字号放大自动换行。
    if window.studio_header.brand_title.height() > window.studio_header.brand_title.fontMetrics().lineSpacing() * 1.6:
        raise RuntimeError("软件名称发生换行或高度异常。")

    # 右侧栏关键块必须按顺序排列，不能出现用户截图中的互相覆盖。
    rail = window.data_lens
    ordered = [
        rail.title_label, rail.dataset_card, rail.quality_title,
        rail.rows[0], rail.numeric[0], rail.missing[0], rail.duplicates[0],
        rail.records_title, rail.result_box, rail.position_title,
        rail.mode_code, rail.mode_title,
    ]
    previous_bottom = -1
    for widget in ordered:
        top = widget.geometry().top()
        bottom = widget.geometry().bottom()
        if top <= previous_bottom:
            raise RuntimeError(f"右侧数据栏控件重叠：{widget.objectName()}")
        previous_bottom = bottom


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

    window.load_demo_data()
    validate_key_geometry(window, app)

    # 视觉验收只检查布局和文字可读性，不在 headless 截图任务中执行
    # Matplotlib 的复杂结果绘制；算法与图形正确性由完整测试套件负责。
    pages = [
        (0, "01_home.png"),
        (1, "02_data.png"),
        (2, "03_statistics_layout.png"),
        (3, "04_pca_layout.png"),
        (4, "05_reduction_layout.png"),
        (5, "06_clustering_layout.png"),
        (6, "07_evaluation_layout.png"),
        (7, "08_results_layout.png"),
    ]
    for section, name in pages:
        snapshot(app, window, section, name, output, args.scale)

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
