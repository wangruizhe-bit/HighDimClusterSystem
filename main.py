"""高维数据降维与聚类分析系统 V1.0。"""
import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.styles import STYLE

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("高维数据降维与聚类分析系统 V1.0")
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
