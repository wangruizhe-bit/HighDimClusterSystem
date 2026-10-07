"""高维数据降维与聚类分析系统 V1.0：Windows 本地桌面程序入口。"""
import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.styles import STYLE


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("高维数据降维与聚类分析系统 V1.0")
    app.setFont(QFont("Microsoft YaHei UI", 11))
    app.setStyleSheet(STYLE)
    win = MainWindow()
    if "--self-check" in sys.argv:
        # CI 和 PyInstaller 可执行程序验收入口；不依赖联网和人工点击。
        try:
            if win.stack.count() != 8:
                raise RuntimeError("软件功能页面数量不是 8。")
            for index in range(8):
                win.goto(index)
                if win.stack.currentIndex() != index:
                    raise RuntimeError("功能页面无法正常切换。")
            win.load_demo_data()
            summary = win.session.data.summary()
            if summary.get("rows") != 90 or summary.get("numeric") != 8:
                raise RuntimeError("内置示例数据未正确打包或无法加载。")
            print("HighDimClusterSystem V1.0: startup + demo-data self-check passed", flush=True)
            return 0
        finally:
            win.close()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
