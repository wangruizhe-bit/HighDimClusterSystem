# -*- mode: python ; coding: utf-8 -*-
"""Console diagnostic PyInstaller spec with explicit Matplotlib backend collection."""
from PyInstaller.utils.hooks import collect_all

sk_datas, sk_binaries, sk_hidden = collect_all("sklearn")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=sk_binaries,
    datas=sk_datas + [("data", "data")],
    hiddenimports=sk_hidden + [
        "matplotlib.backends.backend_qtagg",
        "matplotlib.backends.backend_agg",
        "mpl_toolkits.mplot3d",
    ],
    hookspath=[],
    hooksconfig={
        "matplotlib": {
            "backends": ["QtAgg", "Agg"],
        },
    },
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HighDimClusterSystem-Debug",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HighDimClusterSystem-Debug",
)
