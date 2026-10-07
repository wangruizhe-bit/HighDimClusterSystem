"""第三软著独立视觉结构回归测试。

不是像素级审美测试；用于防止未来又退回前两个软件已经使用过的
“左侧导航栏”或“顶部模块下拉控制台”结构。
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QFrame
from app.main_window import MainWindow


def test_third_app_uses_unique_data_studio_shell():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1500, 900)
    window.show()
    app.processEvents()

    assert window.studio_header.objectName() == "studioHeader"
    assert window.mode_strip.objectName() == "modeStrip"
    assert window.data_lens.objectName() == "dataLensRail"
    assert window.stack.objectName() == "studioCanvas"
    assert len(window.nav_buttons) == 8

    # 第三个软件的一级导航必须是横向模式带，不再使用第一个软件的左侧栏。
    ys = [button.mapTo(window, button.rect().topLeft()).y() for button in window.nav_buttons]
    xs = [button.mapTo(window, button.rect().topLeft()).x() for button in window.nav_buttons]
    assert max(ys) - min(ys) < 8
    assert xs == sorted(xs)
    assert window.data_lens.x() > window.stack.x()

    # 第二个软件使用顶部模块下拉选择器；第三个软件不应出现同名模块选择器。
    selectors = window.findChildren(QComboBox)
    assert all(item.objectName() != "moduleSelector" for item in selectors)
    assert not window.findChildren(QFrame, "sidebar")

    window.close()


def test_data_lens_tracks_dataset_and_mode(tmp_path):
    import pandas as pd
    app = QApplication.instance() or QApplication([])
    path = tmp_path / "lens.csv"
    pd.DataFrame({"x": [1., 2., 3., 4.], "y": [4., 3., 2., 1.]}).to_csv(path, index=False)

    window = MainWindow()
    window.session.load(str(path))
    app.processEvents()

    assert "lens.csv" in window.data_lens.dataset_name.text()
    assert window.data_lens.rows[1].text() == "4"
    assert window.data_lens.numeric[1].text() == "2"

    window.goto(5)
    app.processEvents()
    assert window.data_lens.mode_code.text() == "06"
    assert window.data_lens.mode_title.text() == "聚类分析"

    window.close()


def test_readable_typography_and_chinese_copy():
    from app.styles import STYLE
    import re

    sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", STYLE)]
    assert sizes
    assert min(sizes) >= 13

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.resize(1920, 1080)
    window.show()
    app.processEvents()

    assert window.studio_header.findChild(QFrame, "datasetCapsule") is not None
    assert window.studio_header.dataset_text.fontMetrics().height() >= 13
    assert "高维数据降维与聚类分析系统" in window.windowTitle()
    assert "CURRENT DATASET" not in window.studio_header.findChildren(type(window.data_lens.mode_title))[0].text()

    banned = {
        "DATA LENS", "DATA QUALITY", "ANALYSIS SNAPSHOTS", "CURRENT MODE",
        "WORKSPACE STATUS", "DATA DISCOVERY / DIMENSION REDUCTION / CLUSTERING",
    }
    all_text = "\n".join(
        widget.text() for widget in window.findChildren(type(window.data_lens.mode_title))
        if hasattr(widget, "text")
    )
    for phrase in banned:
        assert phrase not in all_text

    for button in window.nav_buttons:
        metrics = button.fontMetrics()
        lines = button.text().splitlines()
        assert max(metrics.horizontalAdvance(line) for line in lines) <= button.width() - 12
        assert metrics.lineSpacing() * len(lines) <= button.height() - 6

    window.close()


def test_125_percent_equivalent_workspace_keeps_key_controls_visible():
    from app.styles import STYLE
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    window = MainWindow()
    # 1920x1080 at 125% Windows scaling is approximately 1536x864 logical pixels.
    window.resize(1536, 864)
    window.show()
    app.processEvents()

    assert window.stack.width() >= 900
    assert window.data_lens.width() >= 280
    for index in range(8):
        window.goto(index)
        app.processEvents()
        assert window.stack.currentIndex() == index
    for button in window.nav_buttons:
        assert button.height() >= 55
        assert button.width() >= 95

    window.close()
