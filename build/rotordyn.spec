# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for RotorDyn Calculator.

Build command:
    cd build && pyinstaller rotordyn.spec
"""

import importlib
import os

# Find NiceGUI package location for data files
nicegui_path = os.path.dirname(importlib.import_module("nicegui").__file__)

block_cipher = None

a = Analysis(
    ["../main.py"],
    pathex=[],
    binaries=[],
    datas=[
        (nicegui_path, "nicegui"),
    ],
    hiddenimports=[
        "plotly",
        "plotly.graph_objects",
        "plotly.express",
        "numpy",
        "scipy",
        "scipy.optimize",
        "openpyxl",
        "engineio.async_drivers.aiohttp",
        "nicegui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RotorDyn",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --windowed: no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="icon.ico",  # Uncomment when icon is available
)
