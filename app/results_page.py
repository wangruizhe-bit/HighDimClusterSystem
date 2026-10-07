"""结果中心：结果浏览、真实数据导出、离线报告、图形保存。"""
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget,
)
from app.table_model import FrameTableModel
from core.reporting import (
    build_catalog, export_csv, export_excel, export_figure, export_html_report,
)


class ResultsPage(QWidget):
    """只展示当前 session 中存在的真实分析结果；不运行模拟算法。"""

    def __init__(self, session, host, parent=None):
        super().__init__(parent)
        self.session = session
        self.host = host
        self.catalog = []
        self.plots = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        summary_group = QGroupBox("当前数据版本的分析结果")
        summary_layout = QVBoxLayout(summary_group)
        self.summary = QLabel("请先导入数据。")
        self.summary.setWordWrap(True)
        summary_layout.addWidget(self.summary)
        selector = QHBoxLayout()
        selector.addWidget(QLabel("浏览结果表"))
        self.result_combo = QComboBox()
        self.result_combo.setMinimumWidth(370)
        self.result_combo.currentIndexChanged.connect(self.display_selected)
        selector.addWidget(self.result_combo, 1)
        summary_layout.addLayout(selector)
        self.preview_description = QLabel("尚无真实分析结果。")
        self.preview_description.setWordWrap(True)
        summary_layout.addWidget(self.preview_description)
        self.preview = QTableView()
        self.preview.setMinimumHeight(290)
        self.preview.setAlternatingRowColors(True)
        self.preview.horizontalHeader().setStretchLastSection(True)
        self.preview_model = FrameTableModel(self.preview)
        self.preview.setModel(self.preview_model)
        summary_layout.addWidget(self.preview)
        root.addWidget(summary_group)

        export_group = QGroupBox("表格与离线报告导出")
        export_layout = QVBoxLayout(export_group)
        export_layout.addWidget(QLabel("CSV 导出所选表；Excel 导出全部结果；HTML 生成离线报告。"))
        buttons = QGridLayout()
        self.export_csv_button = QPushButton("导出所选表 CSV")
        self.export_xlsx_button = QPushButton("导出全部结果 Excel")
        self.export_html_button = QPushButton("生成离线 HTML 分析报告")
        self.export_csv_button.clicked.connect(self.save_csv)
        self.export_xlsx_button.clicked.connect(self.save_excel)
        self.export_html_button.clicked.connect(self.save_report)
        buttons.addWidget(self.export_csv_button, 0, 0)
        buttons.addWidget(self.export_xlsx_button, 0, 1)
        buttons.addWidget(self.export_html_button, 0, 2)
        export_layout.addLayout(buttons)
        root.addWidget(export_group)

        figures = QGroupBox("保存已计算的图表")
        figure_layout = QVBoxLayout(figures)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("选择当前图表"))
        self.figure_combo = QComboBox()
        self.figure_combo.setMinimumWidth(300)
        bar.addWidget(self.figure_combo, 1)
        self.export_figure_button = QPushButton("保存 PNG / SVG")
        self.export_figure_button.clicked.connect(self.save_figure)
        bar.addWidget(self.export_figure_button)
        figure_layout.addLayout(bar)
        figure_layout.addWidget(QLabel("保存已经生成的图表，支持 PNG 和 SVG。"))
        root.addWidget(figures)

        controls = QHBoxLayout()
        self.clear_button = QPushButton("清空本次分析结果")
        self.clear_button.clicked.connect(self.clear_results)
        controls.addWidget(self.clear_button)
        controls.addStretch()
        root.addLayout(controls)
        self.notice = QLabel("文件保存在本机，不上传数据。")
        self.notice.setWordWrap(True)
        root.addWidget(self.notice)

        self.session.data_changed.connect(self.refresh)
        self.session.results_changed.connect(self.refresh)
        self.session.cluster_changed.connect(self.refresh)
        self.session.k_search_changed.connect(self.refresh)
        self.refresh()

    def _catalog(self):
        return build_catalog(
            self.session.data.current_data,
            data_name=self.session.data.file_name or "当前数据",
            pca=self.session.latest_pca,
            reductions=self.session.reduction_results,
            clusters=self.session.cluster_results,
            k_search=self.session.k_search_result,
            feature_result=self.session.feature_result,
        )

    def _plots(self):
        """只收集当前计算版本已生成的图表（不导出空状态画布）。"""
        host = self.host
        selected = []
        if getattr(host, "feature_figure_ready", False):
            selected.append(("特征统计图", host.statistics_canvas.figure))
        pca = host.pca_page
        if pca.result is not None:
            selected.append(("PCA 方差贡献率图", pca.variance_canvas.figure))
            if pca.result.chosen_components >= 2:
                selected.append(("PCA 二维得分图", pca.scatter2d_canvas.figure))
            if pca.result.chosen_components >= 3:
                selected.append(("PCA 三维得分图", pca.scatter3d_canvas.figure))
        reduction = host.dimension_page
        if reduction.current_result is not None:
            selected.append(("降维二维散点图", reduction.canvas2d.figure))
            if reduction.current_result.dimensions == 3:
                selected.append(("降维三维散点图", reduction.canvas3d.figure))
        if getattr(reduction, "comparison_ready", False):
            selected.append(("多方法降维并排对比图", reduction.comparison_canvas.figure))
        clustering = host.cluster_page
        if clustering.current_result is not None:
            selected.append(("聚类二维投影图", clustering.scatter2d.figure))
            if "PC3" in clustering.current_result.coords.columns:
                selected.append(("聚类三维投影图", clustering.scatter3d.figure))
            if clustering.current_result.linkage_matrix is not None and (
                clustering.current_result.n_samples <= 160
            ):
                selected.append(("层次聚类树状图", clustering.tree_canvas.figure))
        evaluation = host.evaluation_page
        if self.session.cluster_results and getattr(evaluation, "score_plot_ready", False):
            selected.append(("聚类评价轮廓系数对比", evaluation.score_canvas.figure))
        if self.session.k_search_result is not None:
            selected.append(("K 值辅助选择曲线", evaluation.k_canvas.figure))
        return selected

    def refresh(self):
        old_key = self.result_combo.currentData()
        self.catalog = self._catalog()
        self.result_combo.blockSignals(True)
        self.result_combo.clear()
        for item in self.catalog:
            self.result_combo.addItem(f"[{item.category}] {item.title}", item.key)
        if old_key is not None:
            found = self.result_combo.findData(old_key)
            if found >= 0:
                self.result_combo.setCurrentIndex(found)
        self.result_combo.blockSignals(False)

        self.plots = self._plots()
        chosen_plot = self.figure_combo.currentText()
        self.figure_combo.clear()
        for title, _ in self.plots:
            self.figure_combo.addItem(title)
        if chosen_plot:
            found = self.figure_combo.findText(chosen_plot)
            if found >= 0:
                self.figure_combo.setCurrentIndex(found)
        self.export_csv_button.setEnabled(bool(self.catalog))
        self.export_xlsx_button.setEnabled(bool(self.catalog))
        self.export_html_button.setEnabled(bool(self.catalog))
        self.export_figure_button.setEnabled(bool(self.plots))
        self.clear_button.setEnabled(
            self.session.latest_pca is not None or
            bool(self.session.reduction_results) or
            bool(self.session.cluster_results) or
            self.session.k_search_result is not None or
            self.session.feature_result is not None
        )
        self.summary.setText(
            f"已管理 {len(self.catalog)} 张真实结果表、{len(self.plots)} 张可导出图形。"
            "更换数据文件或重新预处理后，旧分析数据自动清除。"
            if self.catalog else "尚未导入可用数据。"
        )
        self.display_selected()

    def selected_item(self):
        index = self.result_combo.currentIndex()
        return self.catalog[index] if 0 <= index < len(self.catalog) else None

    def display_selected(self, *_):
        item = self.selected_item()
        self.preview_model.set_frame(item.frame if item is not None else None)
        if item is None:
            self.preview_description.setText("尚无数据结果可供查看。")
            return
        self.preview_description.setText(
            f"{item.title} · {len(item.frame)} 行 × {len(item.frame.columns)} 列；"
            "这里只预览最多前 500 行。" +
            (f"\n{item.description}" if item.description else "")
        )

    @staticmethod
    def _choose(parent, title, filename, file_filter):
        return QFileDialog.getSaveFileName(parent, title, filename, file_filter)[0]

    def _safe_export(self, callback):
        try:
            destination = callback()
            if destination is not None:
                self.notice.setText(f"导出成功：{destination}")
        except (OSError, ValueError, TypeError, PermissionError) as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
        except Exception:
            QMessageBox.warning(self, "保存失败", "无法完成文件保存，请检查路径、权限或文件是否被占用。")

    def save_csv(self):
        item = self.selected_item()
        if item is None:
            return
        def write():
            path = self._choose(self, "保存所选结果表", "分析结果.csv",
                                "CSV 文件 (*.csv)")
            return export_csv(item, path) if path else None
        self._safe_export(write)

    def save_excel(self):
        if not self.catalog:
            return
        def write():
            path = self._choose(self, "导出所有真实分析结果", "完整分析结果.xlsx",
                                "Excel 工作簿 (*.xlsx)")
            return export_excel(self.catalog, path) if path else None
        self._safe_export(write)

    def save_report(self):
        if not self.catalog:
            return
        def write():
            path = self._choose(self, "保存分析报告", "分析报告.html",
                                "HTML 网页 (*.html)")
            return export_html_report(self.catalog, path) if path else None
        self._safe_export(write)

    def save_figure(self):
        index = self.figure_combo.currentIndex()
        if not (0 <= index < len(self.plots)):
            return
        title, figure = self.plots[index]
        def write():
            path = self._choose(self, "保存真实图像", title + ".png",
                                "PNG 图片 (*.png);;SVG 矢量图 (*.svg)")
            return export_figure(figure, path) if path else None
        self._safe_export(write)

    def clear_results(self):
        if not self.clear_button.isEnabled():
            return
        answer = QMessageBox.question(
            self, "清空分析结果",
            "确定清空当前数据版本的所有统计与模型结果吗？"
            "这不会删除原始或工作数据，但已计算的结果记录将无法恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.session.clear_results()
            self.notice.setText("已清空分析结果；工作数据和原始文件保持不变。")
