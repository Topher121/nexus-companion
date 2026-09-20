"""Local replay results, durable duplicate protection, and personal hero statistics."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import re
import sqlite3
import sys
import time
import uuid

from data import HEROES
from hero_ids import IDS, normalize

ROOT = Path(__file__).resolve().parent
from app_paths import DATA_DIR
DATABASE = DATA_DIR / 'match-history.sqlite3'
MODE_IDS = {50001: 'Quick Match', 50021: 'Versus AI', 50031: 'Brawl',
            50041: 'Practice', 50051: 'Unranked Draft', 50061: 'Hero League',
            50071: 'Team League', 50091: 'Storm League', 50101: 'ARAM'}
MODES = ['Storm League', 'Quick Match', 'ARAM', 'Unranked Draft', 'Versus AI',
         'Custom', 'Brawl', 'Hero League', 'Team League', 'Practice', 'Unknown']
DRAFT_STAT_MODES = ['Storm League', 'Quick Match', 'Unranked Draft', 'ARAM', 'All modes']
ARAM_MAPS = {'Lost Cavern', 'Silver City', 'Industrial District', 'Braxis Outpost'}


class ReplayError(ValueError):
    pass


def text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else str(value)


def profile_from_path(path):
    for part in reversed(Path(path).parts):
        if re.fullmatch(r'\d+-Hero-\d+-\d+', part):
            return part
    return ''


def toon_id(player):
    toon = player.get('m_toon', {})
    if not toon.get('m_id'):
        return ''
    return f"{toon.get('m_region')}-{text(toon.get('m_programId', ''))}-{toon.get('m_realm')}-{toon['m_id']}"


def replay_folders(accounts):
    return sorted(p for p in Path(accounts).glob('*/*/Replays/Multiplayer')
                  if p.is_dir() and profile_from_path(p))


@lru_cache(maxsize=8)
def protocol_for(build=None):
    # heroprotocol's old versions loader uses imp, removed in Python 3.12.
    # Load its unmodified protocol modules with the supported importlib API.
    deps = str(ROOT / '.replay-deps')
    if deps not in sys.path:
        sys.path.insert(0, deps)
    folder = ROOT / '.replay-deps' / 'heroprotocol' / 'versions'
    candidates = sorted(folder.glob('protocol[0-9]*.py'), key=lambda p: int(p.stem[8:]))
    if not candidates:
        raise ReplayError('The local replay reader is missing. Match history can still be entered manually.')
    exact = folder / f'protocol{build}.py'
    if build is None:
        path = candidates[-1]
    elif exact.exists():
        path = exact
    else:
        compatible = [p for p in candidates if int(p.stem[8:]) <= build]
        if not compatible:
            raise ReplayError(f'Unsupported replay version: {build}.')
        path = compatible[-1]
    spec = importlib.util.spec_from_file_location('nexus_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validated_mode(details, lobby):
    """Accept bit-packed init data only if its player records agree with details.

    Replay details/header are self-describing versioned data. Init data is not:
    a later patch must pass identity/team/hero cross-checks before its mode is used.
    Unreadable or changed init layouts give Unknown, never a guessed ranked mode.
    """
    slots = lobby['m_lobbyState']['m_slots']
    options = lobby['m_gameDescription']['m_gameOptions']
    for player in details['m_playerList']:
        if player.get('m_observe', 0) or not toon_id(player):
            continue
        candidates = [s for s in slots if text(s.get('m_toonHandle', '')) == toon_id(player)]
        if len(candidates) != 1:
            return 'Unknown'
        slot = candidates[0]
        if (slot.get('m_teamId') != player.get('m_teamId') or
                slot.get('m_workingSetSlotId') != player.get('m_workingSetSlotId') or
                slot.get('m_observe', 0) != 0):
            return 'Unknown'
        # ARAM choices occur after the lobby's placeholder heroes are recorded.
        if options.get('m_ammId') not in (50031, 50101) and (
                IDS.get(normalize(text(slot.get('m_hero', '')))) !=
                IDS.get(normalize(text(player.get('m_hero', ''))))):
            return 'Unknown'
    if options.get('m_noVictoryOrDefeat'):
        return 'Unknown'
    if options.get('m_amm') is False:
        return 'Custom'
    mode_id = options.get('m_ammId')
    if mode_id == 50031 and text(details['m_title']) in ARAM_MAPS:
        return 'ARAM'
    return MODE_IDS.get(mode_id, 'Unknown')


def result_from_details(header, details, profile, mode='Unknown'):
    players = [p for p in details.get('m_playerList', []) if not p.get('m_observe', 0)]
    mine = [p for p in players if toon_id(p) == profile]
    if len(mine) != 1:
        raise ReplayError('Your account is not a unique participating player in this replay.')
    player = mine[0]
    if player.get('m_result') not in (1, 2):
        raise ReplayError('This replay has no completed win/loss result yet.')
    teams = {}
    for p in players:
        teams.setdefault(p.get('m_teamId'), set()).add(p.get('m_result'))
    if len(teams) != 2 or {tuple(sorted(v)) for v in teams.values()} != {(1,), (2,)}:
        raise ReplayError('The replay does not contain consistent winning and losing teams.')
    hero = IDS.get(normalize(text(player.get('m_hero', ''))))
    if hero not in HEROES:
        raise ReplayError('Your hero could not be recognised in this replay.')
    try:
        played = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=details['m_timeUTC'] // 10)
    except (KeyError, TypeError, OverflowError):
        raise ReplayError('The replay date could not be read.')
    if not 2014 <= played.year <= datetime.now(timezone.utc).year + 1:
        raise ReplayError('The replay date is invalid.')
    # Same game saved/copied under another filename still counts only once.
    identity = [details['m_timeUTC'], text(details['m_title']),
                sorted((toon_id(p), text(p.get('m_hero', '')), p['m_teamId']) for p in players)]
    match_id = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode('utf-8')).hexdigest()
    return dict(id='replay:' + match_id + ':' + profile, profile=profile,
                player=text(player['m_name']), hero=hero, result='Win' if player['m_result'] == 1 else 'Loss',
                played_at=played.isoformat(), map=text(details['m_title']), mode=mode,
                source='Replay', build=header['m_version']['m_baseBuild'])


def read_replay(path, profile):
    protocol = protocol_for()
    import mpyq
    if Path(path).stat().st_size > 64 * 1024 * 1024:
        raise ReplayError('This replay is too large to read.')
    data = Path(path).read_bytes()
    archive = mpyq.MPQArchive(io.BytesIO(data))
    header = protocol.decode_replay_header(archive.header['user_data_header']['content'])
    protocol = protocol_for(header['m_version']['m_baseBuild'])
    details = protocol.decode_replay_details(archive.read_file('replay.details'))
    mode = 'Unknown'
    try:
        lobby = protocol.decode_replay_initdata(archive.read_file('replay.initData'))['m_syncLobbyState']
        mode = validated_mode(details, lobby)
    except Exception:
        pass  # Results remain useful even if a future patch changes the mode layout.
    return result_from_details(header, details, profile, mode)


class HistoryStore:
    def __init__(self, path=DATABASE):
        self.path = Path(path)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY, profile TEXT NOT NULL, player TEXT NOT NULL,
                    hero TEXT NOT NULL, result TEXT NOT NULL CHECK(result IN ('Win','Loss')),
                    played_at TEXT NOT NULL, map TEXT NOT NULL, mode TEXT NOT NULL,
                    source TEXT NOT NULL, build INTEGER NOT NULL DEFAULT 0,
                    excluded INTEGER NOT NULL DEFAULT 0);
                CREATE INDEX IF NOT EXISTS matches_profile_date ON matches(profile, played_at);
                CREATE TABLE IF NOT EXISTS replay_files (
                    path TEXT NOT NULL, profile TEXT NOT NULL, signature TEXT NOT NULL,
                    match_id TEXT NOT NULL, PRIMARY KEY(path, profile));
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add(self, row, file=None, signature=None):
        if row['hero'] not in HEROES or row['result'] not in ('Win', 'Loss'):
            raise ValueError('Choose a valid hero and result.')
        fields = ('id','profile','player','hero','result','played_at','map','mode','source','build')
        with closing(self.connect()) as db, db:
            inserted = db.execute('INSERT OR IGNORE INTO matches (' + ','.join(fields) + ') VALUES (' + ','.join('?' for _ in fields) + ')',
                                  [row.get(k, 0 if k == 'build' else '') for k in fields]).rowcount
            if file:
                db.execute('INSERT OR REPLACE INTO replay_files VALUES (?,?,?,?)',
                           (str(Path(file).resolve()),row['profile'],signature,row['id']))
        return bool(inserted)

    def add_manual(self, profile, player, hero, result, played_at, map_name, mode):
        row = dict(id='manual:' + uuid.uuid4().hex, profile=profile, player=player,
                   hero=hero, result=result, played_at=played_at.astimezone(timezone.utc).isoformat(),
                   map=map_name or 'Unknown map', mode=mode, source='Manual', build=0)
        self.add(row)
        return row['id']

    def imported_files(self, profile):
        with closing(self.connect()) as db:
            return {r['path']:r['signature'] for r in db.execute('SELECT * FROM replay_files WHERE profile=?',(profile,))}

    def records(self, profile, hero='All heroes', mode='All modes', days=None, excluded=False):
        sql, params = 'SELECT * FROM matches WHERE profile=?', [profile]
        if not excluded:
            sql += ' AND excluded=0'
        if hero != 'All heroes':
            sql += ' AND hero=?'; params.append(hero)
        if mode != 'All modes':
            sql += ' AND mode=?'; params.append(mode)
        if days:
            sql += ' AND played_at>=?'; params.append((datetime.now(timezone.utc)-timedelta(days=days)).isoformat())
        with closing(self.connect()) as db:
            return [dict(r) for r in db.execute(sql+' ORDER BY played_at DESC, id',params)]

    def exclude(self, match_ids, excluded=True):
        with closing(self.connect()) as db, db:
            db.executemany('UPDATE matches SET excluded=? WHERE id=?', [(int(excluded), i) for i in match_ids])


def hero_stats(records):
    stats = {}
    for row in records:
        if row.get('excluded'):
            continue
        item = stats.setdefault(row['hero'], dict(hero=row['hero'], games=0, wins=0, losses=0))
        item['games'] += 1
        item['wins' if row['result'] == 'Win' else 'losses'] += 1
    for item in stats.values():
        item['rate'] = 100 * item['wins'] / item['games']
    return sorted(stats.values(), key=lambda r: (-r['games'], r['hero']))


def personal_record_label(stat):
    """Past results with a denominator, never a prediction for this draft."""
    if stat is None:
        return 'Your record: no recorded games'
    games = stat['games']
    label = f"Your record: {stat['rate']:.1f}% · {games} {'game' if games == 1 else 'games'} · {stat['wins']}W / {stat['losses']}L"
    return label + (' · small sample' if games < 20 else '')


def scan_replays(folder, store, stop=None, failed=None):
    folder = Path(folder)
    profile = profile_from_path(folder)
    if not profile or not folder.is_dir():
        raise ReplayError('Choose your account’s Replays / Multiplayer folder inside Heroes of the Storm / Accounts.')
    known = store.imported_files(profile)
    failed = failed if failed is not None else {}
    report = dict(added=0, existing=0, pending=0, errors=[], profile=profile, files=0)
    for path in sorted(folder.rglob('*.StormReplay')):
        if stop and stop.is_set():
            break
        key, signature = str(path.resolve()), None
        try:
            stat = path.stat()
            report['files'] += 1
            signature = f'{stat.st_size}:{stat.st_mtime_ns}'
            key = str(path.resolve())
            if known.get(key) == signature:
                report['existing'] += 1; continue
            if time.time() - stat.st_mtime < 8:
                report['pending'] += 1; continue  # Wait until the game finishes writing.
            previous = failed.get(key)
            if previous and previous[0] == signature and time.monotonic() - previous[1] < 300:
                report['errors'].append((path.name, previous[2])); continue
            row = read_replay(path, profile)
            after = path.stat()
            if (after.st_size, after.st_mtime_ns) != (stat.st_size, stat.st_mtime_ns):
                report['pending'] += 1; continue
            report['added'] += store.add(row, path, signature)
            failed.pop(key, None)
        except Exception as exc:
            message = str(exc) or type(exc).__name__
            report['errors'].append((path.name, message))
            if signature is not None:
                failed[key] = (signature, time.monotonic(), message)
    return report
