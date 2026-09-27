"""Data-driven matchup choices; never clicks talents in the game.

Whole builds are selected before compatible alternatives. Inputs are recorded
picks, not assumed enemy talents, quest progress or player skill.
"""
from datetime import date
from build_library import AUTO_BUILD, CATALOGUE, get_build
from data import HEROES

ADVICE = CATALOGUE['advice']


def enemy_signals(enemies):
    names = list(dict.fromkeys(h for h in enemies if h in HEROES))
    return {signal: [h for h in names if h in members]
            for signal, members in ADVICE['signals'].items()}


def content_status(today=None):
    age = ((today or date.today()) - date.fromisoformat(CATALOGUE['checked'])).days
    return (f"Guides checked {CATALOGUE['checked']}; matchup rules reviewed {ADVICE['reviewed']}. "
            + ('Advice is over 30 days old; check Settings for content updates. ' if age > 30 else '')
            + 'Guide-based advice, not live meta or win-rate rankings.')


def _matches(rule, enemies, allies, plans, battleground):
    when = rule['when']
    enemy, friendly = enemy_signals(enemies), enemy_signals(allies)
    for side, signals in [('enemy', enemy), ('ally', friendly)]:
        if any(len(signals[s]) < n for s, n in when.get(side, {}).items()):
            return False
    # An incomplete draft cannot prove the absence of a threat.
    if when.get('absent') and (len(enemies) != 5 or any(enemy[s] for s in when['absent'])):
        return False
    for key, names in [('enemy_names', enemies), ('ally_names', allies)]:
        if key in when and not set(when[key]) & set(names):
            return False
    if set(when.get('ally_absent_names', [])) & set(allies):
        return False
    if 'maps' in when and battleground not in when['maps']:
        return False
    plan = plans.get(rule['hero'], 'Unconfirmed')
    if 'plan' in when and plan not in when['plan']:
        return False
    if plan in when.get('plan_not', []):
        return False
    return True


def _reason(rule, enemies, allies):
    when = rule['when']
    enemy, friendly = enemy_signals(enemies), enemy_signals(allies)
    names = [h for h in enemies if h in when.get('enemy_names', []) or
             any(h in enemy[s] for s in when.get('enemy', {}))]
    friends = [h for h in allies if h in when.get('ally_names', []) or
               any(h in friendly[s] for s in when.get('ally', {}))]
    return rule['reason'].format(names=', '.join(names), allies=', '.join(friends))


def recommend_talents(hero, enemies, allies=(), plans=None, battleground=None):
    detail = get_build(hero, AUTO_BUILD)
    if not detail:
        return None
    enemies = list(dict.fromkeys(h for h in enemies if h in HEROES and h != hero))
    allies = list(dict.fromkeys(h for h in allies if h in HEROES and h != hero))
    plans = plans or {}
    reasons, changes, matched = [], [], []
    rules = [r for r in ADVICE['rules'] if r['hero'] == hero
             and _matches(r, enemies, allies, plans, battleground)]
    # First whole-build rule wins; do not splice two packages.
    selection = next((r for r in rules if 'build' in r), None)
    if selection:
        previous = detail['name']
        detail = get_build(hero, selection['build'])
        reasons.append(_reason(selection, enemies, allies))
        matched.append(selection['id'])
        if previous != detail['name']:
            changes.append(f"Build: {detail['name']} replaces {previous}.")
    elif hero == 'Varian':
        reasons.append('Taunt is the default tank plan. This package keeps Overpower and '
                       'Warbringer together. Choose Damage build on the Draft page only '
                       'if another hero will tank.')
    # Later alternatives win ties. Explain only the final choice at each tier.
    decisions = {}
    for rule in rules:
        if 'choices' not in rule:
            continue
        targets = []
        for level, talent in rule['choices'].items():
            tier = next(t for t in detail['tiers'] if t['level'] == int(level))
            extras = ADVICE['extra_alternatives'].get(hero, {}).get(level, [])
            if talent not in [tier['talent'], *tier['alternatives'], *extras]:
                break
            targets.append((int(level), talent))
        else:
            for level, talent in targets:
                decisions[level] = (talent, rule)
    for tier in detail['tiers']:
        level = tier['level']
        if level not in decisions:
            continue
        talent, rule = decisions[level]
        previous = tier['talent']
        reasons.append(f'Level {level} · {talent}: '+_reason(rule, enemies, allies))
        matched.append(rule['id'])
        if previous != talent:
            tier['talent'] = talent
            tier['alternatives'] = list(dict.fromkeys([previous] + [t for t in tier['alternatives'] if t != talent]))
            changes.append(f'Level {level}: {talent} replaces {previous}.')
    if not reasons:
        reasons.append('No confirmed enemy picks yet; start with the saved guide build.' if not enemies else
                       'Checked the recorded matchup. No supported alternative is a clear fit; '
                       'keep this complete guide build rather than mix unrelated talent packages.')
    detail.update(adjustments=changes, selection_reasons=reasons,
                  matched_rules=list(dict.fromkeys(matched)), content_status=content_status(),
                  enemy_count=len(enemies))
    return detail
