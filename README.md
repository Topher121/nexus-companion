# Nexus Forge 0.9.0 — public beta

**Your Heroes of the Storm companion, by Pocket Forge Studios.** Free Windows
app for draft suggestions, talents and your personal match history. Previously
called Nexus Companion; existing settings, collections and results still work.

**[Download the Windows installer](https://github.com/Topher121/nexus-companion/releases/latest)**
· [Report a problem](https://github.com/Topher121/nexus-companion/issues)
· [Optional support](https://ko-fi.com/pocketforgestudios)

Choose **NexusForge-Setup-0.9.0.exe** on the release page. The other two files
support app updates; you do not need to open them. The public beta may miss some
draft picks—check highlighted slots and correct them using the dropdowns. Saved
builds are dated guide recommendations, and automatic matchup adjustments cover
supported choices rather than every possible composition.

Upgrading from 0.8.0: run the new installer over your existing installation.
The application ID, executable filename and personal-data folder remain stable
for compatibility. The repository and update address also retain their original
`nexus-companion` name. No data migration is needed for installed users. If you
run the source project, keep using it or export a backup before moving to the
installed app.

Install the Windows x64 setup, then launch **Nexus Forge** from your desktop or Start menu. The installer includes Python, OCR/capture dependencies, portraits and the replay reader. Windows 10 1903 or later and an English Windows OCR language pack are required. No account login or API key is needed. Free rotation and release checks need internet; guide links open in your browser. Developers can still run `Launch.cmd` with the local dependencies installed.

Version 0.8 adds draft-reading warnings, a minimum-games filter, backup/restore and app/build update checks. **Settings & backups** contains the new maintenance controls. The installer is not code-signed; Windows may show an unknown-publisher warning. Obtain it only from the project's releases.

**Support development ♥** in the footer opens Pocket Forge Studios' public Ko-fi page in your browser. Support is optional and every app feature remains free. The link opens only when clicked, with no preset amount, recurring-payment request or game/account data attached. Payments are handled by Ko-fi and PayPal; the companion does not collect payment details. The destination is `SUPPORT_URL` in `app.py`.

The interface includes original navigation/action icons, hero portraits, colour-coded teams, a hero banner for builds and result cards for match history. Compact tabs expand for the active page. Replay-folder controls are under **Match history → Replay settings**. Icons always accompany labels, and match results are labelled Win/Loss as well as coloured.

Version 0.7.2 aligns table headings and talent names, labels hero searches, and adds preference/ownership filters with **Reset filters**. Empty results explain what to do next. Edit and history actions enable when an appropriate row is selected. Collection setup can be expanded when needed, leaving more space for heroes, and ownership buttons stay visible in smaller windows. An unknown unlock level in a rotation entry now excludes only that hero, preserving the other confirmed free heroes.

Draft suggestions now show **your personal win rate, games played and wins/losses** from the active replay account. Use **Your stats** above the picks to choose a mode (Storm League by default). These are all-time recorded results, including manual entries; excluded matches and other accounts are left out. History-page filters do not change this choice. Fewer than 20 games is labelled a small sample; heroes without results show “no recorded games”. New imports and exclusions update the figures automatically. Win rates are context, not a predicted chance of winning or a replacement for team-fit ranking. No online/global win-rate feed is used.

## Use
1. Enter the map, locked allied/enemy heroes and bans. Leave your slot empty to obtain suggestions. Dropdowns support typing the first letter to jump through names.
2. Use My hero pool for favourites, allowed and never suggest. Use Collection for ownership. Search or filter either list; Ctrl-click selects several heroes. These settings are separate and saved locally.
3. **Talents & tips** includes all 90 heroes, 292 named build options and practical advice for each hero, available offline. Your locked hero appears automatically; choose **Playing** to browse manually. The **Build** selector includes the guide's alternative and ARAM builds where available. Chromie's actual early talent levels and Varian's level-4 role choices are shown correctly.
4. Keep on top makes the app a floating companion. It is not an injected game overlay; borderless/windowed gameplay or a second monitor is recommended.

## Draft recommendations

Version 0.7 combines team composition with saved, attributed matchup guidance for **all 90 heroes**: 434 synergy listings and 469 directional counter listings, plus map strengths and weaknesses. These are guide opinions, not measured matchup statistics. A synergy listed by either hero's guide is considered once. A counter points in the stated direction; a missing entry does not imply a favourable matchup. Related guide and ability signals have capped influence.

Picks consider tank/healer coverage, ranged damage, solo-lane options, waveclear, sustained damage, synergies, counters and the map. When slots run out, candidates that can still complete tank/healer coverage rank before those that cannot. If your role or collection filter makes a complete team impossible, suggestions explain the gap. **Watch out** shows difficult matchups and map drawbacks separately from positive reasons. **Plan** labels talent-dependent value, such as Varian needing Taunt or Artanis needing Suppression Pulse for a blind.

When a picked **Varian** or **Blaze** appears, a plan selector lets you confirm their role on either team. Unconfirmed Varian is not counted as a tank; unconfirmed Blaze is counted as a tank and labelled as an assumption. Selecting Taunt or Solo lane immediately updates advice. These are your stated plans, not detected talents. Plans reset when the hero is removed or the draft is cleared. Candidate Varian/Blaze can fill the requested role, with their assumption shown.

Bans evaluate who fits the opposing team with extra weight on counters to your known heroes. All six bans entered, or five enemy picks entered, ends ban advice. Unknown enemy slots are called out rather than assigned imaginary opponents. Favourites add a small tie-break only within five fit points of the strongest eligible option with equally good core-role coverage. Personal win rates remain context only. Never suggest and ownership restrict your picks, never enemy entry or bans. Cho/Gall are omitted because they require a coordinated pair. Equal fits sort alphabetically.

Use **How suggestions work** for the short explanation. `draft_catalogue.json` stores names, per-hero source URLs, source update dates and import dates. **Open talent guide** leads to the full guide, including its Synergies and Counters section; a pairing can be listed in either hero's guide. `import_matchups.py` builds the data from the existing maintainer-only guide cache and never runs while you play. Invalid or unavailable matchup data falls back to basic composition and ability rules with a visible notice.

There is no live global win-rate feed, predicted win percentage, or automatic patch refresh. Guide opinions may depend on talents or playstyle, and the relationship lists are not exhaustive. The weighting is authored guidance, not a statistically trained model. Matchup data was imported on 2026-09-19; source update dates vary.

## Live draft reader

Press **Clear draft** at the start of every match, including consecutive matches on the same map. Enter your in-game name in **Your name**; **Your slot → Auto** identifies your allied player label. A manual slot (1–5 from the top of the blue/left team) is available if your name is unreadable. Auto identification requires a unique name match and two consistent readings; one small OCR error is allowed for player names of at least five characters. Hero names still require exact matches.

Press **Start live draft**. Windows window capture reads HotS even when the companion or another app covers it. Keep HotS restored, preferably in borderless/windowed mode; minimized or suspended fullscreen games may stop producing frames. The app never activates the game or falls back to capturing the whole desktop. A frame older than three seconds is not used.

Map names, committed picks and ban portraits are processed locally every two seconds plus processing time. Pick/ban readings must agree twice before applying. Ban recognition compares both draft and square hero-select artwork, including Johanna's different ban portrait, with a confidence threshold and a margin over the next candidate. Uncertain images remain unread. Dark hover ribbons do not count as locked picks. Name labels retain the original screenshot resolution to improve short-name recognition. The final **Match starting** screen is read as well, retaining the previously detected map and bans. No game memory or game inputs are used.

**Talents & tips → Follow my locked hero** is enabled by default. Your build follows your detected locked pick, and matchup tips name enemy blind priorities and threats. Unseen talent choices are described conditionally (for example, Varian choosing Twin Blades). Manually browsing another hero pauses following; re-enable the checkbox to resume. Before your hero is identified, the page shows a waiting message and disables the old hero's guide button. Repeated identical readings preserve the tips' scroll position.

Correct missed slots using dropdowns. Manual edits remain protected until **Allow auto corrections** or **Clear draft**. Uncertain readings leave slots unchanged. **Read screenshot** imports a saved draft immediately; loading and gameplay screens are ignored. **Stop live draft** stops reading.

An amber **CHECK DRAFT** notice highlights committed-looking picks without a confirmed reading, conflicting saved/manual entries, and detected bans awaiting confirmation. Ban opportunities can be skipped: blank ban slots may be skipped or unread, so check them in HotS while drafting. The app no longer assumes that six heroes must be banned. On the final-team screen, blank hero slots are explicitly labelled **unread locked picks**, pick/ban suggestions stop, and previously confirmed heroes and bans remain saved. Exact-name OCR also retries the isolated name ribbon when the full card is unreadable. A paused/unavailable reader warns that saved entries may be stale. Correct highlighted dropdowns or allow another reading before relying on advice.

Draft state is session-only. The live reader does not save or upload screenshots. There is no telemetry. Keep on top does not obscure the captured game window.

## Collection and free rotation

**Collection → Collection setup → Set up collection exporter** contains the one-time replay setup. Setup is expanded automatically until any ownership records exist. The community exporter is for REPLAYS ONLY, never live observation. Copy the export from your own replay player, paste it into **Import replay export**, review the player name, and confirm. Restore the default Replay Interface afterwards. Repeat after purchases. Compatibility with your current game version still needs a replay check.

Ownership can also be marked manually. Enter your account level under Collection setup for rotation unlock gates. Unknown unlock requirements are not guessed; the rotation status explains how many entries are excluded. Expired or future rotations are labelled explicitly. **Suggest only confirmed owned or currently free heroes** excludes unknown heroes; it is enabled after importing. Never suggest always wins. Availability never limits ban recommendations.

Rotation checks on launch and every six hours. Only unexpired cached data is used after a failed request. The public feed was successfully checked on 2026-09-20; it included ten confirmed base-level heroes and four entries with unknown unlock levels. Failures and unknown requirements are visible in the app.

## Build library

**Auto (matchup)** starts with a saved guide build and selects supported talent alternatives as enemy picks are confirmed. **Why these talents** names the relevant enemies and explains each choice. Rules cover spell protection, basic-attack pressure, dive, stuns/roots, shields and enemy healing. Confirmed allied Ana and Varian role plans also affect the relevant choices. Rules preserve the build's talent dependencies; other tiers keep their guide defaults. Most defaults follow the guide's Recommended build; Azmodan keeps the Gluttony teamfight starter previously chosen for this app. Choosing a named build uses its exact talent list and preserves that choice when enemies change. Changing heroes or clearing the draft returns to Auto. Choosing a build does not disable following your locked hero. The app recommends talents; it never selects them inside the game.

Teammate **hovers** now contribute to suggested team composition and reserve their planned heroes. They are shown separately below the draft boxes and explicitly labelled tentative. Your own hover is excluded: set your player name or slot first. New live hovers require two agreeing readings (one for an imported screenshot); changed, unread or cleared hovers are removed immediately. Hovers never become locked entries or trigger your automatic hero selection. Enemy hovers are not used for talent choices. Reader failure, a different match or stopping the reader clears tentative context. Third ranged picks are discouraged when the team has no established solo laner, with a visible explanation even if collection filters leave no better candidate.

Every hero has three original practical tips, with additional talent-dependent guidance and existing named matchup tips where supported. The guide's own category, source link, last-update date and local import date appear below the tips. Use **Open talent guide** for detailed explanations of alternatives. ARAM choices are manual; the personal win-rate filter does not select an ARAM build. These are full build templates, not automatic optimal counter-builds for every possible composition.

The 90 public guide pages were imported on 2026-09-19. Their individual update dates vary. `build_catalogue.json` stores factual tier/name selections, not copied guide prose. `hero_tips.py` stores the original short notes. `import_guides.py` is a maintainer tool; it caches public pages in `.guide-cache`, and replaces the catalogue only after all heroes succeed. Remove the research cache before a fresh source check; do not distribute it as app content. The app does not run that importer or scrape while you play.

Talents do not automatically track future patches. Published, reviewed build catalogues can now be downloaded from **Settings & backups**. App checks run on launch and daily; installation is explicit. Restart after a saved-build update. Original notes and matchup rules ship with app updates; a build-only update changes the sourced talent catalogue.

## Match history

**Match history** automatically reads completed `.StormReplay` files on launch and every 30 seconds while the app is open. It works independently of live draft reading, including while the companion is in the background or minimized. Games played while it is closed are imported on the next launch. The existing local replay folder is selected automatically when there is exactly one account folder; choose a folder if you have multiple accounts.

The page shows matches played, wins, losses and win rate for each hero, plus a dated match list. Click any heading in either table to sort; click it again to reverse the order. The active heading shows ▲ (ascending) or ▼ (descending). New numeric columns start highest first, dates newest first, and text A–Z. Each table keeps its chosen order during this session, including when filters change or new replays arrive. Filter by hero, game mode or the last 7/30 days. Click a hero's row to filter the match list. **All heroes** restores the full list. These are your personal saved results, not global hero win rates or your complete lifetime record if older replays are missing. Results do not change draft recommendations.

Account identity comes from the replay folder's account ID and the matching participant record, not the draft screenshot or a name guess. Repeated scans and copied replay files do not count a game twice. Unfinished/unreadable files are skipped, never recorded as losses, and retried. **Import details** explains skipped files. The mode is marked **Unknown** if its data cannot be validated against the replay's players.

Use **Log a result manually** for a match without a replay. If that replay is imported later, exclude the manual record to avoid double counting. **Exclude selected** removes entries from statistics without destroying them. **Show excluded → Restore selected** reverses it; rescanning does not restore excluded games automatically.

No exporter, game setting changes, account login, uploads or internet are needed. Installed personal data is stored in `%LOCALAPPDATA%\Nexus Companion`, separately from the program, and survives upgrades and uninstall. Source checkouts retain data beside `app.py`. Use **Settings & backups → Export backup** to move between them. The packaged installer includes the replay reader.

**Minimum games** above the hero table hides heroes below the selected count (0, 5, 10, 20, 50 or 100). It uses the selected mode and period, excludes excluded matches, and survives restarts. It does not change the summary totals, match list, draft suggestions or personal rates shown in the draft. Reset filters restores 0. A minimum sample is context, not a guarantee of predictive accuracy.

## Backup and restore

**Export backup** writes a `.nexus-backup` file containing preferences, collection, settings, free-rotation cache and a consistent SQLite history snapshot, including excluded results and duplicate-import records. It contains your player identity and replay-folder paths; it is not encrypted. Replays, screenshots, app files and downloaded builds are not included.

**Restore backup** first validates filenames, checksums, JSON and database structure. It asks to replace current data, makes a safety backup under the data folder's `backups` subfolder, pauses writers and closes the app after success. Reopen to use restored data. Failed writes roll back in-process. Do not interrupt a restore. To move this source installation to the packaged app, export here, install, then restore in the new app. On another PC choose its replay folder afterwards.

## Releases and updates

The update feed is `https://github.com/Topher121/nexus-companion/releases/latest/download/latest.json`. Checks use HTTPS, send only a versioned User-Agent, and never upload personal data. **Check for updates** also works manually. The automatic checkbox controls launch/daily checks. No installer is run automatically and no game is interrupted.

App downloads verify SHA-256 against the release manifest before offering **Open downloaded installer**. This detects damaged downloads; it does not substitute for publisher signing or trust in the release account. Saved-build downloads additionally validate the full roster, all talent tiers (including Chromie), source URLs and minimum app version before atomically activating a new catalogue for the next launch. Invalid downloads leave the current app/catalogue untouched. Network errors or an unpublished/private release are shown clearly and do not prevent offline use.

Maintainers build with `python build_release.py` after installing the pinned runtime dependencies and PyInstaller 6.22.3. Inno Setup's compiler is expected at `.packaging-deps/inno/ISCC.exe`. The allowlisted spec excludes personal databases, preferences, settings, caches, screenshots and backups. `releases` contains the setup executable, `latest.json` and the versioned build JSON. Publish those three assets together on a stable GitHub release; the manifest uses immutable version-tagged download URLs. Build-only releases must advance the content version and keep a valid compatible app artifact. Only a public, published release is available anonymously to installed apps.

## Verification

The test suite checks all 90 heroes and every saved build, including tier levels, alternatives, source metadata, manual build selection, automatic hero following, and all-hero UI rendering. It also covers ranking, collection import, rotation dates and level gates, manual corrections, repeated readings, stale worker results, player detection and named matchup tips. Ban fixtures include the reported Johanna miss, her portrait in another slot, and empty/pending bans; detected bans are checked through to live recommendation exclusion. `check_screenshots.py` checks nine supplied screenshots, including the reported missed-pick case (all ten heroes now read), the six-ban case, hovers and non-draft rejection. `check_background_capture.py` captures a temporary test window behind other windows and asserts that foreground focus is unchanged. `check_capture.py` checks the real game without activating it. Recognition can still leave uncertain slots unread. The replay exporter remains a first-use check.

See `THIRD_PARTY.md` for sources. UI failures are recorded in `last-error.log`.

## Sources
Talent references: per-hero Icy Veins build-guide URLs and source dates are stored in `build_catalogue.json`. Additional matchup adjustments reference https://www.icy-veins.com/heroes/johanna-talents and https://www.icy-veins.com/heroes/li-li-talents. Curated rules and build adjustments are authored guidance, not claims from a statistical model. Imported 2026-09-19.

Run checks: `python -m unittest discover -v` from this directory. History checks cover account matching, unknown/unfinished results, mode validation, ARAM choices, duplicate prevention, filters, persistence, exclusion/restore and files still being saved.
