"""Measure synthetic Windows Qt workloads; no screen pixels are captured."""
import ctypes,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QPointF,QTimer
from PySide6.QtGui import QColor,QPixmap
from PySide6.QtWidgets import QApplication,QSystemTrayIcon
from screenink.drawing import DrawingCanvas
from screenink.branding import application_icon

class Counters(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('peak_working','working','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile')]

def rss():
    kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=ctypes.c_void_p
    psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    c=Counters();c.cb=ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):raise ctypes.WinError()
    return round(c.working/1048576,2)

def main():
    app=QApplication([]);app.setQuitOnLastWindowClosed(False)
    screenshot=QPixmap(1920,1080);screenshot.fill(QColor('#27352e'))
    canvas=DrawingCanvas(screenshot);canvas.resize(1280,720)
    tray=QSystemTrayIcon(application_icon());tray.show()
    results=[]
    for mode in ('idle_tray','freeze','live','continuous_drawing','magnifier'):
        canvas.controller.clear();canvas.live=mode=='live';canvas.magnifier.enabled=mode=='magnifier'
        canvas.setVisible(mode!='idle_tray');app.processEvents()
        ticks=[0]
        def draw():
            i=ticks[0];ticks[0]+=1
            point=QPointF(20+(i%400)*3,350+100*math.sin(i/20))
            if i%400==0:canvas.controller.press(point)
            canvas.controller.move(point)
            if i%400==399:canvas.controller.release(point)
        timer=QTimer();timer.timeout.connect(draw)
        if mode=='continuous_drawing':timer.start(8)
        started=time.perf_counter();cpu=time.process_time();before=rss()
        QTimer.singleShot(3000,app.quit);app.exec()
        seconds=time.perf_counter()-started
        results.append(dict(mode=mode,seconds=round(seconds,3),cpu_one_core_percent=round(100*(time.process_time()-cpu)/seconds,2),rss_before_mib=before,rss_after_mib=rss(),input_samples=ticks[0]))
        timer.stop();canvas.controller.finish_pending()
    tray.hide();canvas.close()
    report={'platform':sys.platform,'qt_platform':app.platformName(),'screens':[{'geometry':[s.geometry().x(),s.geometry().y(),s.geometry().width(),s.geometry().height()],'dpr':s.devicePixelRatio()} for s in app.screens()], 'workload':'Synthetic pixels; 1280x720 canvas, 3 seconds each, idle magnifier; process CPU normalized to one core. No before/after optimization claim.', 'results':results}
    (ROOT/'docs/PERFORMANCE.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
