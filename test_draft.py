import random
import unittest
from unittest.mock import patch

from data import HEROES, MAPS
from draft_engine import (GUIDANCE, draft_summary, effective_role, rank,
                          recommendation_text)
from import_matchups import extract_matchups


def option(hero, allies=(), enemies=(), **kwargs):
    return next(x for x in rank(list(allies), list(enemies), [], {}, 'Unknown map', **kwargs) if x['hero'] == hero)


class GuidanceTests(unittest.TestCase):
    def test_complete_attributed_catalogue(self):
        self.assertEqual(set(GUIDANCE), set(HEROES))
        for hero, profile in GUIDANCE.items():
            self.assertTrue(profile['source'].startswith('https://www.icy-veins.com/heroes/'))
            self.assertTrue(profile['source_updated'])
            self.assertTrue(profile['checked'])
            for key, allowed in [('synergies', HEROES), ('countered_by', HEROES),
                                 ('strong_maps', MAPS), ('weak_maps', MAPS)]:
                self.assertEqual(len(profile[key]), len(set(profile[key])))
                self.assertTrue(set(profile[key]) <= set(allowed))
            self.assertFalse(set(profile['strong_maps']) & set(profile['weak_maps']))

    def test_import_uses_portraits_not_prose_links_and_preserves_direction(self):
        html = '''<div class="heroes_synergies"><img class="hero_portrait" title="Deckard Cain">
                  <p><a href="something">Johanna</a></p></div>
                  <div class="heroes_counters"><img class="hero_portrait" title="Varian"></div>
                  <div class="heroes_maps_stronger"><img title="Cursed Hollow"></div>
                  <div class="heroes_maps_weaker"><img title="Braxis Holdout"></div>'''
        profile = extract_matchups(html, 'Johanna')
        self.assertEqual(profile['synergies'], ['Deckard'])
        self.assertEqual(profile['countered_by'], ['Varian'])
        with self.assertRaises(ValueError):
            extract_matchups(html.replace('Varian', 'Unknown Hero'), 'Johanna')
        with self.assertRaises(ValueError):
            extract_matchups('<html>No matchup sections</html>', 'Johanna')


class RecommendationTests(unittest.TestCase):
    def test_blind_counters_are_directional(self):
        good = option('Johanna', enemies=['Illidan'])
        bad = option('Illidan', enemies=['Johanna'])
        self.assertTrue(any('Illidan' in r for r in good['why']))
        self.assertTrue(any('Johanna' in r for r in bad['warnings']))
        self.assertGreater(good['score'], option('Johanna')['score'])
        self.assertLess(bad['score'], option('Illidan')['score'])

    def test_named_synergy_counts_pair_once(self):
        base = option('Illidan')
        paired = option('Illidan', allies=['Abathur'])
        self.assertGreater(paired['score'], base['score'])
        effects = [e for e in paired['effects'] if e['category'] == 'synergy']
        self.assertEqual(len(effects), 1)
        self.assertIn('Abathur', effects[0]['text'])
        self.assertTrue(paired['sources'])

    def test_map_drawbacks_are_visible(self):
        results = rank([], [], [], {}, 'Braxis Holdout')
        aba = next(x for x in results if x['hero'] == 'Abathur')
        self.assertTrue(any('Braxis Holdout' in s for s in aba['warnings']))
        self.assertNotIn('map', [e['category'] for e in option('Abathur')['effects']])

    def test_two_remaining_slots_reserved_for_missing_cores(self):
        team = ['Jaina', 'Raynor', 'Sonya']
        prefs = {h: 'Favourite' for h in HEROES if HEROES[h]['role'] not in ('Tank', 'Healer')}
        results = rank(team, ['Illidan', 'Tracer', 'Genji'], [], prefs, 'Infernal Shrines')
        self.assertTrue(all(x['role'] in ('Tank', 'Healer') for x in results[:3]))
        self.assertTrue(all(x['core_risk'] == 0 for x in results[:3]))
        risky = next(x for x in results if x['hero'] == 'Cassia')
        self.assertGreater(risky['core_risk'], 0)
        self.assertEqual(risky['preference_bonus'], 0)

    def test_final_healer_cannot_be_displaced_by_a_counter_favourite(self):
        results = rank(['Johanna', 'Jaina', 'Sonya', 'Raynor'], ['Deathwing', 'Cho', 'Stitches', 'Diablo'], [],
                       {'Tychus': 'Favourite', 'Malthael': 'Favourite'}, 'Battlefield of Eternity')
        self.assertTrue(all(x['role'] == 'Healer' for x in results[:3]))

    def test_restricted_pool_explains_unfillable_role(self):
        results = rank(['Johanna', 'Jaina', 'Sonya', 'Raynor'], [], [], {}, 'Unknown map', available={'Murky'})
        self.assertEqual(len(results), 1)
        self.assertTrue(any('healer' in s for s in results[0]['warnings']))
        self.assertIn('Watch out:', recommendation_text(results[0], 1))

    def test_varian_only_counts_as_tank_when_confirmed(self):
        team = ['Varian', 'Jaina', 'Sonya', 'Anduin']
        unknown = rank(team, [], [], {}, 'Unknown map')
        self.assertTrue(all(x['role'] == 'Tank' for x in unknown[:3]))
        confirmed = rank(team, [], [], {}, 'Unknown map', plans={'Varian': 'Taunt (tank)'})
        self.assertNotEqual(confirmed[0]['role'], 'Tank')
        self.assertIn('Taunt', draft_summary(team, []))
        self.assertNotIn('tank cover', draft_summary(team, [], {'Varian': 'Taunt (tank)'}))
        candidate = option('Varian', role='Tank')
        self.assertEqual(candidate['role'], 'Tank')
        self.assertTrue(any('Taunt' in s for s in candidate['conditions']))

    def test_blaze_solo_lane_keeps_room_for_main_tank(self):
        team = ['Blaze', 'Malfurion', 'Jaina', 'Raynor']
        results = rank(team, [], [], {}, 'Unknown map', plans={'Blaze': 'Solo lane'})
        self.assertTrue(all(x['role'] == 'Tank' for x in results[:3]))
        self.assertEqual(effective_role('Blaze', {'Blaze': 'Solo lane'}), 'Bruiser')
        self.assertEqual(option('Blaze', allies=['Johanna'])['role'], 'Bruiser')

    def test_artanis_blind_is_explicitly_conditional(self):
        art = option('Artanis', enemies=['Raynor'])
        self.assertTrue(any('Suppression Pulse' in x for x in art['conditions']))
        self.assertTrue(any('Suppression Pulse' in x for x in art['why']))

    def test_bans_target_our_carry_and_ignore_our_pool_preferences_and_role(self):
        a = ['Illidan', 'Abathur']
        e = ['Diablo', 'Jaina']
        baseline = rank(a, e, [], {}, 'Cursed Hollow', for_ban=True)
        restricted = rank(a, e, [], {h: 'Never suggest' for h in HEROES}, 'Cursed Hollow',
                          role='Support', available=set(), for_ban=True)
        self.assertEqual([(x['hero'], x['score']) for x in baseline], [(x['hero'], x['score']) for x in restricted])
        self.assertIn(baseline[0]['hero'], GUIDANCE['Illidan']['countered_by'])
        self.assertTrue(any('your Illidan' in r for r in baseline[0]['why']))
        self.assertEqual(rank(a, e, ['Johanna', 'Li Li', 'Brightwing', 'Uther', 'Arthas', 'Muradin'], {}, 'Cursed Hollow', for_ban=True), [])

    def test_blanks_do_not_consume_draft_slots(self):
        self.assertEqual(rank(['Jaina'], [], [], {}, 'Unknown map'),
                         rank(['', 'Jaina', '', '', ''], [''] * 5, [''] * 6, {}, 'Unknown map'))

    def test_missing_guidance_falls_back_honestly(self):
        with patch('draft_engine.GUIDANCE', {}):
            self.assertIn('unavailable', draft_summary([], []))
            candidates = rank(['Jaina'], ['Illidan'], [], {}, 'Unknown map')
            self.assertTrue(candidates)
            self.assertTrue(all(not x['sources'] for x in candidates))

    def test_warnings_never_lost_behind_positive_reason_limit(self):
        result = option('Johanna', enemies=['Leoric', 'Varian'])
        result['why'] = ['Useful reason'] * 10
        text = recommendation_text(result, 1, 'Your record: no recorded games')
        for warning in result['warnings']:
            self.assertIn(warning, text)
        self.assertIn('Your record:', text)

    def test_random_drafts_preserve_exclusions_completion_and_order(self):
        rng = random.Random(82)
        heroes = sorted(HEROES)
        for _ in range(100):
            sample = rng.sample(heroes, 16)
            a, e, b = sample[:rng.randrange(6)], sample[5:5+rng.randrange(6)], sample[10:10+rng.randrange(7)]
            prefs = {h: rng.choice(['Allowed', 'Favourite', 'Never suggest']) for h in heroes}
            available = set(rng.sample(heroes, 45))
            results = rank(a, e, b, prefs, rng.choice(MAPS), available=available)
            self.assertFalse({x['hero'] for x in results} & set(a+e+b))
            self.assertTrue(all(x['hero'] in available and prefs[x['hero']] != 'Never suggest' for x in results))
            self.assertEqual([x['core_risk'] for x in results], sorted(x['core_risk'] for x in results))
            if len(a) == 5:
                self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
