"""
Combat resolution: accuracy roll, damage formula, double-attack, counter-attack.
Physical weapons use STR vs DEF; Magic uses INT vs RES.
"""
import random
from systems.items import weapon_triangle_bonus, weapon_triangle_hit_mod, weapon_triangle_crit_mod, MAGIC
from core.constants import BASE_HIT_RATE, DOUBLE_ATTACK_THRESHOLD, BASE_CRIT_CHANCE


def hit_chance(attacker, defender):
    """Return integer hit% (clamped 0-100)."""
    mod = weapon_triangle_hit_mod(attacker.weapon, defender.weapon)
    return max(0, min(100, BASE_HIT_RATE + mod))


def resolve_combat(attacker, defender):
    """
    Full combat exchange. Modifies hp in place.
    Returns list of log strings.
    """
    log = []

    # Initial strike
    log += _strike(attacker, defender, "attacks")
    if not defender.alive:
        return log

    # Counter-attack (defender retaliates if they can reach the attacker)
    if defender.can_attack(attacker):
        log += _strike(defender, attacker, "counters")
        if not attacker.alive:
            return log
    else:
        log.append(f"  {defender.name} cannot counter-attack (out of range).")

    # Double attack: attacker SPD >= defender SPD * threshold
    if attacker.alive and defender.alive:
        if attacker.speed >= defender.speed * DOUBLE_ATTACK_THRESHOLD:
            log.append(f"  {attacker.name}'s speed allows a follow-up strike!")
            log += _strike(attacker, defender, "follows up on")

    return log


def _strike(attacker, defender, verb):
    chance = hit_chance(attacker, defender)
    roll   = random.randint(1, 100)

    if roll > chance:
        return [f"{attacker.name} {verb} {defender.name} — MISS! (hit: {chance}%)"]

    tri_dmg = weapon_triangle_bonus(attacker.weapon, defender.weapon)

    if attacker.weapon == MAGIC:
        eff_atk = attacker.intelligence   # no triangle for magic
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

    # Critical hit roll (Mages have 0% crit; all other classes use BASE_CRIT_CHANCE ± triangle mod)
    if attacker.weapon == MAGIC:
        crit_chance = 0
    else:
        crit_chance = max(0, BASE_CRIT_CHANCE + weapon_triangle_crit_mod(attacker.weapon, defender.weapon))

    is_crit = crit_chance > 0 and random.randint(1, 100) <= crit_chance
    if is_crit:
        dmg *= 2
        note += " [CRITICAL]"

    defender.take_damage(dmg)
    line = (f"{attacker.name} {verb} {defender.name} "
            f"for {dmg} dmg ({note}). "
            f"[{defender.name} HP: {defender.hp}/{defender.max_hp}]")
    if not defender.alive:
        line += f" — {defender.name} falls!"
    return [line]
