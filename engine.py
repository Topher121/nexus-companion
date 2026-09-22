from data import HEROES
from build_library import AUTO_BUILD, get_build
from hero_tips import HERO_TIPS

def validate(allies, enemies, bans):
 all_names = [n for n in allies + enemies + bans if n]
 if any(n not in HEROES for n in all_names): return 'Choose heroes from the list; an entry is not recognised.'
 if len(all_names) != len(set(all_names)): return 'A hero appears more than once. Remove the duplicate pick or ban.'
 return ''

# Kept here for existing UI and integrations.
from draft_engine import rank

def build_details(hero, enemies, variant=AUTO_BUILD, allies=(), plans=None):
 """Resolve a complete source build, then apply only supported automatic rules."""
 from matchups import matchup_notes
 from talent_advisor import recommend_talents
 detail = recommend_talents(hero, enemies, allies, plans) if variant == AUTO_BUILD else get_build(hero, variant)
 if detail is None:return None
 enemies = list(dict.fromkeys(e for e in enemies if e in HEROES))
 adjustments = detail.get('adjustments', [])
 detail.setdefault('selection_reasons', [])
 talents = [t['talent'] for t in detail['tiers']]
 notes = matchup_notes(hero, enemies, talents) + list(HERO_TIPS.get(hero, []))
 if hero == 'Azmodan':
  if 'Gluttony' in talents:notes.append('Gluttony focuses on Globes in teamfights. Aim for its 225-stack reward; Greed is the alternative build for heavier lane pressure.')
  if 'Art of Chaos' in talents:notes.append('Art of Chaos rewards hitting at least two heroes with a Globe. Follow allied stuns or roots.')
  if 'Tide of Sin' in talents:notes.append('Activate Tide of Sin before launching the Globe you want to empower.')
 if hero == 'Li Li':
  if "Let's Go!" in talents:notes.append('Let’s Go! is an active ally cleanse; it cannot target yourself.')
  if 'Jug of 1,000 Cups' in talents:notes.append('Start Cups before allies are almost dead. Keep moving during it and avoid enemy interrupts.')
 if hero == 'Johanna' and 'Zealous Glare' in talents:notes.append('Space out your Shield Glare charges so their blinds do not overlap.')
 if hero == 'Brightwing' and 'Critical Mist' in talents:notes.append('Critical Mist adds healing to your active D. Use it when nearby allies need a cleanse; Magic Spit attacks help bring it back sooner.')
 if hero == 'Varian':
  if 'Taunt' in talents:notes.append('Taunt at level 4 makes this your tank build. Use it on a target allies can hit, or to stop a diver or channel.')
  elif 'Colossus Smash' in talents:notes.append('Use Colossus Smash before the rest of your burst so the armor reduction benefits it. This build does not replace a main tank.')
  else:notes.append('Twin Blades needs sustained safe attacks. Stay with your team and avoid committing into blinds; this build does not replace a main tank.')
 if hero == 'Kharazim':
  if 'Divine Palm' in talents:notes.append('Time Divine Palm for impending lethal damage; extra healing before it triggers can prevent the rescue heal.')
  if 'Seven-Sided Strike' in talents:notes.append('Use Seven-Sided Strike on an isolated, controlled hero so its damage is not divided across several enemies.')
 if hero in ('Li Li','Brightwing') and 'Stitches' in enemies: notes.append('Keep minions between you and Stitches to block hooks.')
 detail.update(talents=talents, notes=notes, adjustments=adjustments, automatic=variant == AUTO_BUILD)
 return detail


def build_for(hero, enemies, variant=AUTO_BUILD):
 """Compatibility API for consumers that only need talent names and notes."""
 detail = build_details(hero, enemies, variant)
 return (detail['talents'], detail['notes']) if detail else ([], [])
