# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['nodemcu-pyflasher.py'],
    pathex=[],
    binaries=[],
    datas=[("images", "images")],
    hiddenimports=[],
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
    name='NodeMCU PyFlasher',
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
    name='NodeMCU PyFlasher',
    icon='images/icon-256.icns'
)
app = BUNDLE(
    coll,
    name='NodeMCU PyFlasher.app',
    version='5.1.0',
    icon='images/icon-256.icns',
    bundle_identifier='com.frightanic.nodemcu-pyflasher')
