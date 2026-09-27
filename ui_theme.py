"""Shared visual system and local portraits; no runtime imaging dependencies."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from hero_ids import IDS

ROOT = Path(__file__).resolve().parent
# Shared with AddonForge: quiet charcoal surfaces and a single brass accent.
BG, PANEL, RAISED = '#191919', '#20201f', '#292927'
TEXT, MUTED, BLUE = '#eeeae2', '#b1b0a9', '#e8c987'
BORDER, GREEN, RED, PURPLE = '#363632', '#91bf82', '#d97b74', '#d5ae61'


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
                self.cache[key] = self.icon('heroes',24)
        return self.cache[key]


class ScrollPage(ttk.Frame):
    """Keep dense pages accessible when the companion sits beside the game."""
    def __init__(self,parent,padding=14):
        super().__init__(parent)
        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0,borderwidth=0)
        self.scroll=ttk.Scrollbar(self,command=self.canvas.yview)
        self.scroll.pack(side='right',fill='y')
        self.canvas.pack(fill='both',expand=True)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.body=ttk.Frame(self.canvas,padding=padding)
        self.window=self.canvas.create_window(0,0,window=self.body,anchor='nw')
        self.canvas.bind('<Configure>',self.resize)
        self.body.bind('<Configure>',self.resize)
        self.winfo_toplevel().bind('<MouseWheel>',self.wheel,add='+')

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


def apply_theme(root):
    root.configure(bg=BG)
    root.option_add('*Toplevel.background',BG)
    root.option_add('*Text.background',PANEL)
    root.option_add('*Text.foreground',TEXT)
    root.option_add('*Text.insertBackground',TEXT)
    root.option_add('*Text.selectBackground','#574624')
    root.option_add('*Text.selectForeground',TEXT)
    style = ttk.Style(root);style.theme_use('clam')
    style.configure('.',background=BG,foreground=TEXT,font=('Segoe UI',10),borderwidth=0)
    style.configure('TFrame',background=BG)
    style.configure('Card.TFrame',background=PANEL,relief='solid',borderwidth=1,
                    bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
    style.configure('TLabel',background=BG,foreground=TEXT)
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('Card.TLabel',background=PANEL)
    style.configure('Eyebrow.TLabel',font=('Segoe UI',9,'bold'),foreground=MUTED)
    style.configure('TButton',background=RAISED,foreground=TEXT,padding=(10,6),borderwidth=1,
                    lightcolor=BORDER,darkcolor=BORDER,bordercolor=BORDER,focuscolor=BLUE,relief='solid')
    style.map('TButton',background=[('disabled',PANEL),('pressed','#3a352a'),('active','#33312b')],
              foreground=[('disabled','#77746b')])
    style.configure('Primary.TButton',background='#d5ae61',foreground='#211a0e',font=('Segoe UI',10,'bold'),
                    borderwidth=1,bordercolor='#d5ae61',lightcolor='#d5ae61',darkcolor='#d5ae61')
    style.map('Primary.TButton',background=[('disabled',PANEL),('pressed','#c59d51'),('active','#e0bd78')])
    style.configure('Support.TButton',background=BG,foreground=PURPLE,font=('Segoe UI',9),padding=(8,4),borderwidth=0)
    style.map('Support.TButton',background=[('pressed',RAISED),('active',PANEL)],foreground=[('active',TEXT)])
    style.configure('TNotebook',background=BG,borderwidth=0,tabmargins=(0,0,0,7),bordercolor=BG,lightcolor=BG,darkcolor=BG)
    style.configure('TNotebook.Tab',background=BG,foreground=MUTED,padding=(12,8),borderwidth=0,
                    font=('Segoe UI',10),focuscolor=BLUE,bordercolor=BG,lightcolor=BG,darkcolor=BG)
    style.map('TNotebook.Tab',background=[('selected',BG),('active',BG)],
              foreground=[('selected',TEXT),('active',TEXT)],padding=[('selected',(12,8))],
              font=[('selected',('Segoe UI',10,'bold'))])
    # Clam draws pale tab edges even with a dark border colour. Use flat fills.
    tab_images=[]
    idle=tk.PhotoImage(master=root,width=8,height=8);idle.put(BG,to=(0,0,8,8))
    selected=tk.PhotoImage(master=root,width=8,height=8);selected.put(BG,to=(0,0,8,8));selected.put('#d5ae61',to=(0,7,8,8))
    hover=tk.PhotoImage(master=root,width=8,height=8);hover.put('#20201f',to=(0,0,8,8))
    tab_images.extend((idle,selected,hover))
    root._tab_images=tab_images
    style.element_create('Nexus.tab','image',tab_images[0],('selected',tab_images[1]),
                         ('active',tab_images[2]),border=0,sticky='nsew')
    style.layout('TNotebook.Tab',[('Nexus.tab',{'sticky':'nswe','children':[
        ('Notebook.padding',{'side':'top','sticky':'nswe','children':[
            ('Notebook.focus',{'side':'top','sticky':'nswe','children':[
                ('Notebook.label',{'side':'top','sticky':''})]})]})]})])
    style.configure('TCheckbutton',background=BG,foreground=MUTED,indicatorbackground=PANEL,
                    indicatorforeground=BG,upperbordercolor=BORDER,lowerbordercolor=BORDER,focuscolor=BLUE)
    style.map('TCheckbutton',background=[('active',BG),('!active',BG)],foreground=[('disabled','#77746b'),('active',TEXT)],
              indicatorbackground=[('disabled',PANEL),('selected',BLUE),('!selected',RAISED)])
    for name in ('TEntry','TCombobox'):
        style.configure(name,fieldbackground=BG,background=RAISED,foreground=TEXT,arrowcolor=MUTED,
                        insertcolor=TEXT,selectbackground='#574624',selectforeground=TEXT,
                        bordercolor=BORDER,lightcolor=PANEL,darkcolor=PANEL,borderwidth=1,padding=5)
        style.map(name,fieldbackground=[('disabled',BG),('readonly',PANEL),('!disabled',PANEL)],
                  foreground=[('disabled','#77746b'),('!disabled',TEXT)],bordercolor=[('focus',BLUE),('!focus',BORDER)],
                  background=[('active','#3a352a'),('!active',RAISED)])
    for option,value in [('background',PANEL),('foreground',TEXT),('selectBackground','#574624'),('selectForeground',TEXT)]:
        root.option_add('*TCombobox*Listbox.'+option,value)
    style.configure('Treeview',background=BG,fieldbackground=BG,foreground=TEXT,rowheight=34,
                    borderwidth=0,font=('Segoe UI',10),bordercolor=BG,lightcolor=BG,darkcolor=BG)
    style.configure('Treeview.Heading',background=BG,foreground='#999a93',padding=(10,7),
                    font=('Segoe UI',9),relief='flat',borderwidth=0)
    style.map('Treeview',background=[('selected','#3b352a')],foreground=[('selected','#fff7e7')])
    style.map('Treeview.Heading',background=[('active',RAISED)])
    style.configure('Roster.Treeview.Heading',padding=(4,9))
    style.layout('Treeview.Item',[('Treeitem.padding',{'sticky':'nswe','children':[
        ('Treeitem.image',{'side':'left','sticky':''}),('Treeitem.text',{'side':'left','sticky':''})]})])
    style.configure('TScrollbar',background='#505049',troughcolor=BG,borderwidth=0,arrowsize=12,
                    arrowcolor=MUTED,lightcolor=BG,darkcolor=BG,bordercolor=BG,troughborderwidth=0)
    style.map('TScrollbar',background=[('active','#77746b')])
    style.configure('TPanedwindow',background=BG,sashwidth=12)
    style.configure('TSeparator',background=BORDER)
    return style


def stripe(tree,index):
    tree.tag_configure('even',background=BG)
    tree.tag_configure('odd',background='#1d1e1d')
    return 'odd' if index%2 else 'even'


def empty_table(tree, message):
    """Explain empty tables without adding fake, selectable hero/match rows."""
    if not hasattr(tree, '_empty_label'):
        tree._empty_label = ttk.Label(tree, style='Card.TLabel', foreground=MUTED, justify='center')
        tree.bind('<Configure>', lambda e: tree._empty_label.configure(wraplength=max(180,e.width-40)), add='+')
    tree._empty_label.configure(text=message)
    if tree.get_children():
        tree._empty_label.place_forget()
    else:
        tree._empty_label.place(relx=.5, rely=.55, anchor='center')


def metric(parent,icon,label,color):
    card=ttk.Frame(parent,style='Card.TFrame',padding=(14,10))
    ttk.Label(card,image=icon,style='Card.TLabel').pack(side='left',padx=(0,10))
    body=ttk.Frame(card,style='Card.TFrame');body.pack(side='left',fill='x')
    value=ttk.Label(body,text='—',font=('Segoe UI',20,'bold'),foreground=color,style='Card.TLabel');value.pack(anchor='w')
    ttk.Label(body,text=label,foreground=MUTED,font=('Segoe UI',9),style='Card.TLabel').pack(anchor='w')
    return card,value
