"""Verify the redesigned workspace using actual widgets and operations."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
import pytest
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication, QGroupBox, QPushButton

from app.fonts import configure_application
from app.main_window import MainWindow
from app.table_model import FrameTableModel


def window(width=1180, height=760):
    app = QApplication.instance() or QApplication([])
    configure_application(app)
    widget = MainWindow()
    widget.resize(width, height)
    widget.show()
    widget.load_demo_data()
    app.processEvents()
    return app, widget


@pytest.mark.parametrize("size", [(1180, 760), (1536, 864), (1920, 1080)])
def test_visible_data_table_occupies_at_least_half_the_window(size):
    app, widget = window(*size)
    scroll = widget.stack.currentWidget()
    origin = widget.data_table.mapTo(scroll.viewport(), QPoint(0, 0))
    visible = QRect(origin, widget.data_table.size()).intersected(scroll.viewport().rect())
    assert visible.width() >= widget.width() * .95
    assert visible.height() >= widget.height() * .50
    assert widget.data_model.rowCount() == 90
    widget.close()


def test_parameter_panels_keep_results_near_the_top_and_controls_inside():
    app, widget = window()
    for page_index, page in ((3, widget.pca_page), (4, widget.dimension_page), (5, widget.cluster_page)):
        widget.goto(page_index)
        app.processEvents()
        results = page.tabs if hasattr(page, "tabs") else page.workspace_tabs
        assert results.mapTo(widget, QPoint(0, 0)).y() < 240
        assert results.width() > widget.width() * .68
        assert page.run_button.isVisible()
        assert page.run_button.mapTo(widget, QPoint(0, page.run_button.height())).y() <= widget.height() - 20
        panel = page.parameter_panel
        for group in panel.findChildren(QGroupBox):
            assert group.width() <= panel.viewport().width()
    widget.goto(6)
    widget.evaluation_page.workspace_tabs.setCurrentIndex(1)
    app.processEvents()
    group = next(g for g in widget.evaluation_page.findChildren(QGroupBox) if g.title() == "扫描设置")
    assert group.width() <= 280
    widget.close()


@pytest.mark.parametrize("method", range(6))
def test_every_preprocessing_choice_still_runs_the_real_operation(tmp_path, method):
    app, widget = window()
    frame = pd.DataFrame({"x": [1., 2., 2., 7.], "y": [3., 4., 4., 8.]})
    if method in (0, 1, 2):
        frame.loc[1, "x"] = np.nan
    path = tmp_path / "input.csv"
    frame.to_csv(path, index=False)
    widget.session.load(str(path))
    widget.preprocess_selector.setCurrentIndex(method)
    widget.preprocess_apply_button.click()
    output = widget.session.data.current_data
    if method == 0:
        assert len(output) == 3 and not output.isna().any().any()
    elif method == 1:
        assert output.loc[1, "x"] == pytest.approx(10 / 3)
    elif method == 2:
        assert output.loc[1, "x"] == 2
    elif method == 3:
        assert len(output) == 3 and not output.duplicated().any()
    elif method == 4:
        np.testing.assert_allclose(output.mean(), 0, atol=1e-12)
        np.testing.assert_allclose(output.std(ddof=0), 1)
    else:
        np.testing.assert_allclose(output.min(), 0)
        np.testing.assert_allclose(output.max(), 1)
    pd.testing.assert_frame_equal(widget.session.data.raw_data, frame)
    restore = next(b for b in widget.findChildren(QPushButton) if b.text() == "恢复原始数据")
    restore.click()
    pd.testing.assert_frame_equal(widget.session.data.current_data, frame)
    widget.close()


def test_display_rounding_keeps_full_numeric_value_and_tooltip():
    model = FrameTableModel()
    value = 1 / 7
    model.set_frame(pd.DataFrame({"x": [value]}))
    index = model.index(0, 0)
    assert model.data(index) == "0.142857"
    assert model.data(index, Qt.ItemDataRole.ToolTipRole) == str(value)
    assert model.frame.iloc[0, 0] == value
