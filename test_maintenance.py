import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from backup import create_backup,read_backup,restore_backup,FILES
from draft_health import draft_health
from history import HistoryStore
from updates import check_updates,install_builds,download_installer,version,validate_manifest

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.data=self.root/'data';self.data.mkdir()
        (self.data/'preferences.json').write_text(json.dumps({'Li Li':'Favourite'}))
        (self.data/'settings.json').write_text(json.dumps({'player_name':'Test','account_level':123}))
        (self.data/'collection.json').write_text(json.dumps({'heroes':{'Li Li':True,'Johanna':False}}))
        self.store=HistoryStore(self.data/'match-history.sqlite3')
        self.first=self.store.add_manual('profile','Test','Li Li','Win',datetime.now(timezone.utc),'Cursed Hollow','Storm League')
        self.store.exclude([self.first])
        self.archive=self.root/'save.nexus-backup'

    def test_snapshot_roundtrip_preserves_exclusions_and_makes_safety_copy(self):
        create_backup(self.archive,self.data)
        self.store.add_manual('profile','Test','Johanna','Loss',datetime.now(timezone.utc),'Dragon Shire','Storm League')
        (self.data/'preferences.json').write_text('{}')
        safety=restore_backup(self.archive,self.data)
        self.assertTrue(safety.is_file())
        self.assertEqual(len(self.store.records('profile',excluded=True)),1)
        self.assertEqual(self.store.records('profile'),[])
        self.assertEqual(json.loads((self.data/'preferences.json').read_text()),{'Li Li':'Favourite'})
        _,payload=read_backup(safety)
        self.assertEqual(json.loads(payload['preferences.json']),{})

    def test_rejects_corruption_traversal_and_wrong_schema_without_changing_data(self):
        create_backup(self.archive,self.data)
        before={p.name:p.read_bytes() for p in self.data.iterdir() if p.is_file()}
        with zipfile.ZipFile(self.archive,'a') as archive:archive.writestr('../settings.json','{}')
        with self.assertRaises(ValueError):restore_backup(self.archive,self.data)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.data.iterdir() if p.is_file()})
        create_backup(self.archive,self.data)
        manifest,payload=read_backup(self.archive)
        payload['preferences.json']=b'{"Li Li":"Never suggest"}'
        with zipfile.ZipFile(self.archive,'w') as archive:
            archive.writestr('manifest.json',json.dumps(manifest))
            for name,raw in payload.items():archive.writestr(name,raw)
        with self.assertRaisesRegex(ValueError,'checksum'):read_backup(self.archive)

    def test_partial_write_rolls_back_current_data(self):
        import backup
        create_backup(self.archive,self.data)
        (self.data/'preferences.json').write_text('{"Johanna":"Favourite"}')
        real=backup.os.replace;failed=False
        def fail_once(source,target):
            nonlocal failed
            if not failed and Path(target)==self.data/'settings.json':failed=True;raise OSError('simulated disk error')
            return real(source,target)
        with patch('backup.os.replace',side_effect=fail_once):
            with self.assertRaises(OSError):restore_backup(self.archive,self.data)
        self.assertEqual(json.loads((self.data/'preferences.json').read_text()),{'Johanna':'Favourite'})
        self.assertTrue(list((self.data/'backups').glob('*.nexus-backup')))

class UpdateTests(unittest.TestCase):
    def manifest(self):
        return {'format':1,'app':{'version':'0.9.0','url':'https://example.com/setup.exe','sha256':'a'*64},
                'builds':{'version':'2026.10.1.1','min_app':'0.8.0','url':'https://example.com/builds.json','sha256':'b'*64}}

    def test_version_order_and_feed_validation(self):
        self.assertGreater(version('0.10.0'),version('0.9.9'))
        self.assertEqual(version('1.0'),version('1.0.0'))
        for v in ('../1','1.0;run','latest','-1.0',None):
            with self.assertRaises(ValueError):version(v)
        for key,value in [('url','http://example.com/file'),('sha256','bad')]:
            data=self.manifest();data['app'][key]=value
            with self.assertRaises(ValueError):validate_manifest(data)
        with tempfile.TemporaryDirectory() as directory,patch('updates.fetch_bytes',return_value=json.dumps(self.manifest()).encode()):
            result=check_updates(data_dir=directory)
        self.assertTrue(result['app_new']);self.assertTrue(result['builds_new']);self.assertTrue(result['builds_compatible'])

    def test_verified_content_activates_only_complete_valid_catalogue(self):
        from build_library import CATALOGUE
        from content_validation import validate_catalogue
        validate_catalogue(CATALOGUE)
        item=self.manifest()['builds']
        with tempfile.TemporaryDirectory() as directory:
            raw=json.dumps(CATALOGUE).encode();item['sha256']=hashlib.sha256(raw).hexdigest()
            with patch('updates.fetch_bytes',return_value=raw):install_builds(item,directory)
            active=Path(directory)/'content'/'active.json';before=active.read_bytes()
            broken=copy.deepcopy(CATALOGUE);broken['heroes']['Johanna']['builds'][0]['tiers'].pop()
            raw=json.dumps(broken).encode();item['sha256']=hashlib.sha256(raw).hexdigest();item['version']='2026.10.2.1'
            with patch('updates.fetch_bytes',return_value=raw),self.assertRaises(ValueError):install_builds(item,directory)
            self.assertEqual(active.read_bytes(),before)
            item['sha256']='0'*64
            with patch('updates.fetch_bytes',return_value=raw),self.assertRaisesRegex(ValueError,'checksum'):install_builds(item,directory)
            self.assertEqual(active.read_bytes(),before)

    def test_installer_is_verified_but_never_launched_by_download(self):
        item=self.manifest()['app'];raw=b'MZtest';item['sha256']=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory,patch('updates.fetch_bytes',return_value=raw),patch('os.startfile') as launch:
            path=download_installer(item,directory);self.assertEqual(path.read_bytes(),raw);launch.assert_not_called()

class DraftHealthTests(unittest.TestCase):
    def test_blank_bans_can_be_skipped_but_unread_committed_pick_is_flagged(self):
        teams={'allies':['']*5,'enemies':['']*5,'bans':['']*6}
        reading={'valid':True,'slots':[{'side':'allies','index':0,'hero':None,'locked_hint':False}]}
        self.assertEqual(draft_health(reading,teams),([],set()))
        reading['slots'][0]['locked_hint']=True
        problems,marked=draft_health(reading,teams);self.assertIn(('allies',0),marked)
        teams['allies'][0]='Li Li'
        problems,marked=draft_health(reading,teams)
        self.assertEqual(problems,[])
        self.assertNotIn(('allies',0),marked)
        reading['bans']=[{'index':3,'hero':'Johanna'}]
        problems,marked=draft_health(reading,teams)
        self.assertIn(('bans',3),marked)
        self.assertTrue(any('Johanna awaiting confirmation' in text for text in problems))

    def test_final_unreadable_slots_and_manual_conflicts_are_reported(self):
        teams={'allies':['Muradin']+['']*4,'enemies':['']*5,'bans':['']*6}
        reading={'valid':True,'phase':'starting','slots':[{'side':'allies','index':0,'hero':'Johanna','locked':True},
                                                           {'side':'enemies','index':1,'hero':None,'locked':False}]}
        problems,marked=draft_health(reading,teams,{('allies',0)})
        self.assertTrue(any('manual entry' in p for p in problems));self.assertIn(('enemies',1),marked)
        self.assertFalse(any('bans' in p.lower() for p in problems))
        self.assertTrue(any('locked in HotS; hero not recorded' in p for p in problems))

class NewUiTests(unittest.TestCase):
    def test_minimum_games_filters_only_hero_table_and_reset_restores(self):
        import tkinter as tk
        from preview_ui import Preview
        with tempfile.TemporaryDirectory() as directory:
            store=HistoryStore(Path(directory)/'history.sqlite3')
            root=tk.Tk();root.withdraw()
            try:
                with patch('history_ui.HistoryStore',return_value=store):app=Preview(root)
                app.history_min_games.set('0');profile=app.history_profile()
                for hero,count in [('Li Li',5),('Johanna',2)]:
                    for _ in range(count):store.add_manual(profile,'Test',hero,'Win',datetime.now(timezone.utc),'Cursed Hollow','Storm League')
                app.refresh_history();app.history_min_games.set('5');app.minimum_games_changed()
                self.assertEqual(app.hero_stats_tree.get_children(),('Li Li',))
                self.assertEqual(len(app.matches_tree.get_children()),7)
                self.assertIn('7 played',app.history_summary.cget('text'))
                app.history_min_games.set('20');app.minimum_games_changed()
                self.assertFalse(app.hero_stats_tree.get_children())
                self.assertEqual(len(app.matches_tree.get_children()),7)
                app.reset_history_filters();self.assertEqual(len(app.hero_stats_tree.get_children()),2)
            finally:root.destroy()

    def test_warning_clears_after_manual_fix_and_reader_failure_remains_visible(self):
        import tkinter as tk
        from preview_ui import Preview
        root=tk.Tk();root.withdraw()
        try:
            app=Preview(root)
            value={'valid':True,'map':'Cursed Hollow','slots':[{'side':'allies','index':0,'hero':None,'locked':False,'locked_hint':True}], 'bans':[]}
            app.apply_read(value,screenshot=True)
            self.assertIn('looks locked',app.draft_warning.cget('text'))
            app.allies[0].set('Li Li')
            app.refresh();self.assertEqual(app.draft_warning.cget('text'),'')
            app.apply_read({'valid':False,'message':'Game minimized'})
            self.assertIn('not confirming',app.draft_warning.cget('text'))
            app.clear();self.assertEqual(app.draft_warning.cget('text'),'')
        finally:root.destroy()

if __name__=='__main__':unittest.main()
