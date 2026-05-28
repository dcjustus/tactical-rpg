"""
Combat resolution: accuracy roll, damage formula, double-attack, counter-attack.
Physical weapons use STR vs DEF; Magic uses INT vs RES.
Terrain evasion (Forest/Hills) reduces the attacker's effective hit chance.
"""
import random
from systems.items import weapon_triangle_bonus, weapon_triangle_hit_mod, weapon_triangle_crit_mod, MAGIC
from core.constants import BASE_HIT_RATE, DOUBLE_ATTACK_THRESHOLD, BASE_CRIT_CHANCE, EXP_FOR_HIT, EXP_FOR_KILL


def hit_chance(attacker, defender, defender_terrain_ev=0):
    """Return integer hit% (clamped 0-100), reduced by defender's terrain evasion."""
    mod = weapon_triangle_hit_mod(attacker.weapon, defender.weapon)
    return max(0, min(100, BASE_HIT_RATE + mod - defender_terrain_ev))


def resolve_combat(attacker, defender, atk_terrain_ev=0, def_terrain_ev=0):
    """
    Full combat exchange. Modifies hp in place.
    atk_terrain_ev: evasion% the attacker gains from their own terrain (used when defender counters).
    def_terrain_ev: evasion% the defender gains from their own terrain (used on initial + follow-up).
    Returns list of log strings.
    """
    log = []

    # Initial strike — defender's terrain helps them dodge
    log += _strike(attacker, defender, "attacks", def_terrain_ev)
    if not defender.alive:
        return log

    # Counter-attack — attacker's terrain helps them dodge the counter
    if defender.can_attack(attacker):
        log += _strike(defender, attacker, "counters", atk_terrain_ev)
        if not attacker.alive:
            return log
    else:
        log.append(f"  {defender.name} cannot counter-attack (out of range).")

    # Follow-up strike — defender's terrain applies again
    if attacker.alive and defender.alive:
        if attacker.speed >= defender.speed * DOUBLE_ATTACK_THRESHOLD:
            log.append(f"  {attacker.name}'s speed allows a follow-up strike!")
            log += _strike(attacker, defender, "follows up on", def_terrain_ev)

    return log


def _strike(attacker, defender, verb, defender_terrain_ev=0):
    chance = hit_chance(attacker, defender, defender_terrain_ev)
    roll   = random.randint(1, 100)

    if roll > chance:
        terrain_note = f" [terrain -{defender_terrain_ev}%]" if defender_terrain_ev else ""
        return [f"{attacker.name} {verb} {defender.name} — MISS! (hit: {chance}%{terrain_note})"]

    tri_dmg = weapon_triangle_bonus(attacker.weapon, defender.weapon)

    if attacker.weapon == MAGIC:
        eff_atk = attacker.intelligence
        dmg     = max(1, eff_atk - defender.resistance)
        note    = f"INT {attacker.intelligence} vs RES {defender.resistance}"
    else:
        eff_atk = attacker.strength + tri_dmg
        dmg     = max(1, eff_atk - defender.defense)
        note    = f"STR {attacker.strength} vs DEF {defender.defense}"
        if tri_dmg > 0:
            note += f" [+{tri_dmg} advantage]"
        elif tri_dmg < 0:
            note += f" [{tri_dmg} disadvantage]"

    # Critical hit roll (Mages have 0% crit)
    if attacker.weapon == MAGIC:
        crit_chance = 0
    else:
        crit_chance = max(0, BASE_CRIT_CHANCE + weapon_triangle_crit_mod(attacker.weapon, defender.weapon))

    is_crit = crit_chance > 0 and random.randint(1, 100) <= crit_chance
    if is_crit:
        dmg *= 2
        note += " [CRITICAL]"

    if defender_terrain_ev:
        note += f" [terrain -{defender_terrain_ev}%]"

    defender.take_damage(dmg)
    line = (f"{attacker.name} {verb} {defender.name} "
            f"for {dmg} dmg ({note}). "
            f"[{defender.name} HP: {defender.hp}/{defender.max_hp}]")
    killed = not defender.alive
    if killed:
        line += f" — {defender.name} falls!"

    log = [line]
    log += attacker.gain_exp(EXP_FOR_HIT)
    if killed:
        log += attacker.gain_exp(EXP_FOR_KILL)
    return log
