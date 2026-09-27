"""Shared visual system and local portraits; no runtime imaging dependencies."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from hero_ids import IDS

ROOT = Path(__file__).resolve().parent
# Same brass-and-charcoal palette as AddonForge. One accent (brass) is used for
# the active tab, the one primary button per screen and hero names in advice.
BG, PANEL, RAISED = '#191919', '#1f1f1e', '#272725'
BAR = '#1d1d1c'                      # header and status bar
TEXT, MUTED, DIM = '#e9e6de', '#a9a8a1', '#7b7a74'
LINE, LINE2 = '#2f2f2c', '#45443f'
ACCENT, ACCENT2, INK = '#d5ae61', '#e8c987', '#211a0e'
GREEN, RED, WARN = '#91bf82', '#d97b74', '#d9a852'
SELECT = '#3a3427'
# Older names still imported around the app.
BLUE, PURPLE, BORDER = ACCENT2, ACCENT, LINE
FONT = 'Segoe UI'


class Art:
    def __init__(self, root):
        self.root, self.cache, self.originals = root, {}, {}
        self.paths = {IDS.get(p.stem.removeprefix('storm_ui_glues_draft_portrait_')):p
                      for p in (ROOT/'assets').glob('storm_ui_glues_draft_portrait_*.png')}

    def icon(self, name, size=18):
        key = ('icon',name,size)
        if key not in self.cache:
            path = ROOT/'assets'/'ui'/f'{name}-{size}.png'
            self.cache[key] = tk.PhotoImage(master=self.root,file=str(path)) if path.exists() else tk.PhotoImage(master=self.root,width=size,height=size)
        return self.cache[key]

    def portrait(self, hero, size=30):
        key = ('hero',hero,size)
        if key not in self.cache:
            path = self.paths.get(hero)
            if path:
                if hero not in self.originals:
                    self.originals[hero] = tk.PhotoImage(master=self.root,file=str(path))
                original = self.originals[hero]
                # Display a square face crop. The original assets are unchanged.
                square = tk.PhotoImage(master=self.root,width=180,height=180)
                self.root.tk.call(str(square),'copy',str(original),'-from',0,0,180,180)
                self.cache[key] = square.subsample(max(1,180//size))
            else:
                self.cache[key] = self.blank(size)
        return self.cache[key]

    def blank(self, size=30):
        """An empty slot: a dim outlined square the size of a portrait."""
        key = ('blank',size)
        if key not in self.cache:
            image = tk.PhotoImage(master=self.root,width=size,height=size)
            image.put(RAISED,to=(0,0,size,size))
            for edge in ((0,0,size,1),(0,size-1,size,size),(0,0,1,size),(size-1,0,size,size)):
                image.put(LINE2,to=edge)
            self.cache[key] = image
        return self.cache[key]


class ScrollPage(ttk.Frame):
    """Keep dense pages accessible when the companion sits beside the game."""
    def __init__(self,parent,padding=(20,16,20,16)):
        super().__init__(parent)
        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0,borderwidth=0)
        self.scroll=ttk.Scrollbar(self,command=self.canvas.yview)
        self.canvas.pack(side='left',fill='both',expand=True)
        self.canvas.configure(yscrollcommand=self.autohide)
        self.body=ttk.Frame(self.canvas,padding=padding)
        self.window=self.canvas.create_window(0,0,window=self.body,anchor='nw')
        self.canvas.bind('<Configure>',self.resize)
        self.body.bind('<Configure>',self.resize)
        self.winfo_toplevel().bind('<MouseWheel>',self.wheel,add='+')

    def autohide(self,first,last):
        # A page that fits needs no scrollbar; showing an empty one is noise.
        if float(first)<=0 and float(last)>=1:
            if self.scroll.winfo_manager():self.scroll.pack_forget()
        elif not self.scroll.winfo_manager():
            self.scroll.pack(side='right',fill='y',before=self.canvas)
        self.scroll.set(first,last)

    def resize(self,event=None):
        self.canvas.itemconfigure(self.window,width=self.canvas.winfo_width(),
                                  height=max(self.canvas.winfo_height(),self.body.winfo_reqheight()))
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def wheel(self,event):
        if isinstance(event.widget,(tk.Text,ttk.Treeview,ttk.Combobox)):
            return
        widget=event.widget
        while widget is not None:
            if widget is self:
                if self.canvas.yview()!=(0.0,1.0):
                    self.canvas.yview_scroll(-int(event.delta/120),'units')
                return
            widget=getattr(widget,'master',None)


def _box(root,size,fill,edge,mark=None):
    # Six transparent pixels on the right keep the label off the box.
    image=tk.PhotoImage(master=root,width=size+6,height=size)
    image.put(edge,to=(0,0,size,size));image.put(fill,to=(1,1,size-1,size-1))
    if mark:
        # A small hand-set tick, 2px thick.
        for x,y in ((3,7),(4,8),(5,9),(6,8),(7,7),(8,6),(9,5),(10,4)):
            image.put(mark,to=(x,y,x+2,y+2))
    return image


def apply_theme(root):
    root.configure(bg=BG)
    root.option_add('*Toplevel.background',BG)
    root.option_add('*Text.background',BG)
    root.option_add('*Text.foreground',TEXT)
    root.option_add('*Text.insertBackground',TEXT)
    root.option_add('*Text.selectBackground',SELECT)
    root.option_add('*Text.selectForeground',TEXT)
    style = ttk.Style(root);style.theme_use('clam')
    style.configure('.',background=BG,foreground=TEXT,font=(FONT,10),borderwidth=0,focuscolor=BG)
    style.configure('TFrame',background=BG)
    style.configure('Bar.TFrame',background=BAR)
    # Kept for older callers; cards are no longer drawn as boxes.
    style.configure('Card.TFrame',background=BG)
    style.configure('TLabel',background=BG,foreground=TEXT)
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('Dim.TLabel',foreground=DIM,font=(FONT,9))
    style.configure('Card.TLabel',background=BG)
    style.configure('Bar.TLabel',background=BAR,foreground=MUTED,font=(FONT,9))
    style.configure('Section.TLabel',font=(FONT,10,'bold'),foreground=TEXT)
    style.configure('Eyebrow.TLabel',font=(FONT,9,'bold'),foreground=MUTED)

    style.configure('TButton',background=RAISED,foreground=TEXT,padding=(12,4),borderwidth=1,
                    lightcolor=RAISED,darkcolor=RAISED,bordercolor=LINE2,relief='flat',focuscolor=RAISED)
    style.map('TButton',background=[('disabled',PANEL),('pressed','#34322c'),('active','#302f2b')],
              bordercolor=[('disabled','#34332f'),('active','#5c5a52')],
              lightcolor=[('disabled',PANEL),('pressed','#34322c'),('active','#302f2b')],
              darkcolor=[('disabled',PANEL),('pressed','#34322c'),('active','#302f2b')],
              foreground=[('disabled',DIM)])
    style.configure('Primary.TButton',background=ACCENT,foreground=INK,font=(FONT,10,'bold'),
                    bordercolor=ACCENT,lightcolor=ACCENT,darkcolor=ACCENT,focuscolor=ACCENT)
    style.map('Primary.TButton',background=[('disabled',RAISED),('pressed','#c59d51'),('active','#e0bd78')],
              lightcolor=[('pressed','#c59d51'),('active','#e0bd78')],darkcolor=[('pressed','#c59d51'),('active','#e0bd78')],
              bordercolor=[('active','#e0bd78')])
    # Text-only buttons for secondary actions (help, links).
    for name,bg in (('Link.TButton',BG),('Support.TButton',BAR)):
        style.configure(name,background=bg,foreground=ACCENT2,padding=(2,1),borderwidth=0,relief='flat',
                        lightcolor=bg,darkcolor=bg,bordercolor=bg,font=(FONT,9),focuscolor=bg)
        style.map(name,background=[('active',bg),('pressed',bg)],foreground=[('active',TEXT),('disabled',DIM)],
                  lightcolor=[('active',bg)],darkcolor=[('active',bg)],bordercolor=[('active',bg)])

    # The notebook only switches pages; its tabs are drawn by tab_bar().
    style.configure('TNotebook',background=BG,borderwidth=0,tabmargins=0,bordercolor=BG,lightcolor=BG,darkcolor=BG)
    style.layout('TNotebook.Tab',[])
    style.layout('TNotebook',[('Notebook.client',{'sticky':'nswe'})])

    images=root._theme_images=[_box(root,14,PANEL,LINE2),_box(root,14,ACCENT,ACCENT,INK),
                               _box(root,14,RAISED,'#6a685f'),_box(root,14,BG,LINE)]
    style.element_create('Nexus.indicator','image',images[0],('disabled',images[3]),
                         ('selected',images[1]),('active',images[2]),border=0,sticky='')
    style.layout('TCheckbutton',[('Checkbutton.padding',{'sticky':'nswe','children':[
        ('Nexus.indicator',{'side':'left','sticky':''}),
        ('Checkbutton.label',{'side':'left','sticky':'nswe','children':[('Checkbutton.focus',{'sticky':'nswe'})]})]})])
    style.configure('TCheckbutton',background=BG,foreground=TEXT,padding=(0,2),focuscolor=BG)
    style.map('TCheckbutton',background=[('active',BG)],foreground=[('disabled',DIM)])
    style.configure('Bar.TCheckbutton',background=BAR,foreground=MUTED,font=(FONT,9))
    style.map('Bar.TCheckbutton',background=[('active',BAR)],foreground=[('active',TEXT)])

    for name in ('TEntry','TCombobox'):
        style.configure(name,fieldbackground=PANEL,background=PANEL,foreground=TEXT,arrowcolor=MUTED,
                        insertcolor=TEXT,selectbackground=SELECT,selectforeground=TEXT,arrowsize=11,
                        bordercolor=LINE2,lightcolor=PANEL,darkcolor=PANEL,borderwidth=1,padding=(6,3))
        style.map(name,fieldbackground=[('disabled',BG),('readonly',PANEL),('!disabled',PANEL)],
                  foreground=[('disabled',DIM),('!disabled',TEXT)],bordercolor=[('focus',ACCENT),('hover','#5c5a52'),('!focus',LINE2)],
                  lightcolor=[('focus',PANEL)],darkcolor=[('focus',PANEL)],
                  background=[('active',PANEL),('!active',PANEL)],arrowcolor=[('disabled',DIM),('active',TEXT)])
    for option,value in [('background',PANEL),('foreground',TEXT),('selectBackground',SELECT),
                         ('selectForeground',TEXT),('font',(FONT,10)),('borderWidth',0)]:
        root.option_add('*TCombobox*Listbox.'+option,value)
    # A flat combobox field inside the draft slots.
    style.configure('Slot.TCombobox',fieldbackground=BG,background=BG,bordercolor=BG,lightcolor=BG,darkcolor=BG,
                    arrowcolor=DIM,padding=(4,2))
    style.map('Slot.TCombobox',fieldbackground=[('readonly',BG)],background=[('active',BG),('!active',BG)],
              bordercolor=[('focus',LINE2),('hover',LINE2),('!focus',BG)],arrowcolor=[('hover',TEXT),('!hover',DIM)])

    style.configure('Treeview',background=BG,fieldbackground=BG,foreground=TEXT,rowheight=32,
                    borderwidth=0,font=(FONT,10),bordercolor=BG,lightcolor=BG,darkcolor=BG)
    style.configure('Treeview.Heading',background=BG,foreground=DIM,padding=(8,6),
                    font=(FONT,9),relief='flat',borderwidth=0,bordercolor=LINE,lightcolor=BG,darkcolor=LINE)
    style.map('Treeview',background=[('selected',SELECT)],foreground=[('selected','#fff7e7')])
    style.map('Treeview.Heading',background=[('active',BG)],foreground=[('active',TEXT)])
    style.configure('Roster.Treeview.Heading',padding=(4,6))
    style.layout('Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
    style.layout('Treeview.Item',[('Treeitem.padding',{'sticky':'nswe','children':[
        ('Treeitem.image',{'side':'left','sticky':''}),('Treeitem.text',{'side':'left','sticky':''})]})])

    # Thin arrowless scrollbars.
    for orient,side in (('Vertical','ns'),('Horizontal','ew')):
        style.layout(orient+'.TScrollbar',[(orient+'.Scrollbar.trough',{'sticky':side,'children':[
            (orient+'.Scrollbar.thumb',{'expand':'1','sticky':'nswe'})]})])
    style.configure('TScrollbar',background='#3b3a36',troughcolor=BG,borderwidth=0,arrowsize=9,gripcount=0,
                    lightcolor='#3b3a36',darkcolor='#3b3a36',bordercolor=BG,troughborderwidth=0,relief='flat')
    style.map('TScrollbar',background=[('active','#56554e')],lightcolor=[('active','#56554e')],darkcolor=[('active','#56554e')])
    style.configure('TPanedwindow',background=BG,sashwidth=12)
    style.configure('TSeparator',background=LINE)
    return style


class TabBar(tk.Frame):
    """Text tabs in the header, driving a notebook whose own tabs are hidden."""
    def __init__(self,parent,notebook,names):
        super().__init__(parent,bg=BAR)
        self.notebook,self.items=notebook,[]
        for index,name in enumerate(names):
            cell=tk.Frame(self,bg=BAR,cursor='hand2')
            cell.pack(side='left',fill='y',padx=(0 if index==0 else 4,0))
            label=tk.Label(cell,text=name,bg=BAR,fg=MUTED,font=(FONT,10),padx=10,cursor='hand2')
            label.pack(side='top',fill='both',expand=True)
            rule=tk.Frame(cell,height=2,bg=BAR);rule.pack(side='bottom',fill='x')
            for widget in (cell,label):
                widget.bind('<Button-1>',lambda e,i=index:self.notebook.select(i))
                widget.bind('<Enter>',lambda e,i=index:self.hover(i,True))
                widget.bind('<Leave>',lambda e,i=index:self.hover(i,False))
            self.items.append((label,rule))
        notebook.bind('<<NotebookTabChanged>>',lambda e:self.update(),add='+')
        self.update()

    def current(self):
        try:return self.notebook.index('current')
        except tk.TclError:return 0

    def hover(self,index,inside):
        if index!=self.current():
            self.items[index][0].configure(fg=TEXT if inside else MUTED)

    def update(self):
        selected=self.current()
        for index,(label,rule) in enumerate(self.items):
            label.configure(fg=ACCENT2 if index==selected else MUTED)
            rule.configure(bg=ACCENT if index==selected else BAR)


def stripe(tree,index):
    # Hairline-quiet tables: no zebra striping; rows separate by spacing.
    tree.tag_configure('even',background=BG)
    tree.tag_configure('odd',background=BG)
    return 'odd' if index%2 else 'even'


def empty_table(tree, message):
    """Explain empty tables without adding fake, selectable hero/match rows."""
    if not hasattr(tree, '_empty_label'):
        tree._empty_label = ttk.Label(tree, foreground=MUTED, justify='center')
        tree.bind('<Configure>', lambda e: tree._empty_label.configure(wraplength=max(180,e.width-40)), add='+')
    tree._empty_label.configure(text=message)
    if tree.get_children():
        tree._empty_label.place_forget()
    else:
        tree._empty_label.place(relx=.5, rely=.55, anchor='center')


def section(parent,title,right=None):
    """A section heading with a hairline under it; returns the heading row."""
    row=ttk.Frame(parent,height=28);row.pack(fill='x');row.pack_propagate(False)
    ttk.Label(row,text=title,style='Section.TLabel').pack(side='left',anchor='s',pady=(0,4))
    ttk.Separator(parent).pack(fill='x',pady=(0,8))
    return row


def metric(parent,icon,label,color):
    """Retained for compatibility: an inline number + label, no card."""
    card=ttk.Frame(parent)
    value=ttk.Label(card,text='—',font=(FONT,10,'bold'),foreground=color);value.pack(side='left')
    ttk.Label(card,text=label,foreground=MUTED).pack(side='left',padx=(5,0))
    return card,value
