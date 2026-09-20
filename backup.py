"""Portable personal-data backups with SQLite snapshots and reviewed restores."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile

JSON_FILES=('preferences.json','settings.json','collection.json','rotation.json')
FILES=(*JSON_FILES,'match-history.sqlite3')
MAX_BYTES=100*1024*1024

def digest(value):return hashlib.sha256(value).hexdigest()

def validate_file(name,raw):
    if name in JSON_FILES:
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError(f'{name} must contain an object')
        if name=='preferences.json':
            from data import HEROES
            if any(k not in HEROES or v not in ('Favourite','Allowed','Never suggest','Not owned') for k,v in value.items()):
                raise ValueError('Invalid hero preferences')
        if name=='collection.json':
            from data import HEROES
            heroes=value.get('heroes',{})
            if not isinstance(heroes,dict) or any(k not in HEROES or type(v) is not bool for k,v in heroes.items()):
                raise ValueError('Invalid collection')
        if name=='settings.json':
            if 'account_level' in value and (type(value['account_level']) is not int or value['account_level']<0):
                raise ValueError('Invalid account level')
            for key in ('auto_results','only_confirmed','follow_hero','auto_update_checks'):
                if key in value and type(value[key]) is not bool:raise ValueError(f'Invalid {key} setting')
            for key in ('player_name','replay_folder','pick_stats_mode'):
                if key in value and (not isinstance(value[key],str) or len(value[key])>32768):raise ValueError(f'Invalid {key} setting')
        return
    with tempfile.TemporaryDirectory(prefix='nexus-validate-') as temp:
        path=Path(temp)/'history.sqlite3';path.write_bytes(raw)
        with closing(sqlite3.connect(path)) as db:
            db.execute('PRAGMA trusted_schema=OFF');db.execute('PRAGMA query_only=ON')
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Damaged match history')
            schema=db.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            if any(kind not in ('table','index') for kind,_ in schema):raise ValueError('Unexpected database objects')
            if {name for kind,name in schema if kind=='table'}!={'matches','replay_files'}:raise ValueError('Not a Nexus Companion history database')
            required={'matches':{'id','profile','player','hero','result','played_at','map','mode','source','build','excluded'},
                      'replay_files':{'path','profile','signature','match_id'}}
            for table,columns in required.items():
                if {r[1] for r in db.execute(f'PRAGMA table_info({table})')}!=columns:raise ValueError('Unsupported history format')
            from data import HEROES
            for hero,result,stamp,excluded in db.execute('SELECT hero,result,played_at,excluded FROM matches'):
                if hero not in HEROES or result not in ('Win','Loss') or excluded not in (0,1):raise ValueError('Invalid history result')
                parsed=datetime.fromisoformat(stamp)
                if parsed.tzinfo is None:raise ValueError('History date is missing its timezone')

def create_backup(destination,data_dir):
    destination=Path(destination);data_dir=Path(data_dir)
    if destination.resolve() in [(data_dir/name).resolve() for name in FILES]:raise ValueError('Choose a separate backup filename')
    payload={}
    for name in JSON_FILES:
        path=data_dir/name
        payload[name]=path.read_bytes() if path.exists() else b'{}'
        validate_file(name,payload[name])
    database=data_dir/'match-history.sqlite3'
    if database.exists():
        with tempfile.TemporaryDirectory(prefix='nexus-backup-') as temp:
            snapshot=Path(temp)/'snapshot.sqlite3'
            with closing(sqlite3.connect(database)) as source,closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
            payload[database.name]=snapshot.read_bytes()
        validate_file(database.name,payload[database.name])
    manifest={'format':1,'created':datetime.now(timezone.utc).isoformat(),'files':{name:digest(raw) for name,raw in payload.items()}}
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=destination.parent,suffix='.tmp');os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json',json.dumps(manifest))
            for name,raw in payload.items():archive.writestr(name,raw)
        os.replace(tmp,destination)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return destination

def read_backup(path):
    try:
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist();names=[i.filename for i in infos]
            if len(names)!=len(set(names)) or set(names)-set((*FILES,'manifest.json')):raise ValueError('Unexpected files in backup')
            if sum(i.file_size for i in infos)>MAX_BYTES:raise ValueError('Backup is too large')
            manifest=json.loads(archive.read('manifest.json'))
            if not isinstance(manifest,dict) or not isinstance(manifest.get('files'),dict):raise ValueError('Invalid backup manifest')
            created=datetime.fromisoformat(manifest.get('created',''))
            if created.tzinfo is None:raise ValueError('Backup date is missing its timezone')
            if manifest.get('format')!=1 or set(manifest['files'])!=set(names)-{'manifest.json'}:raise ValueError('Unsupported backup format')
            if not set(JSON_FILES)<=set(names):raise ValueError('Incomplete backup')
            payload={name:archive.read(name) for name in manifest['files']}
        for name,raw in payload.items():
            if digest(raw)!=manifest['files'][name]:raise ValueError('Backup checksum did not match')
            validate_file(name,raw)
        return manifest,payload
    except (KeyError,TypeError,sqlite3.Error,zipfile.BadZipFile) as exc:
        raise ValueError('This is not a valid Nexus Companion backup') from exc

def restore_backup(path,data_dir):
    """Caller pauses all writers. Validate everything before touching current data."""
    manifest,payload=read_backup(path);data_dir=Path(data_dir)
    if 'match-history.sqlite3' not in payload:raise ValueError('This backup has no match history; it cannot replace your current data')
    safety=data_dir/'backups'/f'before-restore-{datetime.now():%Y%m%d-%H%M%S-%f}.nexus-backup'
    create_backup(safety,data_dir)
    with tempfile.TemporaryDirectory(prefix='.restore-',dir=data_dir) as temporary:
        stage=Path(temporary)
        originals={name:(data_dir/name).read_bytes() if (data_dir/name).exists() else None for name in payload}
        for name,raw in payload.items():(stage/name).write_bytes(raw)
        replaced=[]
        try:
            for name in payload:
                os.replace(stage/name,data_dir/name);replaced.append(name)
        except OSError:
            for name in reversed(replaced):
                if originals[name] is None:(data_dir/name).unlink(missing_ok=True)
                else:
                    (stage/name).write_bytes(originals[name]);os.replace(stage/name,data_dir/name)
            raise
    return safety
