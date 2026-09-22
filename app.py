import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from pathlib import Path
import webbrowser
import re
from features import Features
from history_ui import HistoryFeatures
from maintenance_ui import MaintenanceFeatures
from data import HEROES, MAPS, guide_url
from build_library import AUTO_BUILD, PROFILES, BUILD_COUNT, build_names
from engine import rank, validate, build_details
from draft_engine import FLEX_CHOICES, GUIDANCE, draft_summary, recommendation_text
from history import DRAFT_STAT_MODES
from ui_theme import Art, ScrollPage, apply_theme, stripe, empty_table, BG, PANEL, TEXT, MUTED, BLUE, BORDER, PURPLE, RED

from app_paths import DATA_DIR as ROOT, APP_VERSION, FROZEN
SAVE = ROOT / 'preferences.json'
SUPPORT_URL = 'https://ko-fi.com/pocketforgestudios'

class Companion(MaintenanceFeatures, HistoryFeatures, Features):
 def __init__(self, root):
  self.root = root
  self.prepare_features()
  root.title('Nexus Companion')
  root.geometry('1250x850'); root.minsize(980, 700); root.configure(bg=BG)
  self.prefs = {} if FROZEN else {'Jaina':'Never suggest','Valla':'Never suggest'}
  self.storage_error = ''
  try:
   if SAVE.exists():
    loaded=json.loads(SAVE.read_text(encoding='utf-8'))
    self.prefs.update({k:v for k,v in loaded.items() if k in HEROES and v in ('Favourite','Allowed','Never suggest','Not owned')})
  except (OSError, ValueError, AttributeError): self.storage_error='Could not read saved preferences. Defaults loaded; your file has not been changed.'
  for hero, mode in list(self.prefs.items()):
   if mode == 'Not owned':
    self.owned.setdefault(hero,False);self.prefs[hero]='Allowed'
  if self.owned and not self.collection.get('heroes'):
   from availability import save_json
   self.collection['heroes']=self.owned
   try:save_json(ROOT/'collection.json',self.collection)
   except OSError:self.storage_error='Ownership migration could not be saved; please check Collection.'
  self.style=apply_theme(root);self.art=Art(root)
  self.style.configure('Attention.TCombobox',bordercolor='#ffc982',lightcolor='#ffc982',darkcolor='#ffc982')
  self.style.map('Attention.TCombobox',bordercolor=[('readonly','#ffc982')])
  root.iconphoto(True,self.art.icon('nexus',64))
  head=ttk.Frame(root,padding=(22,17,22,15));head.pack(fill='x')
  ttk.Label(head,image=self.art.icon('nexus',48)).pack(side='left',padx=(0,12))
  brand=ttk.Frame(head);brand.pack(side='left')
  ttk.Label(brand,text='NEXUS COMPANION',font=('Segoe UI',20,'bold'),foreground=TEXT).pack(anchor='w')
  ttk.Label(brand,text='Draft smarter. Know your heroes.',foreground=MUTED,font=('Segoe UI',10)).pack(anchor='w')
  self.on_top=tk.BooleanVar()
  ttk.Checkbutton(head,text='Keep on top',variable=self.on_top,command=lambda:root.attributes('-topmost',self.on_top.get())).pack(side='right')
  ttk.Label(head,text='PERSONAL COMPANION',foreground=PURPLE,font=('Segoe UI',9,'bold'),padding=(18,0)).pack(side='right')
  self.tabs=ttk.Notebook(root);self.tabs.pack(fill='both',expand=True,padx=18,pady=(0,8))
  self.draft_page=ScrollPage(self.tabs);self.draft=self.draft_page.body
  self.pool=ttk.Frame(self.tabs,padding=16);self.build=ttk.Frame(self.tabs,padding=16)
  for page,name,icon in [(self.draft_page,'Draft advisor','draft'),(self.pool,'My hero pool','heroes'),(self.build,'Talents & tips','build')]:
   self.tabs.add(page,text='  '+name,image=self.art.icon(icon,24),compound='left')
  self.make_draft();self.make_pool();self.make_build()
  self.make_features()
  self.make_history()
  self.make_maintenance()
  self.decorate_buttons(root)
  foot=ttk.Frame(root,padding=(22,7));foot.pack(side='bottom',fill='x',before=self.tabs)
  ttk.Label(foot,text='●  LOCAL & PRIVATE',foreground=BLUE,font=('Segoe UI',8,'bold')).pack(side='left')
  ttk.Label(foot,text='Free app · Optional support',foreground=MUTED,font=('Segoe UI',9)).pack(side='left',padx=18)
  ttk.Label(foot,text='NEXUS  /  '+APP_VERSION,foreground=MUTED,font=('Segoe UI',8,'bold')).pack(side='right')
  self.support_button=ttk.Button(foot,text='Support development ♥',style='Support.TButton',command=self.open_support)
  self.support_button.pack(side='right',padx=(10,18))
  self.refresh()
  if self.storage_error:root.after(200,lambda:messagebox.showwarning('Preferences',self.storage_error))

 def open_support(self):
  try:opened=webbrowser.open(SUPPORT_URL,new=2)
  except (webbrowser.Error,OSError):opened=False
  if not opened:
   messagebox.showinfo('Support development','Nexus Companion is free. Optional support is available at:\n\n'+SUPPORT_URL+'\n\nCopy this address into your browser.',parent=self.root)

 def combo(self,parent,var,values,width=19):
  box=ttk.Combobox(parent,textvariable=var,values=values,state='readonly',width=width)
  box.bind('<<ComboboxSelected>>',lambda e:self.manual_selection(var));return box

 def decorate_buttons(self,parent):
  icons={'Start live draft':'play','Stop live draft':'pause','Read screenshot':'photo',
   'Favourite':'star','Allowed':'check','Never suggest':'ban','Clear draft':'refresh',
   'Open talent guide':'external','Import replay export':'download','Refresh free rotation':'refresh',
   'Mark owned':'check','Mark not owned':'ban','Scan now':'refresh','Log a result manually':'plus'}
  for child in parent.winfo_children():
   if isinstance(child,ttk.Button) and child.cget('text') in icons:
    child.configure(image=self.art.icon(icons[child.cget('text')]),compound='left')
   self.decorate_buttons(child)

 def make_draft(self):
  bar=ttk.Frame(self.draft);bar.pack(fill='x',pady=(0,12))
  self.map=tk.StringVar(value='Unknown map');self.role=tk.StringVar(value='Any')
  stats_mode=self.settings.get('pick_stats_mode','Storm League')
  self.pick_stats_mode=tk.StringVar(value=stats_mode if stats_mode in DRAFT_STAT_MODES else 'Storm League')
  self.pick_stats=None
  ttk.Label(bar,text='Battleground').pack(side='left',padx=(0,8));self.combo(bar,self.map,MAPS,26).pack(side='left')
  ttk.Label(bar,text='Your role').pack(side='left',padx=12);self.combo(bar,self.role,['Any','Tank','Healer','Bruiser','Ranged','Melee','Support']).pack(side='left')
  ttk.Button(bar,text='Clear draft',command=self.clear).pack(side='right')
  ttk.Label(self.draft,text='Start with Clear draft. Boxes are locked picks. Teammate hovers are shown separately and included in suggestions.',foreground=MUTED,wraplength=900).pack(anchor='w',pady=(0,10))
  board=ttk.Frame(self.draft);board.pack(fill='x')
  self.allies=[];self.enemies=[];self.bans=[];self.slot_portraits=[];self.slot_boxes={'allies':[],'enemies':[],'bans':[]}
  for col,(label,collection,count) in enumerate([('YOUR TEAM',self.allies,5),('ENEMY TEAM',self.enemies,5),('BANNED · BOTH TEAMS',self.bans,6)]):
   f=ttk.Frame(board,style='Card.TFrame',padding=(12,10));f.grid(row=0,column=col,sticky='nsew',padx=(0,10 if col<2 else 0));board.columnconfigure(col,weight=1,uniform='teams')
   ttk.Label(f,text=label,foreground=BLUE if col==0 else RED if col==1 else PURPLE,style='Card.TLabel',font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(0,7))
   for i in range(count):
    v=tk.StringVar();collection.append(v)
    row=ttk.Frame(f,style='Card.TFrame');row.pack(fill='x',pady=1)
    if col==0:ttk.Label(row,text=str(i+1),width=2,foreground=MUTED,style='Card.TLabel').pack(side='left')
    icon=ttk.Label(row,image=self.art.icon('ban' if col==2 else 'heroes',24),style='Card.TLabel')
    icon.pack(side='left',padx=(0,8))
    box=self.combo(row,v,['']+sorted(HEROES),19);box.pack(side='left',fill='x',expand=True)
    self.slot_boxes[('allies','enemies','bans')[col]].append(box)
    self.slot_portraits.append((v,icon,col))
  self.hover_status=ttk.Label(self.draft,text='',foreground=PURPLE,wraplength=900)
  self.hover_status.pack(anchor='w',pady=(8,0))
  self.draft.bind('<Configure>',lambda e:self.hover_status.configure(wraplength=max(200,e.width-30)),add='+')
  self.ban_notice=ttk.Label(self.draft,text='Only confirmed bans are listed. Blank ban slots may be skipped or unread; check them in HotS.',foreground=MUTED,wraplength=900)
  self.ban_notice.pack(anchor='w',pady=(6,0))
  self.draft.bind('<Configure>',lambda e:self.ban_notice.configure(wraplength=max(200,e.width-30)),add='+')
  self.flex_bar=ttk.Frame(self.draft)
  self.flex_plans={hero:tk.StringVar(value='Unconfirmed') for hero in FLEX_CHOICES}
  self.flex_controls={}
  for hero,choices in FLEX_CHOICES.items():
   control=ttk.Frame(self.flex_bar);self.flex_controls[hero]=control
   label=ttk.Label(control,text=hero+' plan');label.pack(side='left',padx=(0,8))
   box=ttk.Combobox(control,textvariable=self.flex_plans[hero],values=choices,state='readonly',width=17)
   box.pack(side='left',padx=(0,18));box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
  self.status=ttk.Label(self.draft,text='',foreground='#ffc982',wraplength=1100);self.status.pack(anchor='w',pady=10)
  self.draft.bind('<Configure>',lambda e:self.status.configure(wraplength=max(200,e.width-30)),add='+')
  result=ttk.Frame(self.draft);result.pack(fill='both',expand=True)
  self.pick_text=self.text_panel(result,'YOUR PICKS',0);self.ban_text=self.text_panel(result,'BAN CANDIDATES',1)
  footer=ttk.Frame(self.draft);footer.pack(fill='x',pady=(8,0))
  ttk.Button(footer,text='How suggestions work',command=self.draft_help).pack(side='right',padx=(12,0))
  ttk.Label(footer,text='Team fit + saved guide matchups. Your win rate is context, not a match prediction.\nPersonal records: selected mode, saved games only. Fewer than 20 games = small sample.',foreground=MUTED,wraplength=780).pack(side='left',anchor='w')

 def text_panel(self,parent,title,col):
  f=ttk.Frame(parent);f.grid(row=0,column=col,sticky='nsew',padx=(0,12 if col==0 else 0));parent.columnconfigure(col,weight=1,uniform='advice');parent.rowconfigure(0,weight=1)
  heading=ttk.Frame(f);heading.pack(fill='x',pady=(0,8))
  ttk.Label(heading,text='  '+title,image=self.art.icon('star' if col==0 else 'ban'),compound='left',font=('Segoe UI',10,'bold'),foreground=BLUE).pack(side='left')
  if col==0:
   mode=ttk.Combobox(heading,textvariable=self.pick_stats_mode,values=DRAFT_STAT_MODES,state='readonly',width=16)
   mode.pack(side='right');mode.bind('<<ComboboxSelected>>',self.pick_stats_changed)
   ttk.Label(heading,text='Your stats',foreground=MUTED).pack(side='right',padx=8)
  body=ttk.Frame(f,style='Card.TFrame');body.pack(fill='both',expand=True)
  text=tk.Text(body,bg=PANEL,fg=TEXT,wrap='word',height=10,width=30,font=('Segoe UI',10),padx=16,pady=10,relief='flat',state='disabled',cursor='arrow',spacing1=2)
  scroll=ttk.Scrollbar(body,command=text.yview);scroll.pack(side='right',fill='y')
  text.configure(yscrollcommand=scroll.set);text.pack(fill='both',expand=True)
  return text

 def put(self,widget,text):
  if widget.get('1.0','end-1c')==text:return
  widget.config(state='normal');widget.delete('1.0','end');widget.insert('1.0',text)
  widget.tag_configure('heading',foreground=BLUE,font=('Segoe UI',13,'bold'),spacing1=7,spacing3=6)
  widget.tag_configure('note',foreground=MUTED)
  widget.tag_configure('record',foreground='#cfb9ff',font=('Segoe UI',10),spacing3=5)
  widget.tag_configure('level',foreground=PURPLE,font=('Segoe UI',12,'bold'),spacing1=1,spacing3=1)
  widget.tag_configure('warning',foreground='#ffc982',spacing1=4)
  widget.tag_configure('plan',foreground=PURPLE,spacing1=4)
  for line,value in enumerate(text.split('\n'),1):
   match=re.match(r'\d+\. (.+?)  ·  ',value)
   if match:
    widget.tag_add('heading',f'{line}.0',f'{line}.end')
    widget.image_create(f'{line}.0',image=self.art.portrait(match.group(1),30),padx=8,align='center')
   elif value.endswith(' · TALENTS') or value in ('MATCH NOTES','MATCH ADJUSTMENTS','WHY THESE TALENTS') or value.startswith('Waiting for'):
    widget.tag_add('heading',f'{line}.0',f'{line}.end')
   elif value.startswith('Level '):
    widget.tag_add('level',f'{line}.0',f'{line}.{len(value.split(chr(9),1)[0].rstrip())}')
   elif value.startswith('Your record:'):
    widget.tag_add('record',f'{line}.0',f'{line}.end')
   elif value.startswith(('Watch out:','Lower priority:')):
    widget.tag_add('warning',f'{line}.0',f'{line}.end')
   elif value.startswith(('Plan:','Preference:')):
    widget.tag_add('plan',f'{line}.0',f'{line}.end')
   elif value.startswith(('Source:','Guide updated:','Guide category:','Auto uses','Manual choice:','• ')):
    widget.tag_add('note',f'{line}.0',f'{line}.end')
  widget.config(state='disabled')

 def draft_help(self):
  messagebox.showinfo('How suggestions work',
   'Picks start with the roles and lane coverage your team needs. With few slots left, covering tank and healer takes priority. '
   'Next come named synergies, enemy counters, ability interactions and the map. Watch out highlights drawbacks.\n\n'
   'Bans evaluate who would fit the enemy team, with extra weight on threats to your known picks. '
   'Your ownership and Never suggest choices affect your picks only. Cho/Gall need a coordinated pair and are not suggested.\n\n'
   'A favourite only gets a small tie-break when already close to the best fit. Personal win rates do not change the order. '
   'There is no online win-rate feed or predicted win percentage.\n\n'
   f'Matchup source: {len(GUIDANCE)} saved Icy Veins hero guides, imported 19 September 2026. '
   'Teammate hovers reserve their planned heroes and roles, but stay separate from locked picks. Your own hover is excluded. '
   'Set your player name or slot so the reader can distinguish your hover from your teammates. Hovers can change; recheck suggestions when they do.\n\n'
   'Guide opinions are partial and can depend on talents or playstyle; they are not measured matchup win rates. '
   'Open talent guide on a hero’s Talents & tips page for its Synergies and Counters section. '
   'Future patches need a content update. Equal fits sort alphabetically.')

 def update_flex_controls(self,allies,enemies):
  present=set(allies+enemies)
  for hero,control in self.flex_controls.items():
   if hero in present:
    control.winfo_children()[0].configure(text=('Your ' if hero in allies else 'Enemy ')+hero+' plan')
    if not control.winfo_manager():control.pack(side='left')
   else:
    control.pack_forget();self.flex_plans[hero].set('Unconfirmed')
  if present & set(FLEX_CHOICES):
   if not self.flex_bar.winfo_manager():self.flex_bar.pack(fill='x',before=self.status,pady=(10,0))
  else:self.flex_bar.pack_forget()

 def make_pool(self):
  ttk.Label(self.pool,text='Make the roster yours',font=('Segoe UI',20,'bold')).pack(anchor='w')
  ttk.Label(self.pool,text='Favourites get a boost when they fit the draft. Never suggest hides heroes from your picks.',foreground=MUTED).pack(anchor='w',pady=8)
  row=ttk.Frame(self.pool);row.pack(fill='x',pady=(4,8))
  ttk.Label(row,text='Search heroes').pack(side='left',padx=(0,8))
  self.search=tk.StringVar();self.pool_filter=tk.StringVar(value='All preferences')
  self.search.trace_add('write',lambda *a:self.fill_pool())
  search=ttk.Entry(row,textvariable=self.search,width=28);search.pack(side='left')
  search.bind('<Escape>',lambda e:self.search.set(''))
  ttk.Label(row,text='Show').pack(side='left',padx=(18,8))
  picker=ttk.Combobox(row,textvariable=self.pool_filter,values=['All preferences','Favourite','Allowed','Never suggest'],state='readonly',width=18)
  picker.pack(side='left');picker.bind('<<ComboboxSelected>>',lambda e:self.fill_pool())
  ttk.Button(row,text='Reset filters',command=self.reset_pool_filters).pack(side='left',padx=8)
  table=ttk.Frame(self.pool);table.pack(fill='both',expand=True)
  self.tree=ttk.Treeview(table,columns=('hero','role','preference'),show='tree headings',selectmode='extended',style='Roster.Treeview')
  self.tree.column('#0',width=38,minwidth=38,stretch=False);self.tree.heading('#0',text='')
  for key,label,width in [('hero','Hero',320),('role','Role',240),('preference','Preference',260)]:
   self.tree.heading(key,text=label,anchor='w');self.tree.column(key,width=width,minwidth=130,anchor='w')
  scroll=ttk.Scrollbar(table,command=self.tree.yview);scroll.pack(side='right',fill='y')
  self.tree.configure(yscrollcommand=scroll.set);self.tree.pack(fill='both',expand=True)
  buttons=ttk.Frame(self.pool);buttons.pack(side='bottom',fill='x',pady=12,before=table)
  self.preference_buttons=[]
  for mode in ('Favourite','Allowed','Never suggest'):
   button=ttk.Button(buttons,text=mode,command=lambda m=mode:self.set_pref(m),state='disabled');button.pack(side='left',padx=(0,8));self.preference_buttons.append(button)
  self.pool_status=ttk.Label(self.pool,text='',foreground=MUTED);self.pool_status.pack(side='bottom',anchor='w',before=table)
  self.tree.bind('<<TreeviewSelect>>',lambda e:self.pool_selection_changed())
  self.fill_pool()

 def reset_pool_filters(self):
  self.pool_filter.set('All preferences');self.search.set('')

 def pool_selection_changed(self):
  count=len(self.tree.selection())
  for button in self.preference_buttons:button.configure(state='normal' if count else 'disabled')

 def fill_pool(self,reset_scroll=True):
  if not hasattr(self,'tree'):return
  selected=self.tree.selection();position=self.tree.yview()
  self.tree.delete(*self.tree.get_children())
  for i,hero in enumerate(sorted(HEROES)):
   if self.search.get().strip().casefold() in hero.casefold() and (self.pool_filter.get()=='All preferences' or self.prefs.get(hero,'Allowed')==self.pool_filter.get()):
    self.tree.insert('', 'end',iid=hero,image=self.art.portrait(hero),values=(hero,HEROES[hero]['role'],self.prefs.get(hero,'Allowed')),tags=(stripe(self.tree,i),))
  self.tree.selection_set([hero for hero in selected if self.tree.exists(hero)])
  if not reset_scroll and position:self.tree.yview_moveto(position[0])
  empty_table(self.tree,'No heroes match these filters.\nTry Reset filters.')
  self.pool_status.config(text=f'{len(self.tree.get_children())} of {len(HEROES)} heroes · Select a row to change its preference. Ctrl-click selects several.')
  self.pool_selection_changed()

 def set_pref(self,mode):
  selected=self.tree.selection()
  if not selected:self.pool_status.config(text='Select one or more heroes first.');return
  for name in selected:self.prefs[name]=mode
  result=f'Saved {len(selected)} hero(s) as {mode}.'
  try:
   temp=SAVE.with_suffix('.tmp');temp.write_text(json.dumps(self.prefs,indent=2),encoding='utf-8');temp.replace(SAVE)
  except OSError as exc:
   result='Preferences changed for this session only; saving failed.'
   messagebox.showerror('Unable to save',f'Preferences apply for this session but could not be saved: {exc}')
  self.fill_pool(reset_scroll=False);self.refresh()
  self.pool_status.config(text=result)

 def make_build(self):
  banner=ttk.Frame(self.build,style='Card.TFrame',padding=(16,12));banner.pack(fill='x',pady=(0,14))
  self.build_portrait=ttk.Label(banner,image=self.art.icon('build',24),style='Card.TLabel');self.build_portrait.pack(side='left',padx=(0,16))
  banner_text=ttk.Frame(banner,style='Card.TFrame');banner_text.pack(side='left')
  self.build_name=ttk.Label(banner_text,text='Your next hero',style='Card.TLabel',font=('Segoe UI',21,'bold'));self.build_name.pack(anchor='w')
  self.build_role=ttk.Label(banner_text,text='Builds and advice for this match',foreground=MUTED,style='Card.TLabel');self.build_role.pack(anchor='w')
  bar=ttk.Frame(self.build);bar.pack(fill='x')
  ttk.Label(bar,text='Playing').pack(side='left',padx=(0,8));self.playing=tk.StringVar(value='Johanna')
  self.combo(bar,self.playing,sorted(HEROES),25).pack(side='left')
  ttk.Checkbutton(bar,text='Follow my locked hero',variable=self.follow_hero,command=self.follow_changed).pack(side='left',padx=12)
  self.guide_button=ttk.Button(bar,text='Open talent guide',command=lambda:webbrowser.open(guide_url(self.playing.get())))
  self.guide_button.pack(side='left',padx=12)
  buildbar=ttk.Frame(self.build);buildbar.pack(fill='x',pady=(10,0))
  ttk.Label(buildbar,text='Build').pack(side='left',padx=(0,22))
  self.build_variant=tk.StringVar(value=AUTO_BUILD);self.variant_hero=None
  self.build_picker=ttk.Combobox(buildbar,textvariable=self.build_variant,state='readonly',width=34)
  self.build_picker.pack(side='left');self.build_picker.bind('<<ComboboxSelected>>',lambda e:self.refresh())
  ttk.Label(buildbar,text=f'{len(PROFILES)} heroes · {BUILD_COUNT} builds · tips included',foreground=MUTED).pack(side='left',padx=12)
  self.hero_status=ttk.Label(self.build,text='',foreground=BLUE,wraplength=1100);self.hero_status.pack(anchor='w',pady=(0,10))
  self.build.bind('<Configure>',lambda e:self.hero_status.configure(wraplength=max(200,e.width-38)))
  content=ttk.Frame(self.build);content.pack(fill='both',expand=True)
  self.build_text=tk.Text(content,bg=PANEL,fg=TEXT,font=('Segoe UI',12),padx=22,pady=18,wrap='word',relief='flat',state='disabled',cursor='arrow',spacing1=3,spacing3=3)
  self.build_text.configure(tabs=(tkfont.Font(root=self.root,font=('Segoe UI',12,'bold')).measure('Level 20')+22,))
  scroll=ttk.Scrollbar(content,command=self.build_text.yview);scroll.pack(side='right',fill='y')
  self.build_text.configure(yscrollcommand=scroll.set);self.build_text.pack(fill='both',expand=True)
  self.update_own_hero()

 def clear(self):
  self.generation+=1;self.manual.clear();self.previous_sample.clear();self.detected_map=None
  self.clear_hovers()
  self.previous_self_slot=None;self.detected_self_slot=None;self.last_read={}
  self.reader_notice=''
  self.follow_hero.set(True)
  self.build_variant.set(AUTO_BUILD);self.variant_hero=None
  self.map.set('Unknown map')
  for plan in self.flex_plans.values():plan.set('Unconfirmed')
  for v in self.allies+self.enemies+self.bans:v.set('')
  if hasattr(self,'live_status'):self.live_status.config(text='Draft cleared. Ready for the next match.')
  self.update_own_hero()
  self.refresh()

 def refresh(self):
  if not hasattr(self,'build_text'):return
  self.update_draft_warning()
  self.load_pick_stats()
  for variable,label,col in self.slot_portraits:
   label.configure(image=self.art.portrait(variable.get(),30) if variable.get() else self.art.icon('ban' if col==2 else 'heroes',24))
  allies=[v.get() for v in self.allies if v.get()];enemies=[v.get() for v in self.enemies if v.get()];bans=[v.get() for v in self.bans if v.get()]
  tentative=self.planned_hovers()
  hover_heroes=list(tentative.values())
  hover_text='Teammate hovers · '+', '.join(f'Slot {i+1}: {h}' for i,h in tentative.items())+' · Included as tentative picks.' if tentative else ''
  if self.ally_hovers and self.own_slot() is None: hover_text='Hovers detected. Set your player name or slot above to include teammates without counting your own hover.'
  self.hover_status.configure(text=hover_text)
  error=validate(allies,enemies,bans)
  self.update_flex_controls(allies+hover_heroes,enemies)
  plans={hero:var.get() for hero,var in self.flex_plans.items()}
  final=self.last_read.get('phase')=='starting'
  self.ban_notice.configure(text='Draft finished. Bans are retained from earlier readings; they are not shown on the final-team screen.' if final else 'Only confirmed bans are listed. Blank ban slots may be skipped or unread; check them in HotS.')
  self.status.config(text=error or draft_summary(allies,enemies,plans,hover_heroes,final=final))
  if error:
   self.put(self.pick_text,'Fix the draft above to see suggestions.');self.put(self.ban_text,'Fix the draft above to see suggestions.');self.put(self.build_text,'Fix duplicate or invalid draft entries first.');return
  for is_ban,widget in [(False,self.pick_text),(True,self.ban_text)]:
   own=self.own_slot()
   if not is_ban and own is not None and self.allies[own].get():
    next_step='Talents & tips follows your hero and the enemy picks.' if self.follow_hero.get() else 'Automatic build following is paused. Enable Follow my locked hero in Talents & tips to resume.'
    self.put(widget,f'Your locked hero: {self.allies[own].get()}\n'+self.pick_record(self.allies[own].get())+'\n\n'+next_step);continue
   if final:
    self.put(widget,'Draft finished; no further bans.' if is_ban else 'Draft finished. Your locked hero has not been identified yet. Correct your slot and the highlighted hero entries above.');continue
   complete=len(enemies if is_ban else allies)==5 or (is_ban and len(bans)==6)
   results=rank(allies,enemies,bans,self.prefs,self.map.get(),self.role.get(),is_ban,available=self.available_heroes(),plans=plans,ally_hovers=hover_heroes)
   lines=[]
   for i,x in enumerate(results[:3]):
    record='' if is_ban else self.pick_record(x['hero'])
    lines.append(recommendation_text(x,i+1,record,is_ban))
   self.put(widget,('Bans complete; no further draft ban needed.' if is_ban else 'All five allies entered. Review your build.') if complete else '\n'.join(lines) or 'No eligible heroes. Adjust your role, collection filter or hero preferences.')
  own=self.own_slot()
  hero=self.playing.get()
  # A different hero must never inherit another hero's selected build.
  # Enemy updates retain a manual variant, while Auto can adjust supported tiers.
  if self.variant_hero != hero:
   self.variant_hero=hero;self.build_variant.set(AUTO_BUILD)
   self.build_picker.configure(values=[AUTO_BUILD]+build_names(hero))
  if self.follow_hero.get() and (own is None or not self.allies[own].get()):
   self.build_picker.configure(state='disabled')
   self.guide_button.configure(state='disabled')
   self.build_name.config(text='Your hero is unread' if final else 'Waiting for your pick');self.build_role.config(text='Correct your slot or hero in Draft advisor.' if final else 'Lock a hero to see your build and matchup tips.')
   self.build_portrait.config(image=self.art.icon('build',24))
   self.put(self.build_text,('Draft finished, but your locked hero has not been read.\n\nCorrect your slot and hero in Draft advisor, or choose a hero above to browse its build.' if final else 'Waiting for your locked hero.\n\nStart the live reader. Your player name is '+self.player_name.get()+'. The build will switch automatically when your pick is confirmed.\n\nTo browse builds now, choose a hero above.'));return
  self.build_picker.configure(state='readonly')
  self.guide_button.configure(state='normal')
  detail=build_details(hero,enemies,self.build_variant.get(),allies=allies,plans=plans)
  self.build_name.config(text=hero);self.build_role.config(text=HEROES[hero]['role']+'  /  MATCH GUIDE')
  self.build_portrait.config(image=self.art.portrait(hero,60))
  if detail:
   content=detail['name'].upper()+' · TALENTS\n\n'+'\n'.join(f"Level {tier['level']} \t{tier['talent']}" for tier in detail['tiers'])
   if detail['automatic']:
    content+='\n\nWHY THESE TALENTS\n\n'
    content+='\n\n'.join('• '+n for n in detail['selection_reasons']) or ('Enemy picks are not known yet; using the saved starter build.' if not enemies else 'No specific matchup rule applies here; keeping the saved guide choices.')
    content+='\n\nBased on '+str(len(enemies))+'/5 enemy picks: '+(', '.join(enemies) or 'none yet')+'. Recommendations update as picks are confirmed.'
   notes=list(detail['notes'])
   if HEROES[hero]['role']=='Healer' and 'Deathwing' in allies:notes.append('Deathwing cannot receive your healing.')
   content+='\n\nMATCH NOTES\n\n'+'\n\n'.join('• '+n for n in notes)
   content+='\n\nGuide category: '+detail['category']
   if detail['automatic']:content+='\nAuto selects recommended talents here in the companion; it does not click talents in HotS. Matchup rules cover supported choices; other tiers keep their saved guide defaults.'
   else:content+='\nManual choice: this build stays selected as enemy picks change. Its talents are not automatically replaced.'
   content+='\nSource: Icy Veins · '+detail['source']+'\nGuide updated: '+detail['source_updated']+' · Imported: '+detail['checked']
   content+='\nSaved for offline use. Future patch changes require a catalogue update.'
  else:content=hero+'\n\nNo saved guide is available. Use Open talent guide.'
  self.put(self.build_text,content)

if __name__=='__main__':
 from launcher import main
 main()
