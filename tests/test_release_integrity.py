"""回归：GitHub 上传附件不得遗漏 sklearn/.libs 等隐藏目录。"""
import shutil
import pytest
from tools.verify_release import check_bundle, check_original, sklearn_hidden_dlls, file_map


def test_detect_hidden_sklearn_dll_omitted_during_artifact_transfer(tmp_path):
    source = tmp_path / "pyinstaller"
    destination = tmp_path / "downloaded"
    hidden = source / "_internal" / "sklearn" / ".libs" / "vcomp140.dll"
    hidden.parent.mkdir(parents=True)
    hidden.write_bytes(b"x" * 4096)
    (source / "HighDimClusterSystem.exe").write_bytes(b"test-app")
    shutil.copytree(source, destination)
    assert sklearn_hidden_dlls(file_map(source)) == [
        "_internal/sklearn/.libs/vcomp140.dll"
    ]
    assert check_original(source)
    assert check_bundle(source, destination) == ["_internal/sklearn/.libs/vcomp140.dll"]
    (destination / "_internal" / "sklearn" / ".libs" / "vcomp140.dll").unlink()
    with pytest.raises(ValueError, match="缺失"):
        check_bundle(source, destination)


def test_reject_dll_hash_mismatch_even_if_size_unchanged(tmp_path):
    src = tmp_path / "build"
    dst = tmp_path / "artifact"
    hidden = src / "_internal" / "sklearn" / ".libs" / "vcomp140.dll"
    hidden.parent.mkdir(parents=True)
    hidden.write_bytes(b"x" * 4096)
    shutil.copytree(src, dst)
    (dst / "_internal" / "sklearn" / ".libs" / "vcomp140.dll").write_bytes(b"y" * 4096)
    with pytest.raises(ValueError, match="SHA256"):
        check_bundle(src, dst)
