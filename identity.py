"""Identify only a unique allied player, never guess a hero from player text."""
from hero_ids import normalize


def one_typo(a, b):
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x,y in zip(a,b)) <= 1
    shorter, longer = sorted((a,b), key=len)
    return any(longer[:i] + longer[i+1:] == shorter for i in range(len(longer)))


def player_slot(slots, player_name):
    wanted = normalize(player_name.split('#',1)[0])
    if not wanted:
        return None
    allied = [s for s in slots if s['side'] == 'allies' and s.get('player')]
    exact = [s['index'] for s in allied if normalize(s['player']) == wanted]
    if len(exact) == 1:
        return exact[0]
    if exact or len(wanted) < 5:
        return None
    # Small player text often merges the final letter with the party icon.
    near = [s['index'] for s in allied if one_typo(normalize(s['player']), wanted)]
    return near[0] if len(near) == 1 else None
