import copy
from datetime import date
import unittest
from urllib.parse import urlparse

from build_library import AUTO_BUILD, CATALOGUE, PROFILES, build_names, get_build
from data import HEROES, guide_url
from engine import build_details, build_for
from hero_tips import HERO_TIPS


class BuildLibraryTests(unittest.TestCase):
    def test_complete_roster_and_each_talent_tier(self):
        self.assertEqual(set(PROFILES), set(HEROES))
        self.assertEqual(set(HERO_TIPS), set(HEROES))
        self.assertFalse(CATALOGUE['errors'])
        for hero, profile in PROFILES.items():
            with self.subTest(hero=hero):
                self.assertEqual(len(build_names(hero)), len(set(build_names(hero))))
                self.assertTrue(profile['source_updated'])
                date.fromisoformat(profile['checked'])
                url = urlparse(profile['source'])
                self.assertEqual((url.scheme, url.netloc), ('https', 'www.icy-veins.com'))
                self.assertGreaterEqual(len(HERO_TIPS[hero]), 3)
                for build in profile['builds']:
                    expected = [1, 2, 5, 8, 11, 14, 18] if hero == 'Chromie' else [1, 4, 7, 10, 13, 16, 20]
                    self.assertEqual([t['level'] for t in build['tiers']], expected)
                    for tier in build['tiers']:
                        self.assertTrue(tier['talent'].strip())
                        self.assertNotIn(' Icon', tier['talent'])
                        self.assertNotIn(tier['talent'], tier['alternatives'])

    def test_every_variant_survives_matchup_changes_without_source_mutation(self):
        before = copy.deepcopy(PROFILES)
        for hero in HEROES:
            for name in build_names(hero):
                with self.subTest(hero=hero, build=name):
                    expected = [t['talent'] for t in get_build(hero, name)['tiers']]
                    self.assertEqual(build_for(hero, ['Anduin', 'Zeratul', 'Rehgar'], name)[0], expected)
                    self.assertEqual(build_details(hero, [], name)['adjustments'], [])
        build_for('Johanna', ['Anduin'])
        build_for('Li Li', ['Zeratul'])
        self.assertEqual(PROFILES, before)

    def test_adjustments_can_revert_and_manual_choices_remain_exact(self):
        self.assertEqual(build_for('Johanna', ['Anduin'])[0][2], 'Sins Exposed')
        self.assertEqual(build_for('Johanna', [])[0][2], 'Conviction')
        self.assertEqual(build_for('Li Li', ['Zeratul'])[0][1], 'Safety Sprint')
        self.assertEqual(build_for('Li Li', [])[0][1], 'Surging Winds')
        self.assertEqual(build_for('Li Li', ['Zeratul'], 'Cloud Serpent Build')[0][1], 'Wind Serpent')
        self.assertTrue(build_details('Johanna', ['Anduin'])['adjustments'])

    def test_chromie_varian_and_new_hero_have_real_tiers(self):
        chromie = build_details('Chromie', [])
        self.assertEqual(chromie['tiers'][3]['level'], 8)
        varian = build_details('Varian', [], 'Twin Blades Build')
        self.assertEqual(varian['tiers'][1], {'level':4, 'talent':'Twin Blades of Fury', 'alternatives':[]})
        self.assertEqual(len(build_for('Raynor', [])[0]), 7)
        self.assertIsNone(build_details('Not a hero', []))
        with self.assertRaises(ValueError):get_build('Raynor', 'Twin Blades Build')

    def test_azmodan_tips_match_the_selected_build(self):
        auto = build_details('Azmodan', [])
        self.assertEqual(auto['name'], 'Gluttony Build')
        greed = build_details('Azmodan', [], 'Greed Build')
        self.assertNotIn('Gluttony focuses', '\n'.join(greed['notes']))
        self.assertTrue(all(t['talent'] in greed['talents'] for t in greed['tiers']))

    def test_special_guide_links(self):
        self.assertTrue(guide_url('E.T.C.').endswith('/e-t-c-build-guide'))
        self.assertTrue(guide_url("Kel'Thuzad").endswith('/kel-thuzad-build-guide'))
        self.assertTrue(guide_url('Lúcio').endswith('/lucio-build-guide'))

    def test_blind_advice_requires_a_blind_in_the_build(self):
        from matchups import matchup_notes
        self.assertFalse(any('BLIND' in n for n in matchup_notes('Artanis', ['Illidan'], ['Purifier Beam'])))
        self.assertTrue(any('BLIND' in n for n in matchup_notes('Artanis', ['Illidan'], ['Suppression Pulse'])))

    def test_source_choices_include_correct_heroic_upgrades(self):
        # Prevent a build importer from accidentally pairing an alternative heroic
        # with the selected heroic's upgrade, an easy error with two rows of icons.
        for hero, base, upgrade in [('Chromie', 'Temporal Loop', 'Stuck in a Loop'),
                                    ('Li Li', 'Jug of 1,000 Cups', 'Jug of 1,000,000 Cups')]:
            for name in build_names(hero):
                talents = build_for(hero, [], name)[0]
                if upgrade in talents:self.assertIn(base, talents)


if __name__ == '__main__':
    unittest.main()
