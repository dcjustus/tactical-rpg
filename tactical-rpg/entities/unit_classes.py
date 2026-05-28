"""
Unit class definitions.
STR = physical attack  |  DEF = physical resistance
INT = magic attack     |  RES = magic resistance
SPD = speed (double hit if >= enemy SPD x 1.4)
MOV = movement stat (x MOV_SCALE px per point)

Balance target: ~8-12 neutral damage per hit, ~3-4 hits to kill most units.

growths: per-stat percentage chance of +1 on each level up.
  High growth = stat scales well; low growth = stat stays near base.
"""
from systems.items import SWORD, AXE, LANCE, BOW, MAGIC

CLASS_DEFS = {
    "Fighter": {
        "weapon":      SWORD,
        "max_hp":      32,
        "strength":    17,
        "defense":     7,
        "intelligence":5,
        "resistance":  10,    # raised: Fighters survive magic, Warriors stay vulnerable
        "speed":       7,
        "movement":    5,
        "description": "Balanced warrior. Sword beats Axe.",
        "growths": {
            "max_hp":      70,   # solid HP pool
            "strength":    50,
            "defense":     40,
            "intelligence":20,
            "resistance":  30,
            "speed":       40,
        },
    },
    "Warrior": {
        "weapon":      AXE,
        "max_hp":      40,
        "strength":    20,    # high damage
        "defense":     10,
        "intelligence":2,
        "resistance":  3,     # very weak to magic
        "speed":       5,
        "movement":    4,
        "description": "Brawler. High HP/STR but very vulnerable to magic.",
        "growths": {
            "max_hp":      80,   # biggest HP pool; keeps growing
            "strength":    60,   # consistently gets stronger
            "defense":     50,
            "intelligence":10,
            "resistance":  15,   # stays low — Warriors fear mages
            "speed":       30,
        },
    },
    "Knight": {
        "weapon":      LANCE,
        "max_hp":      26,
        "strength":    19,    # raised: disadvantaged matchups now deal ~6 dmg instead of 1
        "defense":     9,     # durable but not unkillable (down from 18)
        "intelligence":3,
        "resistance":  9,
        "speed":       4,
        "movement":    4,     # raised: same as Warrior — slow but not glacial
        "description": "Armored. Decent DEF/RES but low HP and speed.",
        "growths": {
            "max_hp":      60,
            "strength":    50,
            "defense":     65,   # DEF is the Knight's identity
            "intelligence":20,
            "resistance":  45,   # above-average magic resist
            "speed":       20,   # stays slow
        },
    },
    "Archer": {
        "weapon":      BOW,
        "max_hp":      28,
        "strength":    17,
        "defense":     5,
        "intelligence":5,
        "resistance":  6,
        "speed":       9,
        "movement":    5,
        "description": "Ranged. Cannot target enemies closer than 80 units.",
        "growths": {
            "max_hp":      50,
            "strength":    50,
            "defense":     30,   # stays lightly armored
            "intelligence":25,
            "resistance":  25,
            "speed":       65,   # speed is the Archer's identity
        },
    },
    "Mage": {
        "weapon":      MAGIC,
        "max_hp":      20,
        "strength":    4,
        "defense":     3,
        "intelligence":20,    # devastating magic
        "resistance":  8,
        "speed":       10,
        "movement":    5,
        "description": "Full-range attacker. Fragile but hits INT vs RES.",
        "growths": {
            "max_hp":      30,   # glass cannon — HP barely grows
            "strength":    10,
            "defense":     10,
            "intelligence":70,   # INT is the Mage's identity
            "resistance":  55,   # builds magic resilience over time
            "speed":       50,   # stays fast
        },
    },
}

ALL_CLASSES = list(CLASS_DEFS.keys())
