"""Validate the data-only advice shipped with a content release."""
from datetime import date
import hashlib
import json
from string import Formatter


def content_basis(catalogue):
    raw = json.dumps({'heroes': catalogue['heroes'], 'draft': catalogue.get('draft')},
                     sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def validate_advice(catalogue):
    from data import MAPS
    heroes = catalogue['heroes']
    advice = catalogue.get('advice')
    if not isinstance(advice, dict) or advice.get('schema') != 1:
        raise ValueError('Content needs a supported matchup rule set')
    if advice.get('basis') != content_basis(catalogue):
        raise ValueError('Builds or draft advice changed; matchup rules need review')
    for key in ('reviewed', 'guide_checked'):
        try: date.fromisoformat(advice[key])
        except (ValueError, TypeError, KeyError): raise ValueError('Invalid advice review date') from None
    if advice['guide_checked'] != catalogue['checked']:
        raise ValueError('Advice review does not match the guide check date')
    def names(value, allowed):
        if (not isinstance(value, list) or not value
                or any(not isinstance(n, str) or n not in allowed for n in value)
                or len(value) != len(set(value))):
            raise ValueError('Invalid advice names')
    signals = advice.get('signals')
    if not isinstance(signals, dict) or not signals or len(signals) > 50:
        raise ValueError('Invalid matchup signals')
    for signal, members in signals.items():
        if not isinstance(signal, str) or not signal.isidentifier(): raise ValueError('Invalid signal name')
        names(members, heroes)
    extras = advice.get('extra_alternatives')
    if not isinstance(extras, dict): raise ValueError('Invalid extra alternatives')
    # These independent alternatives have been checked against the talent guide.
    # Additional executable semantics or external talents require an app update.
    allowed_extras = {'Li Li': {'4': ['Safety Sprint']}, 'Ragnaros': {'13': ['Resilient Flame']}}
    for hero, tiers in extras.items():
        if hero not in allowed_extras or not isinstance(tiers, dict): raise ValueError('Unreviewed alternative')
        for level, talents in tiers.items():
            names(talents, allowed_extras[hero].get(level, []))
    rules = advice.get('rules')
    if not isinstance(rules, list) or not 90 <= len(rules) <= 1000: raise ValueError('Incomplete matchup rules')
    ids, covered = set(), set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) - {'id','hero','when','build','choices','reason','source'}:
            raise ValueError('Unsupported matchup rule')
        hero = rule.get('hero')
        if hero not in heroes: raise ValueError('Unknown rule hero')
        covered.add(hero)
        rid = rule.get('id')
        if not isinstance(rid, str) or not rid or len(rid)>100 or rid in ids: raise ValueError('Invalid rule ID')
        ids.add(rid)
        if rule.get('source') != heroes[hero]['source']: raise ValueError('Rule source mismatch')
        reason = rule.get('reason')
        if not isinstance(reason, str) or not reason.strip() or len(reason)>600: raise ValueError('Invalid explanation')
        try:
            if any(field not in (None,'names','allies') or spec or conversion
                   for _,field,spec,conversion in Formatter().parse(reason)):
                raise ValueError('Unsupported explanation template')
        except ValueError: raise ValueError('Invalid explanation template') from None
        when = rule.get('when')
        if not isinstance(when, dict) or not when or set(when)-{
            'enemy','ally','absent','enemy_names','ally_names','ally_absent_names','maps','plan','plan_not'}:
            raise ValueError('Unsupported condition')
        for side in ('enemy','ally'):
            if side in when:
                if not isinstance(when[side],dict) or not when[side]: raise ValueError('Invalid signal conditions')
                for s,n in when[side].items():
                    if s not in signals or type(n) is not int or not 1<=n<=5: raise ValueError('Invalid signal threshold')
        for key, allowed in [('absent',signals),('enemy_names',heroes),('ally_names',heroes),
                             ('ally_absent_names',heroes),('maps',MAPS)]:
            if key in when: names(when[key], allowed)
        for key in ('plan','plan_not'):
            if key in when:
                plans={'Varian':['Taunt (tank)','Damage build'], 'Blaze':['Tank','Solo lane']}
                names(when[key],plans.get(hero,[]))
        builds = heroes[hero]['builds']
        if ('build' in rule) == ('choices' in rule): raise ValueError('Choose one build or tier action')
        if 'build' in rule:
            names([rule['build']], [b['name'] for b in builds if 'aram' not in b['name'].lower()])
        else:
            choices=rule['choices']
            if not isinstance(choices,dict) or not 1<=len(choices)<=7: raise ValueError('Invalid tier choices')
            for level, talent in choices.items():
                legal={t for b in builds for tier in b['tiers'] if str(tier['level'])==level
                       for t in [tier['talent'],*tier['alternatives']]}
                legal.update(extras.get(hero,{}).get(level,[]))
                if not isinstance(talent,str) or talent not in legal: raise ValueError(f'Unlisted talent: {hero} {level} {talent}')
    if covered != set(heroes): raise ValueError('Matchup advice must cover every hero')
    validate_draft(catalogue.get('draft'), heroes, MAPS)


def validate_draft(draft, heroes, maps):
    if not isinstance(draft,dict) or draft.get('version')!=1 or set(draft.get('heroes',{}))!=set(heroes):
        raise ValueError('Content needs complete draft advice')
    for hero,p in draft['heroes'].items():
        if not isinstance(p,dict): raise ValueError('Invalid draft profile')
        for key,allowed in [('synergies',heroes),('countered_by',heroes),('strong_maps',maps),('weak_maps',maps)]:
            entries=p.get(key)
            if not isinstance(entries,list) or any(not isinstance(n,str) or n not in allowed or n==hero for n in entries):
                raise ValueError('Invalid draft relationship')
        if set(p['strong_maps']) & set(p['weak_maps']): raise ValueError('Conflicting map advice')
        if p.get('source')!=heroes[hero]['source']: raise ValueError('Draft source mismatch')
