# Third-party software and redistribution review

ScreenInk code and repository-native SVG/icons: MIT (see LICENSE).
Python 3.14.6: PSF license; Qt 6.12 / PySide6 Essentials / Shiboken6: LGPLv3
or other upstream licensing alternatives. PyInstaller bootloader: GPL with the
bootloader distribution exception. Inno Setup: its own license. Microsoft runtime
DLLs retain Microsoft's redistribution terms; they are supplied with Python.

The one-folder package uses dynamically loaded Qt DLLs. Recipients may replace
compatible Qt/PySide libraries and debug modifications; ScreenInk imposes no
restriction on reverse engineering for that purpose. Rebuild instructions and
application source are in the project repository. Do not remove dependency notices.

License texts from installed distributions and version-tagged upstream Qt sources
are bundled under licenses/. licenses/SOURCES.json records the retrieved URLs.
Some Qt modules are GPL-only: this application uses Core, Gui, Widgets, Network
and SVG, excludes QML/Quick/WebEngine and does not use GPL-only application APIs.
Qt's third-party components can have additional attribution requirements.

Upstream source and guidance:
- https://download.qt.io/archive/qt/6.12/6.12.0/submodules/
- https://code.qt.io/cgit/pyside/pyside-setup.git/
- https://github.com/qt/qtbase/tree/v6.12.0
- https://github.com/qt/qtsvg/tree/v6.12.0
- https://github.com/qt/qtimageformats/tree/v6.12.0
- https://doc.qt.io/qtforpython-6/licenses.html
- https://www.qt.io/development/open-source-lgpl-obligations
- https://pyinstaller.org/en/stable/license.html
- https://jrsoftware.org/isdl.php

Release gate: verify that the final binary dependency inventory matches notices,
include the corresponding Qt third-party attribution/source materials required by
the chosen LGPL distribution method, and retain access to matching dependency
sources. Collected license texts alone are not a legal compliance certification.
No third-party visual assets are used. The local build is an unsigned candidate;
public release approval and final redistribution review are still required.

Final local Qt DLL inventory: Core, Gui, Network, OpenGL, Svg, Widgets. PyInstaller
initially pulled in PDF, QML, Quick and VirtualKeyboard transitively; the maintained
spec now filters those libraries and unused plugins out. Inno Setup compiler
reports non-commercial mode; assess a commercial license before commercial use.
