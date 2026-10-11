"""校验 PyInstaller onedir 产物经 GitHub Artifact 传输后是否完整。

这个工具专门防止 GitHub upload-artifact 忽略 sklearn/.libs 等隐藏目录，
造成打包环境内能启动、实际用户下载后找不到 vcomp140.dll。
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys


def file_map(folder: Path) -> dict[str, Path]:
    if not folder.is_dir():
        raise ValueError(f"目录不存在：{folder}")
    return {
        file.relative_to(folder).as_posix(): file
        for file in folder.rglob("*") if file.is_file()
    }


def sklearn_hidden_dlls(files: dict[str, Path]) -> list[str]:
    """检索 sklearn/.libs 中的真实 DLL；dot 文件夹不得被忽略。"""
    output = []
    for rel in files:
        components = Path(rel).parts
        if (
            rel.lower().endswith(".dll")
            and any(segment.lower() in (".libs", "sklearn.libs") for segment in components)
            and any("sklearn" in segment.lower() for segment in components)
        ):
            output.append(rel)
    return sorted(output)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_bundle(source: Path, transported: Path) -> list[str]:
    """验证文件集合、大小和全部文件的哈希完全一致，包含隐藏 DLL。"""
    originals = file_map(source)
    obtained = file_map(transported)
    if not originals:
        raise ValueError("待打包目录为空。")
    important = sklearn_hidden_dlls(originals)
    if not important:
        raise ValueError(
            "原始 PyInstaller 输出中缺少 sklearn/.libs 下的 DLL，"
            "应先修复依赖收集，而不能发给用户。"
        )
    missing = sorted(set(originals) - set(obtained))
    extra = sorted(set(obtained) - set(originals))
    if missing or extra:
        raise ValueError(
            f"下载附件不完整，缺失 {len(missing)} 个文件，多出 {len(extra)} 个文件。"
            f"缺失示例：{missing[:12]}；多出示例：{extra[:12]}"
        )
    differing = sorted(
        name for name in originals
        if originals[name].stat().st_size != obtained[name].stat().st_size
    )
    if differing:
        raise ValueError(f"下载附件中文件长度不一致：{differing[:12]}")
    for name in originals:
        if digest(originals[name]) != digest(obtained[name]):
            raise ValueError(f"发布文件的 SHA256 不一致：{name}")
    print(
        f"Release integrity OK: {len(originals)} files, "
        f"{len(important)} hidden sklearn DLL(s) retained."
    )
    for name in important:
        print(f"  Verified hidden DLL: {name}")
    return important


def check_original(folder: Path) -> list[str]:
    original = file_map(folder)
    dlls = sklearn_hidden_dlls(original)
    if not dlls:
        raise ValueError(
            "PyInstaller 文件夹中找不到 sklearn 隐藏的 DLL（例如 "
            "_internal/sklearn/.libs/vcomp140.dll）。"
        )
    for name in dlls:
        if original[name].stat().st_size < 1024:
            raise ValueError(f"sklearn DLL 文件不完整：{name}")
    print(f"Original bundle contains {len(dlls)} hidden sklearn DLLs.")
    for name in dlls:
        print(f"  {name}")
    return dlls


def run_exe(folder: Path) -> None:
    exe = folder / "HighDimClusterSystem.exe"
    if not exe.is_file():
        raise ValueError("最终附件缺少 HighDimClusterSystem.exe。")
    # Windows 测试机本身虽然装有 scikit-learn，但是这里刻意避免
    # 继承 Python 的 site-packages 路径，以验证用户下载的完整目录。
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["QT_QPA_PLATFORM"] = "windows" if os.name == "nt" else "offscreen"
    environment["MPLBACKEND"] = "QtAgg" if os.name == "nt" else "Agg"
    p = subprocess.run(
        [str(exe.resolve()), "--self-check"],
        cwd=folder.resolve(),
        env=environment,
        timeout=150,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(f"从 GitHub 下载后的 EXE 启动失败：退出码 {p.returncode}")
    print("Downloaded Windows EXE startup self-check succeeded.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--downloaded")
    args = parser.parse_args()
    original = Path(args.original).resolve()
    check_original(original)
    if args.downloaded:
        downloaded = Path(args.downloaded).resolve()
        check_bundle(original, downloaded)
        run_exe(downloaded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
