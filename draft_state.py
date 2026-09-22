"""Tentative allies are planning context, never committed draft entries."""
from data import HEROES


def teammate_hovers(locked, enemies, bans, hovers, own_slot, manual_slots=()):
    if own_slot is None:
        return {}
    used = set(locked + enemies + bans)
    result = {}
    for slot, hero in sorted(hovers.items()):
        if (slot == own_slot or slot in manual_slots or not 0 <= slot < len(locked)
                or locked[slot] or hero not in HEROES or hero in used):
            continue
        result[slot] = hero
        used.add(hero)
    return result
