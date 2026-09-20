import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from history import (HistoryStore, ReplayError, hero_stats, result_from_details,
                     scan_replays, validated_mode, profile_from_path)


PROFILE = '2-Hero-1-123'


def details_fixture(result=1):
    now = datetime.now(timezone.utc)
    ticks = int((now-datetime(1601,1,1,tzinfo=timezone.utc)).total_seconds()*10_000_000)
    players = []
    for i in range(10):
        players.append(dict(m_name=b'Topher' if i==0 else b'Other',
                            m_toon=dict(m_region=2,m_realm=1,m_programId=b'Hero',m_id=123+i),
                            m_hero=b'Li Li' if i==0 else b'Jaina',m_teamId=i//5,
                            m_result=result if i<5 else 3-result,m_observe=0,m_workingSetSlotId=i))
    return dict(m_playerList=players,m_timeUTC=ticks,m_title=b'Dragon Shire')


def lobby_fixture(details,mode=50091):
    slots=[]
    from history import toon_id
    for p in details['m_playerList']:
        slots.append(dict(m_toonHandle=toon_id(p).encode(),m_teamId=p['m_teamId'],m_observe=0,
                          m_workingSetSlotId=p['m_workingSetSlotId'],m_hero=p['m_hero']))
    return dict(m_lobbyState=dict(m_slots=slots),m_gameDescription=dict(m_gameOptions=dict(m_amm=True,m_ammId=mode)))


class ReplayResultTests(unittest.TestCase):
    def test_result_uses_account_identity_not_duplicate_name_or_team_colour(self):
        d=details_fixture(2)
        d['m_playerList'][6]['m_name']=b'Topher'
        row=result_from_details({'m_version':{'m_baseBuild':98025}},d,PROFILE,'Storm League')
        self.assertEqual((row['hero'],row['result']),('Li Li','Loss'))
        self.assertEqual(row['profile'],PROFILE)
        self.assertEqual(profile_from_path('C:/Accounts/1/'+PROFILE+'/Replays/Multiplayer'),PROFILE)

    def test_reject_unfinished_inconsistent_and_observer_replays(self):
        header={'m_version':{'m_baseBuild':98025}}
        d=details_fixture();d['m_playerList'][0]['m_result']=0
        with self.assertRaises(ReplayError):result_from_details(header,d,PROFILE)
        d=details_fixture();d['m_playerList'][1]['m_result']=2
        with self.assertRaises(ReplayError):result_from_details(header,d,PROFILE)
        d=details_fixture();d['m_playerList'][0]['m_observe']=1
        with self.assertRaises(ReplayError):result_from_details(header,d,PROFILE)
        with self.assertRaises(ReplayError):result_from_details(header,details_fixture(),'2-Hero-1-9999')

    def test_aram_placeholder_heroes_and_future_mode_layout(self):
        d=details_fixture();l=lobby_fixture(d,50101)
        l['m_lobbyState']['m_slots'][0]['m_hero']=b'Abathur'
        self.assertEqual(validated_mode(d,l),'ARAM')
        l['m_lobbyState']['m_slots'][0]['m_teamId']=1
        self.assertEqual(validated_mode(d,l),'Unknown')
        self.assertEqual(validated_mode(d,lobby_fixture(d)),'Storm League')
        self.assertEqual(validated_mode(d,lobby_fixture(d,99999)),'Unknown')

    def test_same_replay_data_has_stable_id(self):
        header={'m_version':{'m_baseBuild':98025}};d=details_fixture()
        a=result_from_details(header,d,PROFILE)
        d['m_playerList'].reverse()
        self.assertEqual(a['id'],result_from_details(header,d,PROFILE)['id'])


class HistoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=HistoryStore(Path(self.temp.name)/'history.sqlite3')

    def tearDown(self):
        self.temp.cleanup()

    def add(self,hero='Li Li',result='Win',mode='Storm League',days=0,profile=PROFILE):
        return self.store.add_manual(profile,'Topher',hero,result,datetime.now(timezone.utc)-timedelta(days=days),'Dragon Shire',mode)

    def test_stats_filters_and_account_separation(self):
        self.add();self.add(result='Loss');self.add();self.add(mode='ARAM')
        self.add(hero='Johanna',result='Loss');self.add(days=50);self.add(profile='different')
        rows=self.store.records(PROFILE,'Li Li','Storm League',30)
        stat=hero_stats(rows)[0]
        self.assertEqual((stat['games'],stat['wins'],stat['losses']),(3,2,1))
        self.assertAlmostEqual(stat['rate'],200/3)
        self.assertEqual(len(self.store.records(PROFILE)),6)
        self.assertEqual(hero_stats([]),[])

    def test_import_duplicates_restart_exclusions_and_restore(self):
        row=result_from_details({'m_version':{'m_baseBuild':98025}},details_fixture(),PROFILE)
        self.assertTrue(self.store.add(row,'copy1.StormReplay','signature1'))
        self.assertFalse(self.store.add(row,'copy2.StormReplay','signature2'))
        self.store.exclude([row['id']])
        reopened=HistoryStore(self.store.path)
        self.assertFalse(reopened.add(row))
        self.assertEqual(reopened.records(PROFILE),[])
        self.assertEqual(len(reopened.records(PROFILE,excluded=True)),1)
        self.assertEqual(hero_stats(reopened.records(PROFILE,excluded=True)),[])
        reopened.exclude([row['id']],False)
        self.assertEqual(len(reopened.records(PROFILE)),1)
        self.assertEqual(len(reopened.imported_files(PROFILE)),2)

    def test_scanner_waits_for_writes_retries_errors_and_skips_already_imported(self):
        import os
        folder=Path(self.temp.name)/PROFILE/'Replays'/'Multiplayer';folder.mkdir(parents=True)
        p=folder/'game.StormReplay';p.write_bytes(b'replay')
        row=result_from_details({'m_version':{'m_baseBuild':98025}},details_fixture(),PROFILE)
        with patch('history.read_replay',return_value=row) as reader:
            self.assertEqual(scan_replays(folder,self.store)['pending'],1)
            reader.assert_not_called()
            past=time.time()-30;os.utime(p,(past,past))
            self.assertEqual(scan_replays(folder,self.store)['added'],1)
            self.assertEqual(scan_replays(folder,self.store)['existing'],1)
            self.assertEqual(reader.call_count,1)
        bad=folder/'unfinished.StormReplay';bad.write_bytes(b'partial');os.utime(bad,(past,past))
        with patch('history.read_replay',side_effect=ReplayError('unfinished')):
            self.assertEqual(len(scan_replays(folder,self.store)['errors']),1)
        self.assertEqual(len(self.store.records(PROFILE)),1)
        stopped=threading.Event();stopped.set()
        self.assertEqual(scan_replays(folder,self.store,stopped)['files'],0)


class HistoryPageTests(unittest.TestCase):
    def test_clickable_hero_headings_sort_numbers_and_preserve_filters_on_refresh(self):
        import tkinter as tk
        from app import Companion
        with tempfile.TemporaryDirectory() as directory:
            store=HistoryStore(Path(directory)/'sorting.sqlite3')
            root=tk.Tk();root.withdraw()
            try:
                with patch('history_ui.HistoryStore',return_value=store):app=Companion(root)
                profile=app.history_profile()
                for hero,wins,losses in [('Johanna',2,10),('Li Li',3,0),('Azmodan',1,10),('Anduin',2,1)]:
                    for result in ['Win']*wins+['Loss']*losses:
                        store.add_manual(profile,'Topher',hero,result,datetime.now(timezone.utc),'Dragon Shire','Storm League')
                app.refresh_history();tree=app.hero_stats_tree
                click=lambda key:root.tk.call(tree.heading(key,'command'))
                self.assertEqual(tree.get_children(),('Johanna','Azmodan','Anduin','Li Li'))
                self.assertEqual(tree.heading('games','text'),'Played ▼')
                click('games')
                self.assertEqual(tree.get_children(),('Anduin','Li Li','Azmodan','Johanna'))
                click('wins')
                self.assertEqual(tree.get_children(),('Li Li','Anduin','Johanna','Azmodan'))
                click('losses')
                self.assertEqual(tree.get_children(),('Azmodan','Johanna','Anduin','Li Li'))
                click('rate')
                self.assertEqual(tree.get_children(),('Li Li','Anduin','Johanna','Azmodan'))
                click('rate')
                self.assertEqual(tree.get_children(),('Azmodan','Johanna','Anduin','Li Li'))
                self.assertEqual(tree.heading('rate','text'),'Win rate ▲')
                self.assertEqual(tree.heading('losses','text'),'Losses')
                tree.selection_set('Li Li');app.select_history_hero()
                self.assertEqual(app.history_hero.get(),'Li Li')
                app.refresh_history()
                self.assertEqual(tree.selection(),('Li Li',))
                self.assertEqual(tree.get_children(),('Azmodan','Johanna','Anduin','Li Li'))
                for _ in range(4):
                    store.add_manual(profile,'Topher','Azmodan','Win',datetime.now(timezone.utc),'Dragon Shire','Storm League')
                app.refresh_history()
                self.assertEqual(tree.get_children(),('Johanna','Azmodan','Anduin','Li Li'))
                self.assertEqual(app.history_hero.get(),'Li Li')
                app.history_mode.set('Practice');app.refresh_history()
                self.assertFalse(tree.get_children())
                app.reset_history_filters()
                self.assertEqual(app.history_sort['heroes'],('rate',False))
                self.assertEqual(tree.get_children(),('Johanna','Azmodan','Anduin','Li Li'))
                click('hero')
                self.assertEqual(tree.get_children(),('Anduin','Azmodan','Johanna','Li Li'))
                click('hero')
                self.assertEqual(tree.get_children(),('Li Li','Johanna','Azmodan','Anduin'))
            finally:root.destroy()

    def test_match_headings_sort_actual_dates_and_retain_selected_match(self):
        import tkinter as tk
        from app import Companion
        with tempfile.TemporaryDirectory() as directory:
            store=HistoryStore(Path(directory)/'match-sorting.sqlite3')
            root=tk.Tk();root.withdraw()
            try:
                with patch('history_ui.HistoryStore',return_value=store):app=Companion(root)
                ids=[]
                for hero,result,when in [('Johanna','Loss','2025-12-31T18:00:00+00:00'),
                                         ('Li Li','Win','2026-01-29T18:00:00+00:00'),
                                         ('Anduin','Win','2026-02-01T18:00:00+00:00')]:
                    ids.append(str(store.add_manual(app.history_profile(),'Topher',hero,result,datetime.fromisoformat(when),'Dragon Shire','Storm League')))
                app.refresh_history();tree=app.matches_tree
                click=lambda key:root.tk.call(tree.heading(key,'command'))
                self.assertEqual(tree.get_children(),tuple(reversed(ids)))
                tree.selection_set(ids[1])
                click('date');self.assertEqual(tree.get_children(),tuple(ids))
                self.assertEqual(tree.heading('date','text'),'Date / time ▲')
                click('hero');self.assertEqual(tree.get_children(),(ids[2],ids[0],ids[1]))
                click('result');self.assertEqual(tree.get_children(),(ids[0],ids[2],ids[1]))
                self.assertEqual(tree.selection(),(ids[1],))
                app.refresh_history()
                self.assertEqual(tree.get_children(),(ids[0],ids[2],ids[1]))
                self.assertEqual(app.history_hero.get(),'All heroes')
                self.assertEqual(app.history_sort['heroes'],('games',True))
            finally:root.destroy()

    def test_draft_records_keep_modes_accounts_and_exclusions_separate(self):
        import tkinter as tk
        from app import Companion
        with tempfile.TemporaryDirectory() as directory, patch.object(Companion,'save_settings'):
            store=HistoryStore(Path(directory)/'draft.sqlite3')
            root=tk.Tk();root.withdraw()
            try:
                with patch('history_ui.HistoryStore',return_value=store):
                    app=Companion(root)
                app.clear();app.owned={'Li Li':True};app.only_confirmed.set(True)
                app.pick_stats_mode.set('Storm League')
                profile=app.history_profile()
                ids=[]
                for result,mode,account in [('Win','Storm League',profile),('Loss','Storm League',profile),
                                             ('Win','ARAM',profile),('Win','Storm League','another-account')]:
                    ids.append(store.add_manual(account,'Topher','Li Li',result,datetime.now(timezone.utc),'Dragon Shire',mode))
                app.refresh_history()
                picks=app.pick_text.get('1.0','end')
                self.assertIn('50.0% · 2 games · 1W / 1L · small sample',picks)
                # History-page filters do not silently change the draft's selected mode.
                app.history_mode.set('ARAM');app.refresh_history()
                self.assertIn('50.0% · 2 games',app.pick_text.get('1.0','end'))
                app.pick_stats_mode.set('ARAM');app.pick_stats_changed()
                self.assertIn('100.0% · 1 game',app.pick_text.get('1.0','end'))
                store.exclude([ids[2]]);app.refresh_history()
                self.assertIn('no recorded games',app.pick_text.get('1.0','end'))
                self.assertNotIn('0.0%',app.pick_text.get('1.0','end'))
                store.exclude([ids[2]],False);app.refresh_history()
                self.assertIn('100.0% · 1 game',app.pick_text.get('1.0','end'))
                app.replay_folder.set('C:/Accounts/other/2-Hero-1-999/Replays/Multiplayer');app.refresh()
                self.assertIn('no recorded games',app.pick_text.get('1.0','end'))
            finally:
                root.destroy()

    def test_hero_and_mode_filters_and_exclusion_controls(self):
        import tkinter as tk
        from app import Companion
        with tempfile.TemporaryDirectory() as directory:
            store=HistoryStore(Path(directory)/'ui.sqlite3')
            root=tk.Tk();root.withdraw()
            try:
                with patch('history_ui.HistoryStore',return_value=store):
                    app=Companion(root)
                profile=app.history_profile()
                for hero,result,mode in [('Li Li','Win','Storm League'),('Li Li','Loss','ARAM'),('Johanna','Loss','Storm League')]:
                    store.add_manual(profile,'Topher',hero,result,datetime.now(timezone.utc),'Dragon Shire',mode)
                app.refresh_history()
                self.assertIn('3 played',app.history_summary.cget('text'))
                app.hero_stats_tree.selection_set('Li Li');app.select_history_hero()
                self.assertEqual(app.history_hero.get(),'Li Li')
                self.assertIn('50.0%',app.history_summary.cget('text'))
                app.history_mode.set('Storm League');app.refresh_history()
                self.assertIn('100.0%',app.history_summary.cget('text'))
                match_id=app.matches_tree.get_children()[0]
                app.matches_tree.selection_set(match_id);app.exclude_history(True)
                self.assertIn('0 played',app.history_summary.cget('text'))
                app.show_excluded.set(True);app.refresh_history()
                app.matches_tree.selection_set(match_id);app.exclude_history(False)
                self.assertIn('1 played',app.history_summary.cget('text'))
                # A late scan for another account must not replace this page's state.
                app.history_events.put(('different-folder',{'errors':[],'files':99,'added':99,'pending':0},None))
                app.poll_history()
                self.assertIn('1 played',app.history_summary.cget('text'))
            finally:
                root.destroy()


if __name__=='__main__':unittest.main()
