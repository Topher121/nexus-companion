"""Explainable draft advice. Scores are priorities, never win probabilities.

Team completion is ordered before preference. Guide relationships are bounded
signals: two pages listing a pair count once, and silence is not a counter.
"""
import json
from pathlib import Path
from data import HEROES, MAPS


def load_guidance():
    try:
        raw = json.loads(Path(__file__).with_name('draft_catalogue.json').read_text(encoding='utf-8'))
        profiles = raw['heroes']
        if raw['version'] != 1 or set(profiles) != set(HEROES):
            raise ValueError('Incomplete catalogue')
        for hero, profile in profiles.items():
            for key, allowed in [('synergies', HEROES), ('countered_by', HEROES),
                                 ('strong_maps', MAPS), ('weak_maps', MAPS)]:
                values = profile[key]
                if not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed or v == hero for v in values):
                    raise ValueError('Invalid relationship')
            if not profile['source'].startswith('https://www.icy-veins.com/heroes/'):
                raise ValueError('Invalid source')
        return profiles
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


GUIDANCE = load_guidance()
BASE_BLINDS = {'Johanna', 'Li Li', 'Cassia', 'Mei'}
SOLO_LANERS = {h for h in HEROES if HEROES[h]['role'] == 'Bruiser'} - {'Varian'}
SOLO_LANERS |= {'Blaze', 'Murky', 'Samuro', 'The Lost Vikings'}
SUSTAINED_DAMAGE = {h for h in HEROES if 'attacks' in HEROES[h]['tags']} | {'Lunara', 'Tychus', 'Sylvanas'}
MAP_CLEAR = {'Infernal Shrines', 'Tomb of the Spider Queen', 'Haunted Mines'}
MAP_GLOBAL = {'Cursed Hollow', 'Sky Temple', 'Warhead Junction', 'Garden of Terror'}
MAP_SOLO = {'Dragon Shire', 'Braxis Holdout'}
FLEX_CHOICES = {
    'Varian': ('Unconfirmed', 'Taunt (tank)', 'Damage build'),
    'Blaze': ('Unconfirmed', 'Tank', 'Solo lane'),
}


def effective_role(hero, plans=None):
    plan = (plans or {}).get(hero, 'Unconfirmed')
    if hero == 'Varian' and plan == 'Taunt (tank)':
        return 'Tank'
    if hero == 'Blaze' and plan == 'Solo lane':
        return 'Bruiser'
    return HEROES[hero]['role']


def candidate_role(hero, team, requested, plans):
    if hero not in FLEX_CHOICES:
        return HEROES[hero]['role']
    if plans.get(hero, 'Unconfirmed') != 'Unconfirmed':
        return effective_role(hero, plans)
    if requested in ('Tank', 'Bruiser'):
        return requested
    return 'Bruiser' if any(effective_role(h, plans) == 'Tank' for h in team) else 'Tank'


def team_needs(team, plans=None):
    roles = {effective_role(h, plans) for h in team}
    return [role for role in ('Tank', 'Healer') if role not in roles]


def draft_summary(allies, enemies, plans=None, ally_hovers=(), final=False):
    allies = [h for h in allies if h in HEROES]
    enemies = [h for h in enemies if h in HEROES]
    if final:
        if len(allies) == len(enemies) == 5:
            return 'Draft finished. All 10 heroes recorded. Review Talents & tips.'
        return (f'Draft finished in HotS. Recorded {len(allies)}/5 allies and {len(enemies)}/5 enemies. '
                'Highlighted blanks are unread locked picks, not open draft slots. Match advice uses the recorded heroes.')
    plans = plans or {}
    tentative = list(dict.fromkeys(h for h in ally_hovers if h in HEROES and h not in allies + enemies))[:max(0, 4-len(allies))]
    missing = team_needs(allies + tentative, plans)
    messages = []
    if len(allies) == 5:
        messages.append('Draft complete. Review Talents & tips.')
    else:
        messages.append(f'{len(allies)}/5 allies locked. {len(tentative)} teammate hover(s) included.' if tentative else f'{5-len(allies)} allied slot(s) left.')
    if missing:
        messages.append('Still needed: ' + ', '.join(r.lower() for r in missing) + '.')
    if 'Varian' in allies + tentative + enemies and plans.get('Varian', 'Unconfirmed') == 'Unconfirmed':
        messages.append('Confirm Varian’s plan below; tank cover requires Taunt.')
    if 'Blaze' in allies + tentative + enemies and plans.get('Blaze', 'Unconfirmed') == 'Unconfirmed':
        messages.append('Blaze is counted as tank until Solo lane is selected.')
    if not enemies:
        messages.append('Enemy picks unknown: recommendations use team and map fit.')
    elif len(enemies) < 5:
        messages.append(f'{len(enemies)}/5 enemy picks known; matchup advice will change.')
    if not GUIDANCE:
        messages.append('Saved matchup guidance unavailable; using basic role and ability rules.')
    return ' '.join(messages)


def rank(allies, enemies, bans, prefs, map_name, role='Any', for_ban=False, available=None, plans=None, ally_hovers=()):
    allies = list(dict.fromkeys(h for h in allies if h in HEROES))
    enemies = list(dict.fromkeys(h for h in enemies if h in HEROES))
    bans = list(dict.fromkeys(h for h in bans if h in HEROES))
    tentative = list(dict.fromkeys(h for h in ally_hovers if h in HEROES and h not in allies + enemies + bans))[:max(0, 4-len(allies))]
    projected = allies + tentative
    team, opposition = (enemies, projected) if for_ban else (projected, enemies)
    if len(team) >= 5 or (for_ban and len(bans) >= 6):
        return []
    used = set(projected + enemies + bans)
    plans = plans or {}
    roles = [effective_role(h, plans) for h in team]
    missing = team_needs(team, plans)
    team_tags = set().union(*(HEROES[h]['tags'] for h in team))
    results = []
    for hero, info in HEROES.items():
        preference = prefs.get(hero, 'Allowed')
        if hero in used or hero in ('Cho', 'Gall'):
            continue
        if not for_ban and (preference in ('Never suggest', 'Not owned') or (available is not None and hero not in available)):
            continue
        r = candidate_role(hero, team, 'Any' if for_ban else role, plans)
        if not for_ban and role != 'Any' and r != role:
            continue
        tags = info['tags']
        effects = []
        warnings = []
        conditions = []
        if tentative:
            conditions.append('Assumes teammate hovers: ' + ', '.join(tentative) + '. These picks can change.')
        evidence = []

        def add(points, message, category):
            effects.append({'points': points, 'text': message, 'category': category})
            if points < 0:
                warnings.append(message)

        if r in missing:
            add(34, f'Fills {"their" if for_ban else "the"} missing {r.lower()} role', 'team')
        if r in ('Tank', 'Healer') and r in roles:
            add(-28, f'Adds a second {r.lower()}; check the team’s damage and lane coverage', 'team')
        if r == 'Ranged' and 'Ranged' not in roles:
            add(20, 'Adds ranged damage', 'team')
        has_solo = any(h in SOLO_LANERS and effective_role(h, plans) != 'Tank' for h in team)
        if r == 'Ranged' and roles.count('Ranged') >= 2 and not has_solo:
            add(-24, 'Third ranged damage pick with no established solo laner; consider a bruiser with waveclear', 'team')
        if len(team) == 4 and not has_solo and hero in SOLO_LANERS and r != 'Tank':
            add(12, 'Last slot can cover the missing solo lane', 'team')
        if hero in SOLO_LANERS and r != 'Tank' and not any(h in SOLO_LANERS and effective_role(h, plans) != 'Tank' for h in team):
            add(14, 'Provides a solo-lane option', 'team')
        if 'clear' in tags and 'clear' not in team_tags:
            add(12, 'Adds missing waveclear', 'team')
        if hero in SUSTAINED_DAMAGE and not set(team) & SUSTAINED_DAMAGE:
            add(7 if team else 0, 'Adds sustained damage alongside the existing picks', 'team')
        if 'spells' in tags and set(team) & SUSTAINED_DAMAGE and 'spells' not in team_tags:
            add(7, 'Adds spell damage alongside basic-attack damage', 'team')

        missing_after = [x for x in missing if x != r]
        core_risk = max(0, len(missing_after) - (4 - len(team)))
        if core_risk:
            warnings.insert(0, 'Not enough remaining slots for: ' + ', '.join(x.lower() for x in missing_after))
        if hero == 'Varian':
            conditions.append('Requires Taunt at level 4 to fill the tank role' if r == 'Tank' else 'Damage Varian does not replace a main tank')
        if hero == 'Blaze':
            conditions.append('Use Blaze in the solo lane; keep the existing main tank' if r == 'Bruiser' else 'Counts Blaze as main tank; confirm his intended role')
        if hero == 'Abathur':
            warnings.append('Needs coordinated rotations; only four allied bodies can contest objectives')

        # Named, directional relationships from saved guides. No fabricated rates.
        profile = GUIDANCE.get(hero, {})
        partners = [h for h in team if h in profile.get('synergies', []) or hero in GUIDANCE.get(h, {}).get('synergies', [])]
        targets = [h for h in opposition if hero in GUIDANCE.get(h, {}).get('countered_by', [])]
        threats = [h for h in opposition if h in profile.get('countered_by', [])]
        if partners:
            add(min(14, 7 * len(partners)), 'Guide synergy with ' + ', '.join(partners), 'synergy')
            evidence.extend([profile.get('source')] + [GUIDANCE[h]['source'] for h in partners])
        if targets:
            add(min(24, 12 * len(targets)), ('Guide counter to your ' if for_ban else 'Guide counter to enemy ') + ', '.join(targets), 'matchup')
            evidence.extend(GUIDANCE[h]['source'] for h in targets)
        if threats:
            add(-min(28, 14 * len(threats)), ('Your team already has guide counters: ' if for_ban else 'Difficult guide matchups: ') + ', '.join(threats), 'matchup')
            evidence.append(profile.get('source'))

        # Ability rules also provide a plain-language reason where known.
        attackers = [h for h in opposition if 'attacks' in HEROES[h]['tags']]
        if hero in BASE_BLINDS and attackers:
            add(min(14, 7 * len(attackers)), 'Blinds against ' + ', '.join(attackers), 'matchup')
        if hero == 'Artanis' and attackers:
            add(5, 'Suppression Pulse can blind ' + ', '.join(attackers), 'matchup')
            conditions.append('Blind value requires Suppression Pulse at level 10')
        blinds = [h for h in opposition if h in BASE_BLINDS]
        if 'attacks' in tags and blinds:
            add(-min(16, 8 * len(blinds)), 'Basic attacks vulnerable to blinds from ' + ', '.join(blinds), 'matchup')
        divers = [h for h in opposition if 'dive' in HEROES[h]['tags']]
        if 'peel' in tags and divers:
            add(9, 'Helps peel ' + ', '.join(divers) + ' off teammates', 'matchup')
        casters = [h for h in opposition if 'spells' in HEROES[h]['tags']]
        if 'spell_defense' in tags and len(casters) >= 2:
            add(9, 'Defensive tools against spells from ' + ', '.join(casters), 'matchup')
        frontliners = [h for h in opposition if effective_role(h, plans) in ('Tank', 'Bruiser') or h == 'Cho']
        if 'anti_tank' in tags and len(frontliners) >= 2:
            add(12, 'Percentage damage against ' + ', '.join(frontliners), 'matchup')
        if 'followup' in tags and 'engage' in team_tags and not partners:
            add(6, 'Follow-up damage for ' + ', '.join(h for h in team if 'engage' in HEROES[h]['tags']), 'synergy')
        if 'engage' in tags and 'followup' in team_tags and not partners:
            add(6, 'Sets up ' + ', '.join(h for h in team if 'followup' in HEROES[h]['tags']), 'synergy')

        # Use a guide map rating OR a generic map capability, not both.
        if map_name in profile.get('strong_maps', []):
            add(10, 'Guide lists ' + map_name + ' as a stronger map', 'map')
            evidence.append(profile.get('source'))
        elif map_name in profile.get('weak_maps', []):
            add(-8, 'Guide lists ' + map_name + ' as a weaker map', 'map')
            evidence.append(profile.get('source'))
        elif map_name in MAP_CLEAR and 'clear' in tags:
            add(8, 'Area damage for ' + map_name, 'map')
        elif map_name in MAP_GLOBAL and 'global' in tags:
            add(8, 'Global presence on ' + map_name, 'map')
        elif map_name == 'Battlefield of Eternity' and 'race' in tags:
            add(10, 'Damage for the Immortal race', 'map')
        elif map_name in MAP_SOLO and hero in SOLO_LANERS and r != 'Tank':
            add(8, 'Solo-lane presence for a split objective', 'map')

        parts = {k: sum(e['points'] for e in effects if e['category'] == k) for k in ('team', 'synergy', 'matchup', 'map')}
        # Related guide/capability evidence must not overwhelm role completion.
        parts['matchup'] = max(-32, min(32, parts['matchup']))
        score = sum(parts.values())
        if for_ban:
            # Threats to our known picks matter more than filling an enemy role.
            score = parts['team'] * .65 + parts['synergy'] + parts['matchup'] * 1.5 + parts['map']
        positives = sorted((e for e in effects if e['points'] > 0), key=lambda e: -e['points'])
        why = [e['text'] for e in positives] or ['General option; no specific advantage found in this partial draft']
        results.append({'hero': hero, 'role': r, 'score': score, 'base_score': score, 'core_risk': core_risk,
                        'why': why, 'warnings': warnings, 'conditions': conditions, 'effects': effects,
                        'sources': sorted(set(x for x in evidence if x)), 'favourite': preference == 'Favourite',
                        'preference_bonus': 0})

    # A favourite can only break a close tie among candidates with the best
    # achievable core-role coverage, and never influences bans.
    best_risk = min((x['core_risk'] for x in results), default=0)
    best = max((x['score'] for x in results if x['core_risk'] == best_risk), default=0)
    for x in results:
        if not for_ban and x['favourite'] and x['core_risk'] == best_risk and x['score'] >= best - 5:
            x['score'] += 3
            x['preference_bonus'] = 3
            x['why'].append('Favourite: already among the closest draft fits')
    return sorted(results, key=lambda x: (x['core_risk'], -x['score'], x['hero']))


def recommendation_text(result, number, record='', for_ban=False):
    """Keep warnings separate so positive-reason truncation cannot hide them."""
    lines = [f"{number}. {result['hero']}  ·  {result['role']}"]
    if record:
        lines.append(record)
    lines.extend('• ' + reason for reason in result['why'][:4])
    if result['preference_bonus']:
        lines.append('Preference: favourite used to break a close fit')
    lines.extend('Plan: ' + condition for condition in result['conditions'])
    prefix = 'Lower priority: ' if for_ban else 'Watch out: '
    lines.extend(prefix + warning for warning in result['warnings'])
    return '\n'.join(lines) + '\n'
