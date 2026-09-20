"""Original short coaching notes; reference pages are recorded per hero in the catalogue.

Keep these independent of a specific talent build. Talent-dependent advice belongs
in engine.build_details, where the actual selected talents are available.
"""
HERO_TIPS = {
    'Abathur': [
        'Hide your body somewhere safe and check it between hats. A helpful Symbiote is worth little if you die to a roaming enemy.',
        'Use mines to watch likely rotations. Move Symbiote between allies who are fighting and unattended waves that need experience.',
        'Join fights as they begin; a late hat or clone can miss the moment your teammate needs support.'
    ],
    'Alarak': [
        'Use Telekinesis to line up Discord Strike. Practise the pull into silence before trying it on a moving target.',
        'Lightning Surge can hit enemies along the beam as well as its target. Look for an angle that catches a hero between you and another unit.',
        'Preserve your Sadism by backing away from lost fights. Telekinesis can move you out of trouble too.'
    ],
    'Alexstrasza': [
        'Your own health matters: Gift of Life heals more when you are healthy. Avoid trading health just for a little poke.',
        'Put Abundance where teammates can safely stand when it blooms; an obvious circle under enemy pressure can become a trap.',
        'Use Dragonqueen for a committed objective fight. Position so its healing reaches your team without exposing you to a collapse.'
    ],
    'Ana': [
        'Keep a clear firing line to injured allies and leave space from enemy divers. You have limited ways to escape a close-range fight.',
        'Save Sleep Dart to stop an attacker or interrupt an important channel. Let allies know before relying on the sleep to last.',
        'A grenade on the enemy being focused can deny their rescue healing. Use it defensively when your own team needs the healing boost.'
    ],
    'Anduin': [
        'Line up Divine Star through enemies, then move so its return passes through injured allies.',
        'Use Chastise after a teammate slows or stuns someone. A predictable target is much easier to root.',
        'Keep yourself in a safe place for Leap of Faith. Pull a teammate out of danger before the finishing damage lands.'
    ],
    "Anub'arak": [
        'Chain your stuns rather than landing them together. Give your damage dealers time to follow each one.',
        'Keep Burrow Charge for retreat when a fight is uncertain. Diving beyond your team can leave you stranded.',
        'Time Harden Carapace for incoming spell damage; use beetles and terrain to interfere with enemy skillshots.'
    ],
    'Artanis': [
        'Keep attacking reachable enemies to bring your shield back sooner. Chasing an unreachable carry can cost you that sustain.',
        'You can cast Phase Prism during Blade Dash. Check where both heroes will end up before attempting a long swap.',
        'Fight near allies who can use your swap. Bringing an enemy to safety while putting yourself inside their team is a losing trade.'
    ],
    'Arthas': [
        'Use Howling Blast to catch a target, then stay close enough for Frozen Tempest to restrict their movement and attacks.',
        'Turn Frozen Tempest off when it has no useful targets to avoid draining your mana.',
        'Death Coil can heal you. Use Frostmourne Hungers immediately after a normal attack to fit in the empowered hit quickly.'
    ],
    'Auriel': [
        'Keep Bestow Hope on an ally actively dealing damage. Move the crown when that ally retreats or stops contributing.',
        'Aim Ray of Heaven to heal several allies together, while keeping enough distance to avoid being caught with them.',
        'Use Detainment Strike to push an attacker away; a nearby wall turns the knockback into a stun.'
    ],
    'Azmodan': [
        'Stack Annihilation by landing Globes on heroes and on minions shortly before they die. Coordinate wave damage with a teammate.',
        'Send Demon Lieutenant to support another lane while you group. Check the minimap instead of walking across the map to use it.',
        'Stay behind your frontline. The laser commits you to a channel, so use it only when enemies cannot easily interrupt or surround you.'
    ],
    'Blaze': [
        'Oil is useful before it burns: its slow helps your team land damage and makes your stun easier to connect.',
        'Use Jet Propulsion after another slow or stun. Keep an exit in mind instead of charging out of your healer’s reach.',
        'Ignite oil when you need its healing or damage. Time Pyromania for the period when enemies are actually hitting you.'
    ],
    'Brightwing': [
        'Stay close enough for Soothing Mist to reach injured allies. It heals automatically around you.',
        'Begin Phase Shift before an ally is nearly dead; check whether you will land somewhere safe.',
        'Use Polymorph on an attacker committing to your backline or after your tank catches a target. Pixie Dust helps protect against spell burst.'
    ],
    'Cassia': [
        'Keep moving between attacks to maintain Avoidance. Standing still makes you much easier to punish.',
        'Use Fend for a safe finish or after enemy control is spent. Charging into several ready enemies can trap you in danger.',
        'Poke with Lightning Fury and fight near your support. Being durable while moving does not make you the team’s tank.'
    ],
    'Chen': [
        'After Keg Smash, weave in an attack before igniting the target with Breath of Fire.',
        'Use Fortifying Brew’s shield to absorb the delayed damage from Stagger. Watch for enemies who can interrupt your drinking.',
        'Flying Kick can target enemy minions and structures as well as heroes. Look for a safe escape target before diving.'
    ],
    'Cho': [
        'Coordinate with Gall: call your engage and Rune Bomb timing so both players contribute to the same target.',
        'Hit several enemies with Consuming Blaze, then attack burning targets to sustain yourself.',
        'Surging Fist can be interrupted while charging. Leave yourself an escape route and coordinate your defensive trait with Gall.'
    ],
    'Chromie': [
        'Predict where enemies will move and use allied crowd control to secure your delayed spells.',
        'Place Time Traps on likely approaches before a fight. They can buy space when an enemy gets through your frontline.',
        'Your talent tiers arrive earlier than other heroes. Use each early power spike with your team instead of waiting for their next tier.'
    ],
    'D.Va': [
        'Aim Defense Matrix at enemies dealing damage and reposition to keep them inside it.',
        'Boosters can push attackers off your teammates. Avoid carrying yourself so far forward that the team cannot help.',
        'Self-Destruct can deny a capture area; launch the mech with Boosters when useful. As a pilot, land safe Big Shots to regain your mech.'
    ],
    'Deathwing': [
        'Your casts have visible delays. Follow your team’s control or cover a route enemies must cross.',
        'Dragonflight restores your health and armor plates. Plan recovery before an objective; allied healers cannot heal you.',
        'Choose your form for the fight’s range. Save a route out rather than assuming your health pool lets you stay forever.'
    ],
    'Deckard': [
        'Prepare potions near the next fight before anyone needs them. Spread some along your team’s retreat route.',
        'Slow targets with Horadric Cube before trying to catch them in Scroll of Sealing.',
        'Stay behind allies when channeling sleep. Gem talents add active buttons: remember to activate the appropriate gem before your Cube.'
    ],
    'Dehaka': [
        'Collect Essence before fighting and spend it while you can still survive the incoming damage.',
        'Soak a side lane while watching your team; Brushstalker lets you join through nearby brush when a fight starts.',
        'Drag is easier at close range. Use Dark Swarm to move through units and get the angle, without abandoning your retreat.'
    ],
    'Diablo': [
        'Look for wall angles before charging. Follow a wall stun with Overpower to keep the target near your team.',
        'Collect Souls steadily and respect how much weaker you are after losing them.',
        'Protect your backline when an enemy dives. Your displacement is often more useful there than chasing a distant carry.'
    ],
    'E.T.C.': [
        'Approach from an angle so Powerslide catches a valuable target without carrying you beyond your team.',
        'Use Face Melt to peel or interrupt. Avoid pushing enemies out of your allies’ damage for no benefit.',
        'Track enemy interrupt abilities before committing to a long channel. Guitar Solo helps you recover between trades.'
    ],
    'Falstad': [
        'Keep Barrel Roll available if opponents can reach you. Using it only for extra damage can leave you without an exit.',
        'Once Lightning Rod connects, maintain its range while continuing to move and attack.',
        'Use Flight to collect distant experience and still reach the team fight. Start moving before the objective is already lost.'
    ],
    'Fenix': [
        'Trade while your shield is available, then step out of damage long enough for it to recover.',
        'Switch weapon modes: use the splash shot for grouped targets and Repeater Cannon for close sustained damage.',
        'Keep Warp for a safe reposition when enemies still have control available. Plasma Cutter’s slow helps set up your damage.'
    ],
    'Gall': [
        'Coordinate your spell timing with Cho’s movement. Both players must agree when to commit or retreat.',
        'Use Dread Orb to cover paths and clustered enemies; keep using Shadowflame for reliable nearby damage.',
        'Watch Cho’s Rune Bomb and detonate it at a useful position. Coordinate your trait so damage bonuses do not cost needed protection.'
    ],
    'Garrosh': [
        'Wrecking Ball grabs the closest valid enemy. Position carefully so a minion or the wrong hero does not take the throw.',
        'Use Groundbreaker to help set up a throw or to hold the target after it lands.',
        'Bloodthirst gives more recovery when you are hurt. Keep teammates close enough to follow your displacement.'
    ],
    'Gazlowe': [
        'Set up turrets around the area your team intends to contest. Their placement can obstruct skillshots and make approaches awkward.',
        'Use Xplodium Charge after allied crowd control; throwing it at a freely moving enemy is easier to dodge.',
        'Aim Deth Lazor through grouped heroes for more recovery. Fight around your setup rather than chasing away from it.'
    ],
    'Genji': [
        'Use Swift Strike when a takedown is realistic so its reset can help you escape. A speculative dash can strand you.',
        'Land multiple Shuriken at close range when safe, but respect enemy stuns before approaching.',
        'Keep enough mana for your exit. Terrain-crossing movement is useful only if you leave it available when needed.'
    ],
    'Greymane': [
        'Begin with safe human-form attacks, then switch to Worgen when your team can finish a vulnerable target.',
        'Keep attacking something safe between exchanges to maintain Inner Beast.',
        'Plan the disengage before going into melee. Use your return to human form to create distance when the kill is no longer available.'
    ],
    "Gul'dan": [
        'Use Fel Flame for efficient waves and repeatable poke. Avoid spending health on Life Tap when enemies can immediately burst you.',
        'Channel Drain Life when the target is controlled or enemy interrupts are unavailable.',
        'Place Corruption along a retreat path or through a crowded choke so more than one section can connect.'
    ],
    'Hanzo': [
        'Check unsafe approaches with Sonic Arrow before walking in. Keep a wall nearby for Natural Agility.',
        'Poke with Storm Bow while adjusting your position; do not stand still waiting for a perfect shot.',
        'Look for useful wall angles for Scatter Arrow. Follow a teammate’s control to make your damage more reliable.'
    ],
    'Hogger': [
        'Use Loot Hoard to create a wall for Staggering Blow or a useful Hogg Wild bounce.',
        'Throw dynamite directly onto a hero for an immediate explosion; knockbacks can also push enemies into it.',
        'Practise bounce routes around camps. Cancel your Hoard when its meat or an open escape path is more valuable than the wall.'
    ],
    'Illidan': [
        'Safe attacks recover health and reduce your cooldowns. Keep hitting reachable targets instead of chasing endlessly.',
        'Dive puts you behind the target. Think about where that leaves you before using it against the enemy frontline.',
        'Save Evasion for incoming attacks; it does not stop spell burst. Sweeping Strike can help you retreat without needing a target.'
    ],
    'Imperius': [
        'Slow with Solarion’s Fire before attempting Celestial Charge. Shorter-range spears give enemies less time to dodge.',
        'Follow ability hits with attacks to consume your marks and gain their benefits.',
        'Activate Molten Armor during your spear’s hold. An isolated target helps concentrate its hits.'
    ],
    'Jaina': [
        'Chill a target before spending the rest of your burst so Frostbite strengthens the follow-up damage.',
        'Use Blizzard after a root, stun or slow. Freely moving enemies can leave before the later waves.',
        'Keep a spell available when clearing waves near opponents. You are vulnerable if everything is on cooldown when a fight starts.'
    ],
    'Johanna': [
        'Group nearby enemies with Condemn, then slow them with Punish so your team can follow up.',
        'Use Iron Skin before incoming control connects. Unstoppable does not let you walk through walls.',
        'Stay close enough to protect your damage dealers. A deep engage is only useful if your team can reach the target.'
    ],
    'Junkrat': [
        'Put Steel Traps on approaches and narrow escape routes before the fight reaches you.',
        'Keep Concussion Mine available for a useful displacement or escape. Detonating it immediately can save an enemy from your team.',
        'Launch a channeled heroic from cover. Keep firing grenades into crowded paths while avoiding a direct frontline fight.'
    ],
    "Kael'thas": [
        'Position behind your frontline and save Gravity Lapse when a diver is still a threat.',
        'Use Verdant Spheres deliberately: empowering your stun helps reach enemies behind units, while empowered Living Bomb is efficient for pressure.',
        'Follow allied control with Flamestrike. Enemies spreading out around Living Bomb are harder to punish with overlapping explosions.'
    ],
    "Kel'Thuzad": [
        'Prioritise safe quest progress early. Your combo becomes much more threatening after Master of the Cold Dark is completed.',
        'Chain two heroes and place Frost Nova where they will meet. With a Glacial Spike anchor, aim at the spike instead.',
        'Follow the root with your damage. Keep space from divers while your combo is unavailable.'
    ],
    'Kerrigan': [
        'Place Impaling Blades first, then use Primal Grasp to pull the enemy into the eruption.',
        'Hold your combo until an opponent commits or an ally controls them. Spending it too early makes your engage easy to dodge.',
        'Look for flanks with team support and conserve mana between fights. Ravage can reposition through enemy units as well as heroes.'
    ],
    'Kharazim': [
        'Keep a Radiant Dash charge for an ally or summoned Ally behind you. Repeatedly pressing it can waste both charges.',
        'Move into position to heal several teammates with Breath of Heaven, then leave if enemy control threatens you.',
        'Choose your moment to attack. Short safe windows are better than staying in melee while your allies need healing elsewhere.'
    ],
    'Leoric': [
        'Slow with Skeletal Swing before attempting Drain Hope. Durable enemies with limited mobility are easier to tether.',
        'Keep Wraith Walk available when enemies can surround you. It does not let you cross the map’s permanent walls.',
        'While dead, keep helping with vision and slows, but choose a safe place to revive. Death still gives the enemy experience.'
    ],
    'Li Li': [
        'Your position influences Healing Brew’s recipient. Stay near the threatened ally rather than a safely injured teammate.',
        'Cloud Serpent works well on a teammate who is close enough to keep attacking enemies.',
        'Keep moving and heal from a safe distance. Do not deliberately take a dangerous burst just to trigger Fast Feet.'
    ],
    'Li-Ming': [
        'Use allied control to land Missiles and Orb together. Useful frequent hits beat waiting indefinitely for a perfect long-range Orb.',
        'Keep Teleport for safety until a takedown is likely. Only commit aggressively when the reset will let you survive.',
        'After a takedown, use your refreshed abilities promptly and reassess the next target instead of continuing an unnecessary chase.'
    ],
    'Lt. Morales': [
        'Keep the healing beam connected without following an ally into a position where enemies can focus you.',
        'Apply Safeguard as meaningful damage arrives. Armor used during a quiet moment provides little protection.',
        'Detonate Displacement Grenade again to control where it explodes. Use it to push an attacker off you or an ally.'
    ],
    'Lunara': [
        'Move between attacks and use your speed to keep enemies at a comfortable distance.',
        'Spread poison when several enemies can be reached safely. Against strong group healing, concentrate pressure with your team instead.',
        'Keep an exit available before using mobility to chase. Your damage over time does not justify standing in a dangerous position.'
    ],
    'Lúcio': [
        'Switch songs with the situation: speed can save an ally from a lethal chase faster than healing alone.',
        'Use Wall Ride to reposition while keeping teammates inside your aura.',
        'Save Soundwave to interrupt an approach or push a diver away. Avoid knocking a caught enemy out of your team’s damage.'
    ],
    'Maiev': [
        'Aim Fan of Knives through at least two heroes to refresh it; grouped fights are where repeated hits matter.',
        'Use Umbral Bind when enemies are close, then move so the tether actually pulls them.',
        'Reserve Vault of the Wardens for an important incoming hit or control effect. Spirit of Vengeance gives another route to reposition.'
    ],
    "Mal'Ganis": [
        'Use the third Fel Claws strike for its stun, and weave attacks between casts when safe.',
        'Night Rush can interrupt and set up a target; coordinate so incidental allied damage does not immediately waste the sleep.',
        'Control nearby enemies before beginning a vulnerable heroic channel. Check whether their interrupts are still available.'
    ],
    'Malfurion': [
        'Keep Regrowth active on allies likely to take damage before the fight becomes urgent.',
        'Hit enemy heroes with Moonfire to heal teammates who already have Regrowth.',
        'Place roots after an ally’s control and use Innervate on a teammate who benefits from mana and cooldown recovery.'
    ],
    'Malthael': [
        'Spread Reaper’s Mark with attacks, then use Soul Rip to sustain against the marked group.',
        'Wraith Strike can reposition you around a marked target to avoid damage; check where you will land.',
        'Fight around your team’s control. Diving alone for percentage damage can get you killed before your sustain matters.'
    ],
    'Medivh': [
        'Use Raven Form to watch rotations and provide information without committing your body to a fight.',
        'Place Portals with a clear safe endpoint and signal them to allies. An escape is only useful if teammates notice it.',
        'Time Force of Will for the incoming burst instead of shielding after the damage has already landed.'
    ],
    'Mei': [
        'Use slows and displacement to keep opponents inside Blizzard until its stun arrives.',
        'Save Icing for peeling or repositioning when your team cannot follow an engage.',
        'Use Cryo-Freeze before lethal damage arrives, and consider where enemies will be standing when it ends.'
    ],
    'Mephisto': [
        'Position so Lightning Nova’s ring touches enemy heroes; standing directly on a target is not the same as hitting it with the ring.',
        'Choose a safe Shade starting point. Enemies can wait at your return location.',
        'Aim Skull Missile into predictable movement or allied control, then use the cooldown reduction from hero hits to keep pressure up.'
    ],
    'Muradin': [
        'Use Thunder Clap’s slow to help land Storm Bolt at close range.',
        'Keep Dwarf Toss for retreat when your team cannot support a jump into the enemy.',
        'Back away between trades so your trait can restore health. You do not need to remain under constant poke.'
    ],
    'Murky': [
        'Hide your egg somewhere that supports your plan without giving enemies an easy free kill.',
        'Use Slime and Pufferfish to pressure waves, while watching whether opponents can immediately remove the fish.',
        'Use Safety Bubble to avoid a dangerous hit or leave a failed engage. Your short respawn is not a reason to waste every life.'
    ],
    'Nazeebo': [
        'Build your trait through minion waves consistently; do not spend the entire early game brawling away from lane experience.',
        'Use Zombie Wall after a slow or stun, and cancel it if it blocks an ally’s escape.',
        'Keep space from divers. Use your summons and toads to make approaching you costly instead of walking into melee.'
    ],
    'Nova': [
        'Slow with Pinning Shot before Snipe so the shot is easier to land.',
        'Use Holo Decoy to test a dangerous approach or interfere with skillshots.',
        'Look for exposed targets your team can finish. Do not chase into the enemy group just because you are cloaked.'
    ],
    'Orphea': [
        'After hitting abilities, use an empowered attack to spend Chaos and restore health.',
        'Land Shadow Waltz before relying on its dash to escape. A miss removes much of your mobility.',
        'Use Dread along the enemy’s movement path and save close-range Chomp for a safe window.'
    ],
    'Probius': [
        'Put Pylons in protected positions near the area you intend to hold. Exposed Pylons are easy for enemies to remove.',
        'Place Warp Rifts on approaches and detonate them with Disruption Pulse when enemies enter the area.',
        'Photon Cannons help defend your setup. Leave danger early: Worker Rush is vulnerable to incoming damage.'
    ],
    'Qhira': [
        'Spread and refresh bleeding on heroes before activating Blood Rage for recovery.',
        'Keep Grappling Hook available for terrain or another safe reposition when your engage is uncertain.',
        'Use Revolving Sweep deliberately to avoid incoming damage, then choose a landing that your team can support.'
    ],
    'Ragnaros': [
        'Use Empower Sulfuras immediately after a normal attack to deliver the next hit sooner.',
        'Blast Wave can help an ally enter or leave a fight; it does not have to be cast on yourself.',
        'Use Molten Core to damage an approaching push before it reaches the structure. Absorbing the whole push shortens your useful time.'
    ],
    'Raynor': [
        'Move between attacks while keeping a reachable target in range. You have no dash to fix an unsafe position.',
        'Save Penetrating Round to interrupt or push an attacker away when you are under threat.',
        'Use Inspire when pushing with allied minions or mercenaries as well as in fights.'
    ],
    'Rehgar': [
        'Place Earthbind Totem where it restricts a retreat or protects your damage dealers from an approach.',
        'Use Lightning Shield on someone who will stay near enemies; it can also help clear waves and camps.',
        'Wolf-form attacks add damage, but do not leap forward if doing so leaves your teammates without a safe healer.'
    ],
    'Rexxar': [
        'Control Misha separately to contest space while Rexxar stays away from danger.',
        'Slow with Spirit Swoop to help Misha land her charge. The charge also works well to peel an attacker off you.',
        'Recall Misha when she is taking unnecessary damage. Save mana by avoiding heals that a nearby regeneration globe could replace.'
    ],
    'Samuro': [
        'Keep a safe image position in mind so Image Transmission can get you out after a trade.',
        'Use Critical Strike after an attack to reset the swing and deliver the next hit promptly.',
        'Wind Walk helps you approach or retreat. Watch enemy reveals and do not assume invisibility makes an isolated push safe.'
    ],
    'Sgt. Hammer': [
        'Siege where your team can protect your flanks. Leave Siege Mode when enemy area damage makes staying still unsafe.',
        'Keep Thrusters for escape and use Concussive Blast to push attackers out of your space.',
        'Place mines on likely flanks, and time Neosteel Plating for incoming ability burst.'
    ],
    'Sonya': [
        'Build Fury before the next fight and weave attacks into your damage rotation.',
        'Whirlwind through several targets for recovery, but wait if enemies still have an easy interrupt.',
        'Use Ancient Spear with a plan: getting in is easier than getting back out when your team cannot follow.'
    ],
    'Stitches': [
        'Hook is most useful when allies can immediately damage the target. Check what is between you and the intended victim.',
        'Keep Devour for meaningful missing health instead of spending most of its healing while nearly full.',
        'Use your body and Slam to protect teammates while Hook is unavailable. A hook can also interrupt a dangerous channel.'
    ],
    'Stukov': [
        'Start Healing Pathogen on an ally positioned to spread it through the team.',
        'Detonate Bio-Kill Switch when its healing will save or restore several affected allies.',
        'Channel Lurking Arm on a choke or controlled enemy from a safe position. Be ready to stop channeling when you need to move.'
    ],
    'Sylvanas': [
        'Focus attacks to build Black Arrows stacks before spending your damage on that target.',
        'Keep Haunting Wave for repositioning unless you have a safe, planned engage.',
        'Time your structure-disabling active with a real team push. A short window with allies can be worth more than using it alone.'
    ],
    'Tassadar': [
        'Cast Shock Ray after a slow or allied control. Its wind-up gives an unpressured enemy time to dodge.',
        'Use Psionic Storm to cover crowded paths and keep enemies from comfortably advancing.',
        'Maintain your beam on safe targets to help recover mana, and watch your position while standing to attack or cast.'
    ],
    'The Butcher': [
        'Collect meat through safe waves and coordinated kills. A risky death can undo your progress.',
        'Use Brand on a target you can actually keep attacking; it is your main way to sustain a committed fight.',
        'Charge when your team can follow and enemy defenses are accounted for. Do not treat every visible low-health target as a safe engage.'
    ],
    'The Lost Vikings': [
        'Prioritise safe lane experience early and warn your team when you are split across lanes.',
        'Keep the Vikings separated when enemies have dangerous area damage.',
        'Use queued orders to reduce the time spent on repetitive movement, and watch each Viking’s route for missing enemies.'
    ],
    'Thrall': [
        'Use Chain Lightning to poke and interrupt objective channels without overcommitting.',
        'Land Feral Spirit before closing with Windfury; keep Windfury for retreat if the fight turns.',
        'Avoid spending your empowered attacks while blinded. Stay near allies who can help finish the rooted target.'
    ],
    'Tracer': [
        'Keep enough mobility to leave after you commit. Spend Blinks to dodge meaningful abilities rather than using every charge to enter.',
        'Use Melee when safely close to add burst and build Pulse Bomb.',
        'Remember where Recall will send you. A previous position can become dangerous while you are fighting.'
    ],
    'Tychus': [
        'Use Minigun when a durable hero is in range and likely to remain there.',
        'If blinded, use Overkill rather than wasting your attack window. It also lets you keep dealing damage while moving.',
        'Save Run and Gun for a necessary reposition. Frag Grenade can interrupt a channel or push away an attacker.'
    ],
    'Tyrael': [
        'Put El’druin’s Might where it gives you a useful engage or escape option; you do not have to teleport immediately.',
        'Shield teammates as damage arrives and place Smite so allies can use its movement bonus.',
        'Manage mana carefully between fights. Repeated low-value spells can leave you unable to protect your team during the objective.'
    ],
    'Tyrande': [
        'Attack safe targets to recover healing cooldowns. Wait for threatening enemy control to be spent before stepping closer.',
        'Use Lunar Flare after a teammate’s stun or slow instead of relying on a difficult raw hit.',
        'Mark the target your team is attacking. Sentinel can check unsafe areas before your team walks into them.'
    ],
    'Uther': [
        'Time your healing for the ally being focused; its protection is valuable while more damage is arriving.',
        'Line up Holy Radiance through several allies and enemies when possible.',
        'Use Hammer of Justice to stop a diver or secure your team’s target. Long cooldowns mean wasted casts are costly.'
    ],
    'Valeera': [
        'Choose your opener for the target: Garrote restricts abilities, while Cheap Shot’s blind is useful against attacks.',
        'Spend Eviscerate with full combo points when possible and avoid burning energy on unnecessary Blade Flurries.',
        'Keep Sinister Strike as a possible escape. Cloak alone does not make diving through the entire enemy team safe.'
    ],
    'Valla': [
        'Maintain Hatred by attacking safe targets between exchanges, and keep moving between shots.',
        'Hold Vault for avoiding control or escaping unless the kill is genuinely secure.',
        'Use Multishot to clear waves and check dangerous approaches. Avoid letting incidental targets absorb the damage you need on a hero.'
    ],
    'Varian': [
        'Decide your role before level 4. Choose Taunt if the team needs you to be its tank.',
        'Protect your damage dealers or attack alongside them; running far ahead wastes your team’s follow-up.',
        'Time defensive abilities for incoming damage instead of spending them as soon as you enter range.'
    ],
    'Whitemane': [
        'Apply Zeal to the allies who need healing before dealing damage to enemy heroes.',
        'Watch Desperation and avoid rapidly repeating expensive Pleas when another healing option will do.',
        'Use Searing Lash on controlled enemies. Clemency provides healing when there is no safe hero to damage.'
    ],
    'Xul': [
        'Clear waves efficiently with Cursed Strikes, then rotate for the next wave rather than waiting in an empty lane.',
        'Tell your team when you stay out to soak so they can avoid a fight without you.',
        'Use Bone Prison after an enemy spends their escape or protection, and avoid walking into the whole team just to apply it.'
    ],
    'Yrel': [
        'Use Divine Purpose when you need an instant fully charged ability, including a quick heal or escape.',
        'Righteous Hammer can push an attacker away from an ally as well as start a fight.',
        'Charge mobility from a safe position and watch enemy interrupts. Do not wait until the last possible moment to use your survival tools.'
    ],
    'Zagara': [
        'Place creep along useful approaches and escape routes so you can see enemies coming.',
        'Use Banelings to clear a lined-up wave and Hunter Killer to pressure a hero without stepping too close.',
        'Use summons to help pressure or scout, but check missing enemies before extending alone.'
    ],
    'Zarya': [
        'Shield yourself or an ally just before damage arrives; shields that absorb nothing generate little value.',
        'Use the energy you gained to pressure safely with attacks and grenades.',
        'Keep a safe position because you lack an easy escape. Grenades can interrupt an objective channel from a distance.'
    ],
    'Zeratul': [
        'Keep Blink available until you know how to escape the fight. Use a flank to approach rather than spending every movement tool.',
        'Follow Singularity Spike’s slow with attacks and Cleave, then leave before the enemy team can surround you.',
        'Cloak does not guarantee you are unseen. Watch detection and avoid predictable approaches through the frontline.'
    ],
    "Zul'jin": [
        'Manage Berserker carefully: more attack speed at low health is useful only if you survive the enemy’s next burst.',
        'Find a safe place to channel Regeneration; even minion damage can interrupt the recovery.',
        'Aim Grievous Throw with a clear line to the hero you want to attack rather than letting other units absorb it.'
    ],
}
