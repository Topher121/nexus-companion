# Nexus Forge 0.9.0 — public beta

- Nexus Companion is now Nexus Forge, by Pocket Forge Studios, with matching crystal artwork throughout the app and Windows installer.
- Existing installed preferences, collection, history, backups and update checks remain compatible. The repository, application ID, executable name and data folder keep their original identifiers.
- Includes all 0.8.1 and 0.8.2 draft recognition, teammate-hover and matchup-talent improvements below.
- The optional support link now opens the studio Ko-fi page.
- Windows x64 installer includes the runtime, OCR/capture dependencies, 90 heroes and 292 saved builds. Beta limitations and setup requirements are explained on the download page.

# Nexus Companion 0.8.2 — included in 0.9.0

- Refreshed crystal app icon, with matching window, desktop, executable and installer artwork at multiple display sizes.
- Final-team screens distinguish unread locked heroes from open draft slots, and stop pick/ban suggestions even when some heroes could not be read.
- Skipped bans no longer produce a false six-ban warning. Existing confirmed picks survive unread frames.
- Hero recognition retries the isolated name ribbon and treats recognised final-screen heroes as locked even during brightness changes.
- Status shows heroes recorded and actual changed entries.

# Nexus Companion 0.8.1 — included in 0.8.2

- Teammate hovers contribute to pick and ban advice, with explicit tentative labels and automatic removal on changes. Your own hover stays out of the team plan.
- Auto (matchup) adjusts supported talent choices for confirmed enemy picks and explains the named threats. Manual build choices remain exact.
- Third ranged picks receive a warning and lower priority when the team still needs a solo laner.
- These changes are included in the Nexus Forge 0.9.0 installer.

# Nexus Companion 0.8.0

Free Windows companion for Heroes of the Storm, with local draft advice, saved talent builds and personal match history.

- Draft warnings highlight unread committed picks, conflicts and missing expected bans. Suggestions remain based on recorded heroes; uncertain heroes are never guessed.
- Match history has clickable sorting and a minimum-games filter for comparing hero records.
- Export and restore preferences, hero ownership, settings and results in one backup. Restores validate the file and make a safety copy first.
- Standalone Windows installer includes the runtime, original navigation icons, credited hero artwork and replay reader. No separate Python installation is needed.
- Optional automatic checks find app and saved-build releases. Downloads are verified; installation waits for your action.

Requires 64-bit Windows 10 1903 or later and Windows English OCR support for live draft reading. Keep HotS restored in windowed or borderless mode; it can stay behind other windows.

For existing source-app users: export a backup in Settings & backups, install, and restore that backup in the installed app. Your existing source data is left intact. Installed personal data lives outside the program folder and survives upgrades and uninstall.

The installer is unsigned, so Windows may show an unknown-publisher warning. Only download from this project's releases. Nexus Companion is unofficial and is not affiliated with Blizzard. Builds are saved guide selections, not a promise of live patch accuracy. Match win rates are personal history, not predictions.

Release files: `NexusCompanion-Setup-0.8.0.exe` is the installer. `latest.json` and `builds-2026.9.19.1.json` support the update checker.
