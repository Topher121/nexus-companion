# Maintaining advice

Advice is authored, guide-based guidance, not a measured win probability or a
claim to know the live meta. All 90 heroes have conditional talent rules. Some
conditions retain a sensible default and explain why; a rule does not need to
change talents merely to demonstrate that it evaluated the draft.

## Runtime behavior

The content package contains the build library, matchup rules, threat groups,
and draft counter/synergy/map relationships. They activate together after
validation and a restart. Manual build choices never change automatically.
Auto selects one complete build, then applies compatible alternatives. It uses
recorded enemy picks, confirmed allies, the battleground and explicit flexible
role plans. It does not infer enemy talents, quest progress or an offlane role.
Teammate hovers continue to inform draft recommendations; they are not locked
talent context. Missing picks never establish that an enemy threat is absent.

Rules are ordered: the first matching build wins; later compatible alternatives
win a conflict at a tier. Review conditions together, not independently. Preserve
heroic upgrades and linked talent packages. Examples: defensive Taunt must not
combine Shield Wall with Overpower; Poly Bomb uses its matching level 20 upgrade.
The numeric thresholds are project heuristics, not claims made by the source.

## Review after balance patches

1. Read Blizzard's patch notes and the affected hero guides. Changes to baseline
   abilities can require edits to the threat groups as well as talent rules.
2. Run `python refresh_advice.py`. It downloads fresh guide facts and stages
   `.content-review/candidate.json` and `review.md`. Live files remain unchanged.
   It checks all 90 heroes, including draft relationships and source revisions.
   Failed downloads stop the refresh; cached pages are never stamped as fresh.
3. Compare the candidate with `build_catalogue.json`. Review changed builds,
   conditions, priorities, heroic upgrades, threat groups and explanations. Edit
   the candidate's `advice` section as needed. An unchanged guide is not proof
   that a recent game patch had no effect. Do not auto-approve the scrape.
4. Run `python refresh_advice.py --approve .content-review/candidate.json` only
   after that review. This validates and creates `reviewed-content.json`; it
   does not activate or publish anything. Renamed/missing talents or incomplete
   coverage block approval. A fingerprint prevents changed guide facts from
   silently inheriting the previous review.
5. Replace the bundled catalogue with the reviewed content, advance
   `CONTENT_VERSION`, and run `python -m unittest discover -v` with temporary
   `NEXUS_DATA_DIR`. Check representative drafts in the app. Update the app
   version/minimum version if the rule schema or supported semantics change.
6. Follow the release procedure and privacy review. The release builder validates
   content before packaging. Distribute its checksummed manifest and content
   together. Installed apps check published releases on launch/daily, and users
   choose when to download. Restart loads the whole new package.

The GitHub `content-review.yml` workflow checks weekly and can run manually once
committed and pushed to the default branch. Changes produce a failing attention
signal and a review artifact, not a public release or automatic activation.
Source failures also fail visibly. A maintainer must review the result; this
workflow is not a promise that the app knows every new patch immediately.

## Current verification limits

Rules reviewed 2026-09-27 use the saved guide catalogue checked 2026-09-19, with
targeted talent-guide checks. The attempted full fresh download on 2026-09-27
returned HTTP 403, so the guide date has deliberately not been advanced. If a
future automated fetch is blocked, review the guides and patch notes manually or
use an authorized data source. Do not silently ship unreviewed replacement data.

The app shows the guide and rule review dates and flags guide data older than
30 days. Age is a reminder, not patch compatibility verification. Statistical
meta ranking would need an additional reliable, licensed, patch-specific source;
the current advice does not pretend to provide that.

## Sources

Every rule carries its hero's guide URL from the bundled catalogue. Separate
independent alternatives were checked against the [Li Li talent guide](https://www.icy-veins.com/heroes/li-li-talents)
and [Ragnaros talent guide](https://www.icy-veins.com/heroes/ragnaros-talents).
The [Varian talent guide](https://www.icy-veins.com/heroes/varian-talents) informs
the complete defensive/offensive Taunt selection. Original source prose and
downloaded HTML remain in the ignored research cache, outside distributions.
