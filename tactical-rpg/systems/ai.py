"""
Enemy AI: greedy — heal if hurt, else move toward nearest ally and attack.

ai_move()  — Phase 1: heal-or-move only. Returns (log, attack_target_or_None).
             Does NOT resolve combat; caller does that after the animation plays.
"""
import math
from systems.movement import clamp_to_radius, path_terrain_cost
from core.constants import AI_HEAL_THRESHOLD, AI_ATTACK_MARGIN


def ai_move(enemy, allies, terrain=None):
    """
    Phase 1 of an enemy's turn: heal if low on HP, then move toward the
    nearest ally.  Combat is intentionally NOT resolved here so the caller
    can wait for the movement animation to finish before spawning effects.

    terrain: list of TerrainPiece objects (optional); used to apply live
             movement cost when crossing Forest/Hills. Mages are exempt.

    Returns (list[str], Unit|None):
      - log lines to display
      - the target to attack once animation is done, or None if no attack follows
        (unit is already exhausted in that case)
    """
    log = []

    # Heal if HP drops below threshold and has a usable item
    if enemy.hp / enemy.max_hp < AI_HEAL_THRESHOLD:
        items = enemy.usable_items()
        if items:
            msg = items[0].use(enemy)
            log.append(f"[AI] {msg}")
            enemy.exhaust()
            return log, None

    alive_allies = [a for a in allies if a.alive]
    if not alive_allies:
        enemy.exhaust()
        return log, None

    target = min(alive_allies, key=lambda a: enemy.dist_to(a))

    # Move toward target if not already in attack range
    if not enemy.can_attack(target):
        tx, ty = _best_position_for_attack(enemy, target)

        # Apply live terrain movement cost (Mages exempt via path_terrain_cost).
        # Check terrain only on the segment the enemy actually travels (clamped to
        # mov_radius), not the full path to the distant target — terrain beyond the
        # movement range should not penalise the current move.
        move_radius = enemy.mov_radius
        if terrain:
            ix, iy = clamp_to_radius(enemy.x, enemy.y, tx, ty, enemy.mov_radius)
            cost, _ = path_terrain_cost(enemy.x, enemy.y, ix, iy, terrain, enemy.weapon)
            move_radius = max(0, move_radius - cost)

        nx, ny = clamp_to_radius(enemy.x, enemy.y, tx, ty, move_radius)
        enemy.x, enemy.y = nx, ny
        log.append(f"[AI] {enemy.name} moves toward {target.name}.")

    # Return the attack target if now in range — caller resolves combat later
    if enemy.can_attack(target):
        log.append(f"[AI] {enemy.name} engages {target.name}!")
        return log, target

    # Couldn't reach — end turn now
    enemy.exhaust()
    return log, None


def _best_position_for_attack(enemy, target):
    from systems.items import WEAPON_RANGE, BOW
    lo, hi = WEAPON_RANGE[enemy.weapon]
    dx   = target.x - enemy.x
    dy   = target.y - enemy.y
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist

    if enemy.weapon == BOW:
        desired = lo + AI_ATTACK_MARGIN
    else:
        desired = max(lo, hi - AI_ATTACK_MARGIN)

    return target.x - ux * desired, target.y - uy * desired
