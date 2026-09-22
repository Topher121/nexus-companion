"""Conservative, explainable matchup choices over the saved talent builds.

Rules select a listed alternative in the current build, preserving its main
synergies and heroic upgrade. No enemy talent choices or player skill are inferred.
"""
from build_library import AUTO_BUILD, get_build
from data import HEROES

# These are baseline abilities, not assumptions about an enemy's future talents.
CONTROL = {'Anub\'arak', 'Arthas', 'Blaze', 'Diablo', 'E.T.C.', 'Garrosh', 'Muradin',
           'Uther', 'Kerrigan', 'Qhira', 'Thrall', 'Malfurion', 'Anduin', 'Tyrande',
           'Imperius', 'Deckard', 'Xul', 'Kel\'Thuzad'}
SHIELDS = {'Artanis', 'Fenix', 'Johanna', 'Tyrael', 'Zarya'}

# Hero, level, talent, signal, minimum named enemies, practical reason.
# Each hero's talent guide is linked by the UI; reviewed 21 September 2026.
RULES = [
    ('Johanna', 7, 'Sins Exposed', 'healers', 1, 'Healing reduction against {names}; apply Punish to the target your team is focusing.'),
    ('Johanna', 1, 'Zealous Glare', 'attackers', 2, 'Extra blind coverage against {names}; space out the charges.'),
    ('Li Li', 4, 'Safety Sprint', 'divers', 1, 'Extra protection against {names}; activate it before their dive overwhelms you.'),
    ('Li Li', 7, "Let's Go!", 'control', 1, 'An ally cleanse for the control from {names}; it cannot target yourself.'),
    ('Brightwing', 13, 'Pixie Power', 'casters', 2, 'More Spell Armor against {names}; use Pixie Dust before their damage lands.'),
    ('Brightwing', 7, 'Critical Mist', 'control', 2, 'Adds healing to your active cleanse against the control from {names}.'),
    ('Arthas', 16, 'Anti-Magic Shell', 'casters', 2, 'Spell protection against {names}; activate it before the burst lands.'),
    ('Valla', 13, 'Gloom', 'casters', 2, 'Spell protection against {names}; keep its active available for burst.'),
    ('Artanis', 13, 'Phase Bulwark', 'casters', 2, 'Spell Armor helps your shield absorb the ability damage from {names}.'),
    ('Illidan', 13, 'Sixth Sense', 'casters', 2, 'Adds spell protection against {names}; Evasion alone covers basic attacks.'),
    ('Lunara', 13, 'Greater Spell Shield', 'casters', 2, 'Spell protection against {names}; keep your distance while it is unavailable.'),
    ('Malthael', 13, 'Shroud of Wisdom', 'casters', 2, 'Prepare the spell protection before {names} use their burst.'),
    ('Thrall', 13, 'Spirit Shield', 'casters', 2, 'Spell protection against the ability damage from {names}.'),
    ('Tychus', 13, 'Neosteel Coating', 'casters', 2, 'An active defensive option against spell damage from {names}.'),
    ('Tychus', 16, 'Titan Grenade', 'casters', 2, 'Pairs with Neosteel Coating against {names}, moving damage away from the longer Overkill channel.'),
    ('Zagara', 13, 'Spell Shield', 'casters', 2, 'Spell protection against {names}; avoid giving them a free opening while it is unavailable.'),
    ('Blaze', 7, 'Nanomachine Coating', 'attackers', 2, 'Oil reduces attack speed, helping control {names}.'),
    ('E.T.C.', 16, 'Imposing Presence', 'attackers', 2, 'Attack-speed reduction helps against {names}; use the active when they commit.'),
    ('Muradin', 16, 'Imposing Presence', 'attackers', 2, 'Attack-speed reduction helps protect you and nearby teammates from {names}.'),
    ('Malfurion', 7, "Nature's Cure", 'control', 2, 'Remove stuns and roots from {names} on allies with Regrowth; keep Regrowth active before the engage.'),
    ('Kharazim', 16, 'Cleansing Touch', 'control', 2, 'Use Radiant Dash to protect allies from the control of {names}.'),
    ('Uther', 7, 'Hand of Protection', 'control', 2, 'An ally cleanse against control from {names}; save it for a dangerous catch.'),
    ('Sylvanas', 16, 'Will of the Forsaken', 'control', 2, 'A personal escape from the control of {names}; keep it for their engage.'),
    ('Zarya', 16, 'Cleansing Shield', 'control', 2, 'Shield Ally can protect a teammate from control by {names}.'),
    ('Jaina', 16, 'Numbing Blast', 'divers', 2, 'A root to help stop {names} when they reach your backline; the target must be Chilled.'),
    ('Li-Ming', 16, 'Diamond Skin', 'divers', 2, 'A defensive Teleport shield when {names} reach you; keep an escape route.'),
    ('Imperius', 1, 'Burn the Impure', 'frontliners', 2, 'Percentage damage for the front line of {names}; consume your marks with attacks.'),
    ('Sgt. Hammer', 16, 'Giant Killer', 'frontliners', 2, 'Percentage damage against the front line of {names}; maintain safe attack uptime.'),
    ('Tracer', 10, 'Quantum Spike', 'frontliners', 2, 'Percentage damage gives Pulse Bomb more value against {names}.'),
    ('Varian', 13, 'Shattering Throw', 'shields', 2, 'Shield removal against {names}; coordinate the follow-up when their shield is broken.'),
]


def enemy_signals(enemies):
    enemies = list(dict.fromkeys(h for h in enemies if h in HEROES))
    return {
        'attackers': [h for h in enemies if 'attacks' in HEROES[h]['tags'] or h in {'Tychus', 'Lunara', 'Sgt. Hammer'}],
        'casters': [h for h in enemies if 'spells' in HEROES[h]['tags'] or h in {'Nazeebo', 'Azmodan', 'Gall'}],
        'divers': [h for h in enemies if 'dive' in HEROES[h]['tags']],
        'healers': [h for h in enemies if HEROES[h]['role'] == 'Healer'],
        'control': [h for h in enemies if h in CONTROL],
        'shields': [h for h in enemies if h in SHIELDS],
        'frontliners': [h for h in enemies if HEROES[h]['role'] in ('Tank', 'Bruiser')],
    }


def recommend_talents(hero, enemies, allies=(), plans=None):
    detail = get_build(hero, AUTO_BUILD)
    if not detail:
        return None
    reasons, changes = [], []
    plans = plans or {}
    if hero == 'Varian' and plans.get(hero) == 'Taunt (tank)':
        detail = get_build(hero, 'Defensive Taunt Build')
        reasons.append('Your confirmed tank plan selects Taunt and the defensive build.')
    elif hero == 'Varian' and plans.get(hero) == 'Damage build':
        detail = get_build(hero, 'Colossus Smash Build')
        reasons.append('Your confirmed damage plan selects Colossus Smash; this does not fill the tank role.')
    signals = enemy_signals(enemies)
    for rule_hero, level, talent, signal, minimum, explanation in RULES:
        names = signals[signal]
        if rule_hero != hero or len(names) < minimum:
            continue
        # Ana already supplies strong healing denial; avoid forcing another
        # anti-heal choice when Johanna's default movement talent still fits.
        if hero == 'Johanna' and talent == 'Sins Exposed' and 'Ana' in allies:
            continue
        tier = next((t for t in detail['tiers'] if t['level'] == level), None)
        extra = ('Safety Sprint',) if (hero, level) == ('Li Li', 4) else ()
        if not tier or talent not in [tier['talent'], *tier['alternatives'], *extra]:
            continue
        reason = explanation.format(names=', '.join(names))
        reasons.append(f'Level {level} · {talent}: {reason}')
        previous = tier['talent']
        if previous != talent:
            tier['talent'] = talent
            tier['alternatives'] = list(dict.fromkeys([previous] + [t for t in tier['alternatives'] if t != talent]))
            changes.append(f'Level {level}: {talent} replaces {previous}. {reason}')
    detail.update(adjustments=changes, selection_reasons=reasons)
    return detail
