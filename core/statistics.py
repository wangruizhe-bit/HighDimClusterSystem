"""可解释的基础统计计算。"""
import pandas as pd

def numeric_data(frame, columns=None):
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("请先导入有效数据。")
    if columns is not None:
        if not columns:
            raise ValueError("请至少选择一个变量。")
        if any(c not in frame.columns for c in columns):
            raise ValueError("所选变量不存在。")
        frame = frame.loc[:,columns]
    out = frame.select_dtypes(include="number")
    if len(out.columns) == 0:
        raise ValueError("没有可分析的数值变量。")
    return out

def describe(frame, columns=None):
    out = numeric_data(frame, columns).describe().T
    out.columns = ["样本数","均值","标准差","最小值","第一四分位数","中位数","第三四分位数","最大值"]
    return out.rename_axis("变量").reset_index()

def correlation(frame, columns=None):
    out = numeric_data(frame, columns)
    if len(out.columns) < 2 or len(out) < 2:
        raise ValueError("相关分析需要至少两列数值变量和两行样本。")
    return out.corr(method="pearson")

def covariance(frame, columns=None):
    out = numeric_data(frame, columns)
    if len(out.columns) < 2 or len(out) < 2:
        raise ValueError("协方差分析需要至少两列数值变量和两行样本。")
    return out.cov()
