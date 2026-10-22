"""Developer-machine installer checks in an isolated, verified workspace path."""
import ctypes,json,os,subprocess,sys,uuid,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from screenink.version import __version__
from screenink.installer_mutex import create_mutex
from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage,QColor

def main():
    uninstall_key=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{940AC59A-791E-4D6C-94E9-76303DB5D734}_is1'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,uninstall_key):
            raise SystemExit('An installed ScreenInk exists; skip automated installer test to preserve it.')
    except FileNotFoundError:pass
    target=(ROOT/'build'/('installer-test-'+uuid.uuid4().hex[:8])).resolve()
    assert target.is_relative_to((ROOT/'build').resolve())
    target.mkdir()
    setup=ROOT/'release'/f'ScreenInk-Setup-{__version__}.exe'
    args=[str(setup),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',f'/DIR={target}','/GROUP=ScreenInk Candidate Validation','/TASKS=']
    subprocess.run(args,check=True,timeout=90)
    assert (target/'ScreenInk.exe').is_file()
    link=Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/ScreenInk Candidate Validation/ScreenInk.lnk'
    assert link.exists()
    env=os.environ.copy();env['PATH']=r'C:\Windows\System32;C:\Windows'
    for key in ('PYTHONHOME','PYTHONPATH','QT_PLUGIN_PATH','QML2_IMPORT_PATH'):env.pop(key,None)
    for _ in range(2):subprocess.run([str(target/'ScreenInk.exe'),'--smoke-test'],env=env,cwd=target,check=True,timeout=30)
    screenshot=target/'user-created.png';image=QImage(10,10,QImage.Format.Format_ARGB32);image.fill(QColor('green'));assert image.save(str(screenshot))
    store=QSettings('ScreenInk','ScreenInk');key='validation/'+uuid.uuid4().hex;store.setValue(key,'preserve');store.sync()
    handle=create_mutex()
    kernel=ctypes.WinDLL('kernel32');kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    try:
        update=subprocess.run(args,timeout=30)
        uninstall=subprocess.run([str(target/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],timeout=30)
        assert update.returncode!=0 and uninstall.returncode!=0
        assert (target/'ScreenInk.exe').exists()
    finally:kernel.CloseHandle(handle)
    subprocess.run(args,check=True,timeout=90)
    subprocess.run([str(target/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=90)
    assert not (target/'ScreenInk.exe').exists()
    assert not link.exists()
    assert screenshot.exists()
    assert store.value(key)=='preserve'
    store.remove(key);store.sync()
    result={'install':True,'start_menu':True,'reopen_smoke_twice':True,'mutex_blocks_update_uninstall':True,'update_after_exit':True,'uninstall':True,'screenshot_preserved':True,'settings_preserved':True,'test_directory':str(target),'clean_machine':False}
    (ROOT/'docs/INSTALLER_TEST.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
