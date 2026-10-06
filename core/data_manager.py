"""原始数据与工作数据的独立管理。"""
from pathlib import Path
import pandas as pd
from .io import load_table

class DataManager:
    def __init__(self):
        self.raw_data = None
        self.current_data = None
        self.file_path = None
        self.file_name = None

    def load_file(self, path):
        frame = load_table(path)
        self.raw_data = frame.copy(deep=True)
        self.current_data = frame.copy(deep=True)
        self.file_path = str(Path(path).resolve())
        self.file_name = Path(path).name

    def get_data(self):
        if self.current_data is None:
            raise ValueError("请先导入数据。")
        return self.current_data.copy(deep=True)

    def set_data(self, frame):
        if self.raw_data is None:
            raise ValueError("请先导入数据。")
        if not isinstance(frame, pd.DataFrame):
            raise TypeError("处理结果必须为 DataFrame。")
        if frame.columns.duplicated().any():
            raise ValueError("不能使用重复的列名。")
        self.current_data = frame.copy(deep=True)

    def restore_original(self):
        if self.raw_data is None:
            raise ValueError("没有可恢复的原始数据。")
        self.current_data = self.raw_data.copy(deep=True)

    def get_numeric_columns(self):
        if self.current_data is None:
            return []
        return list(self.current_data.select_dtypes(include="number").columns)

    def summary(self):
        if self.current_data is None:
            return dict(name="尚未导入数据", rows=0, columns=0, numeric=0,
                        non_numeric=0, missing=0, duplicates=0)
        f = self.current_data
        n = len(f.select_dtypes(include="number").columns)
        return dict(name=self.file_name or "当前数据", rows=len(f),
                    columns=len(f.columns), numeric=n, non_numeric=len(f.columns)-n,
                    missing=int(f.isna().sum().sum()), duplicates=int(f.duplicated().sum()))

    def column_summary(self):
        f = self.get_data()
        return pd.DataFrame({"变量": [str(x) for x in f.columns],
            "类型": [str(x) for x in f.dtypes],
            "非空数": f.notna().sum().values,
            "缺失数": f.isna().sum().values,
            "唯一值数": f.nunique(dropna=True).values})
