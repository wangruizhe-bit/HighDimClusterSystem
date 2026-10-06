"""分页式预览：只读取 DataFrame 当前前 500 行并限制单元显示长度。"""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

class FrameTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = None
        self.limit = 500

    def set_frame(self, frame):
        self.beginResetModel()
        self.frame = frame.head(self.limit).copy() if frame is not None else None
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() or self.frame is None else len(self.frame)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() or self.frame is None else len(self.frame.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self.frame is None or role != Qt.ItemDataRole.DisplayRole:
            return None
        value = self.frame.iat[index.row(),index.column()]
        import pandas as pd
        if pd.isna(value):
            return "—"
        return str(value)[:180]

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or self.frame is None:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self.frame.columns[section])
        return str(section+1)
