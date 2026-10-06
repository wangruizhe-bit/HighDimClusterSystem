"""PySide6 available in CI; software rendering is used for headless smoke test."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

def test_ui_launch_and_pages():
    from PySide6.QtWidgets import QApplication
    from app.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.stack.count() == 8
    for index in range(8):
        window.goto(index)
        assert window.stack.currentIndex() == index
    window.close()
