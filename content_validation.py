"""Strict data-only build catalogue validation; no imported executable content."""
from urllib.parse import urlparse

TIERS = [1, 4, 7, 10, 13, 16, 20]

def validate_catalogue(value, expected_heroes=None):
    if not isinstance(value, dict) or not isinstance(value.get('heroes'), dict):
        raise ValueError('Invalid build catalogue')
    heroes = value['heroes']
    if expected_heroes is None:
        # Read the immutable roster without importing data/build_library recursively.
        import json
        from pathlib import Path
        expected_heroes = json.loads(Path(__file__).with_name('build_catalogue.json').read_text('utf-8'))['heroes']
    if set(heroes) != set(expected_heroes):
        raise ValueError('The build update must include every supported hero')
    def short(text, maximum=500):
        if not isinstance(text, str) or not text.strip() or len(text) > maximum:
            raise ValueError('Invalid catalogue text')
    short(value.get('checked'), 30)
    for hero, profile in heroes.items():
        short(hero, 60)
        if not isinstance(profile, dict):raise ValueError('Invalid hero profile')
        for key in ('source_updated','checked'):short(profile.get(key), 80)
        short(profile.get('source'))
        url = urlparse(profile['source'])
        if url.scheme != 'https' or url.hostname != 'www.icy-veins.com' or not url.path.startswith('/heroes/'):
            raise ValueError('Unexpected build source')
        builds = profile.get('builds')
        if not isinstance(builds, list) or not 1 <= len(builds) <= 30:raise ValueError('Invalid builds')
        names = set()
        for build in builds:
            if not isinstance(build,dict):raise ValueError('Invalid build')
            short(build.get('name'), 150);short(build.get('category'), 80)
            if build['name'] in names:raise ValueError('Duplicate build name')
            names.add(build['name'])
            tiers=build.get('tiers')
            expected=[1,2,5,8,11,14,18] if hero=='Chromie' else TIERS
            if not isinstance(tiers,list) or [t.get('level') for t in tiers if isinstance(t,dict)] != expected:
                raise ValueError('A build is missing talent tiers')
            for tier in tiers:
                short(tier.get('talent'), 150)
                alternatives=tier.get('alternatives',[])
                if not isinstance(alternatives,list) or len(alternatives)>12:raise ValueError('Invalid alternatives')
                for alternative in alternatives:short(alternative,150)
    return value
