# -*- mode: python ; coding: utf-8 -*-

# We need to add the flasher stub JSON files explicitly: https://github.com/espressif/esptool/issues/1059
local_stub_flasher_path = "./.venv/Lib/site-packages/esptool/targets/stub_flasher"

a = Analysis(
    ['nodemcu-pyflasher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ("images", "images"),
        ("{}/1".format(local_stub_flasher_path), "./esptool/targets/stub_flasher/1"),
        ("{}/2".format(local_stub_flasher_path), "./esptool/targets/stub_flasher/2")
    ],
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
    a.binaries,
    a.datas,
    [],
    name='NodeMCU-PyFlasher',
    version='windows-version-info.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='images\\icon-256.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
