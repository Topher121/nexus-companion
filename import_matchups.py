"""Maintainer-only extraction of named guide relationships; never run during play.

Uses the already reviewed guide cache. Saves names and provenance, not guide prose.
Counter lists are directional: a hero's list names heroes that counter THEM.
"""
import json
from pathlib import Path
from data import HEROES, MAPS
from build_library import PROFILES
from import_guides import Page, slug

ROOT = Path(__file__).resolve().parent
ALIASES = {'Deckard Cain': 'Deckard', 'Lt. Morales': 'Lt. Morales', 'Lucio': 'Lúcio'}


def extract_matchups(html, hero):
    root = Page(html).root
    result = {}
    for key, cls in [('synergies', 'heroes_synergies'), ('countered_by', 'heroes_counters'),
                     ('strong_maps', 'heroes_maps_stronger'), ('weak_maps', 'heroes_maps_weaker')]:
        blocks = root.find(cls=cls)
        if len(blocks) != 1:
            raise ValueError(f'{hero}: expected exactly one {cls} section')
        names = []
        for img in blocks[0].find('img'):
            if key in ('synergies', 'countered_by') and 'hero_portrait' not in img.attrs.get('class', '').split():
                continue
            name = img.attrs.get('title')
            if not name:
                continue
            name = ALIASES.get(name, name)
            allowed = HEROES if key in ('synergies', 'countered_by') else MAPS
            if name not in allowed or name == hero:
                raise ValueError(f'{hero}: unknown/self relationship {name!r}')
            names.append(name)
        result[key] = sorted(set(names))
    if set(result['strong_maps']) & set(result['weak_maps']):
        raise ValueError(f'{hero}: contradictory map ratings')
    source = PROFILES[hero]
    result.update(source=source['source'], source_updated=source['source_updated'], checked=source['checked'])
    return result


def main():
    heroes = {hero: extract_matchups((ROOT / '.guide-cache' / (slug(hero) + '.html')).read_text(encoding='utf-8'), hero)
              for hero in sorted(HEROES)}
    catalogue = {'version': 1, 'kind': 'guide relationships, not win-rate statistics', 'heroes': heroes}
    target = ROOT / 'draft_catalogue.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(target)
    print(f"Saved {len(heroes)} heroes; {sum(len(h['synergies']) for h in heroes.values())} synergy listings; "
          f"{sum(len(h['countered_by']) for h in heroes.values())} counter listings.")


if __name__ == '__main__':
    main()
