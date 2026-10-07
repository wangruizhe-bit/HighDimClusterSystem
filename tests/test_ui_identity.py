"""界面差异化回归：第三软件固定采用 Data Studio 双层顶部结构。"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_data_studio_shell_is_horizontal_and_has_no_sidebar():
    from PySide6.QtWidgets import QApplication, QFrame, QLabel
    from app.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.stack.count() == 8
    assert window.studio_header.objectName() == "studioHeader"
    assert window.mode_strip.objectName() == "modeStrip"
    assert len(window.nav_buttons) == 8
    assert all(button.objectName() == "modeButton" for button in window.nav_buttons)
    assert not window.findChildren(QFrame, "sidebar")

    for index in range(8):
        window.goto(index)
        assert window.stack.currentIndex() == index
        assert window.nav_buttons[index].isChecked()
        assert window.nav_buttons[index].property("active") is True

    brands = window.studio_header.findChildren(QLabel, "studioBrand")
    assert len(brands) == 1
    assert brands[0].text() == "高维数据降维与聚类分析系统"
    assert "HIGH-DIMENSIONAL DATA STUDIO" not in brands[0].text()
    window.close()


def test_home_dashboard_uses_real_metric_tiles():
    from PySide6.QtWidgets import QApplication
    from app.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert set(window.metric_tiles) == {"rows", "numeric", "missing", "results"}
    assert window.metric_tiles["rows"].value_label.text() == "0"
    window.close()
