"""正式源代码清理检查。"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = [ROOT / "main.py"]
SOURCE_FILES += sorted((ROOT / "app").glob("*.py"))
SOURCE_FILES += sorted((ROOT / "core").glob("*.py"))

BANNED = [
    "第三个软著",
    "第三软著",
    "前两个软著",
    "为软著设计",
    "第一阶段",
    "第二阶段",
    "第三阶段",
    "第四阶段",
    "第五阶段",
    "后续阶段",
    "后续开发",
    "尚未完成",
    "def placeholder(",
    "def not_ready(",
    "def settings_box(",
]


def test_formal_source_has_no_submission_or_development_traces():
    offenders = {}
    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        hits = [term for term in BANNED if term in text]
        if hits:
            offenders[path.relative_to(ROOT).as_posix()] = hits
    assert not offenders, offenders
