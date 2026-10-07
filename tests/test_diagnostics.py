"""崩溃日志与绘图异常保护回归。"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "QtAgg")
os.environ.setdefault("QT_API", "pyside6")


def test_python_plot_exception_is_written_to_crash_log(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication
    from app.plot_canvas import PlotCanvas

    app = QApplication.instance() or QApplication([])
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    else:
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("HIGHDIM_SELF_CHECK", "1")

    canvas = PlotCanvas()

    def broken(_axes):
        raise RuntimeError("intentional-render-failure")

    try:
        canvas.safe_update("测试图", broken)
    except RuntimeError as exc:
        assert "intentional-render-failure" in str(exc)
    else:
        raise AssertionError("自检模式必须把绘图异常重新抛出")

    log = tmp_path / "HighDimClusterSystem" / "logs" / "crash.log"
    assert log.is_file()
    text = log.read_text(encoding="utf-8")
    assert "图形绘制失败: 测试图" in text
    assert "intentional-render-failure" in text
    assert "Matplotlib" in text
    canvas.close()
    app.processEvents()
