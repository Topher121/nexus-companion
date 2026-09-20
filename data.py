"""Curated draft attributes, not live statistics or a tier list."""
ROLES = {
 'Tank': "Anub'arak|Arthas|Blaze|Cho|Diablo|E.T.C.|Garrosh|Johanna|Mal'Ganis|Mei|Muradin|Stitches|Tyrael",
 'Healer': 'Alexstrasza|Ana|Anduin|Auriel|Brightwing|Deckard|Kharazim|Li Li|Lt. Morales|Lúcio|Malfurion|Rehgar|Stukov|Tyrande|Uther|Whitemane',
 'Bruiser': 'Artanis|Chen|D.Va|Deathwing|Dehaka|Gazlowe|Hogger|Imperius|Leoric|Malthael|Ragnaros|Rexxar|Sonya|Thrall|Varian|Xul|Yrel',
 'Ranged': 'Azmodan|Cassia|Chromie|Falstad|Fenix|Gall|Genji|Greymane|Gul\'dan|Hanzo|Jaina|Junkrat|Kael\'thas|Kel\'Thuzad|Li-Ming|Lunara|Mephisto|Nazeebo|Nova|Orphea|Probius|Raynor|Sgt. Hammer|Sylvanas|Tassadar|Tracer|Tychus|Valla|Zagara|Zul\'jin',
 'Melee': 'Alarak|Illidan|Kerrigan|Maiev|Murky|Qhira|Samuro|The Butcher|Valeera|Zeratul',
 'Support': 'Abathur|Medivh|The Lost Vikings|Zarya',
}
HEROES = {h: {'role': role, 'tags': set()} for role, names in ROLES.items() for h in names.split('|')}
def tag(names, value):
 for name in names.split('|'): HEROES[name]['tags'].add(value)
tag("Illidan|The Butcher|Raynor|Valla|Zul'jin|Greymane|Tracer|Samuro|Artanis|Cassia|Fenix", 'attacks')
tag("Johanna|Li Li|Cassia|Artanis|Mei", 'blind')
tag("Illidan|The Butcher|Zeratul|Genji|Qhira|Kerrigan|Tracer|Diablo|Anub'arak", 'dive')
tag("Uther|Brightwing|Johanna|Muradin|E.T.C.|Arthas|Garrosh|Mal'Ganis|Stukov", 'peel')
tag("Jaina|Kael'thas|Gul'dan|Orphea|Li-Ming|Chromie|Kel'Thuzad|Mephisto|Tassadar", 'spells')
tag("Anub'arak|Brightwing", 'spell_defense')
tag("Johanna|Blaze|Gazlowe|Hogger|Xul|Ragnaros|Sonya|Leoric|Malthael|Jaina|Kael'thas|Gul'dan|Nazeebo|Azmodan|Tassadar|Zagara|Sylvanas|Falstad|Deathwing|Mephisto|Orphea", 'clear')
tag("Dehaka|Falstad|Brightwing|The Lost Vikings|Abathur", 'global')
tag("Valla|Greymane|Raynor|Hanzo|Artanis", 'race')
tag("Tychus|Malthael|Leoric", 'anti_tank')
tag("Diablo|E.T.C.|Garrosh|Anub'arak|Muradin|Maiev|Kerrigan", 'engage')
tag("Jaina|Kael'thas|Orphea|Gul'dan|Hanzo|Tassadar", 'followup')
MAPS = ['Unknown map','Alterac Pass','Battlefield of Eternity','Blackheart\'s Bay','Braxis Holdout','Cursed Hollow','Dragon Shire','Garden of Terror','Haunted Mines','Hanamura Temple','Infernal Shrines','Sky Temple','Tomb of the Spider Queen','Towers of Doom','Volskaya Foundry','Warhead Junction']
from build_library import CATALOGUE, PROFILES, get_build
BUILDS = {hero: [t['talent'] for t in get_build(hero)['tiers']] for hero in HEROES if hero in PROFILES}
SOURCE_DATE = CATALOGUE['checked']
def guide_url(hero):
 return PROFILES.get(hero, {}).get('source', 'https://www.icy-veins.com/heroes/')
