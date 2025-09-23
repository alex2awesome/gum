# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = []
hiddenimports = ['Quartz', 'AppKit', 'pyobjc_framework_AppKit', 'dotenv', 'gum.observers.base.observer', 'gum.observers.macos.screen', 'gum.observers.macos.ui', 'gum.observers.fallback.keyboard']
datas += collect_data_files('shapely')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('sqlalchemy_utils')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('aiosqlite')
hiddenimports += collect_submodules('shapely')
hiddenimports += collect_submodules('pynput')
hiddenimports += collect_submodules('mss')
hiddenimports += collect_submodules('gum.observers')


a = Analysis(
    ['app_entry.py'],
    pathex=[],
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
    name='Gum Recorder v0.0.41',
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
    name='Gum Recorder v0.0.41',
)
app = BUNDLE(
    coll,
    name='Gum Recorder v0.0.41.app',
    icon=None,
    bundle_identifier='com.local.gumrecorder.v0.0.41',
)
