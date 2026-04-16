# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Основные данные (скрипты и иконки)
datas = [
    ('velox_bot.py', '.'), 
    ('velox_security.py', '.'), 
    ('velox_config.py', '.'), 
    ('VELOX.ico', '.'), 
    ('VELOX_logo.png', '.')
]
binaries = []
hiddenimports = [
    'duckduckgo_search', 
    'requests', 
    'json', 
    're', 
    'PIL._tkinter_finder'
]

# Автоматический сбор зависимостей для тяжелых библиотек
packages = ['aiogram', 'requests', 'certifi', 'PIL', 'duckduckgo_search', 'customtkinter']

for package in packages:
    tmp_ret = collect_all(package)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# Если используешь PyArmor, оставляем эту часть
try:
    tmp_ret = collect_all('pyarmor_runtime_000000')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
except:
    pass

a = Analysis(
    ['velox_miner.py'],
    pathex=[],
    binaries=binaries,
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
    a.binaries,
    a.datas,
    [],
    name='VELOX VPN',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Окно консоли будет скрыто
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True, # Запуск от имени администратора (нужно для VPN)
    icon=['VELOX.ico'],
)