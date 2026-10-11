"""Actual widget sizing and glyph support for release rendering."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFont, QRawFont
from PySide6.QtWidgets import QApplication

from app.fonts import GLYPH_SAMPLE, configure_application
from app.plot_canvas import StaticPlotCanvas
from app.studio_components import ElidedLabel


def test_application_font_contains_chinese_glyphs():
    app = QApplication.instance() or QApplication([])
    previous_font, previous_style = app.font(), app.styleSheet()
    try:
        family = configure_application(app)
        raw = QRawFont.fromFont(QFont(family, 11))
        assert all(raw.supportsCharacter(ord(char)) for char in GLYPH_SAMPLE)
        assert f'"{family}"' in app.styleSheet()
    finally:
        app.setFont(previous_font)
        app.setStyleSheet(previous_style)


def test_static_plot_can_shrink_after_repeated_large_draws():
    app = QApplication.instance() or QApplication([])
    canvas = StaticPlotCanvas()
    canvas.axes.plot([1, 2, 3], [2, 4, 1])
    canvas.show()
    for width, height in ((1300, 800), (600, 400), (1200, 600), (500, 300)):
        canvas.resize(width, height)
        app.processEvents()
        canvas.draw()
        app.processEvents()
        assert canvas.width() == width
        assert canvas.height() == height
        assert canvas.minimumSizeHint().height() <= 100
        assert canvas._image.width() == round(canvas.image_label.width() * canvas.devicePixelRatioF())
    canvas.close()


def test_dataset_name_uses_pixel_ellipsis_and_preserves_full_name():
    app = QApplication.instance() or QApplication([])
    name = "中文长文件名_" * 20 + ".csv"
    label = ElidedLabel(name, "datasetValue")
    label.resize(160, 30)
    label.show()
    app.processEvents()
    assert label.toolTip() == name
    assert label.text().endswith("…")
    assert label.fontMetrics().horizontalAdvance(label.text()) <= label.contentsRect().width()
    label.close()
