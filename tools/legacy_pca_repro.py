"""旧版 PCA/QtAgg 实现的独立复现脚本。

兼容性工作流会在问题版本的完整源码树中运行本脚本，
避免新旧模块混用导致 ImportError。
"""
from __future__ import annotations

import faulthandler
import os
from pathlib import Path
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("MPLBACKEND", "QtAgg")

faulthandler.enable(all_threads=True)

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow


def events(rounds=6):
    app = QApplication.instance()
    for _ in range(rounds):
        app.processEvents()
        time.sleep(.01)


def make_data() -> Path:
    rng = np.random.default_rng(2026)
    frame = pd.DataFrame(
        rng.normal(size=(90, 8)),
        columns=[f"Feature_{i}" for i in range(1, 9)],
    )
    path = Path(tempfile.gettempdir()) / "highdim_legacy_pca_repro.csv"
    frame.to_csv(path, index=False)
    return path


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1500, 900)
    window.show()
    events()

    window.session.load(str(make_data()))
    window.goto(3)
    events()

    page = window.pca_page
    page.mode.setCurrentIndex(1)
    page.count.setValue(3)

    plot_tabs = {
        4: page.variance_canvas,
        5: page.scatter2d_canvas,
        6: page.scatter3d_canvas,
    }
    sequence = (0, 1, 2, 3, 4, 5, 6, 3, 6)

    for cycle in range(20):
        page.run_analysis()
        events()
        if page.result is None:
            raise RuntimeError(f"legacy PCA cycle {cycle + 1}: no result")
        for index in sequence:
            print(
                f"LEGACY_TRACE cycle={cycle + 1} tab={index} phase=before_set",
                flush=True,
            )
            page.tabs.setCurrentIndex(index)
            events()
            print(
                f"LEGACY_TRACE cycle={cycle + 1} tab={index} phase=after_events",
                flush=True,
            )
            canvas = plot_tabs.get(index)
            if canvas is not None:
                canvas.draw()
                events()
                print(
                    f"LEGACY_TRACE cycle={cycle + 1} tab={index} phase=after_draw",
                    flush=True,
                )
            pix = window.grab()
            if pix.isNull():
                raise RuntimeError("legacy window grab failed")
            events(2)
        print(f"legacy PCA cycle {cycle + 1}/20 OK", flush=True)

    # 再进行 20 轮快速 Tab 切换，逼近用户连续点击场景。
    for cycle in range(20):
        for index in range(page.tabs.count()):
            page.tabs.setCurrentIndex(index)
            events(2)
            canvas = plot_tabs.get(index)
            if canvas is not None:
                canvas.draw()
            window.grab()
            events(1)
        print(f"legacy rapid tabs {cycle + 1}/20 OK", flush=True)

    window.close()
    print("LEGACY_PCA_REPRO_COMPLETED_WITHOUT_CRASH", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
