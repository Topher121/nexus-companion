"""Maintainer build: produces an installer and checksum manifest, never publishes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'.packaging-deps'),str(ROOT/'.deps')]
from app_paths import APP_VERSION
from updates import CONTENT_VERSION

if __name__=='__main__':
    if '--manifest-only' not in sys.argv:
        import PyInstaller.__main__
        PyInstaller.__main__.run([str(ROOT/'NexusCompanion.spec'),'--noconfirm','--clean'])
        compiler=Path(os.environ.get('INNO_COMPILER',str(ROOT/'.packaging-deps'/'inno'/'ISCC.exe')))
        subprocess.run([str(compiler),'/DAppVersion='+APP_VERSION,str(ROOT/'installer.iss')],check=True,cwd=ROOT)
    out=ROOT/'releases';out.mkdir(exist_ok=True)
    installer=out/f'NexusCompanion-Setup-{APP_VERSION}.exe'
    builds=out/f'builds-{CONTENT_VERSION}.json'
    builds.write_bytes((ROOT/'build_catalogue.json').read_bytes())
    base=f'https://github.com/Topher121/nexus-companion/releases/download/v{APP_VERSION}/'
    manifest={'format':1,
              'app':{'version':APP_VERSION,'url':base+installer.name,'sha256':hashlib.sha256(installer.read_bytes()).hexdigest()},
              'builds':{'version':CONTENT_VERSION,'min_app':'0.8.0','url':base+builds.name,'sha256':hashlib.sha256(builds.read_bytes()).hexdigest()}}
    (out/'latest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Release files ready in',out)
