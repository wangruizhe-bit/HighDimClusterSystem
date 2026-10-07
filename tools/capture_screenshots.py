"""真实 Qt 界面截图与布局验收。

覆盖 1920×1080 100%、1920×1080 125% 等效逻辑尺寸、
默认 1600×940 和最小 1180×760。截图只用于界面布局验收，
算法与图表数值正确性由自动化测试套件验证。
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


PROFILES = {
    "1080_100": (1920, 1080, 1.0),
    "1080_125": (1536, 864, 1.25),
    "default": (1600, 940, 1.0),
    "minimum": (1180, 760, 1.0),
}


def pump(app, timeout=1.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


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


def snapshot(app, window, name, destination, scale):
    pump(app, 0.25)
    target = destination / name
    render_window(window, target, scale)
    print(f"Screenshot {name}: {target.stat().st_size} bytes", flush=True)


def validate_shell(window, app):
    app.processEvents()

    for button in window.nav_buttons:
        metrics = button.fontMetrics()
        lines = button.text().splitlines()
        max_width = max(metrics.horizontalAdvance(line) for line in lines)
        required_height = metrics.lineSpacing() * len(lines)
        if max_width > button.width() - 14:
            raise RuntimeError(f"顶部导航横向截断：{button.text()}")
        if required_height > button.height() - 8:
            raise RuntimeError(f"顶部导航纵向截断：{button.text()}")

    brand = window.studio_header.brand_title
    if brand.wordWrap():
        raise RuntimeError("软件名称不允许自动换行。")
    if brand.fontMetrics().horizontalAdvance(brand.text()) > brand.width() - 4:
        raise RuntimeError("软件名称可用宽度不足。")

    rail = window.data_lens
    if not 245 <= rail.width() <= 275:
        raise RuntimeError(f"右侧数据概览宽度异常：{rail.width()}px")

    labels = [
        window.studio_header.dataset_text,
        rail.dataset_name,
        rail.dataset_shape,
        rail.mode_title,
    ]
    for widget in labels:
        if widget.width() <= 20 or widget.height() <= 12:
            raise RuntimeError(f"关键文字控件尺寸异常：{widget.objectName()}")


def validate_home_bottom(window, app):
    window.goto(0)
    app.processEvents()
    scroll = window.stack.widget(0)
    bar = scroll.verticalScrollBar()
    bar.setValue(bar.maximum())
    pump(app, 0.25)

    if bar.value() != bar.maximum():
        raise RuntimeError("首页滚动条无法到达最大值。")

    last = window.home_capability_rows[-1]
    bottom = last.mapTo(scroll.viewport(), QPoint(0, last.height())).y()
    remaining = scroll.viewport().height() - bottom
    if remaining < 20:
        raise RuntimeError(
            f"首页最后一项滚到底后仅剩 {remaining}px 空白，小于 20px。"
        )

    pipeline_last = window.home_pipeline_steps[-1]
    pipeline_bottom = pipeline_last.mapTo(
        scroll.viewport(), QPoint(0, pipeline_last.height())
    ).y()
    if pipeline_bottom > scroll.viewport().height() - 20:
        raise RuntimeError("首页“评价与交付”未完整露出。")

    return remaining


def validate_default_ratio(window):
    rail = window.data_lens.width()
    workspace = window.stack.width()
    ratio = workspace / (workspace + rail)
    if not 0.80 <= ratio <= 0.84:
        raise RuntimeError(
            f"默认窗口主工作区占比 {ratio:.3f}，未落在 80%–84%。"
        )
    body_total = window.home_pipeline.width() + window.home_capability.width()
    pipeline_ratio = window.home_pipeline.width() / body_total
    if not 0.64 <= pipeline_ratio <= 0.69:
        raise RuntimeError(
            f"首页分析路径占比 {pipeline_ratio:.3f}，未达到约 2:1。"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=tuple(PROFILES), default="1080_100")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    width, height, scale = PROFILES[args.profile]
    output = root / "screenshots" / args.profile
    output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 11))
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.resize(width, height)
    window.show()
    pump(app, 0.4)
    window.load_demo_data()
    window.goto(0)
    pump(app, 0.4)

    validate_shell(window, app)
    if args.profile == "default":
        validate_default_ratio(window)

    home_scroll = window.stack.widget(0)
    home_scroll.verticalScrollBar().setValue(0)
    snapshot(app, window, "01_home_top.png", output, scale)

    bottom_space = validate_home_bottom(window, app)
    snapshot(app, window, "02_home_bottom.png", output, scale)

    # 100%/125% 下额外检查参数较多的功能页。
    if args.profile in {"1080_100", "1080_125"}:
        for page, filename in [
            (3, "03_pca.png"),
            (4, "04_reduction.png"),
            (5, "05_clustering.png"),
        ]:
            window.goto(page)
            scroll = window.stack.currentWidget()
            scroll.verticalScrollBar().setValue(0)
            snapshot(app, window, filename, output, scale)

    window.close()
    print(
        f"Visual profile {args.profile} passed; "
        f"home bottom whitespace={bottom_space}px.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        message = traceback.format_exc().encode(
            "ascii", "backslashreplace"
        ).decode("ascii")
        print(message, file=sys.stderr, flush=True)
        raise
