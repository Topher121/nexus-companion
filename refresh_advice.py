"""Stage fresh guide facts for review; never activate or publish scraped advice.

After reviewing the diff and updating rule conditions, --approve FILE validates
the candidate and writes a reviewed package beside it. Activation is a separate
maintainer decision. Download failures leave all live content untouched.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
import json
from pathlib import Path

from advice_schema import content_basis
from content_validation import validate_catalogue

ROOT = Path(__file__).resolve().parent


def changed_heroes(before, after):
    changed=[]
    for hero in sorted(before['heroes']):
        old,new=before['heroes'][hero],after['heroes'][hero]
        relationships=lambda c: {k:c['draft']['heroes'][hero][k] for k in
                                ('synergies','countered_by','strong_maps','weak_maps')}
        if (old['builds']!=new['builds'] or old['source_updated']!=new['source_updated']
                or relationships(before)!=relationships(after)):
            changed.append(hero)
    return changed


def approve(candidate):
    value=deepcopy(candidate)
    value['advice']['guide_checked']=value['checked']
    value['advice']['reviewed']=date.today().isoformat()
    value['advice']['basis']=content_basis(value)
    validate_catalogue(value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approve',type=Path,help='Explicit maintainer sign-off after reviewing and editing this candidate')
    parser.add_argument('--output',type=Path,default=ROOT/'.content-review')
    parser.add_argument('--fail-on-change',action='store_true',help='CI attention signal after staging changed advice')
    args=parser.parse_args()
    if args.approve:
        candidate=json.loads(args.approve.read_text('utf-8'))
        reviewed=approve(candidate)
        target=args.approve.with_name('reviewed-content.json')
        target.write_text(json.dumps(reviewed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Reviewed content validated. Bump CONTENT_VERSION and release it after testing; nothing was activated.')
        return
    from import_guides import fetch, CACHE, slug
    from import_matchups import extract_matchups
    current=json.loads((ROOT/'build_catalogue.json').read_text('utf-8'))
    candidate=deepcopy(current)
    with ThreadPoolExecutor(max_workers=3) as pool:
        profiles=dict(pool.map(fetch,sorted(current['heroes'])))
    candidate['heroes']=dict(sorted(profiles.items()))
    candidate['checked']=date.today().isoformat()
    candidate['draft']['heroes']={hero:extract_matchups(
        (CACHE/(slug(hero)+'.html')).read_text('utf-8'),hero,profile)
        for hero,profile in candidate['heroes'].items()}
    changed=changed_heroes(current,candidate)
    # Keep the old review fingerprint: this file cannot activate without review.
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=['# Content review', '', f'Fresh guide check: {candidate["checked"]}.',
            'These are guide recommendations, not measured win rates or a verified game-patch tier list.', '',
            f'{len(changed)} heroes have changed builds, source revision, or draft relationships.', '']
    report += [f'- {hero}: {profiles[hero]["source"]}' for hero in changed]
    report += ['', 'Review changed talents, related matchup rules and Blizzard patch notes. Run the advice tests.',
               'Then use --approve candidate.json to validate a separate reviewed-content.json.',
               'Nothing has been activated, committed or published.']
    (args.output/'review.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(f'Checked {len(profiles)} heroes; {len(changed)} need review. Live content unchanged.')
    if changed and args.fail_on_change: raise SystemExit(2)


if __name__=='__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        from urllib.error import HTTPError
        error=f'Guide source returned HTTP {exc.code}' if isinstance(exc,HTTPError) else type(exc).__name__
        raise SystemExit(error+'. Content refresh did not complete; live advice was not changed. Retry or review the source manually.') from None
