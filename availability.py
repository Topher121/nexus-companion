"""Owned heroes and time-bounded free rotation, independent of preferences."""
import json
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from data import HEROES
from hero_ids import IDS, normalize

ROOT = Path(__file__).resolve().parent
ROTATION_URL = 'https://nexuscompendium.com/api/currently/herorotation'

def load_json(path, default):
    try:
        result = json.loads(path.read_text(encoding='utf-8'))
        return result if isinstance(result, dict) else default
    except (OSError, ValueError):
        return default

def save_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)

def parse_collection(text):
    if len(text) > 2_000_000:
        raise ValueError('Export is too large.')
    text = text.strip()
    if not text.startswith('{') or not text.endswith('}'):
        raise ValueError('Paste the complete owned-items export from your replay player button.')
    if '{' in text[1:-1] or '}' in text[1:-1]:
        raise ValueError('More than one export was pasted. Clear the box and paste one player export.')
    player = re.sub(r'<[^>]*>', '', text[1:].split('[', 1)[0]).strip(' ,')
    values = {}
    # The exporter writes heroes first, then mounts, sprays, announcers and
    # emoticons. Those other catalogs can reuse a hero ID (e.g. an Abathur
    # announcer). Only hero records have the three comma-separated bit fields:
    # ownership/base tints, voice lines, mastery; nested skins use parentheses.
    # Never resolve a collision by taking the first/last occurrence or OR-ing bits.
    hero_record = re.compile(
        r'\[([A-Za-z0-9_]+)\s+([01]+)\s*,\s*([01]*)\s*,\s*([01]*)\s*'
        r'(?:\([A-Za-z0-9_]+\s+[01]+\)\s*,?\s*)*\]')
    for match in hero_record.finditer(text):
        identifier, bits = match.group(1, 2)
        hero = IDS.get(normalize(identifier))
        if hero:
            owned = bits[0] == '1'
            if hero in values and values[hero] != owned:
                raise ValueError(f'Conflicting hero records for {hero}. Clear the box and paste one complete player export.')
            values[hero] = owned
    if len(values) < 20:
        raise ValueError('This does not look like a complete hero collection export (fewer than 20 recognised heroes).')
    return player, values

def rotation_available(rotation, level=0, today=None):
    today = today or date.today()
    try:
        start = date.fromisoformat(rotation['StartDate'][:10])
        end = date.fromisoformat(rotation['EndDate'][:10])
        if not start <= today < end:
            return set()
        if rotation.get('AllHeroesFree') is True:
            return set(HEROES)
        heroes = rotation['Heroes']
    except (KeyError, TypeError, ValueError):
        return set()
    free = set()
    for hero in heroes if isinstance(heroes,list) else []:
        if not isinstance(hero,dict) or hero.get('Name') not in HEROES:
            continue
        requirement = hero.get('ReqLevel')
        # The feed sometimes uses "?". Skip that entry, not the entire rotation,
        # and never invent an unlock level for heroes with missing information.
        if isinstance(requirement,bool) or not str(requirement).isdigit():
            continue
        if int(requirement) <= level:
            free.add(hero['Name'])
    return free


def rotation_summary(rotation, level=0, today=None):
    today = today or date.today()
    try:
        start = date.fromisoformat(rotation['StartDate'][:10])
        end = date.fromisoformat(rotation['EndDate'][:10])
    except (KeyError,TypeError,ValueError):
        return 'Free rotation unavailable. Use Refresh free rotation to check.'
    period = f'{start:%d %b}–{end:%d %b %Y}'
    if today >= end:
        return f'Free rotation expired ({period}). Refresh to check the latest heroes.'
    if today < start:
        return f'Saved rotation starts {start:%d %b %Y}; it is not active yet.'
    if rotation.get('AllHeroesFree') is not True and not isinstance(rotation.get('Heroes'),list):
        return 'Free rotation unavailable. Use Refresh free rotation to check.'
    count = len(rotation_available(rotation,level,today))
    message = f'Free rotation: {count} confirmed available at your level · {period}.'
    entries = rotation.get('Heroes',[])
    unknown = sum(isinstance(h,dict) and h.get('Name') in HEROES and
                  (isinstance(h.get('ReqLevel'),bool) or not str(h.get('ReqLevel')).isdigit())
                  for h in (entries if isinstance(entries,list) else []))
    if unknown and rotation.get('AllHeroesFree') is not True:
        message += f' {unknown} heroes have unconfirmed unlock levels and are excluded.'
    return message

def fetch_rotation():
    request = urllib.request.Request(ROTATION_URL, headers={'User-Agent': 'NexusCompanion/0.2', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=12) as response:
        value = json.loads(response.read(1_000_000))
    if isinstance(value, dict) and 'RotationHero' in value:
        value = value['RotationHero']
    if not isinstance(value, dict) or not isinstance(value.get('Heroes'), list):
        raise ValueError('Rotation service returned an unexpected format.')
    for field in ('StartDate', 'EndDate'):
        date.fromisoformat(value[field][:10])
    # Do not infer unknown hero names or drop level gates.
    for hero in value['Heroes']:
        canonical = IDS.get(normalize(hero.get('Name', ''))) or IDS.get(normalize(hero.get('ID', '')))
        hero['Name'] = canonical or hero.get('Name', '')
    value['checked_at'] = datetime.now(timezone.utc).isoformat()
    return value

def eligible(owned, rotation, level, only_confirmed):
    free = rotation_available(rotation, level)
    return {hero for hero in HEROES if owned.get(hero) is True or hero in free
            or (not only_confirmed and hero not in owned)}
