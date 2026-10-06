"""本地 CSV、Excel 文件读取。"""
from pathlib import Path
import pandas as pd

def load_table(path):
    p = Path(path)
    if not p.is_file():
        raise ValueError("文件不存在，请重新选择。")
    if p.stat().st_size == 0:
        raise ValueError("文件为空。")
    if p.suffix.lower() not in (".csv", ".xlsx", ".xls"):
        raise ValueError("仅支持 CSV、XLSX 和 XLS 文件。")
    try:
        if p.suffix.lower() == ".csv":
            for encoding in ("utf-8-sig", "gb18030"):
                try:
                    frame = pd.read_csv(p, encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("CSV 文件编码无法识别。")
        else:
            frame = pd.read_excel(p)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("文件读取失败，请确认编码与文件格式。") from exc
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("文件没有可用数据行或列。")
    frame.columns = [str(c).strip() for c in frame.columns]
    if frame.columns.duplicated().any() or any(not c for c in frame.columns):
        raise ValueError("文件列名有重复或为空。")
    return frame
