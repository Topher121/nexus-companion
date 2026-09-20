import unittest
from datetime import date
from unittest.mock import patch, MagicMock
import json
from availability import parse_collection, rotation_available, eligible, fetch_rotation
from data import HEROES
from hero_ids import normalize
from engine import rank


class AvailabilityTests(unittest.TestCase):
    def test_export_reads_first_bit_not_skin_bits(self):
        heroes = list(HEROES)[:25]
        text = '{Topher' + ''.join('[' + normalize(h) + (' 0111,01,00(skin 1)],' if i % 2 else ' 1000,10,0],') for i,h in enumerate(heroes)) + '}'
        player, owned = parse_collection(text)
        self.assertEqual(player, 'Topher')
        self.assertEqual(len(owned), 25)
        for i,h in enumerate(heroes):
            self.assertEqual(owned[h], i % 2 == 0)

    def export_fixture(self):
        return '{Topher' + ''.join('['+normalize(h)+' 1000,010,00('+normalize(h)+'Skin 011),(MoreSkin 100)],'
                                  for h in HEROES) + '}'

    def test_cosmetics_reusing_hero_ids_do_not_override_owned_heroes(self):
        # Reproduces the reported failure with announcer/emoticon IDs from the
        # exporter's later catalogs. Cosmetics also use square brackets.
        export = self.export_fixture()[:-1] + '[Abathur 0],[LiLi 0],[Jaina 011],[FaerieDragon 0]}'
        player, owned = parse_collection(export)
        self.assertEqual(player, 'Topher')
        self.assertEqual(len(owned), 90)
        self.assertTrue(all(owned.values()))

    def test_owned_cosmetic_cannot_grant_unowned_hero(self):
        export = self.export_fixture().replace('[abathur 1000,', '[abathur 0111,')
        export = export[:-1] + '[Abathur 1]}'
        self.assertFalse(parse_collection(export)[1]['Abathur'])

    def test_empty_voice_mastery_fields_and_internal_hero_aliases(self):
        export = self.export_fixture().replace('[lili 1000,010,00(liliSkin 011),(MoreSkin 100)]', '[LiLi 1000,,]')
        export = export.replace('[brightwing 1000,', '[FaerieDragon 1000,')
        export = export.replace('[gazlowe 1000,','[Tinker 1000,').replace('[johanna 1000,','[Crusader 1000,').replace('[lunara 1000,','[Dryad 1000,')
        owned = parse_collection(export)[1]
        self.assertTrue(owned['Li Li'])
        self.assertTrue(owned['Brightwing'])
        for hero in ('Gazlowe','Johanna','Lunara'):
            self.assertTrue(owned[hero])

    def test_genuine_hero_conflict_and_combined_exports_still_rejected(self):
        export = self.export_fixture()
        for invalid in (export[:-1] + '[Abathur 0,,]}', export + export):
            with self.assertRaises(ValueError):
                parse_collection(invalid)

    def test_reject_partial_and_unrelated_clipboard(self):
        for value in ('hello', '{Topher[Johanna 1]}', '{Topher[FakeHero 1]}'):
            with self.assertRaises(ValueError): parse_collection(value)

    def test_rotation_level_and_expiry(self):
        rotation = {'StartDate':'2026-09-15','EndDate':'2026-09-22','Heroes':[{'Name':'Johanna','ReqLevel':15},{'Name':'Li Li','ReqLevel':0}]}
        self.assertEqual(rotation_available(rotation, 10, date(2026,9,19)), {'Li Li'})
        self.assertEqual(rotation_available(rotation, 20, date(2026,9,22)), set())
        self.assertEqual(rotation_available(rotation, 20, date(2026,9,14)), set())
        self.assertEqual(rotation_available({'AllHeroesFree':True},20), set())

    def test_unknown_policy_and_ban_independence(self):
        owned = {'Johanna':True, 'Li Li':False}
        self.assertEqual(eligible(owned, {}, 20, True), {'Johanna'})
        self.assertNotIn('Li Li', eligible(owned, {}, 20, False))
        picks = rank([], [], [], {}, 'Unknown map', available={'Johanna'})
        self.assertEqual([p['hero'] for p in picks], ['Johanna'])
        self.assertGreater(len(rank([], [], [], {}, 'Unknown map', for_ban=True, available=set())), 80)
        self.assertEqual(rank([], [], [], {'Johanna':'Never suggest'}, 'Unknown map', available={'Johanna'}), [])

    def test_unknown_rotation_unlock_does_not_hide_confirmed_free_heroes(self):
        rotation={'StartDate':'2026-09-15','EndDate':'2026-09-22','Heroes':[
            {'Name':'Li Li','ReqLevel':0}, {'Name':'Johanna','ReqLevel':'15'},
            {'Name':'Genji','ReqLevel':'?'}, {'Name':'Jaina'},
            {'Name':'Valla','ReqLevel':True}, {'Name':'Muradin','ReqLevel':-1}, None]}
        self.assertEqual(rotation_available(rotation,0,date(2026,9,20)),{'Li Li'})
        self.assertEqual(rotation_available(rotation,20,date(2026,9,20)),{'Li Li','Johanna'})
        self.assertEqual(rotation_available(rotation,20,date(2026,9,22)),set())

    def test_rotation_status_distinguishes_missing_expired_and_unknown_unlocks(self):
        from availability import rotation_summary
        self.assertIn('unavailable',rotation_summary({},today=date(2026,9,20)))
        rotation={'StartDate':'2026-09-15','EndDate':'2026-09-22','Heroes':[
            {'Name':'Li Li','ReqLevel':0},{'Name':'Genji','ReqLevel':'?'}]}
        self.assertIn('1 confirmed available',rotation_summary(rotation,0,date(2026,9,20)))
        self.assertIn('unconfirmed unlock',rotation_summary(rotation,0,date(2026,9,20)))
        self.assertIn('expired',rotation_summary(rotation,20,date(2026,9,22)))
        self.assertIn('not active yet',rotation_summary(rotation,20,date(2026,9,14)))

    def test_api_wrapper(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'RotationHero':{'StartDate':'2026-09-15','EndDate':'2026-09-22','Heroes':[{'Name':'Lucio','ReqLevel':15}]}}).encode()
        with patch('urllib.request.urlopen', return_value=response):
            data = fetch_rotation()
        self.assertEqual(data['Heroes'][0]['Name'], 'Lúcio')


class LiveStateTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from app import Companion
        self.root = tk.Tk(); self.root.withdraw()
        self.app = Companion(self.root)
        self.app.clear()

    def tearDown(self):
        self.root.destroy()

    def reading(self, hero='Johanna', locked=True):
        return {'valid':True, 'map':'Infernal Shrines','slots':[{'side':'allies','index':0,'hero':hero,'locked':locked}], 'bans':[]}

    def test_roster_filters_preserve_hero_identity_and_handle_empty_results(self):
        a=self.app
        a.prefs['Johanna']='Favourite';a.pool_filter.set('Favourite');a.search.set(' joh ')
        self.assertEqual(a.tree.get_children(),('Johanna',))
        self.assertEqual(a.tree.item('Johanna','values'),('Johanna','Tank','Favourite'))
        a.tree.selection_set('Johanna');a.pool_selection_changed()
        self.assertFalse(any('disabled' in b.state() for b in a.preference_buttons))
        a.search.set('Not a hero')
        self.assertFalse(a.tree.get_children())
        self.assertTrue(all('disabled' in b.state() for b in a.preference_buttons))
        a.reset_pool_filters();self.assertEqual(len(a.tree.get_children()),90)

    def test_collection_filters_keep_selection_bound_to_the_correct_hero(self):
        a=self.app;a.owned={'Johanna':True,'Li Li':False};a.rotation={}
        a.collection_filter.set('Owned');a.collection_search.set('')
        self.assertEqual(a.availability_tree.get_children(),('Johanna',))
        a.availability_tree.selection_set('Johanna');a.collection_selection_changed()
        self.assertFalse(any('disabled' in b.state() for b in a.collection_buttons))
        a.show_availability();self.assertEqual(a.availability_tree.selection(),('Johanna',))
        a.collection_filter.set('Not owned');a.show_availability()
        self.assertEqual(a.availability_tree.get_children(),('Li Li',))
        self.assertFalse(a.availability_tree.selection())
        self.assertTrue(all('disabled' in b.state() for b in a.collection_buttons))
        a.reset_collection_filters();self.assertEqual(len(a.availability_tree.get_children()),90)

    def test_waiting_for_pick_cannot_open_a_stale_hero_guide(self):
        a=self.app
        self.assertIn('disabled',a.guide_button.state())
        a.playing.set('Li Li');a.manual_selection(a.playing)
        self.assertNotIn('disabled',a.guide_button.state())

    def test_invalid_account_level_keeps_previous_saved_level(self):
        a=self.app;a.settings['account_level']=15
        for value in ('-1','not a number'):
            a.account_level.set(value)
            with patch.object(a,'save_settings') as save,patch('features.messagebox.showinfo') as notice:
                a.availability_changed()
                save.assert_not_called();notice.assert_called_once()
            self.assertEqual(a.account_level.get(),'15')

    def test_flexible_roles_update_advice_and_reset_between_matches(self):
        a = self.app
        for var, hero in zip(a.allies, ['Varian', 'Jaina', 'Sonya', 'Anduin']):
            var.set(hero)
        a.refresh()
        self.assertEqual(a.flex_bar.winfo_manager(), 'pack')
        self.assertIn('tank', a.status.cget('text'))
        a.flex_plans['Varian'].set('Taunt (tank)'); a.refresh()
        self.assertNotIn('Still needed: tank', a.status.cget('text'))
        self.assertNotIn('Fills the missing tank role', a.pick_text.get('1.0', 'end'))
        a.clear()
        self.assertEqual(a.flex_plans['Varian'].get(), 'Unconfirmed')
        self.assertEqual(a.flex_bar.winfo_manager(), '')

    def test_six_bans_stop_ban_suggestions_even_with_enemy_slots_left(self):
        a = self.app
        for var, hero in zip(a.bans, ['Johanna', 'Li Li', 'Brightwing', 'Uther', 'Arthas', 'Muradin']):
            var.set(hero)
        a.refresh()
        self.assertIn('Bans complete', a.ban_text.get('1.0', 'end'))

    def test_two_samples_manual_override_and_clear(self):
        a = self.app
        a.apply_read(self.reading())
        self.assertEqual(a.allies[0].get(), '')
        a.apply_read(self.reading())
        self.assertEqual(a.allies[0].get(), 'Johanna')
        a.allies[0].set('Muradin'); a.manual_selection(a.allies[0])
        a.apply_read(self.reading())
        self.assertEqual(a.allies[0].get(), 'Muradin')
        a.clear()
        a.apply_read(self.reading(locked=False), screenshot=True)
        self.assertEqual(a.allies[0].get(), '')

    def test_new_map_requires_clear_and_self_build_updates(self):
        a = self.app
        a.self_slot.set('1')
        a.apply_read(self.reading('Li Li'), screenshot=True)
        self.assertEqual(a.playing.get(), 'Li Li')
        other = self.reading('Muradin'); other['map'] = 'Cursed Hollow'
        a.apply_read(other, screenshot=True)
        self.assertEqual(a.allies[0].get(), 'Li Li')

    def test_stopped_generation_discards_late_result(self):
        a = self.app
        a.events.put(('draft', (a.generation - 1, self.reading(), True), None))
        a.poll_events()
        self.assertEqual(a.allies[0].get(), '')

    def test_final_teams_keep_map_and_follow_player_without_slot_setup(self):
        a = self.app
        a.map.set('Dragon Shire'); a.detected_map = 'Dragon Shire'
        a.self_slot.set('Auto'); a.player_name.set('Topher')
        value = {'valid': True, 'map': None, 'phase': 'starting', 'bans': [], 'slots': [
            {'side':'allies','index':0,'hero':'Qhira','locked':True,'player':'Someone'},
            {'side':'allies','index':1,'hero':'Li Li','locked':True,'player':'Tophei%'},
            {'side':'enemies','index':0,'hero':'Sylvanas','locked':True,'player':'Opponent'}]}
        a.apply_read(value)
        self.assertIsNone(a.detected_self_slot)
        a.apply_read(value)
        self.assertEqual(a.map.get(), 'Dragon Shire')
        self.assertEqual(a.playing.get(), 'Li Li')
        self.assertEqual(a.detected_self_slot, 1)
        self.assertIn('Sylvanas', a.build_text.get('1.0','end'))
        # More enemies update tips without losing the identified hero.
        value['slots'].append({'side':'enemies','index':1,'hero':'Varian','locked':True,'player':'Other'})
        a.apply_read(value); a.apply_read(value)
        self.assertIn('Twin Blades', a.build_text.get('1.0','end'))
        self.assertEqual(a.playing.get(), 'Li Li')

    def test_manual_build_browse_can_resume_following(self):
        a = self.app
        a.self_slot.set('1'); a.allies[0].set('Li Li'); a.update_own_hero()
        a.playing.set('Johanna'); a.manual_selection(a.playing)
        a.update_own_hero()
        self.assertEqual(a.playing.get(), 'Johanna')
        a.follow_hero.set(True); a.update_own_hero()
        self.assertEqual(a.playing.get(), 'Li Li')

    def test_repeated_read_preserves_tip_scroll_position(self):
        a = self.app
        for var, hero in zip(a.enemies,['Sylvanas','Varian','Leoric','Malfurion','Abathur']): var.set(hero)
        a.playing.set('Li Li'); a.refresh()
        a.build_text.yview_moveto(.5)
        before = a.build_text.yview()
        a.refresh()
        self.assertEqual(a.build_text.yview(), before)

    def test_build_variant_survives_enemy_reads_and_resets_for_a_new_hero(self):
        from build_library import AUTO_BUILD
        a = self.app
        a.self_slot.set('1')
        a.apply_read(self.reading('Varian'), screenshot=True)
        a.build_variant.set('Twin Blades Build'); a.refresh()
        a.enemies[0].set('Anduin'); a.refresh()
        self.assertEqual(a.build_variant.get(), 'Twin Blades Build')
        self.assertIn('Twin Blades of Fury', a.build_text.get('1.0','end'))
        a.allies[0].set('Chromie'); a.update_own_hero(); a.refresh()
        self.assertEqual(a.build_variant.get(), AUTO_BUILD)
        text = a.build_text.get('1.0','end')
        self.assertIn('Level 8 ', text)
        self.assertIn('Level 18 ', text)
        self.assertNotIn('Level 20 ', text)
        self.assertNotIn('Twin Blades Build', a.build_picker['values'])
        a.clear()
        self.assertIn('disabled', a.build_picker.state())

    def test_every_hero_can_be_browsed_in_the_build_page(self):
        a = self.app
        for hero in HEROES:
            with self.subTest(hero=hero):
                a.playing.set(hero); a.manual_selection(a.playing)
                text = a.build_text.get('1.0','end')
                self.assertEqual(a.build_name['text'], hero)
                self.assertEqual(sum(line.startswith('Level ') for line in text.splitlines()), 7)
                self.assertIn('MATCH NOTES', text)
                self.assertIn('Source: Icy Veins', text)
                self.assertNotIn('No saved guide', text)

    def test_confirmed_johanna_ban_removes_live_pick_suggestion(self):
        from pathlib import Path
        from vision import read_bans, Image
        a = self.app
        for var, hero in zip(a.allies, ['Varian','','','Li Li','Nazeebo']):var.set(hero)
        for var, hero in zip(a.enemies, ['','','Valla','Sonya','']):var.set(hero)
        a.prefs['Johanna']='Favourite';a.refresh()
        with Image.open(Path(__file__).parent/'tests/fixtures/complete-bans.png') as source:
            bans=read_bans(source.convert('RGB'))
        value={'valid':True,'map':'Cursed Hollow','phase':'draft','slots':[],'bans':bans}
        a.apply_read(value)
        self.assertEqual(a.bans[3].get(),'')  # Still requires a consistent second frame.
        a.apply_read(value)
        self.assertEqual(a.bans[3].get(),'Johanna')
        self.assertEqual(a.bans[2].get(),'Qhira')
        self.assertNotIn('Johanna',a.pick_text.get('1.0','end'))


class IdentityAndTipsTests(unittest.TestCase):
    def test_unique_player_with_small_ocr_error(self):
        from identity import player_slot
        slots = [{'side':'allies','index':1,'player':'Tophei%'}, {'side':'enemies','index':0,'player':'Topher'}]
        self.assertEqual(player_slot(slots,'Topher#1234'), 1)
        slots.append({'side':'allies','index':3,'player':'Tophez'})
        self.assertIsNone(player_slot(slots,'Topher'))
        self.assertIsNone(player_slot(slots,'Bob'))

    def test_named_blind_targets_and_varian_uncertainty(self):
        from matchups import matchup_notes
        notes = '\n'.join(matchup_notes('Li Li',['Abathur','Leoric','Sylvanas','Varian','Malfurion']))
        self.assertIn('Sylvanas', notes.split('\n')[0])
        self.assertIn('Varian', notes.split('\n')[0])
        self.assertNotIn('Abathur', notes.split('\n')[0])
        self.assertIn('two nearest', notes)
        self.assertIn('Twin Blades', notes)
        self.assertIn('Malfurion', notes)
        self.assertIn('Drain Hope', notes)

    def test_spell_team_does_not_get_fictional_blind_priority(self):
        from matchups import matchup_notes
        notes = '\n'.join(matchup_notes('Li Li',['Jaina',"Kael'thas",'Orphea']))
        self.assertIn('No obvious attack-focused carry', notes)
        self.assertNotIn('BLIND PRIORITY', notes)

if __name__ == '__main__': unittest.main()
