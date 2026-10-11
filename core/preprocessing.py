"""真实的数据清洗与标准化，全部返回新的 DataFrame。"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def _check(frame):
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("数据为空，请先导入有效数据。")
    return frame.copy(deep=True)

def drop_missing(frame):
    return _check(frame).dropna().reset_index(drop=True)

def fill_missing(frame, method="mean"):
    out = _check(frame)
    if method not in ("mean", "median"):
        raise ValueError("不支持的缺失值填补方法。")
    names = out.select_dtypes(include="number").columns
    if len(names) == 0:
        raise ValueError("没有可填补的数值变量。")
    if np.isinf(out[names].to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValueError("数值变量存在无穷值，请先移除或修正，不能用其填补缺失值。")
    values = out[names].mean() if method == "mean" else out[names].median()
    if any(pd.isna(values[c]) and out[c].isna().any() for c in names):
        raise ValueError("存在整列缺失的数值变量，不能按均值或中位数填补。")
    out.loc[:,names] = out[names].fillna(values)
    return out

def remove_duplicates(frame):
    return _check(frame).drop_duplicates().reset_index(drop=True)

def scale_numeric(frame, method="zscore"):
    out = _check(frame)
    names = out.select_dtypes(include="number").columns
    if len(names) == 0:
        raise ValueError("没有数值变量。")
    if out[names].isna().any().any():
        raise ValueError("请先填补数值变量的缺失值。")
    if not np.isfinite(out[names].to_numpy(dtype=float)).all():
        raise ValueError("数值变量存在无穷值，请先清洗。")
    if method == "zscore":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    else:
        raise ValueError("不支持的标准化方法。")
    out[names] = scaler.fit_transform(out[names].astype(float))
    return out
