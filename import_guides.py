"""Maintainer tool: extract factual talent choices from public guide pages.

This is not run by the app. Cached pages are research material, not distributed
guide content. Original guide prose is not bundled in the build catalogue.
"""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re
import time
import unicodedata
import urllib.request

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'.guide-cache'

class Node:
    def __init__(self,tag='',attrs=(),parent=None):
        self.tag,self.attrs,self.parent=tag,dict(attrs),parent
        self.children=[]
    def text(self):
        return ''.join(c if isinstance(c,str) else c.text() for c in self.children).strip()
    def find(self,tag=None,cls=None):
        found=[]
        for c in self.children:
            if isinstance(c,Node):
                if (tag is None or c.tag==tag) and (cls is None or cls in c.attrs.get('class','').split()):found.append(c)
                found.extend(c.find(tag,cls))
        return found

class Page(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True)
        self.root=Node();self.current=self.root;self.feed(html)
    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs,self.current);self.current.children.append(node)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
            self.current=node
    def handle_endtag(self,tag):
        node=self.current
        while node.parent is not None:
            if node.tag==tag:
                self.current=node.parent;return
            node=node.parent
    def handle_data(self,data):self.current.children.append(data)

def slug(hero):
    special={'E.T.C.':'e-t-c',"Kel'Thuzad":'kel-thuzad'}
    if hero in special:return special[hero]
    text=unicodedata.normalize('NFKD',hero).encode('ascii','ignore').decode().lower()
    return re.sub('[^a-z0-9 -]','',text).replace(' ','-')

def extract(html,hero,url):
    root=Page(html).root
    dates=root.find(cls='local_date_date')
    variants=[]
    for block in root.find(cls='heroes_build'):
        headers=block.find('h3')
        if not headers:continue
        tags=block.find(cls='heroes_build_tag')
        tiers=[]
        for tier in block.find(cls='heroes_build_talent_tier'):
            level=int(re.search(r'\d+',tier.find(cls='heroes_build_talent_tier_subtitle')[0].text()).group())
            chosen=tier.find('a','heroes_build_talent_tier_recommended')
            if len(chosen)!=1:raise ValueError(f'{hero}: no unique choice at {level}')
            def name(link):return link.find('img')[0].attrs['alt'].removesuffix(' Icon')
            tiers.append({'level':level,'talent':name(chosen[0]),
                          'alternatives':[name(a) for a in tier.find('a','heroes_build_talent_tier_situational')]})
        if len(tiers)!=7 or len({t['level'] for t in tiers})!=7:raise ValueError(f'{hero}: incomplete build')
        variants.append({'name':headers[0].text(),'category':tags[0].text() if tags else 'Alternative',
                         'tiers':tiers})
    if not variants:raise ValueError(f'{hero}: no builds extracted')
    return {'source':url,'source_updated':dates[0].text() if dates else 'Not stated',
            'checked':date.today().isoformat(),'builds':variants}

def fetch(hero, refresh=True):
    url='https://www.icy-veins.com/heroes/'+slug(hero)+'-build-guide'
    path=CACHE/(slug(hero)+'.html')
    if refresh or not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=30) as response:html=response.read().decode('utf-8')
        CACHE.mkdir(exist_ok=True)
        path.write_text(html,encoding='utf-8');time.sleep(.3)
    else:html=path.read_text(encoding='utf-8')
    result=extract(html,hero,url)
    if not refresh:
        from datetime import datetime
        result['checked']=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return hero,result

if __name__=='__main__':
    raise SystemExit('Use python refresh_advice.py to stage a complete content review. This importer no longer overwrites live advice.')
