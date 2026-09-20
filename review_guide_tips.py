"""Print guide tips for editorial review only; never imported by the app."""
import sys
from import_guides import CACHE, Page, slug
from data import HEROES

for hero in sorted(HEROES)[int(sys.argv[1]):int(sys.argv[2])]:
    root=Page((CACHE/(slug(hero)+'.html')).read_text(encoding='utf-8')).root
    headings=[n for n in root.find('h2') if 'Tips and Tricks' in n.text()]
    print('\n'+hero.upper())
    if not headings:continue
    heading=headings[0].parent
    siblings=heading.parent.children
    for n in siblings[siblings.index(heading)+1:]:
        if isinstance(n,str):continue
        if n.find('h2'):break
        if n.tag=='ul':
            for tip in n.find('li'):print(' '.join(tip.text().split()))
