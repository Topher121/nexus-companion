"""Explain incomplete observations without guessing heroes in unreadable slots."""

def draft_health(reading, teams, manual=()):
    if not reading or not reading.get('valid'):
        return [], set()
    problems, marked = [], set()
    final = reading.get('phase') == 'starting'
    names = {'allies':'Your team', 'enemies':'Enemy team', 'bans':'Ban'}
    for slot in reading.get('slots', []):
        side,index=slot['side'],slot['index']
        hero=slot.get('hero'); current=teams[side][index]
        if (final or slot.get('locked_hint') or slot.get('locked')) and not current:
            status = 'locked in HotS; hero not recorded yet' if final else 'looks locked; hero unread or awaiting confirmation'
            problems.append(f'{names[side]} slot {index+1}: {status}')
            marked.add((side,index))
        elif hero and slot.get('locked') and current and current != hero:
            action='manual entry differs from screen' if (side,index) in manual else 'reading conflicts with saved pick'
            problems.append(f'{names[side]} slot {index+1}: {action}')
            marked.add((side,index))
    # Ban opportunities can be skipped. A blank is not proof of a missed ban,
    # and the final screen does not display bans at all.
    for ban in reading.get('bans',[]):
        index=ban['index'];current=teams['bans'][index]
        if not current:
            problems.append(f'Ban slot {index+1}: {ban["hero"]} awaiting confirmation');marked.add(('bans',index))
        elif current != ban['hero']:
            problems.append(f'Ban slot {index+1} differs from screen');marked.add(('bans',index))
    return problems,marked
