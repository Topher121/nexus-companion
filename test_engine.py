import unittest
from engine import rank, validate, build_for
from data import HEROES

class DraftTests(unittest.TestCase):
 def test_exclusions_only_affect_picks(self):
  prefs={h:'Never suggest' for h in HEROES}
  self.assertEqual(rank([],[],[],prefs,'Unknown map'),[])
  self.assertTrue(rank([],[],[],prefs,'Unknown map',for_ban=True))
 def test_favourite_cannot_override_missing_healer(self):
  team=['Johanna','Jaina','Sonya','Raynor']
  picks=rank(team,[],[],{'Murky':'Favourite'},'Unknown map')
  self.assertEqual(HEROES[picks[0]['hero']]['role'],'Healer')
 def test_favourite_breaks_close_tie(self):
  picks=rank([],[],[],{'Whitemane':'Favourite'},'Unknown map',role='Healer')
  self.assertEqual(picks[0]['hero'],'Whitemane')
 def test_banned_and_picked_not_recommended(self):
  results=rank(['Johanna'],['Li Li'],['Rehgar'],{},'Unknown map')
  self.assertFalse({'Johanna','Li Li','Rehgar'} & {x['hero'] for x in results})
 def test_duplicate_validation(self):self.assertTrue(validate(['Johanna'],[],['Johanna']))
 def test_matchup_build(self):
  self.assertEqual(build_for('Li Li',['Zeratul'])[0][1],'Safety Sprint')
  self.assertEqual(build_for('Johanna',['Anduin'])[0][2],'Sins Exposed')
 def test_unknown_build_is_not_fabricated(self):self.assertEqual(build_for('Not a hero',[])[0],[])

if __name__=='__main__':unittest.main()
