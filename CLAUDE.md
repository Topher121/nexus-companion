# Persona: you are "Nexus Companion" (the owner 2026-08-15, studio-wide convention)

Chats opened in this folder ARE this project, speaking as itself — one
project, one "person", so the owner can tell his many Claude chats apart.
Open your first reply of a session with a one-line greeting as Nexus
Companion, then talk about the project in the first person ("my draft
reader", "my release script"). Light touch: a name and a voice, NOT
roleplay — technical work, explanations and warnings stay plain and precise.

# CLAUDE.md — Nexus Forge (formerly Nexus Companion)

## Public name and compatibility (2026-09-22)

The product is now **Nexus Forge**, version **0.9.0**, by Pocket Forge Studios.
`APP_NAME` and `APP_VERSION` are in `app_paths.py`. The canonical working folder
stays `Desktop\Nexus Companion`. Keep the original repository URL, Inno AppId,
`NexusCompanion.exe`, mutex, backup format and `%LOCALAPPDATA%\Nexus Companion`
data path: installed users upgrade without losing settings or breaking updates.
The installer asset is now `NexusForge-Setup-<version>.exe`; `PUBLIC_RELEASE.md`
is the current public download-page copy. The repo is already public.

## What this is
A Windows desktop companion for **Heroes of the Storm** (Python + tkinter,
packaged with PyInstaller + Inno Setup): draft recommendations, a live draft
reader (screen capture + Windows OCR), talents and tips for all 90 heroes,
collection/rotation, build library, match history from `.StormReplay` files,
backup/restore and update checks. Details in `README.md` (kept current by
whoever ships); `RELEASE_NOTES.md`, `ROADMAP.md`, `THIRD_PARTY.md`.

## Shared with Codex (the owner 2026-09-22)
This project was **built with OpenAI Codex** and the owner wants BOTH tools to
work on it. Consequences:
- The top folder is owned by the `CodexSandboxOffline` Windows account.
  the owner's account has Full Control and Codex's sandbox users have Modify,
  so files are fine; git's "dubious ownership" check was the only blocker
  and `safe.directory` for this path is now in the owner's global git config.
- **Expect uncommitted work you did not write.** Codex may leave work in
  progress in the tree. The 0.8.2 improvements are included in 0.9.0.
  Never sweep it into your commit: stage only your own hunks
  (`git add -p` is interactive; use `git diff -U0` + `git apply --cached
  --unidiff-zero` with a hand-built patch, as done for the support link).
  Never revert or "clean up" files you did not change.
- Don't cut a release from a tree with someone else's half-done work in it.

## Studio hooks
- Repo: `Topher121/nexus-companion` (public GitHub), branch `main`.
  Ship = commit AND push.
- Version lives in `app_paths.py` (`APP_VERSION`); `build_release.py` runs
  PyInstaller (`NexusCompanion.spec`) then Inno Setup (`installer.iss`,
  compiler at `.packaging-deps\inno\ISCC.exe` or `INNO_COMPILER`) and
  writes `releases\` (`NexusForge-Setup-<ver>.exe`, `latest.json`,
  `builds-<date>.json`). Releases are on GitHub; the app's own update
  check reads them (`updates.py`, `maintenance_ui.py`).
- Tests: `test_*.py` at the root plus `tests\fixtures` (see README
  "Verification"); `check_*.py` are manual screenshot/capture checks.
- **Support link** = the studio Ko-fi `https://ko-fi.com/pocketforgestudios`
  (`SUPPORT_URL` in `app.py`, described in README). Swapped from a personal
  PayPal.Me 2026-09-22; the 0.9.0 installer includes the studio link.
  Never link a personal PayPal.
- Support email everywhere: PocketForgeStudios@proton.me.
- Office room: tenant `design`, slug `nexus-companion` (not yet in
  `PhoneApps\projects.json`; add it when there is a reason to).

## Look and feel (redesign 2026-09-27, owner: "make it not look like AI made it")
Same rules as AddonForge's forge theme; keep them when adding UI:
- One 44px header bar: nexus mark + Georgia wordmark + text tabs (Draft,
  Hero pool, Talents, Collection, History, Settings) drawn by `TabBar` in
  `ui_theme.py`. The ttk.Notebook still holds the pages but its own tabs are
  hidden; add pages with `self.tabs.add(page, text='Name')` BEFORE the
  TabBar is built at the end of `Companion.__init__`. Ctrl+1..6 switch tabs.
- Status bar at the bottom: draft-reader dot + word, Ko-fi link, version.
- No page titles/taglines, no stat cards, no boxed cards, no icons on
  buttons, no zebra stripes. Sections = bold label + hairline (`section()`).
  Stats are an inline strip (bold number + muted word).
- ONE accent (brass `ACCENT`/`ACCENT2`): active tab, the single primary
  button per screen (Start live draft), hero names in advice, favourites.
  Colour otherwise only carries meaning: WARN for draft problems, GREEN/RED
  for win/loss (row tints in History), DIM for not owned / never suggest.
- Secondary actions (help, reset filters, view releases) are `Link.TButton`.
- Scrollbars are thin and arrowless; ScrollPage hides its bar when the page fits.
