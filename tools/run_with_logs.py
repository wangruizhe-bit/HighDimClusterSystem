"""运行子进程后无论成功失败都打印 HighDimClusterSystem 诊断日志。"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _log_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "HighDimClusterSystem" / "logs"


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit("usage: python -m tools.run_with_logs COMMAND [ARGS...]")
    print("RUN:", " ".join(args), flush=True)
    completed = subprocess.run(
        args, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace",
    )
    print(completed.stdout, flush=True)
    if completed.returncode and os.environ.get("GITHUB_ACTIONS") == "true":
        details = completed.stdout[-12000:]
        details = details.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Command failed::exit={completed.returncode}%0A{details}", flush=True)
    directory = _log_dir()
    print(f"DIAGNOSTIC LOG DIRECTORY: {directory}", flush=True)
    for name in ("crash.log", "fatal.log"):
        path = directory / name
        print(f"--- {name} ---", flush=True)
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                safe = content.encode("ascii", "backslashreplace").decode("ascii")
                print(safe, flush=True)
            except Exception as exc:
                print(f"cannot read {path}: {exc}", flush=True)
        else:
            print("(not created)", flush=True)
    return int(completed.returncode)


if __name__ == "__main__":
    sys.exit(main())
