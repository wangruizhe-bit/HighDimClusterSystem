"""第三软著专用 Data Studio 视觉主题。

与前两个软著刻意区分：
- 不使用左侧白色工作流导航；
- 不使用可靠性系统的青绿色工业控制台与顶部下拉模块；
- 使用深墨紫品牌栏、横向模式带、紫/琥珀强调色和全宽分析画布。
"""

STYLE = """
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC";
    font-size: 14px;
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
    color: #74629f;
    font-size: 13px;
    font-weight: 600;
}
QLabel#lensTitle {
    color: #2c2642;
    font-size: 20px;
    font-weight: 700;
}
QLabel#lensHint {
    color: #6f6978;
    font-size: 13px;
    font-weight: 500;
}
QFrame#lensDatasetCard {
    background: #211c34;
    border: 1px solid #393051;
    border-radius: 11px;
}
QLabel#lensCardEyebrow {
    color: #c8bdec;
    font-size: 13px;
    font-weight: 600;
}
QLabel#lensDatasetName {
    color: #f6f2ff;
    font-size: 15px;
    font-weight: 700;
}
QLabel#lensDatasetShape {
    color: #d1c8e7;
    font-size: 13px;
    font-weight: 500;
}
QLabel#lensSection {
    color: #615775;
    font-size: 14px;
    font-weight: 700;
    margin-top: 8px;
}
QFrame#lensMetric {
    background: #f9f8fc;
    border: 1px solid #e4dfec;
    border-radius: 8px;
}
QLabel#lensMetricCaption {
    color: #5f5968;
    font-size: 14px;
    font-weight: 500;
}
QLabel#lensMetricValue {
    color: #493b7a;
    font-size: 16px;
    font-weight: 700;
}
QFrame#lensResultCard {
    background: #fff8ed;
    border: 1px solid #f0d8b4;
    border-radius: 9px;
}
QLabel#lensResultValue {
    color: #a85f18;
    font-size: 28px;
    font-weight: 700;
}
QLabel#lensResultCaption {
    color: #7c5d3e;
    font-size: 13px;
    font-weight: 500;
}
QLabel#lensModeCode {
    color: #6b50c8;
    font-size: 14px;
    font-weight: 700;
}
QLabel#lensModeTitle {
    color: #322b48;
    font-size: 16px;
    font-weight: 700;
}
QLabel#lensModeHint {
    color: #655e70;
    font-size: 13px;
    font-weight: 500;
}
QFrame#lensOffline {
    background: #e9e4f6;
    border: 1px solid #d8cfed;
    border-radius: 9px;
}
QLabel#lensOfflineTitle {
    color: #5946a7;
    font-size: 14px;
    font-weight: 700;
}
QLabel#lensOfflineHint {
    color: #625975;
    font-size: 13px;
    font-weight: 500;
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
    border-radius: 14px;
    font-size: 16px;
    font-weight: 700;
}
QLabel#studioBrand {
    color: #f4f1ff;
    background: transparent;
    font-size: 21px;
    font-weight: 700;
}
QLabel#studioBrandSub {
    color: #beb7d6;
    background: transparent;
    font-size: 13px;
    font-weight: 500;
}
QFrame#datasetCapsule {
    background: rgba(255,255,255,16);
    border: 1px solid #50496d;
    border-radius: 10px;
}
QLabel#datasetEyebrow {
    color: #c1b9dc;
    background: transparent;
    font-size: 13px;
    font-weight: 600;
}
QLabel#datasetValue {
    color: #f3f0ff;
    background: transparent;
    font-size: 14px;
    font-weight: 600;
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
    padding: 7px 9px 9px 9px;
    color: #625d6f;
    font-size: 15px;
    font-weight: 600;
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
    color: #7867b0;
    font-size: 14px;
    font-weight: 700;
}
QLabel#pageTitle {
    color: #24213a;
    font-size: 26px;
    font-weight: 700;
}
QLabel#pageHint {
    color: #6f6879;
    font-size: 14px;
    font-weight: 500;
}
QLabel#heading {
    color: #28233f;
    font-size: 20px;
    font-weight: 700;
}
QLabel#subtitle {
    color: #625b6d;
    font-size: 14px;
    font-weight: 500;
}

/* ------------------------- Home studio dashboard ------------------------- */
QFrame#homeHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #29233f, stop:0.55 #443477, stop:1 #684fc3);
    border: 1px solid #6656a1;
    border-radius: 17px;
}
QLabel#heroEyebrow {
    color: #e3dcfa;
    background: transparent;
    font-size: 13px;
    font-weight: 600;
}
QLabel#heroTitle {
    color: white;
    background: transparent;
    font-size: 27px;
    font-weight: 700;
}
QLabel#heroSubtitle {
    color: #f0ecfb;
    background: transparent;
    font-size: 15px;
    font-weight: 500;
}
QFrame#homeContext {
    background: rgba(19,17,33,90);
    border: 1px solid rgba(255,255,255,45);
    border-radius: 12px;
    min-width: 255px;
}
QLabel#contextEyebrow {
    color: #d4caf3;
    background: transparent;
    font-size: 13px;
    font-weight: 600;
}
QLabel#contextTitle {
    color: white;
    background: transparent;
    font-size: 19px;
    font-weight: 700;
}
QLabel#contextHint { color: #e2dced; background: transparent; font-size: 14px; font-weight: 500; }
QLabel#contextBadge {
    color: #2f2459;
    background: #e3dbff;
    border-radius: 7px;
    padding: 8px 11px;
    font-size: 14px;
    font-weight: 700;
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
QLabel#metricCaption { color: #625d69; font-size: 14px; font-weight: 600; }
QLabel#metricValue { color: #29233f; font-size: 28px; font-weight: 700; }
QLabel#metricFoot { color: #746e7b; font-size: 13px; font-weight: 500; }

QFrame#studioPanel {
    background: #ffffff;
    border: 1px solid #e6e2ec;
    border-radius: 13px;
}
QLabel#panelTitle { color: #2a263e; font-size: 18px; font-weight: 700; }
QLabel#panelHint { color: #686170; font-size: 13px; font-weight: 500; }
QFrame#pipelineStep {
    background: #faf9fc;
    border: 1px solid #ece8f1;
    border-radius: 9px;
}
QFrame#pipelineStep:hover { background: #f6f2ff; border-color: #d8cdfa; }
QLabel#pipelineNumber {
    color: white;
    background: #7057d7;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 700;
}
QLabel#pipelineTitle { color: #343047; font-size: 15px; font-weight: 700; }
QLabel#pipelineHint { color: #655f6e; font-size: 13px; font-weight: 500; }
QPushButton#pipelineJump {
    background: #efeaff;
    color: #654bc5;
    border: 1px solid #dcd2ff;
    border-radius: 7px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 700;
}
QPushButton#pipelineJump:hover { background: #dfd6ff; }
QFrame#capabilityRow {
    background: #faf9fc;
    border: 1px solid #eeeaf2;
    border-radius: 8px;
}
QLabel#capabilityName { color: #5946a7; font-size: 15px; font-weight: 700; }
QLabel#capabilityHint { color: #655f6e; font-size: 13px; font-weight: 500; }

/* ------------------------- Reusable analysis surfaces ------------------------- */
QFrame#card {
    background: #ffffff;
    border: 1px solid #e7e3ed;
    border-radius: 12px;
}
QLabel#cardTitle {
    color: #3f3858;
    font-size: 18px;
    font-weight: 700;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #e6e1ed;
    border-radius: 11px;
    margin-top: 15px;
    padding: 15px 14px 13px 14px;
    font-size: 15px;
    font-weight: 600;
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
    padding: 9px 14px;
    color: #4f4864;
    font-size: 14px;
    font-weight: 600;
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
    font-size: 14px;
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
QListWidget::item { padding: 8px 7px; border-radius: 4px; }
QListWidget::item:selected { background: #e9e3ff; color: #503cad; }

QTableView {
    gridline-color: #efecf2;
    alternate-background-color: #fbfafc;
}
QHeaderView::section {
    background: #f1edf8;
    color: #655b78;
    padding: 10px;
    font-size: 14px;
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
    color: #625c6c;
    padding: 10px 15px;
    font-size: 14px;
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
    color: #d1cadf;
    border-top: 1px solid #302944;
    font-size: 13px;
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
