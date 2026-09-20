"""Ban-reader regressions using only the top icon strips of supplied screenshots."""
import unittest
from pathlib import Path
import bootstrap
from PIL import Image
from vision import read_bans
from engine import rank

FIXTURES = Path(__file__).parent/'tests'/'fixtures'


class BanPortraitTests(unittest.TestCase):
    def read(self, name):
        with Image.open(FIXTURES/(name+'.png')) as source:
            return read_bans(source.convert('RGB'))

    def test_reported_missing_johanna_ban_and_pick_exclusion(self):
        bans = self.read('complete-bans')
        names = [b['hero'] for b in bans]
        self.assertEqual(names, ["Kael'thas", 'Li-Ming', 'Qhira', 'Johanna', 'Brightwing', 'Azmodan'])
        self.assertEqual([b['index'] for b in bans], list(range(6)))
        picks = rank(['Varian', 'Li Li', 'Nazeebo'], ['Valla', 'Sonya'], names,
                     {'Johanna':'Favourite'}, 'Cursed Hollow')
        self.assertNotIn('Johanna', [p['hero'] for p in picks])
        self.assertFalse(set(names) & {p['hero'] for p in picks})

    def test_pending_and_empty_ban_slots_are_not_heroes(self):
        for fixture, expected in [
            ('partial-bans', {0:'Whitemane',1:'Muradin',3:'Li-Ming',4:'Brightwing'}),
            ('empty-ban-slots', {0:'Brightwing',1:'Anduin',3:'Azmodan',4:'Dehaka'}),
        ]:
            with self.subTest(fixture=fixture):
                self.assertEqual({b['index']:b['hero'] for b in self.read(fixture)}, expected)

    def test_johanna_in_another_ban_slot_and_match(self):
        bans = {b['index']:b['hero'] for b in self.read('johanna-early-ban')}
        self.assertEqual(bans[4], 'Johanna')
        self.assertNotIn(2, bans)
        self.assertNotIn(5, bans)


if __name__ == '__main__':
    unittest.main()
