"""旧 PCA/PlotCanvas 实现的复现脚本。

仅由兼容性诊断工作流使用；工作流会先把两个模块恢复到问题版本。
"""
from __future__ import annotations

import faulthandler
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("MPLBACKEND", "QtAgg")

faulthandler.enable(all_threads=True)

from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow


def events():
    app = QApplication.instance()
    for _ in range(6):
        app.processEvents()
        time.sleep(.01)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1500, 900)
    window.show()
    events()
    window.load_demo_data()
    window.goto(3)
    events()

    page = window.pca_page
    page.mode.setCurrentIndex(1)
    page.count.setValue(3)

    for cycle in range(20):
        page.run_analysis()
        events()
        for index in (0, 1, 2, 3, 4, 5, 6, 3, 6):
            page.tabs.setCurrentIndex(index)
            events()
            if index == 4:
                page.variance_canvas.draw()
            elif index == 5:
                page.scatter2d_canvas.draw()
            elif index == 6:
                page.scatter3d_canvas.draw()
            events()
            pix = window.grab()
            if pix.isNull():
                raise RuntimeError("legacy window grab failed")
        print(f"legacy PCA cycle {cycle + 1}/20 OK", flush=True)

    window.close()
    print("LEGACY_PCA_REPRO_COMPLETED_WITHOUT_CRASH", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
