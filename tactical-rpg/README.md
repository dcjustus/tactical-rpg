# Tactical RPG — Fantasy Battle Demo

A browser-compatible tactical RPG built with **pygame-ce**, inspired by Fire Emblem. Two sides clash on a randomised battlefield: you command the blue allies, the red enemies are controlled by AI. Defeat every enemy to win.

---

## How to Run

### Locally (recommended for development)

```bash
cd tactical-rpg
pip install pygame-ce
python main.py
```

### In the browser (via Pygbag)

```bash
pip install pygbag
python -m pygbag --build tactical-rpg/
# then open http://localhost:8000 in Chrome or Firefox
```

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
2. Defender **counter-attacks** if the attacker is within their own attack range.
3. If the attacker's **Speed is ≥ 1.4× the defender's Speed**, they land a **follow-up strike**.

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

## Sound Effects

Sound effects play automatically during combat and movement. The game reads MP3 files from `assets/sounds/`:

| File | Trigger |
|---|---|
| `slash.mp3` | Sword attacks |
| `swing.mp3` | Axe attacks |
| `strike.mp3` | Lance / Spear attacks |
| `arrow.mp3` | Bow attacks |
| `magic.mp3` | Magic attacks |
| `movement.mp3` | Unit movement |

To add your own sounds, drop MP3 files into `tactical-rpg/assets/sounds/` using the names above. The game loads them at startup and falls back silently if any file is missing or unreadable (placeholder text files are included in the repository as slots).

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

| Shape | Class |
|---|---|
| Circle (medium) | Fighter (Sword) |
| Circle (large) | Warrior (Axe) |
| Rounded square | Knight (Lance) |
| Small circle + arc | Archer (Bow) |
| Diamond | Mage (Magic) |

- **Blue** = your allies. **Red** = enemies. **Grey** = exhausted (already acted this turn).
- The **blue ring** around a selected ally shows movement range.
- The **red ring** shows attack range — visible whenever a unit is selected so you can plan before moving. For Archers, a dark inner ring marks the dead zone.
- Clicking a **red enemy** on your turn shows their stats and attack range in view-only mode (gold ring, stats in the right panel). You cannot control them.
- The **HP bar** above each unit turns yellow below 50% and red below 25%.
- A **white flash** on a unit means they just took a hit.

---

## Tips

- Mages shred Warriors but die in two hits from almost anything — keep them protected.
- Archers need room; don't back them into a corner where enemies close to melee range.
- The weapon triangle hit bonus matters: a disadvantaged Fighter attacking a Knight misses more often.
- Use **Back** freely — repositioning is free until you commit to an action.
- Check chests early; Str/Int Tonics can swing a tight match.
- Before moving, click an enemy to see their attack range — knowing their reach helps you decide where to position safely.
