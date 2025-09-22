# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent

datas = []
hiddenimports = ['Quartz', 'dotenv']
datas += collect_data_files('shapely')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('sqlalchemy_utils')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('aiosqlite')
hiddenimports += collect_submodules('shapely')
hiddenimports += collect_submodules('pynput')
hiddenimports += collect_submodules('mss')
hiddenimports += collect_submodules('tkinter')


a = Analysis(
    [str(APP_DIR / 'app_entry.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gum Recorder v0.0.32',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gum Recorder v0.0.32',
)
app = BUNDLE(
    coll,
    name='Gum Recorder v0.0.32.app',
    icon=None,
    bundle_identifier='com.local.gumrecorder.v0.0.32',
)
