"""Compact scientific workspace: quiet surfaces and restrained violet accents."""
STYLE = """
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC";
    font-size: 14px; color: #293142;
}
QMainWindow, QWidget#studioWorkspace, QStackedWidget#studioCanvas,
QScrollArea#studioScroll, QScrollArea#studioScroll > QWidget > QWidget,
QWidget#studioPage { background: #f5f6f9; }
QScrollArea#studioScroll { border: none; }
QScrollArea#parameterPanel, QScrollArea#parameterPanel > QWidget > QWidget {
    background: #f5f6f9; border: none;
}
QFrame#studioHeader { background: #ffffff; border-bottom: 1px solid #e8eaf0; }
QLabel#studioMark {
    background: #6b56ce; color: white; border-radius: 9px;
    font-size: 13px; font-weight: 600;
}
QLabel#studioBrand { color: #232839; font-size: 18px; font-weight: 600; }
QFrame#datasetCapsule { background: #f6f7fa; border-radius: 6px; }
QLabel#datasetValue { color: #6a7181; font-size: 13px; font-weight: 400; }
QFrame#modeStrip { background: white; border-bottom: 1px solid #e4e7ed; }
QPushButton#modeButton {
    background: transparent; border: none; border-radius: 5px;
    padding: 5px 12px; min-height: 22px; color: #656d7d; font-weight: 400;
}
QPushButton#modeButton:hover { background: #f5f3fc; color: #5d48be; }
QPushButton#modeButton[active="true"] {
    background: #eeeafb; color: #5c45be; font-weight: 600;
}
QFrame#pageBanner { background: transparent; }
QLabel#pageTitle { font-size: 17px; font-weight: 600; color: #303647; }
QLabel#homeHeading { font-size: 17px; font-weight: 600; }
QLabel#muted { color: #828896; font-size: 13px; }
QFrame#card { background: white; border: 1px solid #e4e7ed; border-radius: 8px; }
QLabel#cardTitle { font-size: 14px; font-weight: 600; color: #485062; }
QFrame#metricTile { background: white; border: 1px solid #e4e7ed; border-radius: 8px; }
QLabel#metricCaption { color: #818897; font-size: 13px; }
QLabel#metricValue { color: #343b4c; font-size: 23px; font-weight: 500; }
QPushButton#quickAction {
    text-align: left; padding: 13px 18px; color: #5944b5; background: #f0edfa;
    border: 1px solid #e6dff5; font-weight: 500;
}
QPushButton#quickAction:hover { background: #e9e3f9; border-color: #d0c4ef; }
QGroupBox {
    background: white; border: 1px solid #e4e7ed; border-radius: 8px;
    margin-top: 14px; padding: 12px; font-weight: 500;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 5px;
    color: #656d7d; background: #f5f6f9;
}
QPushButton {
    background: #ffffff; border: 1px solid #dce0e8; border-radius: 5px;
    padding: 6px 12px; min-height: 20px; font-size: 14px; font-weight: 400;
    color: #495366;
}
QPushButton:hover { background: #f7f6fc; border-color: #c2b8e3; color: #5d48be; }
QPushButton:pressed { background: #eae5f8; }
QPushButton:disabled { background: #f4f5f7; color: #a7acb7; border-color: #e7e9ee; }
QPushButton#primary, QPushButton#headerPrimary {
    background: #6b56ce; border-color: #6b56ce; color: white; font-weight: 500;
}
QPushButton#primary:hover, QPushButton#headerPrimary:hover { background: #5e49c1; }
QPushButton#headerGhost { color: #737c8b; border: none; background: transparent; }
QPushButton#headerGhost:checked { background: #eeeafb; color: #5c45be; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: white; border: 1px solid #dce0e8; border-radius: 4px;
    padding: 5px 8px; min-height: 20px;
    selection-background-color: #ede8fb; selection-color: #5c45be;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #9a88dd;
}
QComboBox::drop-down { width: 24px; border: none; }
QListWidget {
    background: #fafbfc; border: 1px solid #e2e5ed; border-radius: 4px;
    selection-background-color: #ede8fb; selection-color: #5c45be;
}
QListWidget::item { padding: 5px 8px; }
QTableView {
    background: white; alternate-background-color: #fafbfe;
    border: 1px solid #e5e8ef; gridline-color: #f0f1f5;
    selection-background-color: #eeeafb; selection-color: #493e86;
}
QTableView::item { padding: 5px 8px; }
QHeaderView::section {
    background: #f5f6fa; color: #697284; padding: 8px 10px;
    border: none; border-right: 1px solid #e8eaf0; border-bottom: 1px solid #e3e7ee;
    font-size: 13px; font-weight: 500;
}
QTabWidget::pane { background: white; border: 1px solid #e2e6ed; border-radius: 5px; }
QTabBar::tab {
    background: transparent; color: #737c8b; padding: 8px 13px;
    font-size: 13px; border: none; border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: #5c45be; border-bottom-color: #7861d6; font-weight: 500; }
QTabBar::tab:hover { color: #5c45be; background: #f7f5fc; }
QCheckBox { spacing: 7px; }
QStatusBar { background: #ffffff; color: #8a919d; border-top: 1px solid #e8eaf0; font-size: 13px; }
QScrollBar:vertical { background: #f2f3f7; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #c9ced9; border-radius: 4px; min-height: 34px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #f2f3f7; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #c9ced9; border-radius: 4px; min-width: 34px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QFrame#dataLensRail { background: white; border-left: 1px solid #e4e7ed; }
QScrollArea#lensScroll, QWidget#lensContent { background: white; border: none; }
QLabel#lensTitle { font-size: 15px; font-weight: 500; }
QLabel#lensSection { color: #818897; font-size: 13px; margin-top: 6px; }
QFrame#lensDatasetCard, QFrame#lensResultCard {
    background: #f7f8fb; border: 1px solid #e8eaf0; border-radius: 6px;
}
QLabel#lensCardEyebrow, QLabel#lensDatasetShape, QLabel#lensResultCaption {
    color: #828a99; font-size: 13px;
}
QLabel#lensDatasetName { color: #434c5c; font-size: 14px; font-weight: 500; }
QFrame#lensMetric { border-bottom: 1px solid #eef0f4; }
QLabel#lensMetricCaption { color: #7c8595; font-size: 13px; }
QLabel#lensMetricValue, QLabel#lensResultValue { color: #5743b5; font-size: 16px; font-weight: 500; }
QLabel#lensModeCode { color: #9ba2ad; font-size: 13px; }
QLabel#lensModeTitle { color: #596273; font-size: 14px; }
"""
