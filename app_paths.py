"""Read-only bundled resources and writable personal data have separate homes."""
import os
import sys
from pathlib import Path

APP_NAME = 'Nexus Forge'
APP_VERSION = '0.9.0'
CONTENT_VERSION = '2026.9.19.1'
RESOURCE_DIR = Path(__file__).resolve().parent
FROZEN = bool(getattr(sys, 'frozen', False))
# Retain the original data folder so the public rename never hides saved records.
DATA_DIR = Path(os.environ['NEXUS_DATA_DIR']) if os.environ.get('NEXUS_DATA_DIR') else (
    Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'Nexus Companion'
    if FROZEN else RESOURCE_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def catalogue_path(name):
    """Only a previously validated, atomically activated catalogue is used."""
    import json
    try:
        version = json.loads((DATA_DIR / 'content' / 'active.json').read_text('utf-8'))['version']
        if not isinstance(version, str) or not version.replace('.', '').isdigit():
            raise ValueError('Invalid content version')
        if tuple(map(int,version.split('.'))) < tuple(map(int,CONTENT_VERSION.split('.'))):
            raise ValueError('Bundled catalogue is newer')
        from content_validation import validate_catalogue
        path = DATA_DIR / 'content' / version / name
        validate_catalogue(json.loads(path.read_text('utf-8')))
        return path
    except (OSError, ValueError, KeyError, TypeError):
        return RESOURCE_DIR / name
