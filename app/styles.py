"""第三软著专用 Data Studio 视觉主题。

与前两个软著刻意区分：
- 不使用左侧白色工作流导航；
- 不使用可靠性系统的青绿色工业控制台与顶部下拉模块；
- 使用深墨紫品牌栏、横向模式带、紫/琥珀强调色和全宽分析画布。
"""

STYLE = """
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC";
    font-size: 13px;
    color: #292842;
}
QMainWindow, QWidget#studioWorkspace, QStackedWidget#studioCanvas,
QScrollArea#studioScroll, QScrollArea#studioScroll > QWidget > QWidget,
QWidget#studioPage {
    background: #f7f6fb;
}
QScrollArea#studioScroll { border: none; }

QFrame#dataLensRail {
    background: #f0edf6;
    border-left: 1px solid #dfd8ea;
}
QLabel#lensEyebrow {
    color: #8b75c2;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1px;
}
QLabel#lensTitle {
    color: #2c2642;
    font-size: 19px;
    font-weight: 900;
}
QLabel#lensHint {
    color: #8c8598;
    font-size: 9px;
}
QFrame#lensDatasetCard {
    background: #211c34;
    border: 1px solid #393051;
    border-radius: 11px;
}
QLabel#lensCardEyebrow {
    color: #a99cdc;
    font-size: 8px;
    font-weight: 850;
}
QLabel#lensDatasetName {
    color: #f6f2ff;
    font-size: 13px;
    font-weight: 850;
}
QLabel#lensDatasetShape {
    color: #c0b5dc;
    font-size: 10px;
}
QLabel#lensSection {
    color: #776c90;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1px;
    margin-top: 6px;
}
QFrame#lensMetric {
    background: #f9f8fc;
    border: 1px solid #e4dfec;
    border-radius: 8px;
}
QLabel#lensMetricCaption {
    color: #756f80;
    font-size: 10px;
}
QLabel#lensMetricValue {
    color: #493b7a;
    font-size: 13px;
    font-weight: 900;
}
QFrame#lensResultCard {
    background: #fff8ed;
    border: 1px solid #f0d8b4;
    border-radius: 9px;
}
QLabel#lensResultValue {
    color: #b66b1c;
    font-size: 26px;
    font-weight: 900;
}
QLabel#lensResultCaption {
    color: #9b7449;
    font-size: 9px;
}
QLabel#lensModeCode {
    color: #7d63dc;
    font-size: 9px;
    font-weight: 900;
}
QLabel#lensModeTitle {
    color: #322b48;
    font-size: 13px;
    font-weight: 850;
}
QLabel#lensModeHint {
    color: #888094;
    font-size: 9px;
}
QFrame#lensOffline {
    background: #e9e4f6;
    border: 1px solid #d8cfed;
    border-radius: 9px;
}
QLabel#lensOfflineTitle {
    color: #5946a7;
    font-size: 9px;
    font-weight: 900;
}
QLabel#lensOfflineHint {
    color: #786d91;
    font-size: 9px;
}

/* ------------------------- Top Data Studio shell ------------------------- */
QFrame#studioHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #171628, stop:0.55 #211d38, stop:1 #292241);
    border: none;
    border-bottom: 1px solid #3c345c;
}
QLabel#studioMark {
    color: #ffffff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #8c72ff, stop:1 #6547d8);
    border: 1px solid #a492ff;
    border-radius: 13px;
    font-size: 18px;
    font-weight: 900;
}
QLabel#studioBrand {
    color: #f4f1ff;
    background: transparent;
    font-size: 14px;
    font-weight: 850;
    letter-spacing: 1px;
}
QLabel#studioBrandSub {
    color: #a9a2c6;
    background: transparent;
    font-size: 11px;
}
QFrame#datasetCapsule {
    background: rgba(255,255,255,16);
    border: 1px solid #50496d;
    border-radius: 10px;
}
QLabel#datasetEyebrow {
    color: #9f96c7;
    background: transparent;
    font-size: 9px;
    font-weight: 800;
}
QLabel#datasetValue {
    color: #f3f0ff;
    background: transparent;
    font-size: 12px;
    font-weight: 700;
}
QPushButton#headerPrimary {
    background: #8066ef;
    color: white;
    border: 1px solid #8f79ef;
    border-radius: 8px;
    padding: 9px 15px;
    font-weight: 800;
}
QPushButton#headerPrimary:hover { background: #927cff; }
QPushButton#headerGhost {
    background: transparent;
    color: #e5e0fb;
    border: 1px solid #5b5377;
    border-radius: 8px;
    padding: 9px 15px;
    font-weight: 700;
}
QPushButton#headerGhost:hover { background: #39334f; border-color: #8177a6; }

/* Horizontal mode strip: primary navigation unique to this app */
QFrame#modeStrip {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e7e3ef;
}
QPushButton#modeButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 5px 8px 7px 8px;
    color: #767188;
    font-size: 11px;
    text-align: center;
}
QPushButton#modeButton:hover {
    background: #f4f1fb;
    color: #5c46b5;
}
QPushButton#modeButton[active="true"] {
    background: #eee9ff;
    color: #5d45c6;
    border-bottom: 3px solid #7a5fe8;
    font-weight: 850;
}

/* ------------------------- Page framing ------------------------- */
QFrame#pageBanner {
    background: transparent;
    border-bottom: 1px solid #e8e5ef;
}
QLabel#pageCode {
    color: #8e82bd;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
}
QLabel#pageTitle {
    color: #24213a;
    font-size: 23px;
    font-weight: 850;
}
QLabel#pageHint {
    color: #898398;
    font-size: 11px;
}
QLabel#heading {
    color: #28233f;
    font-size: 20px;
    font-weight: 850;
}
QLabel#subtitle {
    color: #746e84;
    font-size: 12px;
}

/* ------------------------- Home studio dashboard ------------------------- */
QFrame#homeHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #29233f, stop:0.55 #443477, stop:1 #684fc3);
    border: 1px solid #6656a1;
    border-radius: 17px;
}
QLabel#heroEyebrow {
    color: #d8cffd;
    background: transparent;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1px;
}
QLabel#heroTitle {
    color: white;
    background: transparent;
    font-size: 29px;
    font-weight: 900;
}
QLabel#heroSubtitle {
    color: #e6e1f7;
    background: transparent;
    font-size: 12px;
}
QFrame#homeContext {
    background: rgba(19,17,33,90);
    border: 1px solid rgba(255,255,255,45);
    border-radius: 12px;
    min-width: 255px;
}
QLabel#contextEyebrow {
    color: #c1b7ec;
    background: transparent;
    font-size: 9px;
    font-weight: 900;
}
QLabel#contextTitle {
    color: white;
    background: transparent;
    font-size: 18px;
    font-weight: 850;
}
QLabel#contextHint { color: #d1cae8; background: transparent; font-size: 10px; }
QLabel#contextBadge {
    color: #2f2459;
    background: #dcd1ff;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 11px;
    font-weight: 850;
}

QFrame#metricTile {
    background: white;
    border: 1px solid #e7e2ef;
    border-radius: 12px;
}
QFrame#metricTile[accent="violet"] { border-top: 3px solid #795ce8; }
QFrame#metricTile[accent="amber"]  { border-top: 3px solid #f0a54f; }
QFrame#metricTile[accent="rose"]   { border-top: 3px solid #d97498; }
QFrame#metricTile[accent="mint"]   { border-top: 3px solid #3aa995; }
QLabel#metricCaption { color: #8a8494; font-size: 10px; font-weight: 750; }
QLabel#metricValue { color: #29233f; font-size: 27px; font-weight: 900; }
QLabel#metricFoot { color: #9a94a4; font-size: 9px; }

QFrame#studioPanel {
    background: #ffffff;
    border: 1px solid #e6e2ec;
    border-radius: 13px;
}
QLabel#panelTitle { color: #2a263e; font-size: 16px; font-weight: 850; }
QLabel#panelHint { color: #918b9e; font-size: 10px; }
QFrame#pipelineStep {
    background: #faf9fc;
    border: 1px solid #ece8f1;
    border-radius: 9px;
}
QFrame#pipelineStep:hover { background: #f6f2ff; border-color: #d8cdfa; }
QLabel#pipelineNumber {
    color: white;
    background: #7057d7;
    border-radius: 9px;
    font-size: 11px;
    font-weight: 900;
}
QLabel#pipelineTitle { color: #343047; font-size: 12px; font-weight: 800; }
QLabel#pipelineHint { color: #8e8999; font-size: 9px; }
QPushButton#pipelineJump {
    background: #efeaff;
    color: #654bc5;
    border: 1px solid #dcd2ff;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 10px;
    font-weight: 800;
}
QPushButton#pipelineJump:hover { background: #dfd6ff; }
QFrame#capabilityRow {
    background: #faf9fc;
    border: 1px solid #eeeaf2;
    border-radius: 8px;
}
QLabel#capabilityName { color: #5946a7; font-size: 11px; font-weight: 850; }
QLabel#capabilityHint { color: #8e8999; font-size: 9px; }

/* ------------------------- Reusable analysis surfaces ------------------------- */
QFrame#card {
    background: #ffffff;
    border: 1px solid #e7e3ed;
    border-radius: 12px;
}
QLabel#cardTitle {
    color: #3f3858;
    font-size: 14px;
    font-weight: 850;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #e6e1ed;
    border-radius: 11px;
    margin-top: 15px;
    padding: 15px 14px 13px 14px;
    font-weight: 700;
    color: #4c4563;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 13px;
    padding: 0 6px;
    color: #655a82;
    background: #f7f6fb;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #dcd6e7;
    border-radius: 8px;
    padding: 8px 13px;
    color: #4f4864;
}
QPushButton:hover {
    background: #f5f1ff;
    color: #5d46bb;
    border-color: #c9bcf0;
}
QPushButton:pressed { background: #e9e2ff; }
QPushButton:disabled { background: #f3f1f5; color: #aaa4b1; border-color: #e4e0e7; }
QPushButton#primary {
    background: #7358dd;
    color: white;
    border: 1px solid #7358dd;
    font-weight: 800;
}
QPushButton#primary:hover { background: #8067e4; border-color: #8067e4; }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget, QTableView {
    background: #ffffff;
    border: 1px solid #ddd8e6;
    border-radius: 7px;
    padding: 5px;
    selection-background-color: #e8e0ff;
    selection-color: #3d2f77;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QListWidget:focus, QTableView:focus {
    border: 1px solid #8c73e8;
}
QListWidget::item { padding: 5px; border-radius: 4px; }
QListWidget::item:selected { background: #e9e3ff; color: #503cad; }

QTableView {
    gridline-color: #efecf2;
    alternate-background-color: #fbfafc;
}
QHeaderView::section {
    background: #f1edf8;
    color: #655b78;
    padding: 8px;
    border: none;
    border-right: 1px solid #e2ddea;
    border-bottom: 1px solid #ddd7e6;
    font-weight: 750;
}
QTabWidget::pane {
    border: 1px solid #e5e0eb;
    background: white;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #f2eff7;
    color: #777083;
    padding: 9px 14px;
    margin-right: 3px;
    border: 1px solid #e5e0eb;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}
QTabBar::tab:selected {
    background: white;
    color: #6048bd;
    font-weight: 800;
    border-top: 3px solid #7b5ce2;
}
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 16px; height: 16px; }

QStatusBar {
    background: #201c31;
    color: #bdb6d0;
    border-top: 1px solid #302944;
}
QStatusBar QLabel { color: #bdb6d0; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 3px; }
QScrollBar::handle:vertical { background: #cfc8db; border-radius: 4px; min-height: 32px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: #f0edf4; height: 10px; }
QScrollBar::handle:horizontal { background: #cbc4d8; border-radius: 4px; min-width: 34px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""
