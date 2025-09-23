# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent

datas = []
hiddenimports = ['Quartz', 'AppKit', 'pyobjc_framework_AppKit', 'dotenv', 'pyobjc', 'pyobjc_core', 'pyobjc_framework_Quartz', 'gum.observers.base.observer', 'gum.observers.macos.screen', 'gum.observers.macos.ui', 'gum.observers.fallback.keyboard']
datas += collect_data_files('shapely')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('gum.observers')
hiddenimports += collect_submodules('sqlalchemy_utils')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('aiosqlite')
hiddenimports += collect_submodules('shapely')
hiddenimports += collect_submodules('pynput')
hiddenimports += collect_submodules('mss')
# Exclude tkinter to avoid surprise Tk mainloops
# hiddenimports += collect_submodules('tkinter')


# Exclude Tk to avoid surprise Tk mainloops
EXCLUDES = ['tkinter', '_tkinter', 'tcl', 'tk', 'Tkinter']

a = Analysis(
    [str(APP_DIR / 'app_entry.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gum Recorder',
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
    name='Gum Recorder',
)
app = BUNDLE(
    coll,
    name='Gum Recorder.app',
    icon=None,
    bundle_identifier='com.local.gumrecorder',
)
