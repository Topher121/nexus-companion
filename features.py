"""Background services and controls for the local companion."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date
from pathlib import Path
import shutil
import webbrowser
from availability import load_json, save_json, parse_collection, eligible, fetch_rotation, rotation_available, rotation_summary
from ui_theme import BG, PANEL, TEXT, MUTED, BLUE, stripe, empty_table, ScrollPage

from app_paths import DATA_DIR as ROOT, RESOURCE_DIR, FROZEN

def interfaces_folder():
    """Use Windows' Documents location, including redirected/OneDrive folders."""
    import ctypes
    documents = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, documents) == 0:
        return Path(documents.value) / 'Heroes of the Storm' / 'Interfaces'
    return Path.home() / 'Documents' / 'Heroes of the Storm' / 'Interfaces'

class Features:
    def prepare_features(self):
        self.events = queue.Queue()
        self.watch = False
        self.busy = False
        self.generation = 0
        self.manual = set()
        self.last_read = {}
        self.reader_notice = ''
        self.detected_map = None
        self.previous_sample = {}
        self.ally_hovers = {}
        self.previous_hovers = {}
        self.previous_self_slot = None
        self.detected_self_slot = None
        self.game_capture = None
        self.settings = load_json(ROOT / 'settings.json', {})
        self.collection = load_json(ROOT / 'collection.json', {})
        self.owned = {h: v for h, v in self.collection.get('heroes', {}).items() if type(v) is bool}
        self.rotation = load_json(ROOT / 'rotation.json', {})
        self.only_confirmed = tk.BooleanVar(value=self.settings.get('only_confirmed', bool(self.owned)))
        self.account_level = tk.StringVar(value=str(self.settings.get('account_level', 0)))
        self.self_slot = tk.StringVar(value='Auto')
        self.player_name = tk.StringVar(value=self.settings.get('player_name', '' if FROZEN else 'Topher'))
        self.follow_hero = tk.BooleanVar(value=self.settings.get('follow_hero', True))

    def make_features(self):
        live = ttk.Frame(self.draft)
        live.pack(fill='x', before=self.draft.winfo_children()[0], pady=(0, 12))
        self.watch_button = ttk.Button(live, text='Start live draft', command=self.toggle_watch, style='Primary.TButton')
        self.watch_button.pack(side='left')
        ttk.Button(live, text='Read screenshot', command=self.choose_screenshot).pack(side='left', padx=6)
        ttk.Label(live, text='Your name').pack(side='left', padx=(10, 4))
        player = ttk.Entry(live, textvariable=self.player_name, width=12); player.pack(side='left')
        player.bind('<FocusOut>', lambda e: self.identity_changed())
        player.bind('<Return>', lambda e: self.identity_changed())
        ttk.Label(live, text='Your slot').pack(side='left', padx=(8,4))
        slot = ttk.Combobox(live, textvariable=self.self_slot, values=['Auto','1','2','3','4','5'], state='readonly', width=6)
        slot.pack(side='left')
        slot.bind('<<ComboboxSelected>>', lambda e: self.identity_changed())
        ttk.Button(live, text='Allow auto corrections', command=self.release_manual).pack(side='right')
        self.live_status = ttk.Label(self.draft, text='Live reader off • HotS can stay behind other windows. Keep it restored, preferably borderless.', wraplength=1110,foreground=MUTED)
        self.live_status.pack(fill='x', before=self.draft.winfo_children()[1], pady=(0, 8))
        self.draft_warning=ttk.Label(self.draft,text='',foreground='#ffc982',wraplength=1050,justify='left')
        self.draft_warning.pack(fill='x',after=self.live_status,pady=(0,8))
        self.draft.bind('<Configure>',lambda e:self.draft_warning.configure(wraplength=max(240,e.width-32)),add='+')
        self.collection_page = ScrollPage(self.tabs)
        self.tabs.add(self.collection_page, text='  Collection',image=self.art.icon('collection',24),compound='left')
        p = self.collection_page.body
        ttk.Label(p, text='Your collection', font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(p, text='Track heroes you own and heroes currently free to play. Set favourites in My hero pool.', foreground=MUTED).pack(anchor='w', pady=(6,8))
        row = ttk.Frame(p); row.pack(fill='x',pady=(0,8))
        ttk.Label(row,text='Search heroes').pack(side='left',padx=(0,8))
        self.collection_search=tk.StringVar();self.collection_filter=tk.StringVar(value='All heroes')
        search=ttk.Entry(row,textvariable=self.collection_search,width=24);search.pack(side='left')
        search.bind('<Escape>',lambda e:self.collection_search.set(''))
        self.collection_search.trace_add('write',lambda *a:self.show_availability())
        ttk.Label(row,text='Show').pack(side='left',padx=(14,8))
        picker=ttk.Combobox(row,textvariable=self.collection_filter,values=['All heroes','Owned','Free rotation','Not owned','Unknown'],state='readonly',width=15)
        picker.pack(side='left');picker.bind('<<ComboboxSelected>>',lambda e:self.show_availability())
        ttk.Button(row,text='Reset filters',command=self.reset_collection_filters).pack(side='left',padx=8)
        self.collection_setup_button=ttk.Button(row,text='Collection setup',command=self.toggle_collection_setup)
        self.collection_setup_button.pack(side='right')
        row = ttk.Frame(p); row.pack(fill='x', pady=(0,4))
        ttk.Checkbutton(row, text='Suggest only confirmed owned or currently free heroes', variable=self.only_confirmed, command=self.availability_changed).pack(side='left')
        ttk.Button(row, text='Refresh free rotation', command=self.start_rotation).pack(side='right')
        self.collection_setup=ttk.Frame(p)
        row=ttk.Frame(self.collection_setup);row.pack(fill='x',pady=(0,6))
        ttk.Button(row, text='Import replay export', command=self.import_collection).pack(side='left')
        ttk.Button(row, text='Set up collection exporter', command=self.exporter_setup).pack(side='left', padx=8)
        ttk.Label(row, text='Account level').pack(side='left', padx=(15,5))
        level = ttk.Entry(row, textvariable=self.account_level, width=7); level.pack(side='left')
        level.bind('<FocusOut>', lambda e: self.availability_changed())
        level.bind('<Return>', lambda e: self.availability_changed())
        ttk.Label(self.collection_setup,text='Enter your account level for free-hero unlocks. Re-import after buying heroes; ownership is not detected live.',foreground=MUTED,wraplength=860).pack(anchor='w')
        self.collection_status = ttk.Label(p, text='', wraplength=1080); self.collection_status.pack(anchor='w', pady=(6,4))
        self.rotation_status = ttk.Label(p, text='', wraplength=1080,foreground=MUTED); self.rotation_status.pack(anchor='w', pady=(0,4))
        p.bind('<Configure>',lambda e:[label.configure(wraplength=max(240,e.width-32)) for label in (self.collection_status,self.rotation_status)])
        table=ttk.Frame(p);table.pack(fill='both',expand=True,pady=8)
        self.availability_tree = ttk.Treeview(table, columns=('hero','state'), show='tree headings', selectmode='extended', height=5, style='Roster.Treeview')
        self.availability_tree.column('#0',width=38,minwidth=38,stretch=False)
        self.availability_tree.heading('#0',text='')
        for key,label in [('hero','Hero'),('state','Availability')]:
            self.availability_tree.heading(key,text=label,anchor='w')
            self.availability_tree.column(key,width=360,minwidth=180,anchor='w')
        scroll=ttk.Scrollbar(table,command=self.availability_tree.yview);scroll.pack(side='right',fill='y')
        self.availability_tree.configure(yscrollcommand=scroll.set);self.availability_tree.pack(fill='both',expand=True)
        controls=ttk.Frame(self.collection_page,padding=(16,8,16,0))
        controls.pack(side='bottom',fill='x',before=self.collection_page.canvas)
        self.collection_selection_status=ttk.Label(controls,text='',foreground=MUTED)
        self.collection_selection_status.pack(anchor='w',pady=(0,8))
        row = ttk.Frame(controls); row.pack(fill='x')
        self.collection_buttons=[]
        for label, value in [('Mark owned', True), ('Mark not owned', False), ('Reset to unknown', None)]:
            button=ttk.Button(row, text=label, command=lambda v=value: self.mark_owned(v),state='disabled')
            button.pack(side='left', padx=(0,8));self.collection_buttons.append(button)
        self.availability_tree.bind('<<TreeviewSelect>>',lambda e:self.collection_selection_changed())
        self.show_availability()
        if not self.owned:self.toggle_collection_setup()
        self.root.after(150, self.poll_events)
        self.root.after(600, self.start_rotation)
        self.root.protocol('WM_DELETE_WINDOW', self.close_app)

    def save_settings(self):
        try:
            level = max(0, int(self.account_level.get()))
        except ValueError:
            level = 0
        self.settings.update(only_confirmed=self.only_confirmed.get(), account_level=level, player_name=self.player_name.get(), follow_hero=self.follow_hero.get())
        try:
            save_json(ROOT / 'settings.json', self.settings)
        except OSError as exc:
            messagebox.showerror('Settings not saved', str(exc))

    def available_heroes(self):
        try:
            level = max(0, int(self.account_level.get()))
        except ValueError:
            level = 0
        return eligible(self.owned, self.rotation, level, self.only_confirmed.get())

    def availability_changed(self):
        try:level=int(self.account_level.get())
        except ValueError:level=-1
        if level<0:
            self.account_level.set(str(self.settings.get('account_level',0)))
            messagebox.showinfo('Account level','Enter a whole number of 0 or more. Your previous level has been kept.',parent=self.root)
            return
        self.save_settings(); self.show_availability(); self.refresh()

    def show_availability(self):
        from data import HEROES
        if not hasattr(self, 'availability_tree'):
            return
        try:
            level = int(self.account_level.get())
        except ValueError:
            level = 0
        free = rotation_available(self.rotation, level)
        selected=self.availability_tree.selection();position=self.availability_tree.yview()
        self.availability_tree.delete(*self.availability_tree.get_children())
        for i,hero in enumerate(sorted(HEROES)):
            state = 'Owned' if self.owned.get(hero) else 'Free rotation' if hero in free else 'Not owned' if self.owned.get(hero) is False else 'Unknown'
            category=self.collection_filter.get()
            visible={'All heroes':True,'Owned':self.owned.get(hero) is True,'Free rotation':hero in free,
                     'Not owned':self.owned.get(hero) is False,'Unknown':hero not in self.owned}
            if self.collection_search.get().strip().casefold() not in hero.casefold() or not visible.get(category,True):continue
            self.availability_tree.insert('', 'end', iid=hero, image=self.art.portrait(hero),values=(hero,state),tags=(stripe(self.availability_tree,i),))
        self.availability_tree.selection_set([h for h in selected if self.availability_tree.exists(h)])
        if position:self.availability_tree.yview_moveto(position[0])
        empty_table(self.availability_tree,'No heroes match these filters.\nTry Reset filters.')
        self.collection_status.config(text=f'{sum(v is True for v in self.owned.values())} owned · {len(self.owned)} ownership records · Last import: {self.collection.get("imported", "none")}')
        self.rotation_status.config(text=rotation_summary(self.rotation,level))
        self.collection_selection_changed()

    def reset_collection_filters(self):
        self.collection_filter.set('All heroes');self.collection_search.set('')

    def toggle_collection_setup(self):
        if self.collection_setup.winfo_manager():
            self.collection_setup.pack_forget();self.collection_setup_button.configure(text='Collection setup')
        else:
            self.collection_setup.pack(fill='x',pady=8,before=self.collection_status)
            self.collection_setup_button.configure(text='Hide setup')

    def collection_selection_changed(self):
        count=len(self.availability_tree.selection())
        for button in self.collection_buttons:button.configure(state='normal' if count else 'disabled')
        message=f'{count} selected' if count else 'Select heroes to edit ownership. Ctrl-click selects several.'
        self.collection_selection_status.config(text=f'{len(self.availability_tree.get_children())} heroes shown · {message}')

    def store_collection(self):
        self.collection['heroes'] = self.owned
        save_json(ROOT / 'collection.json', self.collection)
        self.show_availability(); self.refresh()

    def mark_owned(self, value):
        if not self.availability_tree.selection():return
        for hero in self.availability_tree.selection():
            if value is None:
                self.owned.pop(hero, None)
            else:
                self.owned[hero] = value
        try:
            self.store_collection()
        except OSError as exc:
            messagebox.showerror('Collection not saved', str(exc))

    def import_collection(self):
        dialog = tk.Toplevel(self.root); dialog.title('Import your hero collection'); dialog.geometry('650x420');dialog.configure(bg=BG)
        dialog.minsize(560,360);dialog.bind('<Escape>',lambda e:dialog.destroy())
        ttk.Label(dialog,text='Import your owned heroes',font=('Segoe UI',16,'bold'),padding=(12,12,12,4)).pack(anchor='w')
        hint=ttk.Label(dialog,text='Copy the export from YOUR player button in a replay, then paste it here. The next step shows the player name for you to confirm.',padding=(12,0,12,12),wraplength=600)
        hint.pack(fill='x');dialog.bind('<Configure>',lambda e:hint.configure(wraplength=max(240,dialog.winfo_width()-32)))
        content=ttk.Frame(dialog);content.pack(fill='both',expand=True,padx=12)
        box = tk.Text(content, height=12, wrap='word',bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',padx=12,pady=12)
        scroll=ttk.Scrollbar(content,command=box.yview);scroll.pack(side='right',fill='y')
        box.configure(yscrollcommand=scroll.set);box.pack(fill='both',expand=True)
        def paste():
            try:
                box.delete('1.0','end'); box.insert('1.0', self.root.clipboard_get())
            except tk.TclError:
                messagebox.showinfo('Clipboard', 'Copy your replay export first.', parent=dialog)
        def accept():
            try:
                player, values = parse_collection(box.get('1.0','end'))
                if not messagebox.askyesno('Confirm your collection', f'Player: {player or "Unknown — check the replay button"}\n{sum(values.values())} owned out of {len(values)} recognised heroes.\n\nIs this your player? Import these ownership values?\nFavourites and exclusions will be preserved.', parent=dialog):
                    return
                self.owned.update(values)
                self.collection.update(player=player, imported=date.today().isoformat())
                self.only_confirmed.set(True)
                self.store_collection(); self.save_settings(); dialog.destroy()
            except (ValueError, OSError) as exc:
                messagebox.showerror('Could not import', str(exc), parent=dialog)
        row = ttk.Frame(dialog, padding=12); row.pack(fill='x')
        ttk.Button(row, text='Paste clipboard', command=paste).pack(side='left')
        ttk.Button(row, text='Review & import', command=accept).pack(side='right')
        ttk.Button(row,text='Cancel',command=dialog.destroy).pack(side='right',padx=8)

    def exporter_setup(self):
        dialog = tk.Toplevel(self.root); dialog.title('One-time collection setup'); dialog.geometry('780x550');dialog.configure(bg=BG)
        dialog.minsize(740,540);dialog.bind('<Escape>',lambda e:dialog.destroy())
        ttk.Label(dialog,text='Set up your collection import',font=('Segoe UI',18,'bold'),padding=(18,16,18,6)).pack(anchor='w')
        text = ('Use this exporter in REPLAYS ONLY, never as a live observer interface.\n\n'
                '1. Copy the exporter\nUse Copy exporter to folder below and select your Heroes of the Storm / Interfaces folder.\n\n'
                '2. Choose the replay interface\nIn HotS, open Options → Observer and Replay. Set Replay Interface to HeroesOwnedItems.\n\n'
                '3. Open your replay and copy your heroes\nOpen Watch and start a recent replay you played in. On the RIGHT, click the player button with YOUR name (for example, Topher: …%). Your collection is copied to the clipboard.\n\n'
                '4. Import into Nexus Companion\nReturn to Collection → Collection setup → Import replay export. Click Paste clipboard, then Review & import. Confirm your player name.\n\n'
                '5. Restore the default Replay Interface in HotS\nRepeat the export after buying heroes. This app does not change your game settings.')
        instructions=ttk.Label(dialog,text=text,wraplength=730,padding=(18,6),anchor='nw',justify='left')
        instructions.pack(fill='both',expand=True)
        dialog.bind('<Configure>',lambda e:instructions.configure(wraplength=max(300,dialog.winfo_width()-40)))
        ttk.Label(dialog,text='Community exporter: spazzo966 v1.1 · Verify it works with your current game in a replay.',foreground=MUTED,padding=(18,6)).pack(anchor='w')
        def install():
            suggested = interfaces_folder()
            initial = suggested if suggested.is_dir() else suggested.parent if suggested.parent.is_dir() else suggested.parent.parent
            folder = filedialog.askdirectory(title='Select Heroes of the Storm / Interfaces folder', initialdir=str(initial), parent=dialog)
            if not folder:
                return
            target = Path(folder) / 'HeroesOwnedItems.StormInterface'
            if target.exists():
                messagebox.showinfo('Already present', 'An exporter is already in that folder; it has not been overwritten.', parent=dialog); return
            try:
                shutil.copyfile(RESOURCE_DIR / 'assets' / target.name, target)
                messagebox.showinfo('Exporter copied', 'Now select it as your Replay Interface inside HotS.', parent=dialog)
            except OSError as exc:
                messagebox.showerror('Could not copy exporter', str(exc), parent=dialog)
        row = ttk.Frame(dialog, padding=12); row.pack(fill='x')
        ttk.Button(row, text='Copy exporter to folder', command=install).pack(side='left')
        ttk.Button(row, text='Exporter source & instructions', command=lambda: webbrowser.open('https://github.com/spazzo966/HeroesOwnedItemsInterface')).pack(side='right')
        ttk.Button(row,text='Close',command=dialog.destroy).pack(side='right',padx=8)

    def start_rotation(self):
        if getattr(self, 'rotation_busy', False) or getattr(self,'maintenance_restoring',False):
            return
        self.rotation_busy = True
        self.rotation_status.config(text='Checking current free rotation…')
        def work():
            try:
                value = fetch_rotation()
                save_json(ROOT / 'rotation.json', value)
                self.events.put(('rotation', value, None))
            except Exception as exc:
                self.events.put(('rotation', None, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def manual_selection(self, variable):
        if variable is self.playing:
            self.follow_hero.set(False)
        else:
            self.manual.add(str(variable))
        self.update_own_hero()
        self.refresh()

    def identity_changed(self):
        self.previous_self_slot = None
        self.detected_self_slot = None
        self.save_settings()
        self.update_own_hero()
        self.refresh()

    def own_slot(self):
        if self.self_slot.get() in ('1','2','3','4','5'):
            return int(self.self_slot.get()) - 1
        return self.detected_self_slot

    def planned_hovers(self):
        from draft_state import teammate_hovers
        return teammate_hovers([v.get() for v in self.allies], [v.get() for v in self.enemies],
                               [v.get() for v in self.bans], self.ally_hovers, self.own_slot(),
                               {i for i,v in enumerate(self.allies) if str(v) in self.manual})

    def clear_hovers(self):
        self.ally_hovers.clear()
        self.previous_hovers.clear()

    def update_own_hero(self):
        slot = self.own_slot()
        if self.follow_hero.get() and slot is not None and self.allies[slot].get():
            self.playing.set(self.allies[slot].get())
        if hasattr(self, 'hero_status'):
            if not self.follow_hero.get():
                text = 'Browsing a hero manually. Enable Follow my locked hero to resume automatic builds.'
            elif slot is not None and self.allies[slot].get():
                text = f'Following your locked {self.allies[slot].get()} · allied slot {slot + 1}. Match tips update with the enemy picks.'
            else:
                text = f'Waiting to identify {self.player_name.get()} and a locked pick. You can set your slot on the draft page.'
            self.hero_status.config(text=text)

    def follow_changed(self):
        self.save_settings(); self.update_own_hero(); self.refresh()

    def release_manual(self):
        self.manual.clear()
        self.live_status.config(text='Automatic corrections allowed again. Unreadable slots remain unchanged.')

    def toggle_watch(self):
        self.watch = not self.watch
        self.generation += 1
        self.previous_sample.clear()
        self.clear_hovers()
        self.previous_self_slot = None
        self.watch_button.config(text='Stop live draft' if self.watch else 'Start live draft',image=self.art.icon('pause' if self.watch else 'play'),compound='left')
        self.live_status.config(text='Watching for the HotS draft window…' if self.watch else 'Live reader stopped.')
        if self.watch:
            self.schedule_read()
        elif self.game_capture:
            threading.Thread(target=self.game_capture.close, daemon=True).start()
        self.refresh()

    def schedule_read(self):
        if self.watch and not self.busy:
            self.start_read(None)

    def choose_screenshot(self):
        if self.busy:
            self.live_status.config(text='Finishing the current reading; try again in a moment.'); return
        path = filedialog.askopenfilename(title='Read a HotS draft screenshot', filetypes=[('Images','*.png *.jpg *.jpeg')])
        if path:
            self.start_read(path)

    def start_read(self, path):
        if getattr(self,'maintenance_restoring',False):return
        self.busy = True
        generation = self.generation
        def work():
            try:
                from vision import read_image, Image
                if path:
                    image, status = Image.open(path), ''
                else:
                    from capture import GameCapture
                    if generation != self.generation:
                        self.events.put(('draft', (generation, None, False), None)); return
                    if self.game_capture is None:
                        self.game_capture = GameCapture()
                    image, status = self.game_capture.read()
                value = read_image(image) if image is not None else {'valid': False, 'message': status}
                if not path and generation != self.generation and self.game_capture:
                    self.game_capture.close()
                self.events.put(('draft', (generation, value, bool(path)), None))
            except Exception as exc:
                self.events.put(('draft', (generation, None, bool(path)), str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def apply_read(self, value, screenshot=False):
        if not value['valid']:
            self.previous_sample.clear()
            self.clear_hovers()
            self.previous_self_slot = None
            self.live_status.config(text=value['message'])
            self.reader_notice='Reader is not confirming the screen. Saved picks and bans remain; verify them before following suggestions.' if self.last_read else ''
            self.refresh();return
        if value.get('map') and self.detected_map and self.detected_map != value['map']:
            self.live_status.config(text='A different battleground was detected. Press Clear draft to start the new match.')
            self.reader_notice='Different match detected. Press Clear draft before using these suggestions.'
            self.clear_hovers()
            self.refresh();return
        if value.get('map'):
            self.detected_map = value['map']
        if value.get('map') and str(self.map) not in self.manual:
            self.map.set(value['map'])
        self.last_read = value
        self.reader_notice = ''
        candidate = {}
        hovers = []
        for slot in value['slots']:
            if slot['hero'] and slot['locked']:
                candidate[(slot['side'], slot['index'])] = slot['hero']
            elif slot['hero']:
                hovers.append(slot['hero'])
        for ban in value['bans']:
            candidate[('bans', ban['index'])] = ban['hero']
        changed = 0
        for key, hero in candidate.items():
            if not screenshot and self.previous_sample.get(key) != hero:
                continue
            variable = getattr(self, key[0])[key[1]]
            if str(variable) in self.manual:
                continue
            other = [v.get() for v in self.allies + self.enemies + self.bans if v is not variable]
            if hero in other:
                continue
            if variable.get() != hero:
                variable.set(hero); changed += 1
        self.previous_sample = candidate
        # A changed or unread hover is removed immediately. A new live hover
        # needs two agreeing frames, just like a locked pick; screenshots need one.
        hover_sample = {s['index']: s['hero'] for s in value['slots']
                        if s['side'] == 'allies' and s['hero'] and not s['locked']
                        and value.get('phase') != 'starting'}
        self.ally_hovers = {i:hero for i,hero in hover_sample.items()
                            if screenshot or self.previous_hovers.get(i) == hero}
        self.previous_hovers = hover_sample
        from identity import player_slot
        own = player_slot(value['slots'], self.player_name.get())
        if own is not None and (screenshot or self.previous_self_slot == own):
            self.detected_self_slot = own
        self.previous_self_slot = own
        self.update_own_hero()
        own_text = f'Your slot: {self.own_slot()+1}' if self.own_slot() is not None else f'Looking for player {self.player_name.get()}'
        label = 'Final teams' if value.get('phase') == 'starting' else self.map.get()
        recorded=sum(bool(v.get()) for v in self.allies+self.enemies)
        self.live_status.config(text=f'{label} • {recorded}/10 heroes recorded · {changed} entries updated. {own_text}. Hovers: {", ".join(hovers) or "none read"}. Manual edits preserved.')
        self.refresh()

    def update_draft_warning(self):
        if not hasattr(self,'draft_warning'):return
        from draft_health import draft_health
        teams={key:[v.get() for v in getattr(self,key)] for key in ('allies','enemies','bans')}
        manual={(key,i) for key in teams for i,v in enumerate(getattr(self,key)) if str(v) in self.manual}
        problems,marked=draft_health(self.last_read,teams,manual)
        if self.reader_notice:problems.insert(0,self.reader_notice)
        self.draft_warning.config(text=('CHECK DRAFT · Suggestions use only the heroes recorded below.\n'+'\n'.join('• '+p for p in problems)+'\nCorrect the highlighted slots manually, or wait for another reading.') if problems else '')
        for key,boxes in getattr(self,'slot_boxes',{}).items():
            for i,box in enumerate(boxes):box.configure(style='Attention.TCombobox' if (key,i) in marked else 'TCombobox')

    def poll_events(self):
        try:
            while True:
                kind, value, error = self.events.get_nowait()
                if kind == 'draft':
                    self.busy = False
                    generation, result, screenshot = value
                    if generation == self.generation:
                        if error:
                            self.clear_hovers()
                            self.previous_sample.clear()
                            self.previous_self_slot = None
                            self.live_status.config(text='Reader unavailable: ' + error)
                            self.reader_notice='Reader unavailable. Saved draft may be out of date; check picks and bans manually.'
                            self.refresh()
                        else:
                            self.apply_read(result, screenshot)
                    if self.watch:
                        self.root.after(1800, self.schedule_read)
                else:
                    self.rotation_busy = False
                    if value:
                        self.rotation = value
                    self.show_availability(); self.refresh()
                    if error:
                        self.rotation_status.config(text=self.rotation_status.cget('text') + ' Refresh unavailable: ' + error)
                    if hasattr(self, 'rotation_timer'):
                        self.root.after_cancel(self.rotation_timer)
                    self.rotation_timer = self.root.after(6 * 60 * 60 * 1000, self.start_rotation)
        except queue.Empty:
            pass
        self.root.after(150, self.poll_events)

    def close_app(self):
        self.watch = False
        if hasattr(self, 'history_stop'):
            self.history_stop.set()
        self.generation += 1
        if self.game_capture:
            threading.Thread(target=self.game_capture.close, daemon=True).start()
        self.root.destroy()
