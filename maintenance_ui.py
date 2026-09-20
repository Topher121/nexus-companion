"""Backup and update controls. Downloads stay separate from personal records."""
from datetime import datetime
import queue
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
import os
import webbrowser

from app_paths import APP_VERSION,DATA_DIR
from ui_theme import BLUE,MUTED,ScrollPage
from updates import DEFAULT_FEED,CONTENT_VERSION,current_content_version,check_updates,download_installer,install_builds
from backup import create_backup,read_backup,restore_backup

class MaintenanceFeatures:
    def make_maintenance(self):
        self.maintenance_events=queue.Queue();self.update_busy=False;self.update_result=None
        self.maintenance_page=ScrollPage(self.tabs);page=self.maintenance_page.body
        self.tabs.add(self.maintenance_page,text='  Settings & backups',image=self.art.icon('collection',24),compound='left')
        ttk.Label(page,text='Keep your companion up to date',font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(page,text=f'App {APP_VERSION} · Saved builds {current_content_version()}',foreground=BLUE).pack(anchor='w',pady=(8,14))
        ttk.Label(page,text='Updates',font=('Segoe UI',14,'bold')).pack(anchor='w')
        self.auto_update_checks=tk.BooleanVar(value=self.settings.get('auto_update_checks',True))
        ttk.Checkbutton(page,text='Check for app and build updates automatically',variable=self.auto_update_checks,command=self.update_setting_changed).pack(anchor='w',pady=(8,4))
        ttk.Label(page,text='Checks on launch and daily while open. You choose when to download or install. Nothing restarts during a game.',foreground=MUTED,wraplength=850).pack(anchor='w')
        row=ttk.Frame(page);row.pack(fill='x',pady=12)
        self.update_check_button=ttk.Button(row,text='Check for updates',command=self.start_update_check);self.update_check_button.pack(side='left')
        self.update_app_button=ttk.Button(row,text='Download app update',command=lambda:self.start_update_download('app'),state='disabled');self.update_app_button.pack(side='left',padx=8)
        self.update_build_button=ttk.Button(row,text='Update saved builds',command=lambda:self.start_update_download('builds'),state='disabled');self.update_build_button.pack(side='left')
        ttk.Button(row,text='View releases',command=lambda:webbrowser.open('https://github.com/Topher121/nexus-companion/releases')).pack(side='left',padx=8)
        self.update_status=ttk.Label(page,text='Ready to check GitHub releases. Your match history, collection and screenshots are never sent.',foreground=MUTED,wraplength=850,justify='left')
        self.update_status.pack(anchor='w',pady=(0,16))
        ttk.Separator(page).pack(fill='x',pady=10)
        ttk.Label(page,text='Back up or move your data',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(8,6))
        ttk.Label(page,text='Save your favourites, excluded heroes, owned collection, settings and complete match history in one file.\nReplays and app files are not included. Keep backups somewhere safe: they contain your player name and local folder paths.',foreground=MUTED,wraplength=850,justify='left').pack(anchor='w')
        row=ttk.Frame(page);row.pack(fill='x',pady=12)
        ttk.Button(row,text='Export backup…',command=self.export_backup).pack(side='left')
        ttk.Button(row,text='Restore backup…',command=self.import_backup).pack(side='left',padx=8)
        ttk.Button(row,text='Open data folder',command=lambda:os.startfile(DATA_DIR)).pack(side='left')
        self.backup_status=ttk.Label(page,text='Restore replaces your current data. A safety backup is made first, and the app closes after a successful restore.',foreground=MUTED,wraplength=850,justify='left')
        self.backup_status.pack(anchor='w')
        ttk.Label(page,text='Personal data folder: '+str(DATA_DIR),foreground=MUTED,wraplength=850).pack(anchor='w',pady=(20,0))
        page.bind('<Configure>',lambda e:[w.configure(wraplength=max(240,e.width-32)) for w in page.winfo_children() if isinstance(w,ttk.Label) and int(float(w.cget('wraplength') or 0))>0])
        self.root.after(250,self.poll_maintenance)
        self.root.after(2500,self.update_tick)

    def update_setting_changed(self):
        self.settings['auto_update_checks']=self.auto_update_checks.get();self.save_settings()
        if self.auto_update_checks.get():self.start_update_check()

    def update_tick(self):
        if self.auto_update_checks.get():self.start_update_check()
        self.root.after(24*60*60*1000,self.update_tick)

    def start_update_check(self):
        if self.update_busy or getattr(self,'maintenance_restoring',False):return
        self.update_busy=True;self.update_result=None
        self.update_check_button.configure(state='disabled')
        self.update_app_button.configure(text='Download app update',command=lambda:self.start_update_download('app'))
        self.update_app_button.configure(state='disabled');self.update_build_button.configure(state='disabled')
        self.update_status.config(text='Checking app and saved-build releases…')
        def work():
            try:self.maintenance_events.put(('check',check_updates(),None))
            except Exception as exc:self.maintenance_events.put(('check',None,str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def start_update_download(self,kind):
        if self.update_busy or not self.update_result:return
        item=dict(self.update_result['manifest'][kind]);self.update_busy=True
        self.update_check_button.configure(state='disabled')
        self.update_app_button.configure(state='disabled');self.update_build_button.configure(state='disabled')
        self.update_status.config(text='Downloading and verifying '+('the installer…' if kind=='app' else 'saved builds…'))
        def work():
            try:
                result=download_installer(item) if kind=='app' else install_builds(item)
                self.maintenance_events.put((kind,result,None))
            except Exception as exc:self.maintenance_events.put((kind,None,str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def poll_maintenance(self):
        try:
            while True:
                kind,value,error=self.maintenance_events.get_nowait()
                self.update_busy=False;self.update_check_button.configure(state='normal')
                if error:
                    self.update_status.config(text=('No published release is accessible yet. The app and saved builds remain available.' if '404' in error else 'Could not complete the update: '+error)+' You can try Check for updates again.')
                    continue
                if kind=='check':
                    self.update_result=value;parts=[]
                    if value['app_new']:
                        parts.append('App '+value['manifest']['app']['version']+' is available.')
                        self.update_app_button.configure(state='normal')
                    else:parts.append('App is up to date.')
                    if value['builds_new']:
                        parts.append('New saved builds are available.' if value['builds_compatible'] else 'New builds require an app update first.')
                        if value['builds_compatible']:self.update_build_button.configure(state='normal')
                    else:parts.append('Saved builds are up to date.')
                    self.update_status.config(text=' '.join(parts)+f' Checked {datetime.now():%d %b %H:%M}.')
                elif kind=='builds':
                    self.update_status.config(text='Saved builds updated and verified. Close and reopen Nexus Companion when convenient to use them.')
                else:
                    self.downloaded_installer=value
                    self.update_status.config(text='Installer downloaded and verified. Open it when you are ready; your personal data will be kept.')
                    self.update_app_button.configure(text='Open downloaded installer',state='normal',command=self.open_downloaded_installer)
        except queue.Empty:pass
        self.root.after(250,self.poll_maintenance)

    def open_downloaded_installer(self):
        # No shell arguments, silent installation or automatic interruption.
        try:os.startfile(self.downloaded_installer)
        except OSError as exc:messagebox.showerror('Could not open installer',str(exc),parent=self.root)

    def export_backup(self):
        destination=filedialog.asksaveasfilename(parent=self.root,title='Save Nexus Companion backup',defaultextension='.nexus-backup',initialfile=f'Nexus-Backup-{datetime.now():%Y-%m-%d}.nexus-backup',filetypes=[('Nexus Companion backup','*.nexus-backup')])
        if not destination:return
        try:
            create_backup(destination,DATA_DIR)
            self.backup_status.config(text='Backup saved: '+destination)
        except Exception as exc:messagebox.showerror('Backup not saved',str(exc),parent=self.root)

    def import_backup(self):
        source=filedialog.askopenfilename(parent=self.root,title='Choose a Nexus Companion backup',filetypes=[('Nexus Companion backup','*.nexus-backup')])
        if not source:return
        try:
            manifest,payload=read_backup(source)
            if 'match-history.sqlite3' not in payload:raise ValueError('This backup does not contain match history.')
        except Exception as exc:
            messagebox.showerror('Backup cannot be restored',str(exc),parent=self.root);return
        if self.history_busy or self.busy or self.update_busy or getattr(self,'rotation_busy',False) or self.watch:
            messagebox.showinfo('Finish the current check first','Wait for the current scan or download, stop live draft reading, then restore again.',parent=self.root);return
        self.maintenance_restoring=True
        if not messagebox.askyesno('Replace current personal data?',f"Backup created: {manifest['created']}\n\nThis replaces your preferences, collection, settings and match history. A safety backup of your current data will be saved first. Nexus Companion will close afterwards.\n\nRestore this backup?",parent=self.root):
            self.maintenance_restoring=False;return
        try:
            safety=restore_backup(source,DATA_DIR)
        except Exception as exc:
            self.maintenance_restoring=False
            messagebox.showerror('Restore failed',str(exc),parent=self.root);return
        messagebox.showinfo('Backup restored','Reopen Nexus Companion to load your restored data.\n\nSafety backup: '+str(safety),parent=self.root)
        self.close_app()
