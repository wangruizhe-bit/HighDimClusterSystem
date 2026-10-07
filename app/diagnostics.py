"""崩溃与绘图异常诊断。

未捕获 Python 异常写入 crash.log；faulthandler 写入 fatal.log。
日志位于 LOCALAPPDATA/HighDimClusterSystem/logs（非 Windows 时使用用户缓存目录）。
"""
from __future__ import annotations

from datetime import datetime
import faulthandler
import os
from pathlib import Path
import platform
import sys
import traceback
from typing import Callable

import matplotlib
import numpy
import PySide6


VERSION = "V1.0"
_FATAL_STREAM = None
_PAGE_PROVIDER: Callable[[], str] | None = None


def log_directory() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    path = root / "HighDimClusterSystem" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _header(kind: str) -> str:
    page = "未知"
    if _PAGE_PROVIDER is not None:
        try:
            page = str(_PAGE_PROVIDER())
        except Exception:
            page = "无法读取"
    return (
        f"\n{'=' * 72}\n"
        f"{kind}\n"
        f"时间: {datetime.now().astimezone().isoformat()}\n"
        f"软件: 高维数据降维与聚类分析系统 {VERSION}\n"
        f"当前页面: {page}\n"
        f"Python: {sys.version.replace(chr(10), ' ')}\n"
        f"系统: {platform.platform()}\n"
        f"PySide6: {PySide6.__version__}\n"
        f"Matplotlib: {matplotlib.__version__}\n"
        f"Matplotlib backend: {matplotlib.get_backend()}\n"
        f"NumPy: {numpy.__version__}\n"
    )


def set_page_provider(provider: Callable[[], str] | None) -> None:
    global _PAGE_PROVIDER
    _PAGE_PROVIDER = provider


def append_exception(kind: str, exc_type=None, exc=None, tb=None) -> Path:
    path = log_directory() / "crash.log"
    if exc_type is None and exc is not None:
        exc_type = type(exc)
        tb = exc.__traceback__
    with path.open("a", encoding="utf-8") as stream:
        stream.write(_header(kind))
        if exc_type is not None:
            traceback.print_exception(exc_type, exc, tb, file=stream)
        else:
            stream.write("没有可用的 Python traceback。\n")
        stream.flush()
    return path


def log_plot_exception(title: str, exc: BaseException) -> Path:
    return append_exception(f"图形绘制失败: {title}", type(exc), exc, exc.__traceback__)


def _excepthook(exc_type, exc, tb):
    path = append_exception("未捕获 Python 异常", exc_type, exc, tb)
    # console/debug 构建仍保留标准错误输出。
    sys.__excepthook__(exc_type, exc, tb)
    try:
        sys.stderr.write(f"Crash log: {path}\n")
    except Exception:
        pass


def install_crash_handlers() -> tuple[Path, Path]:
    """安装全局异常与 native fatal 诊断，返回两个日志路径。"""
    global _FATAL_STREAM
    directory = log_directory()
    crash_path = directory / "crash.log"
    fatal_path = directory / "fatal.log"
    sys.excepthook = _excepthook

    if _FATAL_STREAM is None:
        _FATAL_STREAM = fatal_path.open("a", encoding="utf-8")
        _FATAL_STREAM.write(_header("faulthandler 启动"))
        _FATAL_STREAM.flush()
        faulthandler.enable(file=_FATAL_STREAM, all_threads=True)
    return crash_path, fatal_path
