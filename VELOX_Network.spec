# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['velox_miner.py'],
    pathex=[],
    binaries=[],
    datas=[('favicon (2).ico', '.'), ('velox_bot.py', '.')],
    hiddenimports=['aiogram', 'aiogram.filters', 'aiogram.types', 'aiogram.methods'],
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
    name='VELOX_Network',
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
    icon=['favicon (2).ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VELOX_Network',
)
