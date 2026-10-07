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
    assert window.data_lens.mode_code.text() == "06 / CLUSTER"
    assert window.data_lens.mode_title.text() == "聚类分析"

    window.close()
