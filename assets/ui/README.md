# App artwork

`nexus.svg` is the editable original crystal-and-portal mark. It shares a dark,
rounded metal tile with Addon Forge's ember-and-anvil mark; cyan and violet keep
Nexus distinct. This is original app artwork, not an official Blizzard logo.

`nexus-master.png` is its transparent 512px render. `make_ui_icons.py` generates
the window/header PNGs and the Windows ICO from this master. The ICO includes
16, 20, 24, 32, 40, 48, 64, 128 and 256px images for different display scales.
After editing the SVG, render it to the master PNG, then run that script.

`NexusCompanion.spec` and `installer.iss` both use `nexus.ico`; the application
uses the matching PNGs. Rebuild the executable/installer after changing artwork.
