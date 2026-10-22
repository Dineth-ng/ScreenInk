# Installation and exact build commands

Target: Windows 11 x64. Local 1.0.0 is a release candidate, not a published release.
Installer: release/ScreenInk-Setup-1.0.0.exe. Portable: extract the entire ZIP and
run ScreenInk/ScreenInk.exe, preserving _internal and adjacent runtime DLLs.
The installer installs for the current user without administrator privileges.
Desktop shortcut is optional; Start Menu and uninstall entry are included.
Exit ScreenInk from the tray before update/uninstall. Unsaved annotations are
not restored after exit. Settings and user screenshots survive uninstall.
Windows startup is off by default; opt in through Preferences and Apply.

## Build on Windows x64

Install official Python 3.14.6 x64. In PowerShell, from the repository root:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\python.exe tools\build_beta.py
powershell -ExecutionPolicy Bypass -File tools\setup_inno.ps1
.\.venv\Scripts\python.exe tools\build_installer.py --iscc build\tools\InnoSetup\ISCC.exe
Get-FileHash release\ScreenInk-Setup-1.0.0.exe -Algorithm SHA256
```

The historical build_beta.py filename is retained for compatibility. It uses the
maintained ScreenInk.spec, pinned requirements, source version, bundled license
texts, and one-folder layout. Output: dist/ScreenInk/ScreenInk.exe and portable ZIP
plus checksum in release/. No one-file build is produced. Reproducible procedure
means consistent inputs/layout, not byte-identical signed/timestamped artifacts.
The installer script also emits a SHA-256 file. Normal launches have no console.

Run from source: `.\.venv\Scripts\python.exe main.py`.
Installer compiler is downloaded only from official GitHub and checked by SHA-256
and Windows Authenticode before execution. Application startup never downloads it.
