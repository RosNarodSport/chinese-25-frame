# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

pyqt_datas, pyqt_binaries, pyqt_hiddenimports = collect_all('PyQt5')

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=pyqt_binaries,
    datas=[
        (os.path.join(ROOT, 'views', 'main_window.ui'), 'views'),
        (os.path.join(ROOT, 'templates', 'word_list_template.xlsx'), 'templates'),
        (os.path.join(ROOT, 'favicon.ico'), '.'),
    ] + pyqt_datas,
    hiddenimports=['data.hieroglyphs'] + pyqt_hiddenimports,
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
    name='Reading25',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, 'favicon.ico'),
)
