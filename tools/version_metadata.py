"""Generate Windows version resource from the application version."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from screenink.version import __version__


def generate():
    numbers=tuple(map(int,__version__.split('.'))) + (0,)
    text=f"""VSVersionInfo(
ffi=FixedFileInfo(filevers={numbers},prodvers={numbers},mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),
kids=[StringFileInfo([StringTable('040904B0',[
StringStruct('FileDescription','ScreenInk screen annotation'),
StringStruct('FileVersion','{__version__}'),
StringStruct('ProductVersion','{__version__}'),
StringStruct('ProductName','ScreenInk'),
StringStruct('OriginalFilename','ScreenInk.exe')])]),
VarFileInfo([VarStruct('Translation',[1033,1200])])])
"""
    (ROOT/'packaging/windows-version.txt').write_text(text,encoding='utf-8')

if __name__=='__main__':generate()
