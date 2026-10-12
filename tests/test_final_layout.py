"""最终界面布局回归测试：滚动边界、工作区比例和最小窗口可用性。"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.styles import STYLE


def _app():
    app = QApplication.instance() or QApplication([])
    app.setFont(QFont("Microsoft YaHei UI", 11))
    app.setStyleSheet(STYLE)
    return app


def _window(width, height):
    app = _app()
    window = MainWindow()
    window.resize(width, height)
    window.show()
    app.processEvents()
    window.load_demo_data()
    window.goto(0)
    app.processEvents()
    return app, window


def _assert_home_bottom_reachable(app, window):
    scroll = window.stack.widget(0)
    bar = scroll.verticalScrollBar()
    bar.setValue(bar.maximum())
    app.processEvents()
    assert bar.value() == bar.maximum()

    last = window.home_dataset_hint
    bottom = last.mapTo(scroll.viewport(), QPoint(0, last.height())).y()
    remaining = scroll.viewport().height() - bottom
    assert remaining >= 20, (
        f"首页最后一行底部仅剩 {remaining}px；滚动到底后应至少保留 20px 空白。"
    )

    pipeline_last = window.home_preview
    pipeline_bottom = pipeline_last.mapTo(
        scroll.viewport(), QPoint(0, pipeline_last.height())
    ).y()
    assert pipeline_bottom <= scroll.viewport().height() - 20


def test_home_bottom_is_fully_reachable_in_required_windows():
    # 1920×1080 / 100%、1920×1080 / 125% 等效逻辑尺寸、
    # 默认 1600×940、最小 1180×760。
    for width, height in [(1920, 1080), (1536, 864), (1600, 940), (1180, 760)]:
        app, window = _window(width, height)
        _assert_home_bottom_reachable(app, window)
        window.close()
        app.processEvents()


def test_workspace_dominates_right_rail_at_default_width():
    app, window = _window(1600, 940)
    workspace = window.stack.width()
    assert not window.data_lens.isVisible()
    assert workspace / window.centralWidget().width() >= .98
    window.studio_header.result_button.click()
    app.processEvents()
    assert window.data_lens.isVisible()
    assert 245 <= window.data_lens.width() <= 285
    assert window.stack.width() < workspace
    window.studio_header.result_button.click()
    app.processEvents()
    assert window.stack.width() == workspace
    window.close()
    app.processEvents()


def test_home_pipeline_is_primary_column():
    app, window = _window(1600, 940)
    assert len(window.home_pipeline_steps) == 4
    assert window.home_preview.height() >= 280
    assert window.home_preview_model.rowCount() == 90
    for step, target in zip(window.home_pipeline_steps, (3, 4, 5, 6)):
        assert step.width() >= window.home_pipeline.width() * .20
        step.click()
        assert window.stack.currentIndex() == target
    window.close()
    app.processEvents()


def test_analysis_pages_receive_wider_workspace():
    app, window = _window(1600, 940)
    for index in (3, 4, 5, 6, 7):
        window.goto(index)
        app.processEvents()
        scroll = window.stack.currentWidget()
        assert scroll.viewport().width() >= 1550
        assert scroll.viewport().height() >= window.height() * .85
    window.close()
    app.processEvents()
