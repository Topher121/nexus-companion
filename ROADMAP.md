# Nexus Forge follow-ups

## Public beta — 0.9.0

- [x] Rename the app and installer while retaining existing update and data compatibility.
- [x] Run all 101 tests and the standalone UI, OCR, replay, SQLite and build checks.
- [x] Verify fresh installation, upgrade from 0.8.0, and data preservation during uninstall.
- [x] Check the Windows installer and installed app outside the development environment.
- [x] Document beta limitations, download instructions, support and reporting links.

## Reliability and distribution — 0.8

- [x] Show missed-pick/ban and stale-reader warnings without guessing heroes.
- [x] Minimum-games filter for the hero history table.
- [x] Personal-data export/restore with validation and a safety backup.
- [x] Standalone Windows installer, separate personal-data directory, release and saved-build update checks.
- [x] Publish the first public release after owner approval. Version 0.8.0 is public; anonymous update checks and release downloads verified on 2026-09-20.

## Better draft advice — shipped in 0.7

- [x] Add saved synergy/counter and map guidance for all 90 heroes, with source metadata.
- [x] Prioritise finishing core roles when draft slots run out; warn about incomplete coverage.
- [x] Show named enemy drawbacks separately from reasons for a pick.
- [x] Account for confirmed Varian/Blaze plans without pretending to detect talents.
- [x] Rank bans for threats to our picks and fit with the enemy team; preserve own-pool exclusions for picks only.
- [x] Keep personal win rates and sample sizes visible without treating them as match predictions.
- [ ] Add a licensed, reliable statistical dataset with patch/mode/rank/sample filters. Heroes Profile's API requires an account/billing plan and compliant data storage; it is not an anonymous app endpoint.

## Builds and tips for every hero

Requested by the owner on 2026-09-19. The roster-wide build library and basic tips shipped in version 0.6.

- [x] Cover all 90 heroes with sourced talent choices at every tier: 292 complete build options.
- [x] Include basic playstyle, ability-use and positioning advice for every hero.
- [ ] Expand map-specific lane/objective plans and deeper coaching across the roster.
- [ ] Provide matchup tips naming relevant enemies: blind targets, cleanse/polymorph targets, interrupt priorities, dangerous abilities and positioning threats.
- [x] Provide named alternative and ARAM builds where the source offers them; preserve manual selections. Explain existing Auto matchup changes.
- [ ] Add concise selection explanations for every alternative, beyond the guide category and source link.
- [x] Record sources, source update dates and import dates for each hero; do not claim live patch verification.
- [x] Keep automatically following the player's locked hero and updating supported matchup advice as compositions change.

Current local coverage: all 90 heroes, 292 builds and three basic tips per hero, with additional talent-dependent advice for selected heroes. Source-recommended defaults are used except Azmodan, which retains his previously selected Gluttony starter. Deeper matchup automation is still a separate expansion.

Azmodan references checked:
- https://www.icy-veins.com/heroes/azmodan-talents
- https://www.icy-veins.com/heroes/azmodan-build-guide
