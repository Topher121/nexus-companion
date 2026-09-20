"""Windows entry point, single-instance guard, and isolated packaged self-check."""
import bootstrap
import ctypes
import json
import sys
import traceback
from pathlib import Path

def self_test(destination):
    import asyncio
    import tempfile
    import tkinter as tk
    from PIL import Image
    import cv2
    import numpy
    from windows_capture import WindowsCapture
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.globalization import Language
    from history import HistoryStore,protocol_for
    from build_library import PROFILES,BUILD_COUNT
    from content_validation import validate_catalogue
    from build_library import CATALOGUE
    from preview_ui import Preview
    from vision import ocr
    validate_catalogue(CATALOGUE)
    root=tk.Tk();root.withdraw();app=Preview(root);root.update_idletasks()
    assert len(app.tabs.tabs())==6
    assert OcrEngine.try_create_from_language(Language('en-US')) is not None
    asyncio.run(ocr(Image.new('RGB',(200,80),'white')))
    assert protocol_for().__name__.startswith('nexus_protocol')
    with tempfile.TemporaryDirectory() as folder:
        store=HistoryStore(Path(folder)/'test.sqlite3');assert store.records('test')==[]
    root.destroy()
    Path(destination).write_text(json.dumps({'ok':True,'heroes':len(PROFILES),'builds':BUILD_COUNT,'checks':['UI and portraits','Windows OCR','capture imports','replay protocols','SQLite','build validation']}),encoding='utf-8')

def main():
    if '--self-test' in sys.argv:
        destination=sys.argv[sys.argv.index('--self-test')+1]
        try:self_test(destination)
        except Exception:
            Path(destination).write_text(json.dumps({'ok':False,'error':traceback.format_exc()}),encoding='utf-8');raise
        return
    from app_paths import DATA_DIR
    user=ctypes.windll.kernel32
    user.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]
    user.CreateMutexW.restype=ctypes.c_void_p
    mutex=user.CreateMutexW(None,False,'NexusCompanionApp')
    if user.GetLastError()==183:
        ctypes.windll.user32.MessageBoxW(None,'Nexus Companion is already running. Open its existing window.','Nexus Companion',0x40);return
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError,OSError):pass
    import tkinter as tk
    from tkinter import messagebox
    from app import Companion
    root=tk.Tk()
    def report_error(kind,value,tb):
        detail=''.join(traceback.format_exception(kind,value,tb))
        try:(DATA_DIR/'last-error.log').write_text(detail,encoding='utf-8')
        except OSError:pass
        messagebox.showerror('Nexus Companion',str(value)+'\n\nDetails saved in your data folder.',parent=root)
    root.report_callback_exception=report_error
    Companion(root);root.mainloop()

if __name__=='__main__':main()
