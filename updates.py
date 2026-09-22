"""Release checks and verified downloads. Checking never runs an installer."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse
from urllib.request import Request,urlopen

from app_paths import APP_VERSION,CONTENT_VERSION,DATA_DIR,RESOURCE_DIR
from content_validation import validate_catalogue

DEFAULT_FEED='https://github.com/Topher121/nexus-companion/releases/latest/download/latest.json'
MAX_MANIFEST=100_000

def version(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d+(\.\d+){1,3}',value):raise ValueError('Invalid release version')
    parts=tuple(int(p) for p in value.split('.'))
    return parts+(0,)*(4-len(parts))

def https_url(value):
    parsed=urlparse(value)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Update addresses must use HTTPS')
    return value

def fetch_bytes(address,maximum):
    https_url(address)
    with urlopen(Request(address,headers={'User-Agent':'NexusCompanion/'+APP_VERSION}),timeout=20) as response:
        https_url(response.geturl())
        if int(response.headers.get('Content-Length','0'))>maximum:raise ValueError('Download is too large')
        value=response.read(maximum+1)
        if len(value)>maximum:raise ValueError('Download is too large')
        return value

def validate_manifest(value):
    if not isinstance(value,dict) or value.get('format')!=1:raise ValueError('Unsupported release information')
    for key in ('app','builds'):
        item=value.get(key)
        if not isinstance(item,dict):raise ValueError('Incomplete release information')
        version(item.get('version'));https_url(item.get('url',''))
        if not re.fullmatch('[0-9a-f]{64}',str(item.get('sha256',''))):raise ValueError('Missing release checksum')
        if key=='builds':version(item.get('min_app'))
    return value

def current_content_version(data_dir=DATA_DIR):
    try:
        value=json.loads((Path(data_dir)/'content'/'active.json').read_text('utf-8'))['version']
        return value if version(value)>version(CONTENT_VERSION) else CONTENT_VERSION
    except (OSError,ValueError,KeyError,TypeError):return CONTENT_VERSION

def check_updates(feed=DEFAULT_FEED,data_dir=DATA_DIR):
    manifest=validate_manifest(json.loads(fetch_bytes(feed,MAX_MANIFEST)))
    return {'manifest':manifest,'app_new':version(manifest['app']['version'])>version(APP_VERSION),
            'builds_new':version(manifest['builds']['version'])>version(current_content_version(data_dir)),
            'builds_compatible':version(manifest['builds']['min_app'])<=version(APP_VERSION),
            'checked':datetime.now(timezone.utc).isoformat()}

def download_verified(item,maximum):
    raw=fetch_bytes(item['url'],maximum)
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Download checksum did not match; nothing was installed')
    return raw

def download_installer(item,data_dir=DATA_DIR):
    version(item['version'])
    raw=download_verified(item,450*1024*1024)
    if raw[:2]!=b'MZ':raise ValueError('The release is not a Windows installer')
    folder=Path(data_dir)/'downloads';folder.mkdir(parents=True,exist_ok=True)
    destination=folder/f"NexusForge-Setup-{item['version']}.exe"
    atomic_write(destination,raw)
    return destination

def atomic_write(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
        os.replace(temp,path)
    finally:Path(temp).unlink(missing_ok=True)

def install_builds(item,data_dir=DATA_DIR):
    version(item['version'])
    if version(item['min_app'])>version(APP_VERSION):raise ValueError('Update the app before installing these builds')
    if version(item['version'])<=version(current_content_version(data_dir)):raise ValueError('These builds are already installed or older')
    raw=download_verified(item,5*1024*1024)
    validate_catalogue(json.loads(raw))
    folder=Path(data_dir)/'content'/item['version']
    atomic_write(folder/'build_catalogue.json',raw)
    # Previous catalogue remains on disk; one atomic pointer switches versions.
    atomic_write(Path(data_dir)/'content'/'active.json',json.dumps({'version':item['version']}).encode())
    return folder
