"""Draft-specific coaching rules; enemy talent choices are not read from the draft."""
BLIND_VALUE = {
    'Illidan': (100, 'while he is attacking your team; missed attacks also deny his attack-based sustain'),
    'The Butcher': (100, 'after his charge connects and he starts attacking, especially during his Brand'),
    "Zul'jin": (95, 'during his rapid low-health attacks; keep your distance'),
    'Tychus': (95, 'while Minigun is active against your frontline'),
    'Greymane': (90, 'when he commits in Worgen form'),
    'Valla': (90, 'when she steps up to attack; blinds will not stop her ability damage'),
    'Raynor': (90, 'while he is firing at an ally'),
    'Tracer': (85, 'when she commits to a nearby ally'),
    'Artanis': (85, 'while he is attacking; missed attacks limit his attack-based shield cooldown reduction'),
    'Samuro': (85, 'when he and his images commit to a teammate'),
    'Fenix': (85, 'during sustained attacks'),
    'Cassia': (80, 'during attacks; her spell damage still gets through'),
    'Sgt. Hammer': (80, 'during sustained fire, if safely reachable'),
    'Lunara': (80, 'before attacks apply more poison; an existing poison is not removed'),
    'Sylvanas': (75, 'when she is attacking your team; her spell damage still gets through'),
    'Thrall': (75, 'during Windfury attacks'),
    'Zeratul': (70, 'when he commits to attack a vulnerable ally'),
    'Hanzo': (60, 'if he steps into attack range; arrows from his abilities are unaffected'),
    'Varian': (70, 'when he reaches an ally; Twin Blades makes him a much higher blind priority'),
}

def matchup_notes(hero, enemies, talents=None):
    enemies = list(dict.fromkeys(enemies))
    notes = []
    if not enemies:
        return ['Enemy picks are not known yet. Match-specific targets will appear as they lock.']
    can_blind = hero in ('Li Li','Johanna','Cassia','Mei','Artanis')
    if hero == 'Artanis' and talents is not None and 'Suppression Pulse' not in talents:
        can_blind = False
    if can_blind:
        priority = sorted((e for e in enemies if e in BLIND_VALUE), key=lambda e: -BLIND_VALUE[e][0])
        if priority:
            notes.append('BLIND PRIORITY — ' + '; '.join(f'{e}: {BLIND_VALUE[e][1]}' for e in priority[:3]) + '. Prioritise whoever is actively threatening an ally.')
        else:
            notes.append('BLINDS — No obvious attack-focused carry in the known picks. Blind whoever is actively attacking a vulnerable ally; do not chase a target just to blind them.')
        if 'Varian' in enemies:
            notes.append('CHECK VARIAN AT LEVEL 4 — Twin Blades makes him a top blind target. With Taunt or Colossus Smash, still blind his follow-up attacks, but respect the crowd control or burst. His build cannot be known from draft alone.')
        if hero == 'Li Li':
            notes.append('LANDING YOUR BLIND — E automatically hits the two nearest enemies, preferring heroes. Stay safe and let the attackers enter range; you cannot click a distant priority target. Blinds stop basic attacks, not spell damage or crowd control.')
        elif hero == 'Johanna':
            notes.append('LANDING YOUR BLIND — Aim Shield Glare through the dangerous attacker as they start dealing damage. Keep it for a diver when needed. Blinds do not stop abilities.')
    if hero == 'Li Li':
        dangers = {'Stitches':'stay behind minions to block Hook', 'Arthas':'avoid his root and do not let his slow trap you',
                   'Malfurion':'avoid his root zone', 'Blaze':'sidestep Jet Propulsion', 'Muradin':'avoid Storm Bolt',
                   'Diablo':'stay away from wall-stun angles', 'Alarak':'keep clear of his pull/silence combo',
                   'Tyrande':'move out of her stun marker', 'Anub\'arak':'watch for his stuns and Cocoon',
                   'Uther':'do not walk into his stun range'}
        threats = [f'{e}: {dangers[e]}' for e in enemies if e in dangers]
        if threats:
            notes.append('KEEP HEALING SAFELY — ' + '; '.join(threats[:3]) + '. Start Cups from a safe position; save Let’s Go! for a threatened ally, not yourself.')
        if 'Leoric' in enemies:
            notes.append('LEORIC — Keep space so Entomb cannot trap you with your backline. Blind will not break Drain Hope; move out of its tether range.')
    if hero == 'Brightwing':
        from data import HEROES
        divers = [e for e in enemies if 'dive' in HEROES[e]['tags']]
        if divers:
            notes.append('POLYMORPH TARGETS — ' + ', '.join(divers[:3]) + ': save W for the one committing to your backline, or chain it after your tank’s control.')
    if hero == 'Johanna':
        if 'Stitches' in enemies:
            notes.append('STITCHES — Keep yourself between his Hook and your damage dealers when safe. Use Iron Skin before control connects.')
        if 'Anduin' in enemies:
            interrupt = 'Blessed Shield' if talents is None or 'Blessed Shield' in talents else 'Condemn'
            notes.append(f'ANDUIN — Keep {interrupt} available to interrupt Holy Word: Salvation if he chooses it and you can reach him safely. Do not spend the whole team’s burst into his protected target.')
    return notes
