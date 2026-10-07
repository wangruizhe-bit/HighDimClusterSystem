"""高维数据降维与聚类分析系统 V1.0：Windows 本地桌面程序入口。"""
from __future__ import annotations

import json
import os
import sys

# Matplotlib/Qt backend 必须在导入 MainWindow / FigureCanvasQTAgg 前确定。
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("MPLBACKEND", "QtAgg")

import matplotlib

# 用字面量显式选择 backend，既保证运行时一致，也让 PyInstaller 的
# Matplotlib hook 能在静态扫描时识别 QtAgg。无头测试明确设置 Agg 时保留 Agg。
if os.environ.get("MPLBACKEND", "").lower() == "agg":
    matplotlib.use("Agg", force=True)
else:
    matplotlib.use("QtAgg", force=True)

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.diagnostics import install_crash_handlers, set_page_provider
from app.main_window import MainWindow, PAGES
from app.styles import STYLE


def _page_name(window: MainWindow) -> str:
    index = window.stack.currentIndex()
    if 0 <= index < len(PAGES):
        return f"{index + 1:02d} {PAGES[index]}"
    return f"index={index}"


def _basic_self_check(window: MainWindow) -> dict:
    if window.stack.count() != 8:
        raise RuntimeError("软件功能页面数量不是 8。")
    for index in range(8):
        window.goto(index)
        if window.stack.currentIndex() != index:
            raise RuntimeError("功能页面无法正常切换。")
    window.load_demo_data()
    summary = window.session.data.summary()
    if summary.get("rows") != 90 or summary.get("numeric") != 8:
        raise RuntimeError("内置示例数据未正确打包或无法加载。")
    return {
        "pages": window.stack.count(),
        "rows": summary.get("rows"),
        "numeric": summary.get("numeric"),
        "backend": matplotlib.get_backend(),
    }


def main():
    crash_log, fatal_log = install_crash_handlers()

    app = QApplication(sys.argv)
    app.setApplicationName("高维数据降维与聚类分析系统 V1.0")
    app.setFont(QFont("Microsoft YaHei UI", 11))
    app.setStyleSheet(STYLE)

    window = MainWindow()
    set_page_provider(lambda: _page_name(window))

    try:
        if "--self-check" in sys.argv:
            os.environ["HIGHDIM_SELF_CHECK"] = "1"
            result = _basic_self_check(window)
            print(
                "HighDimClusterSystem V1.0: startup + demo-data self-check passed "
                + json.dumps(result, ensure_ascii=False),
                flush=True,
            )
            return 0

        if "--pca-gui-self-check" in sys.argv:
            os.environ["HIGHDIM_SELF_CHECK"] = "1"
            window.show()
            app.processEvents()
            from tools.gui_self_check import run_pca_gui_self_check
            result = run_pca_gui_self_check(window, cycles=20)
            print(
                "HighDimClusterSystem V1.0: PCA GUI self-check passed "
                + json.dumps(result, ensure_ascii=False),
                flush=True,
            )
            return 0

        if "--graphics-gui-self-check" in sys.argv:
            os.environ["HIGHDIM_SELF_CHECK"] = "1"
            window.show()
            app.processEvents()
            from tools.gui_self_check import run_all_graphics_gui_self_check
            result = run_all_graphics_gui_self_check(window)
            print(
                "HighDimClusterSystem V1.0: all graphics GUI self-check passed "
                + json.dumps(result, ensure_ascii=False),
                flush=True,
            )
            return 0

        window.show()
        return app.exec()
    finally:
        try:
            window.close()
        finally:
            print(f"Crash log: {crash_log}", flush=True)
            print(f"Fatal log: {fatal_log}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
