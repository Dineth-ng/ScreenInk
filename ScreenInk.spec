# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('screenink/assets', 'screenink/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml', 'PySide6.QtQuick'],
    noarchive=False,
    optimize=0,
)
# QtGui's broad plugin discovery can pull in PDF/VirtualKeyboard and their QML
# dependencies. This Widgets application deliberately ships only needed plugins.
allowed_qt = {'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Network.dll', 'Qt6OpenGL.dll',
              'Qt6Svg.dll', 'Qt6Widgets.dll'}
def wanted_binary(entry):
    name = entry[0].replace('\\', '/')
    leaf = name.rsplit('/', 1)[-1]
    if leaf.startswith('Qt6') and leaf.endswith('.dll'):
        return leaf in allowed_qt
    if '/plugins/' in name:
        category = name.split('/plugins/', 1)[1].split('/')[0]
        return category in {'platforms', 'styles', 'imageformats', 'iconengines', 'tls', 'networkinformation'} and leaf != 'qpdf.dll'
    return True
a.binaries = [entry for entry in a.binaries if wanted_binary(entry)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScreenInk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='packaging/windows-version.txt',
    icon=['screenink/assets/screenink.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ScreenInk',
)
