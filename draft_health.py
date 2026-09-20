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
            problems.append(f'{names[side]} slot {index+1} unread or awaiting confirmation')
            marked.add((side,index))
        elif hero and slot.get('locked') and current and current != hero:
            action='manual entry differs from screen' if (side,index) in manual else 'reading conflicts with saved pick'
            problems.append(f'{names[side]} slot {index+1}: {action}')
            marked.add((side,index))
    # Only infer bans that must already exist from committed pick progression.
    counts=[sum(bool(h) for h in teams[side]) for side in ('allies','enemies')]
    expected=6 if final or max(counts,default=0)>=4 else 4 if sum(counts) else 0
    known=sum(bool(h) for h in teams['bans'])
    if known < expected:
        problems.append(f'Only {known}/{expected} expected bans recorded — check both ban rows in HotS')
        marked.update(('bans',i) for i,h in enumerate(teams['bans']) if not h)
    for ban in reading.get('bans',[]):
        index=ban['index'];current=teams['bans'][index]
        if current and current != ban['hero']:
            problems.append(f'Ban slot {index+1} differs from screen');marked.add(('bans',index))
    return problems,marked
