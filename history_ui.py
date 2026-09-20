"""Match-history page and a background watcher independent of draft capture."""
from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from data import HEROES, MAPS
from history import HistoryStore, hero_stats, replay_folders, profile_from_path, scan_replays, MODES, personal_record_label
from ui_theme import BG, TEXT, BLUE, MUTED, GREEN, RED, PURPLE, metric, stripe, ScrollPage, empty_table


class HistoryFeatures:
    def make_history(self):
        from features import interfaces_folder
        self.history_stop = threading.Event()
        self.history_events = queue.Queue()
        self.history_busy = False
        self.history_failed = {}
        self.history_errors = []
        self.history_checked = False
        self.history_store = None
        try:
            self.history_store = HistoryStore()
            storage_error = ''
        except Exception as exc:
            storage_error = 'Match history could not be opened: ' + str(exc)
        folders = replay_folders(interfaces_folder().parent / 'Accounts')
        folder = self.settings.get('replay_folder', '')
        if not folder and len(folders) == 1:
            folder = str(folders[0])
        self.replay_folder = tk.StringVar(value=folder)
        self.auto_results = tk.BooleanVar(value=self.settings.get('auto_results', True))
        self.history_hero = tk.StringVar(value='All heroes')
        self.history_mode = tk.StringVar(value='All modes')
        self.history_period = tk.StringVar(value='All time')
        minimum=str(self.settings.get('history_min_games',0))
        self.history_min_games=tk.StringVar(value=minimum if minimum in ('0','5','10','20','50','100') else '0')
        self.show_excluded = tk.BooleanVar(value=False)
        self.history_sort = {'heroes':('games',True),'matches':('date',True)}
        self.history_sort_labels = {}
        self.history_trees = {}
        self.history_container = ScrollPage(self.tabs)
        self.history_page = self.history_container.body
        self.tabs.add(self.history_container, text='  Match history',image=self.art.icon('history',24),compound='left')
        page = self.history_page
        row = ttk.Frame(page); row.pack(fill='x')
        ttk.Label(row, text='Your match history', font=('Segoe UI',20,'bold')).pack(side='left')
        ttk.Checkbutton(row, text='Automatically log completed games', variable=self.auto_results,
                        command=self.history_settings_changed).pack(side='right')
        ttk.Label(page, text='Wins, losses and win rate from your saved replays. New results appear after the game saves its replay.',
                  foreground=MUTED, wraplength=1080).pack(anchor='w', pady=(6,8))
        row = ttk.Frame(page)
        self.replay_settings_row=row
        ttk.Label(row, text='Replay folder').pack(side='left', padx=(0,8))
        folder_box = ttk.Combobox(row, textvariable=self.replay_folder, values=[str(p) for p in folders], state='readonly')
        folder_box.pack(side='left', fill='x', expand=True)
        folder_box.bind('<<ComboboxSelected>>', lambda e:self.history_folder_changed())
        ttk.Button(row, text='Choose folder', command=self.choose_replay_folder).pack(side='left', padx=(8,0))
        self.history_status = ttk.Label(page, text=storage_error or 'Ready to read your saved results.', wraplength=1080, foreground=MUTED)
        self.history_status.pack(anchor='w', pady=8)
        row = ttk.Frame(page); row.pack(fill='x', pady=(0,8))
        self.history_filter_row=row
        for label, variable, values, width in (
                ('Hero',self.history_hero,['All heroes']+sorted(HEROES),20),
                ('Mode',self.history_mode,['All modes']+MODES,16),
                ('Period',self.history_period,['All time','Last 30 days','Last 7 days'],13)):
            ttk.Label(row,text=label).pack(side='left',padx=(0,6))
            box = ttk.Combobox(row,textvariable=variable,values=values,state='readonly',width=width)
            box.pack(side='left',padx=(0,14));box.bind('<<ComboboxSelected>>',lambda e:self.refresh_history())
        self.log_result_button=ttk.Button(row, text='Log result',image=self.art.icon('plus'),compound='left',command=self.manual_result)
        self.log_result_button.pack(side='right')
        ttk.Button(row,text='Reset filters',command=self.reset_history_filters).pack(side='right',padx=(0,8))
        self.history_summary = ttk.Label(page, text='', foreground=MUTED)
        metrics=ttk.Frame(page);metrics.pack(fill='x',pady=(0,12))
        self.history_metrics=[]
        for i,(icon,label,color) in enumerate([('history','MATCHES PLAYED',TEXT),('trophy','VICTORIES',GREEN),('loss','DEFEATS',RED),('target','WIN RATE',PURPLE)]):
            card,value=metric(metrics,self.art.icon(icon,24),label,color)
            card.grid(row=0,column=i,sticky='ew',padx=(0,10 if i<3 else 0));metrics.columnconfigure(i,weight=1,uniform='metrics')
            self.history_metrics.append(value)
        tables = ttk.Frame(page); tables.pack(fill='both',expand=True)
        stats_frame = ttk.Frame(tables); recent_frame = ttk.Frame(tables)
        stats_frame.grid(row=0,column=0,sticky='nsew',pady=(0,12));recent_frame.grid(row=1,column=0,sticky='nsew')
        tables.columnconfigure(0,weight=1)
        tables.rowconfigure(0,weight=1,uniform='history_tables');tables.rowconfigure(1,weight=1,uniform='history_tables')
        stats_heading=ttk.Frame(stats_frame);stats_heading.pack(fill='x',pady=(0,4))
        ttk.Label(stats_heading,text='BY HERO · click headings to sort; click a hero to filter matches',foreground=BLUE).pack(side='left')
        minimum=ttk.Combobox(stats_heading,textvariable=self.history_min_games,values=['0','5','10','20','50','100'],state='readonly',width=5)
        minimum.pack(side='right');minimum.bind('<<ComboboxSelected>>',lambda e:self.minimum_games_changed())
        ttk.Label(stats_heading,text='Minimum games',foreground=MUTED).pack(side='right',padx=(8,6))
        self.minimum_games_note=ttk.Label(stats_frame,text='',foreground=MUTED)
        self.minimum_games_note.pack(anchor='w',pady=(0,4))
        self.hero_stats_tree = self.history_table(stats_frame,
            [('hero','Hero',220),('games','Played',90),('wins','Wins',90),('losses','Losses',90),('rate','Win rate',100)],height=2,kind='heroes')
        self.hero_stats_tree.bind('<<TreeviewSelect>>', self.select_history_hero)
        ttk.Label(recent_frame,text='MATCHES · click a heading to sort',foreground=BLUE).pack(anchor='w',pady=(8,4))
        self.matches_tree = self.history_table(recent_frame,
            [('date','Date / time',160),('hero','Hero',145),('result','Result',135),('map','Battleground',185),
             ('mode','Mode',125),('source','Logged by',90)],height=2,kind='matches')
        for tree in (self.hero_stats_tree,self.matches_tree):
            tree.tag_configure('win',foreground='#92dfb1')
            tree.tag_configure('loss',foreground='#f3a5a5')
            tree.tag_configure('excluded',foreground='#8993a5')
        row = ttk.Frame(page);row.pack(side='bottom',fill='x',pady=(8,0),before=tables)
        self.scan_button = ttk.Button(row, text='Scan now', command=lambda:self.start_history_scan(force=True))
        self.scan_button.pack(side='right')
        ttk.Button(row,text='Replay settings',command=self.toggle_replay_settings).pack(side='right',padx=8)
        self.exclude_button=ttk.Button(row,text='Exclude selected',command=lambda:self.exclude_history(True),state='disabled');self.exclude_button.pack(side='left')
        self.restore_button=ttk.Button(row,text='Restore selected',command=lambda:self.exclude_history(False),state='disabled');self.restore_button.pack(side='left',padx=8)
        self.matches_tree.bind('<<TreeviewSelect>>',lambda e:self.history_selection_changed())
        ttk.Checkbutton(row,text='Show excluded',variable=self.show_excluded,command=self.refresh_history).pack(side='left')
        ttk.Button(row,text='Import details',command=self.history_import_details).pack(side='right',padx=(0,8))
        ttk.Label(page,text='Only saved games for this account are counted. Excluded games stay excluded after rescanning. Small samples can be misleading.',
                  foreground=MUTED,wraplength=1080).pack(side='bottom',anchor='w',pady=(8,0),before=tables)
        if storage_error:
            self.scan_button.configure(state='disabled')
            self.log_result_button.configure(state='disabled')
        page.bind('<Configure>',lambda e:self.history_status.configure(wraplength=max(240,e.width-32)))
        self.refresh_history()
        self.history_poll_timer = self.root.after(250,self.poll_history)
        self.history_scan_timer = self.root.after(1200,self.history_tick)

    def history_table(self,parent,columns,height,kind):
        frame = ttk.Frame(parent);frame.pack(fill='both',expand=True)
        tree = ttk.Treeview(frame,columns=[c[0] for c in columns],show='tree headings',height=height,selectmode='extended',style='Roster.Treeview')
        tree.column('#0',width=38,minwidth=38,stretch=False);tree.heading('#0',text='')
        for key,label,width in columns:
            anchor='center' if key in ('games','wins','losses','rate') else 'w'
            minimum={'date':140,'hero':115,'result':120,'map':140,'mode':95,'source':70}.get(key,65)
            tree.heading(key,text=label,anchor=anchor,command=lambda column=key:self.sort_history(kind,column))
            tree.column(key,width=width,minwidth=minimum,anchor=anchor)
        scroll = ttk.Scrollbar(frame,command=tree.yview);scroll.pack(side='right',fill='y')
        tree.configure(yscrollcommand=scroll.set);tree.pack(fill='both',expand=True)
        self.history_trees[kind]=tree
        self.history_sort_labels[kind]={key:label for key,label,_ in columns}
        self.update_history_sort_heading(kind)
        return tree

    def update_history_sort_heading(self,kind):
        column,descending=self.history_sort[kind]
        for key,label in self.history_sort_labels[kind].items():
            arrow=(' ▼' if descending else ' ▲') if key==column else ''
            self.history_trees[kind].heading(key,text=label+arrow)

    def sort_history(self,kind,column):
        previous,descending=self.history_sort[kind]
        # New numeric/date columns start highest/newest first; names start A–Z.
        descending=not descending if column==previous else column in ('games','wins','losses','rate','date')
        self.history_sort[kind]=(column,descending)
        self.update_history_sort_heading(kind)
        self.refresh_history()
        self.history_trees[kind].yview_moveto(0)

    def sorted_history_rows(self,kind,rows):
        column,descending=self.history_sort[kind]
        if kind=='heroes':
            # Sort actual counts/rates, not their displayed strings. Hero name is
            # a predictable tie-break in either numeric direction.
            rows=sorted(rows,key=lambda row:row['hero'].casefold())
            key=(lambda row:row['hero'].casefold()) if column=='hero' else (lambda row:row[column])
        else:
            # Keep equally named/result rows newest first. Parse timestamps so
            # dates spanning months/years never sort as their formatted labels.
            rows=sorted(rows,key=lambda row:datetime.fromisoformat(row['played_at']),reverse=True)
            key=(lambda row:datetime.fromisoformat(row['played_at'])) if column=='date' else (lambda row:row[column].casefold())
        return sorted(rows,key=key,reverse=descending)

    def reset_history_filters(self):
        self.history_hero.set('All heroes');self.history_mode.set('All modes');self.history_period.set('All time')
        self.history_min_games.set('0');self.show_excluded.set(False);self.minimum_games_changed()

    def minimum_games_changed(self):
        self.settings['history_min_games']=int(self.history_min_games.get())
        self.save_settings();self.refresh_history()

    def history_selection_changed(self):
        selected=self.matches_tree.selection()
        excluded=[('excluded' in self.matches_tree.item(row,'tags')) for row in selected]
        self.exclude_button.configure(state='normal' if any(not value for value in excluded) else 'disabled')
        self.restore_button.configure(state='normal' if any(excluded) else 'disabled')

    def toggle_replay_settings(self):
        if self.replay_settings_row.winfo_manager():
            self.replay_settings_row.pack_forget()
        else:
            self.replay_settings_row.pack(fill='x',pady=(0,8),before=self.history_filter_row)

    def history_profile(self):
        return profile_from_path(self.replay_folder.get()) or 'manual:' + self.player_name.get().strip().casefold()

    def history_settings_changed(self):
        self.settings.update(replay_folder=self.replay_folder.get(),auto_results=self.auto_results.get())
        self.save_settings()
        if self.auto_results.get():
            self.start_history_scan()
        else:
            self.history_status.config(text='Automatic logging paused. Saved results remain available; Scan now still works.')

    def history_folder_changed(self):
        self.history_failed = {}
        self.history_errors = []
        self.history_checked = False
        self.history_hero.set('All heroes')
        self.refresh_history()
        self.history_settings_changed()

    def choose_replay_folder(self):
        folder = filedialog.askdirectory(title='Choose your HotS account’s Replays / Multiplayer folder',
                                          initialdir=self.replay_folder.get() or str(Path.home() / 'Documents'))
        if not folder:
            return
        if not profile_from_path(folder):
            messagebox.showinfo('Choose your account folder','Open Heroes of the Storm → Accounts → your account → the folder ending Hero-1-… → Replays → Multiplayer.')
            return
        self.replay_folder.set(folder);self.history_folder_changed()

    def history_tick(self):
        if self.auto_results.get():
            self.start_history_scan()
        self.history_scan_timer = self.root.after(30000,self.history_tick)

    def start_history_scan(self,force=False):
        if self.history_busy or not self.history_store or getattr(self,'maintenance_restoring',False):
            return
        folder = self.replay_folder.get()
        if not folder:
            self.history_status.config(text='Choose your replay folder to start automatic logging. You can also log results manually.')
            return
        if force:
            self.history_failed.clear()
        self.history_busy=True
        self.scan_button.configure(state='disabled')
        self.history_status.config(text='Checking saved replays…')
        # Snapshot UI values on the Tk thread; the reader never touches widgets.
        failed = self.history_failed
        def work():
            try:
                result=scan_replays(folder,self.history_store,self.history_stop,failed)
                self.history_events.put((folder,result,None))
            except Exception as exc:
                self.history_events.put((folder,None,str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def poll_history(self):
        try:
            while True:
                folder,result,error=self.history_events.get_nowait()
                self.history_busy=False
                self.scan_button.configure(state='normal')
                if folder != self.replay_folder.get():
                    continue
                if error:
                    self.history_errors=[('Replay scan',error)]
                    self.history_status.config(text='Could not read replays: '+error)
                else:
                    self.history_checked=True
                    self.history_errors=result['errors']
                    status=f"Checked {result['files']} replays · {result['added']} new results · {datetime.now():%H:%M}"
                    if result['pending']:
                        status+=f" · {result['pending']} still being saved"
                    if result['errors']:
                        status+=f" · {len(result['errors'])} skipped — see Import details"
                    if not self.auto_results.get():
                        status+=' · Automatic logging paused'
                    self.history_status.config(text=status)
                    self.refresh_history()
        except queue.Empty:
            pass
        self.history_poll_timer=self.root.after(250,self.poll_history)

    def refresh_history(self):
        self.load_pick_stats(force=True)
        self.refresh()
        if not self.history_store:
            self.history_summary.config(text='Match history unavailable')
            empty_table(self.hero_stats_tree,'Match history is unavailable.\nSee the message above.')
            empty_table(self.matches_tree,'Match history is unavailable.\nSee the message above.')
            return
        days={'Last 30 days':30,'Last 7 days':7}.get(self.history_period.get())
        try:
            records=self.history_store.records(self.history_profile(),self.history_hero.get(),self.history_mode.get(),days,self.show_excluded.get())
            all_heroes=self.history_store.records(self.history_profile(),mode=self.history_mode.get(),days=days)
        except Exception as exc:
            self.history_status.config(text='Could not load history: '+str(exc));return
        counted=[r for r in records if not r['excluded']]
        wins=sum(r['result']=='Win' for r in counted);games=len(counted)
        rate=f'{100*wins/games:.1f}%' if games else '—'
        self.history_summary.config(text=f'{games} played    {wins} wins    {games-wins} losses    {rate} win rate')
        for widget,value in zip(self.history_metrics,(games,wins,games-wins,rate)):
            widget.config(text=str(value))
        selected_matches=self.matches_tree.selection()
        match_position=self.matches_tree.yview()
        hero_position=self.hero_stats_tree.yview()
        self.hero_stats_tree.delete(*self.hero_stats_tree.get_children())
        minimum=int(self.history_min_games.get())
        stats=hero_stats(all_heroes);visible=[s for s in stats if s['games']>=minimum]
        self.minimum_games_note.config(text=f'{len(visible)} of {len(stats)} heroes shown · Minimum applies to this table, using the selected mode and period. Totals and match list stay unchanged.')
        for i,stat in enumerate(self.sorted_history_rows('heroes',visible)):
            self.hero_stats_tree.insert('', 'end',iid=stat['hero'],image=self.art.portrait(stat['hero']),values=(stat['hero'],stat['games'],stat['wins'],stat['losses'],f"{stat['rate']:.1f}%"),tags=(stripe(self.hero_stats_tree,i),))
        if self.hero_stats_tree.exists(self.history_hero.get()):self.hero_stats_tree.selection_set(self.history_hero.get())
        if hero_position:self.hero_stats_tree.yview_moveto(hero_position[0])
        self.matches_tree.delete(*self.matches_tree.get_children())
        for i,row in enumerate(self.sorted_history_rows('matches',records)):
            when=datetime.fromisoformat(row['played_at']).astimezone().strftime('%d %b %Y %H:%M')
            result=row['result']+(' (excluded)' if row['excluded'] else '')
            self.matches_tree.insert('','end',iid=row['id'],image=self.art.portrait(row['hero']),values=(when,row['hero'],result,row['map'],row['mode'],row['source']),
                                     tags=(stripe(self.matches_tree,i),'excluded' if row['excluded'] else row['result'].lower()))
        self.matches_tree.selection_set([row for row in selected_matches if self.matches_tree.exists(row)])
        if match_position:self.matches_tree.yview_moveto(match_position[0])
        filtered=self.history_hero.get()!='All heroes' or self.history_mode.get()!='All modes' or self.history_period.get()!='All time'
        message='No matches for these filters.\nTry Reset filters.' if filtered else 'No saved matches yet.\nChoose Replay settings or Log result.'
        empty_table(self.hero_stats_tree,'No heroes meet the minimum games for this mode and period.\nLower Minimum games or use Reset filters.' if minimum else 'No hero results for this mode and period.\nTry Reset filters or import replays.')
        empty_table(self.matches_tree,message)
        self.history_selection_changed()

    def load_pick_stats(self,force=False):
        store=getattr(self,'history_store',None)
        if store is None:
            self.pick_stats=None
            return
        key=(self.history_profile(),self.pick_stats_mode.get(),str(store.path))
        if not force and getattr(self,'pick_stats_key',None)==key:
            return
        try:
            rows=store.records(key[0],mode=key[1])
            self.pick_stats={s['hero']:s for s in hero_stats(rows)}
        except Exception:
            self.pick_stats=None
        self.pick_stats_key=key

    def pick_record(self,hero):
        if self.pick_stats is None:
            return 'Your record: history unavailable'
        return personal_record_label(self.pick_stats.get(hero))

    def pick_stats_changed(self,event=None):
        self.settings['pick_stats_mode']=self.pick_stats_mode.get()
        self.save_settings()
        self.load_pick_stats(force=True)
        self.refresh()

    def select_history_hero(self,event=None):
        selected=self.hero_stats_tree.selection()
        if selected and self.history_hero.get()!=selected[0]:
            self.history_hero.set(selected[0]);self.refresh_history()

    def exclude_history(self,excluded):
        selected=self.matches_tree.selection()
        if not selected:
            self.history_status.config(text='Select a match in the lower table first.');return
        try:
            self.history_store.exclude(selected,excluded)
            self.refresh_history()
            self.history_status.config(text='Selected results excluded. Use Show excluded → Restore selected to undo.' if excluded else 'Selected results restored.')
        except Exception as exc:
            messagebox.showerror('History not saved',str(exc))

    def history_import_details(self):
        message='The last replay scan completed without skipped files.' if self.history_checked else 'No replay scan has completed in this session. Use Scan now to check your replay folder.'
        if self.history_errors:
            message='These files were skipped; they do not count as losses.\n\n'+'\n\n'.join(name+'\n'+error for name,error in self.history_errors[:15])
        messagebox.showinfo('Replay import',message+'\n\nOnly your local replays are read. No collection exporter is needed.')

    def manual_result(self):
        if not self.history_store:
            return
        dialog=tk.Toplevel(self.root);dialog.title('Log a match result');dialog.configure(bg=BG);dialog.geometry('520x450')
        dialog.minsize(520,420);dialog.bind('<Escape>',lambda e:dialog.destroy())
        panel=ttk.Frame(dialog,padding=20);panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='For a game without a saved replay.',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(panel,text='If its replay is imported later, exclude this manual entry to avoid counting it twice.',wraplength=460,foreground=MUTED).pack(anchor='w',pady=(8,16))
        hero=tk.StringVar(value=self.playing.get());result=tk.StringVar(value='Win')
        mode=tk.StringVar(value=self.history_mode.get() if self.history_mode.get()!='All modes' else 'Unknown')
        map_name=tk.StringVar(value=self.map.get());when=tk.StringVar(value=datetime.now().strftime('%Y-%m-%d %H:%M'))
        form=ttk.Frame(panel);form.pack(fill='x')
        form.columnconfigure(1,weight=1)
        for i,(label,var,values) in enumerate([('Hero',hero,sorted(HEROES)),('Result',result,['Win','Loss']),('Mode',mode,MODES),('Battleground',map_name,MAPS)]):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',pady=5)
            ttk.Combobox(form,textvariable=var,values=values,state='readonly',width=32).grid(row=i,column=1,sticky='ew',padx=12)
        ttk.Label(form,text='Date / time').grid(row=4,column=0,sticky='w',pady=5)
        ttk.Entry(form,textvariable=when,width=34).grid(row=4,column=1,padx=12,sticky='ew')
        ttk.Label(panel,text='Local time: YYYY-MM-DD HH:MM',foreground=MUTED).pack(anchor='w',pady=8)
        # Keep the destination fixed if the main page changes while this is open.
        profile,player=self.history_profile(),self.player_name.get()
        def save():
            try:
                played=datetime.strptime(when.get().strip(),'%Y-%m-%d %H:%M').astimezone()
                if played>datetime.now().astimezone():
                    raise ValueError('Choose a date and time in the past.')
                self.history_store.add_manual(profile,player,hero.get(),result.get(),played,map_name.get(),mode.get())
                self.refresh_history();dialog.destroy()
            except Exception as exc:
                messagebox.showerror('Could not save result',str(exc),parent=dialog)
        actions=ttk.Frame(panel);actions.pack(fill='x',pady=12)
        ttk.Button(actions,text='Save result',command=save).pack(side='right')
        ttk.Button(actions,text='Cancel',command=dialog.destroy).pack(side='right',padx=8)
