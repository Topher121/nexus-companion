"""Offline guide selections. No requests or user data are involved in reading builds."""
from copy import deepcopy
import json
from pathlib import Path

from app_paths import catalogue_path
CATALOGUE = json.loads(catalogue_path('build_catalogue.json').read_text(encoding='utf-8'))
PROFILES = CATALOGUE['heroes']
AUTO_BUILD = 'Auto (matchup)'
# Preserve the ranged teamfight starter previously chosen for this companion.
DEFAULTS = {'Azmodan': 'Gluttony Build'}


def build_names(hero):
    return [b['name'] for b in PROFILES.get(hero, {}).get('builds', [])]


def get_build(hero, variant=AUTO_BUILD):
    """Return an independent copy, so matchup adjustments never alter source data."""
    profile = PROFILES.get(hero)
    if not profile:
        return None
    builds = profile['builds']
    if variant == AUTO_BUILD:
        name = DEFAULTS.get(hero)
        selected = next((b for b in builds if b['name'] == name), None)
        if selected is None:
            selected = next((b for b in builds if b['category'] == 'Recommended'), builds[0])
    else:
        selected = next((b for b in builds if b['name'] == variant), None)
        if selected is None:
            raise ValueError(f'No {variant} for {hero}')
    return deepcopy({**{k: v for k, v in profile.items() if k != 'builds'}, **selected})


BUILD_COUNT = sum(len(p['builds']) for p in PROFILES.values())
