"""Opt-in current-user Windows startup registration; never needs elevation."""
import sys
import subprocess
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def set_startup(enabled):
    if sys.platform != 'win32':
        if enabled:
            raise OSError('Launch at startup is supported on Windows only.')
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            if getattr(sys, 'frozen', False):
                args = [sys.executable, '--startup']
            else:
                executable = Path(sys.executable).with_name('pythonw.exe')
                args = [str(executable), str(Path(__file__).resolve().parents[1] / 'main.py'), '--startup']
            winreg.SetValueEx(key, 'ScreenInk', 0, winreg.REG_SZ, subprocess.list2cmdline(args))
        else:
            try:
                winreg.DeleteValue(key, 'ScreenInk')
            except FileNotFoundError:
                pass
