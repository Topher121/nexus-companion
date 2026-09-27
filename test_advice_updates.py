import copy
from datetime import date, timedelta
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from advice_schema import content_basis
from build_library import CATALOGUE, PROFILES, get_build
from content_validation import validate_catalogue
from data import HEROES
from engine import build_details
from talent_advisor import ADVICE, content_status, _matches


class MatchupRegressionTests(unittest.TestCase):
    def test_varian_keeps_role_but_changes_damage_defense_package(self):
        plan={'Varian':'Taunt (tank)'}
        attacks=build_details('Varian',['Tychus',"Zul'jin"],plans=plan)
        burst=build_details('Varian',['Jaina',"Kael'thas"],plans=plan)
        self.assertIn('Overpower',attacks['talents'])
        self.assertIn('Warbringer',attacks['talents'])
        self.assertIn('Shield Wall',burst['talents'])
        self.assertNotIn('Overpower',burst['talents'])
        self.assertIn('Taunt',burst['talents'])
        self.assertIn('Colossus Smash',build_details('Varian',['Jaina',"Kael'thas"],
                     plans={'Varian':'Damage build'})['talents'])

    def test_whole_builds_respond_to_threats(self):
        for hero,enemies,build in [
            ('Falstad',['Johanna'],'Hammerang Build'),
            ('Anduin',['Zeratul','Genji'],'Inner Focus Build'),
            ('Mei',['Tychus',"Zul'jin"],'Snow Blind Build'),
            ("Gul'dan",['Muradin','Uther','Brightwing'],'Corruption Build'),
            ('Zeratul',['Mei','Brightwing'],'Void Prison Build'),
            ('Sgt. Hammer',['Garrosh','Stitches'],'Siege Tactics Build')]:
            with self.subTest(hero=hero):
                detail=build_details(hero,enemies)
                self.assertEqual(detail['name'],build)
                self.assertTrue(detail['adjustments'])
                self.assertTrue(detail['matched_rules'])

    def test_only_stuns_trigger_stun_defense(self):
        self.assertNotIn('Resilient Flame',build_details('Ragnaros',['Malfurion','Xul'])['talents'])
        self.assertIn('Resilient Flame',build_details('Ragnaros',['Muradin','Uther'])['talents'])

    def test_no_absence_assumptions_in_incomplete_draft(self):
        rule=next(r for r in ADVICE['rules'] if r['hero']=='Sonya' and 'absent' in r['when'])
        partial=['Artanis','Chen','Malthael']
        self.assertFalse(_matches(rule,partial,[],{},None))
        self.assertTrue(_matches(rule,partial+['Valla','Raynor'],[],{},None))

    def test_heroic_and_upgrade_switch_together(self):
        d=build_details('Medivh',['Genji','Illidan'])
        self.assertIn('Poly Bomb',d['talents']);self.assertIn('Glyph Of Poly Bomb',d['talents'])
        self.assertNotIn('Medivh Cheats!',d['talents'])
        self.assertIn('Medivh Cheats!',build_details('Medivh',[])['talents'])

    def test_map_and_allies_are_real_inputs(self):
        self.assertIn('Serrated Arrows',build_details('Hanzo',[],battleground='Battlefield of Eternity')['talents'])
        self.assertIn('Explosive Arrows',build_details('Hanzo',[],battleground='Unknown map')['talents'])
        self.assertNotIn('Sins Exposed',build_details('Johanna',['Anduin'],allies=['Ana'])['talents'])

    def test_all_rules_have_reachable_conditions_and_safe_outputs(self):
        # Exercise every rule with a synthetic draft; conflicting higher-priority
        # rules may win, but output must stay a legal, explained complete build.
        before=copy.deepcopy(CATALOGUE)
        for r in ADVICE['rules']:
            hero=r['hero'];when=r['when']
            enemies=list(when.get('enemy_names',[])[:1])
            allies=list(when.get('ally_names',[])[:1])
            for side,team in [('enemy',enemies),('ally',allies)]:
                for signal,count in when.get(side,{}).items():
                    candidates=[h for h in ADVICE['signals'][signal] if h!=hero and h not in team
                                and not any(h in ADVICE['signals'][s] for s in when.get('absent',[]))]
                    team.extend(candidates[:count])
            if when.get('absent'):
                pool=[h for h in HEROES if h!=hero and h not in enemies
                      and not any(h in ADVICE['signals'][s] for s in when['absent'])]
                enemies+=pool[:5-len(enemies)]
            plan={hero:when['plan'][0]} if 'plan' in when else {}
            battleground=when.get('maps',[None])[0]
            with self.subTest(rule=r['id']):
                self.assertTrue(_matches(r,enemies,allies,plan,battleground))
                detail=build_details(hero,enemies,allies=allies,plans=plan,battleground=battleground)
                self.assertEqual(len(detail['tiers']),7)
                base=get_build(hero,detail['name'])
                for tier,original in zip(detail['tiers'],base['tiers']):
                    allowed=[original['talent'],*original['alternatives'],
                             *ADVICE['extra_alternatives'].get(hero,{}).get(str(tier['level']),[])]
                    self.assertIn(tier['talent'],allowed)
                    self.assertNotIn(tier['talent'],tier['alternatives'])
                self.assertTrue(detail['selection_reasons'])
        self.assertEqual(CATALOGUE,before)

    def test_random_full_drafts_do_not_mutate_or_duplicate_tiers(self):
        rng=random.Random(17)
        for hero in HEROES:
            for _ in range(8):
                enemies=rng.sample([h for h in HEROES if h!=hero],5)
                d=build_details(hero,enemies)
                self.assertEqual(len({t['level'] for t in d['tiers']}),7)
                self.assertFalse(any('aram' in d['name'].lower() for _ in [0]))


class ContentReviewTests(unittest.TestCase):
    def test_changed_build_cannot_reuse_stale_review(self):
        c=copy.deepcopy(CATALOGUE);c['heroes']['Johanna']['builds'][0]['tiers'][0]['talent']='Renamed Talent'
        with self.assertRaisesRegex(ValueError,'need review'):validate_catalogue(c)

    def test_incomplete_and_unknown_rules_rejected(self):
        for change in ('missing','talent','condition','source'):
            c=copy.deepcopy(CATALOGUE)
            if change=='missing':c['advice']['rules']=[r for r in c['advice']['rules'] if r['hero']!='Gall']
            elif change=='talent':c['advice']['rules'][-1]['choices']={'13':'Invented talent'}
            elif change=='condition':c['advice']['rules'][0]['when']={'execute':'anything'}
            else:c['advice']['rules'][0]['source']='https://example.com'
            with self.subTest(change=change),self.assertRaises(ValueError):validate_catalogue(c)

    def test_freshness_does_not_claim_current_meta(self):
        checked=date.fromisoformat(CATALOGUE['checked'])
        self.assertNotIn('over 30 days',content_status(checked))
        self.assertIn('over 30 days',content_status(checked+timedelta(days=31)))
        self.assertIn('not live meta',content_status(checked))

    def test_invalid_installed_content_does_not_hide_available_updates(self):
        from updates import current_content_version,CONTENT_VERSION
        with tempfile.TemporaryDirectory() as folder:
            content=Path(folder)/'content';content.mkdir()
            (content/'active.json').write_text('{"version":"2099.1.1.1"}')
            self.assertEqual(current_content_version(folder),CONTENT_VERSION)

    def test_review_tool_separates_date_only_checks_from_real_changes(self):
        from refresh_advice import changed_heroes,approve
        c=copy.deepcopy(CATALOGUE);c['checked']='2026-09-28'
        self.assertEqual(changed_heroes(CATALOGUE,c),[])
        c['heroes']['Johanna']['source_updated']='Sep 28, 2026'
        self.assertEqual(changed_heroes(CATALOGUE,c),['Johanna'])
        checked=approve(c)
        validate_catalogue(checked)
        self.assertEqual(checked['advice']['guide_checked'],'2026-09-28')

    def test_failed_fetch_does_not_create_candidate_or_touch_bundled_content(self):
        import refresh_advice
        before=(refresh_advice.ROOT/'build_catalogue.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'review'
            with patch('sys.argv',['refresh_advice','--output',str(target)]),patch('import_guides.fetch',side_effect=OSError('offline')):
                with self.assertRaises(OSError):refresh_advice.main()
            self.assertFalse(target.exists())
        self.assertEqual((refresh_advice.ROOT/'build_catalogue.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
