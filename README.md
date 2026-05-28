# FE:Lite — A Lightweight Tactical RPG

A browser-compatible tactical RPG built with **pygame-ce**, inspired by Fire Emblem. Two sides clash on a randomised battlefield: you command the blue allies, the red enemies are controlled by AI. Defeat every enemy to win.

---

## How to Run

### Locally (recommended for development)

```bash
pip install pygame-ce
python main.py
```

### In the browser (via Pygbag)

```bash
pip install pygbag
python -m pygbag --title "FE:Lite" --disable-sound-format-error --build .
# then open http://localhost:8000 in Chrome or Firefox
```

> **Note:** Audio is disabled in the web build — the Pygbag bundler requires OGG format but the game ships MP3s. The game runs fully otherwise; the sound system degrades silently.

---

## Controls

| Action | Input |
|---|---|
| Select a unit | Left-click a blue unit |
| Inspect an enemy | Left-click a red unit (view stats only) |
| Move | Click inside the blue circle |
| Switch selection | Click another blue unit while selecting |
| Undo move | Choose **Back** in the action menu |
| Attack | Choose **Attack**, then click a red unit in the red zone |
| Use item | Choose **Item**, then pick from the list |
| End turn without acting | Choose **Wait** |
| Navigate menus | Mouse or **W / S** + **Enter** |

---

## Gameplay Overview

Each battle is randomly generated with **3–5 allies vs 3–5 enemies** (always equal counts). Units are randomly classed and named.

Turns alternate between **Player Phase** and **Enemy Phase**. During your phase, activate each ally once — move them, then choose an action. Units move with a smooth gliding animation rather than teleporting. When all allies have acted the enemies take their turn automatically; each enemy visually moves to their destination before striking, with a short delay between each so you can follow along.

**Win** by defeating all enemies. **Lose** if all allies fall.

---

## Unit Classes

| Class | Weapon | HP | STR | DEF | INT | RES | SPD | MOV |
|---|---|---|---|---|---|---|---|---|
| Fighter | Sword | 32 | 17 | 7 | 5 | 10 | 7 | 5 |
| Warrior | Axe | 40 | 20 | 10 | 2 | 3 | 5 | 4 |
| Knight | Lance | 26 | 19 | 9 | 3 | 9 | 4 | 4 |
| Archer | Bow | 28 | 17 | 5 | 5 | 6 | 9 | 5 |
| Mage | Magic | 20 | 4 | 3 | 20 | 8 | 10 | 5 |

All stats have ±15% random variance on spawn, so no two units are identical. MOV determines how far a unit can travel per turn (MOV 5 = large range, MOV 4 = short range).

**Class identities:**
- **Fighter** — jack-of-all-trades, solid in any situation.
- **Warrior** — hits hard and soaks physical hits, but magic tears right through them (RES 3).
- **Knight** — slow, low HP, but above-average DEF and RES — absorbs punishment before going down.
- **Archer** — fast, hits from long range, but has a **dead zone** and cannot attack enemies that are too close.
- **Mage** — attacks at any range using INT vs RES; devastating against Warriors and fragile vs everything.

---

## Combat

### Attack ranges

- **Sword / Axe / Lance** — melee only (must be adjacent).
- **Bow** — ranged only; cannot target enemies within ~80 px. The dead zone is shown as a dark inner ring.
- **Magic** — full range; attacks from point-blank to long distance.

### How a combat exchange works

1. Attacker strikes.
2. On a hit, there is a chance for a **critical hit** that deals **2× damage** (logged as `[CRITICAL]`).
3. Defender **counter-attacks** if the attacker is within their own attack range.
4. If the attacker's **Speed is ≥ 1.4× the defender's Speed**, they land a **follow-up strike**.

### Critical hits

- **All classes except Mage** have a **10% base crit chance**.
- **Mages** have **0% crit** — their magic damage is powerful enough on its own.
- Having the **weapon triangle advantage** adds **+5%** to crit chance; disadvantage subtracts **5%**.
- Bow and Magic are neutral to the triangle and receive no crit modifier.

### Damage formula

```
Physical damage = max(1,  Attacker STR − Defender DEF  ± triangle bonus)
Magic damage    = max(1,  Attacker INT − Defender RES)
```

Magic ignores the weapon triangle entirely.

### Weapon triangle

```
Sword  →  beats  →  Axe
 ↑                   ↓
Lance  ←  beats  ←  (nothing beats lance except sword)
```

Having the **advantage** gives **+3 damage** and **+10% accuracy**.
Having the **disadvantage** gives **−3 damage** and **−10% accuracy**.

Base hit rate is **90%**. Bow and Magic are neutral to the triangle.

---

## Audio

All audio is read from `assets/sounds/`. Drop real MP3 files in with the names below and they load automatically — no code changes needed. The game falls back silently if any file is missing.

### Music

| File | Plays during |
|---|---|
| `menu_music.mp3` | Title screen (loops) |
| `battle_music.mp3` | Battle (loops) |
| `victory.mp3` | Victory screen |
| `defeat.mp3` | Defeat screen |

### Sound Effects

| File | Trigger |
|---|---|
| `slash.mp3` | Sword attacks |
| `swing.mp3` | Axe attacks |
| `strike.mp3` | Lance / Spear attacks |
| `arrow.mp3` | Bow attacks |
| `magic.mp3` | Magic attacks |
| `movement.mp3` | Unit movement (loops while animating, stops on arrival) |
| `death.mp3` | Any unit killed in combat |

---

## Items & Loot

Every unit spawns with 0–2 consumable items:

| Item | Effect |
|---|---|
| Heal Potion | Restore 25% of max HP |
| Vulnerary | Restore 15% max HP (2 uses) |
| Elixir | Restore 50% of max HP |

**Treasure chests** (golden boxes) spawn in the centre of the battlefield. Move a unit within range and choose **Open Chest** to claim a special reward:

| Chest reward | Effect |
|---|---|
| Str / Def / Int / Res Tonic | +4 to that stat, permanently for this battle |
| Mega Potion | Restore 40% HP |
| Elixir | Restore 50% HP |

**Item drops** — when a unit is defeated, each item they carried has a 30% chance to go directly to the killer's inventory. The rest scatter to the ground as golden diamonds; walk any unit over them to automatically pick them up.

---

## Visual Guide

Each class has a unique 3-frame idle animation that cycles continuously on the battlefield.

| Colour | Meaning |
|---|---|
| Blue sprites | Your allies |
| Red-tinted sprites | Enemies |
| Grey-tinted sprites | Exhausted unit (already acted this turn) |

- The **blue ring** around a selected ally shows movement range.
- The **red ring** shows attack range — visible whenever a unit is selected so you can plan before moving. For Archers, a dark inner ring marks the dead zone.
- Clicking a **red enemy** on your turn shows their stats and attack range in view-only mode (gold ring, stats in the right panel). You cannot control them.
- The **HP bar** above each unit turns yellow below 50% and red below 25%.
- A **white flash** on a unit means they just took a hit.

---

## Levels & EXP

Every unit has a level (shown in the right panel). Units start each battle at a random level between 1 and 10, with stats already grown to reflect that level.

- **Hitting** an enemy awards **10 EXP**. Counter-attackers also earn EXP.
- **Killing** an enemy awards a bonus **40 EXP** on top of the hit EXP.
- **100 EXP** triggers a level up. Each stat has a class-specific growth rate (% chance of gaining +1 per level). A level-up message appears in the combat log listing which stats improved.
- Level cap is **20**. EXP stops accumulating at max level.

Each class grows differently:

| Class | Grows best in... |
|---|---|
| Fighter | HP, balanced across all stats |
| Warrior | HP and STR; poor magic stats |
| Knight | DEF and RES; stays slow |
| Archer | SPD; light armour |
| Mage | INT; glass cannon stays fragile |

No two units are ever identical — each one rolls an independent **±3 random modifier** on every stat when they spawn. Combined with level variance and growth-rate randomness, every battle features genuinely unique combatants.

---

## Terrain

Terrain pieces in the centre of the battlefield aren't just decoration — they affect combat and movement.

| Terrain | Evasion | Movement penalty |
|---|---|---|
| **Trees (Forest)** | −15% to attacker's hit chance | −50 px from movement range |
| **Rocks (Hills)** | −10% to attacker's hit chance | −25 px from movement range |

- **Movement is live**: if your path to the destination crosses terrain, your unit stops short of where you clicked. The log shows *"Name is slowed by Forest."* when this happens.
- **Evasion** applies when the *defender* is standing inside terrain at the moment they are attacked. The combat log notes *[terrain −15%]* on both hits and misses.
- **Mages** are exempt from movement penalties (they float over terrain), but still benefit from evasion bonuses when defending.
- Terrain costs stack if your path crosses multiple pieces, but evasion is capped at 30% so units can't become untouchable.

---

## Tips

- Mages shred Warriors but die in two hits from almost anything — keep them protected.
- Archers need room; don't back them into a corner where enemies close to melee range.
- The weapon triangle hit bonus matters: a disadvantaged Fighter attacking a Knight misses more often.
- Use **Back** freely — repositioning is free until you commit to an action.
- Check chests early; Str/Int Tonics can swing a tight match.
- Before moving, click an enemy to see their attack range — knowing their reach helps you decide where to position safely.
