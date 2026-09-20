import re
import unicodedata
from data import HEROES

def normalize(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub('[^a-z0-9]', '', value)

IDS = {normalize(h): h for h in HEROES}
IDS.update(dict(amazon='Cassia', barbarian='Sonya', butcher='The Butcher', demonhunter='Valla',
                faeriedragon='Brightwing', firebat='Blaze', genngreymane='Greymane', l90etc='E.T.C.',
                lostvikings='The Lost Vikings', medic='Lt. Morales', meiow='Mei', monk='Kharazim',
                necromancer='Xul', nexushunter='Qhira', witchdoctor='Nazeebo', wizard='Li-Ming',
                tinker='Gazlowe', crusader='Johanna', dryad='Lunara'))
