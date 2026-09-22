"""Temporary visual QA window. Services and saving are disabled."""
import ctypes
import sys
import tkinter as tk
from app import Companion

class Preview(Companion):
    def update_tick(self): pass
    def start_rotation(self): pass
    def history_tick(self): pass
    def start_history_scan(self,force=False): pass
    def save_settings(self): pass
    def set_pref(self,mode): pass
    def mark_owned(self,value): pass
    def exclude_history(self,value): pass
    def manual_result(self): pass
    def import_collection(self): pass
    def exporter_setup(self): pass
    def toggle_watch(self): pass

if __name__=='__main__':
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (OSError,AttributeError):pass
    root=tk.Tk();app=Preview(root)
    root.title('Nexus Forge — design preview')
    app.map.set('Infernal Shrines')
    for var,hero in zip(app.allies,['','Malfurion','Samuro','Gazlowe',"Gul'dan"]):var.set(hero)
    for var,hero in zip(app.enemies,['Abathur',"Zul'jin",'Zarya','Diablo','Rehgar']):var.set(hero)
    app.self_slot.set('1');app.refresh()
    if '--build' in sys.argv:
        hero=sys.argv[sys.argv.index('--build')+1]
        app.playing.set(hero);app.manual_selection(app.playing);app.tabs.select(app.build)
    if '--compact' in sys.argv:root.geometry('980x700')
    root.mainloop()
