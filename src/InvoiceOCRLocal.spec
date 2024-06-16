# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Path to the tesseract binary
tesseract_bin = os.path.join('tesseract', 'tesseract.exe')

# List of additional files to be included (adjust paths as necessary)
tesseract_dependencies = [
    (os.path.join('tesseract', 'tesseract.exe'), 'tesseract'),
    (os.path.join('tesseract', 'tessdata'), 'tessdata'),
]

a = Analysis(
    ['InvoiceOCRLocal.py'],
    pathex=[],
    binaries=tesseract_dependencies,
    datas=[],
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
    name='InvoiceOCRLocal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
