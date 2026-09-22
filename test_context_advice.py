import copy
import tkinter as tk
import unittest
from unittest.mock import patch

from build_library import AUTO_BUILD, PROFILES, get_build
from draft_engine import rank, draft_summary
from draft_state import teammate_hovers
from engine import build_details
from talent_advisor import RULES, enemy_signals


class TalentContextTests(unittest.TestCase):
    def test_spell_pressure_changes_the_right_tier_then_reverts(self):
        for hero, level, talent in [('Brightwing',13,'Pixie Power'), ('Arthas',16,'Anti-Magic Shell'), ('Valla',13,'Gloom')]:
            with self.subTest(hero=hero):
                before=build_details(hero,[])
                after=build_details(hero,['Jaina',"Kael'thas"])
                chosen=next(t for t in after['tiers'] if t['level']==level)
                self.assertEqual(chosen['talent'],talent)
                self.assertNotIn(talent,chosen['alternatives'])
                self.assertIn('Jaina',' '.join(after['selection_reasons']))
                self.assertEqual(build_details(hero,[])['tiers'],before['tiers'])

    def test_manual_build_never_changes_with_match_context(self):
        for hero in PROFILES:
            name=get_build(hero)['name']
            detail=build_details(hero,['Jaina',"Kael'thas",'Illidan','Muradin','Uther'],name,
                                 allies=['Ana'],plans={'Varian':'Damage build'})
            self.assertEqual(detail['tiers'],get_build(hero,name)['tiers'])
            self.assertEqual(detail['selection_reasons'],[])

    def test_supported_rules_are_legal_and_do_not_modify_catalogue(self):
        before=copy.deepcopy(PROFILES)
        scenarios=[['Jaina',"Kael'thas"],['Illidan','The Butcher'],['Muradin','Uther'],
                   ['Johanna','Artanis'],['Anduin'],['Diablo',"Anub'arak"]]
        for hero,level,talent,signal,minimum,_ in RULES:
            enemies=next(s for s in scenarios if len(enemy_signals(s)[signal])>=minimum)
            detail=build_details(hero,enemies)
            self.assertEqual(next(t['talent'] for t in detail['tiers'] if t['level']==level),talent,(hero,talent))
            self.assertTrue(detail['selection_reasons'])
            default=get_build(hero)
            # No heroic upgrade or other tier is silently dropped by an adjustment.
            self.assertEqual([t['level'] for t in detail['tiers']],[t['level'] for t in default['tiers']])
        self.assertEqual(PROFILES,before)

    def test_allied_healing_denial_and_varian_plan_are_respected(self):
        self.assertIn('Sins Exposed',build_details('Johanna',['Anduin'])['talents'])
        self.assertNotIn('Sins Exposed',build_details('Johanna',['Anduin'],allies=['Ana'])['talents'])
        self.assertIn('Taunt',build_details('Varian',[],plans={'Varian':'Taunt (tank)'})['talents'])
        self.assertIn('Colossus Smash',build_details('Varian',[],plans={'Varian':'Damage build'})['talents'])


class HoverRankingTests(unittest.TestCase):
    def test_only_other_players_valid_available_hovers_are_included(self):
        locked=['','Johanna','','','']
        hovers={0:'Valla',1:'Muradin',2:'Li Li',3:'Li Li',4:'Jaina'}
        self.assertEqual(teammate_hovers(locked,[],['Jaina'],hovers,0),{2:'Li Li'})
        self.assertEqual(teammate_hovers(locked,[],[],hovers,None),{})
        self.assertEqual(teammate_hovers(locked,[],['Jaina'],hovers,0,{2,3}),{})

    def test_hovers_fill_planned_roles_without_consuming_our_slot(self):
        allies=['Valla','Jaina'];hovers=['Johanna','Li Li']
        results=rank(allies,[],[],{},'Infernal Shrines',ally_hovers=hovers)
        self.assertTrue(results)
        self.assertEqual(results[0]['role'],'Bruiser')
        self.assertFalse(set(hovers)&{x['hero'] for x in results})
        self.assertIn('Assumes teammate hovers',' '.join(results[0]['conditions']))
        self.assertNotIn('Draft complete',draft_summary(allies,[],ally_hovers=hovers))
        self.assertIn('2/5 allies locked',draft_summary(allies,[],ally_hovers=hovers))
        healer_options=rank(allies+['Johanna'],[],[],{},'Infernal Shrines')
        self.assertEqual(healer_options[0]['role'],'Healer')

    def test_final_composition_from_guldan_screenshot_prefers_lane_coverage(self):
        allies=["Anub'arak",'Ana','Tychus','Nova']
        enemies=['Brightwing','Thrall','Qhira','Muradin','Jaina']
        results=rank(allies,enemies,[],{},'Alterac Pass')
        guldan=next(r for r in results if r['hero']=="Gul'dan")
        self.assertIn('Third ranged',' '.join(guldan['warnings']))
        self.assertEqual(results[0]['role'],'Bruiser')
        # Collection restrictions must still win over a preferred composition.
        restricted=rank(allies,enemies,[],{},'Alterac Pass',available={"Gul'dan"})
        self.assertEqual([r['hero'] for r in restricted],["Gul'dan"])
        self.assertTrue(restricted[0]['warnings'])


class LiveContextTests(unittest.TestCase):
    def setUp(self):
        from preview_ui import Preview
        self.root=tk.Tk();self.root.withdraw()
        self.app=Preview(self.root);self.app.clear();self.app.self_slot.set('1')
        self.app.only_confirmed.set(False)

    def tearDown(self):
        self.root.destroy()

    def frame(self,hero='Li Li',locked=False):
        return {'valid':True,'map':'Infernal Shrines','bans':[], 'slots':[
            {'side':'allies','index':1,'hero':hero,'locked':locked}]}

    def test_live_confirmation_swap_disappearance_and_lock(self):
        a=self.app;frame=self.frame()
        a.apply_read(frame);self.assertEqual(a.planned_hovers(),{})
        a.apply_read(frame);self.assertEqual(a.planned_hovers(),{1:'Li Li'})
        self.assertEqual(a.allies[1].get(),'')
        self.assertIn('Slot 2: Li Li',a.hover_status['text'])
        a.apply_read(self.frame('Jaina'));self.assertEqual(a.planned_hovers(),{})
        a.apply_read(self.frame('Jaina'));self.assertEqual(a.planned_hovers(),{1:'Jaina'})
        a.apply_read(self.frame(None));self.assertEqual(a.planned_hovers(),{})
        a.apply_read(self.frame('Li Li'),screenshot=True)
        a.apply_read(self.frame('Li Li',True))
        self.assertEqual(a.planned_hovers(),{})
        a.apply_read(self.frame('Li Li',True));self.assertEqual(a.allies[1].get(),'Li Li')

    def test_own_hover_is_never_treated_as_a_lock_or_teammate(self):
        a=self.app;frame=self.frame('Johanna');frame['slots'][0]['index']=0
        a.apply_read(frame,screenshot=True)
        self.assertEqual(a.planned_hovers(),{})
        self.assertEqual(a.build_name['text'],'Waiting for your pick')
        self.assertNotIn('Your locked hero',a.pick_text.get('1.0','end'))

    def test_manual_overrides_bans_and_reader_failure_remove_hovers(self):
        a=self.app;a.apply_read(self.frame(),screenshot=True)
        a.allies[1].set('');a.manual.add(str(a.allies[1]));a.refresh()
        self.assertEqual(a.planned_hovers(),{})
        a.manual.clear();a.bans[0].set('Li Li');a.refresh()
        self.assertEqual(a.planned_hovers(),{})
        a.bans[0].set('');a.apply_read(self.frame(),screenshot=True)
        a.apply_read({'valid':False,'message':'Not a draft'})
        self.assertEqual(a.planned_hovers(),{})
        self.assertEqual(a.previous_hovers,{})

    def test_enemy_confirmation_updates_talents_manual_selection_survives(self):
        a=self.app
        a.allies[0].set('Brightwing');a.update_own_hero();a.refresh()
        frame={'valid':True,'map':'Infernal Shrines','bans':[],'slots':[
            {'side':'enemies','index':0,'hero':'Jaina','locked':True},
            {'side':'enemies','index':1,'hero':"Kael'thas",'locked':True}]}
        a.apply_read(frame,screenshot=True)
        text=a.build_text.get('1.0','end')
        self.assertIn('Pixie Power',text);self.assertIn('WHY THESE TALENTS',text)
        self.assertIn("Jaina, Kael'thas",text)
        a.build_variant.set('Critical Mist Build');a.refresh()
        self.assertIn('Safety Dust',a.build_text.get('1.0','end'))
        self.assertNotIn('WHY THESE TALENTS',a.build_text.get('1.0','end'))
        a.build_variant.set(AUTO_BUILD);a.refresh()
        self.assertIn('Pixie Power',a.build_text.get('1.0','end'))

    def test_reset_and_different_match_never_keep_tentative_context(self):
        a=self.app;a.apply_read(self.frame(),screenshot=True)
        frame=self.frame();frame['map']='Cursed Hollow'
        a.apply_read(frame,screenshot=True);self.assertEqual(a.planned_hovers(),{})
        a.clear();self.assertEqual(a.previous_hovers,{})

    def test_enemy_hover_does_not_drive_talents(self):
        a=self.app;a.allies[0].set('Brightwing');a.update_own_hero()
        a.apply_read({'valid':True,'map':'Infernal Shrines','bans':[],'slots':[
            {'side':'enemies','index':0,'hero':'Jaina','locked':False},
            {'side':'enemies','index':1,'hero':"Kael'thas",'locked':False}]},screenshot=True)
        self.assertIn('Safety Dust',a.build_text.get('1.0','end'))
        self.assertNotIn('Pixie Power',a.build_text.get('1.0','end'))


if __name__=='__main__':
    unittest.main()
