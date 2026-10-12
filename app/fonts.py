"""Select an installed font with Chinese glyphs for every Qt entrypoint."""
from PySide6.QtGui import QFont, QFontDatabase, QRawFont

from app.styles import STYLE


CANDIDATES = (
    "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC",
    "Noto Sans CJK JP", "Noto Sans SC", "SimHei", "WenQuanYi Zen Hei",
    "PingFang SC", "Arial Unicode MS",
)
GLYPH_SAMPLE = "高维数据降维聚类分析系统轮廓参数导出"


def chinese_font_family():
    available = set(QFontDatabase.families())
    fallback = QFontDatabase.families(QFontDatabase.WritingSystem.SimplifiedChinese)
    for family in dict.fromkeys((*CANDIDATES, *fallback)):
        if family not in available:
            continue
        raw = QRawFont.fromFont(QFont(family, 11))
        if raw.isValid() and all(raw.supportsCharacter(ord(char)) for char in GLYPH_SAMPLE):
            return family
    raise RuntimeError("未找到包含中文字符的字体。Windows 请安装微软雅黑；Linux 请安装 Noto CJK。")


def configure_application(app):
    family = chinese_font_family()
    font = QFont(family, 11)
    if app.font() != font:
        app.setFont(font)
    # Use the same verified family in QSS: otherwise QSS overrides app.setFont.
    style = STYLE.replace(
        '"Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC"',
        f'"{family}"',
    )
    if app.styleSheet() != style:
        app.setStyleSheet(style)
    return family
