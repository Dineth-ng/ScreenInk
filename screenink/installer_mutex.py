"""Let Inno Setup safely refuse updates/uninstall while ScreenInk runs."""
import ctypes
import sys


def create_mutex():
    if sys.platform != 'win32':
        return None
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]
    kernel.CreateMutexW.restype=ctypes.c_void_p
    handle=kernel.CreateMutexW(None,False,'Local\\ScreenInk.Desktop.Running')
    if not handle:
        raise OSError('Cannot create the installer safety mutex.')
    # Windows closes this handle at process exit, after Qt has finished shutdown.
    return handle
