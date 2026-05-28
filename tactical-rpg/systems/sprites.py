"""
Idle-animation sprite loader for unit classes.

Loads three 31×31 PNG frames ([class]_idle1/2/3.png) per class, scales them to
the display size, pre-bakes tinted variants (ally / enemy / exhausted-ally /
exhausted-enemy) for each frame, and exposes a simple frame-index API.

Units drive animation by incrementing their own elapsed time; call
get_sprite(class_name, team, exhausted, frame_index) each draw call.
Falls back to None on any load failure; unit.py then uses primitive shapes.
"""
import os
import pygame

_SPRITE_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')

# Source size of every idle PNG.
SOURCE_PX = 31

# Display size: scale 31→62 (2×) then add a couple pixels for presence.
# UNIT_RADIUS = 20 → diameter = 40.  64 px sits comfortably over it.
TARGET_PX = 64

# Seconds per idle frame (3 frames → full cycle every ~0.75 s)
FRAME_DURATION = 0.25

# Tints applied after optional greyscale conversion.
_TINTS = {
    "ally":      (255, 255, 255),   # no shift — original palette
    "enemy":     (255,  85,  65),   # red-orange
    "ally_ex":   (140, 155, 185),   # muted blue-grey
    "enemy_ex":  (155, 110, 110),   # muted red-grey
}
_GREYSCALE = {
    "ally": False, "enemy": True, "ally_ex": True, "enemy_ex": True,
}

# Cache: class_name → list of 3 dicts, each {"ally": surf, "enemy": surf, ...}
_cache: dict = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_frame(class_name: str, idx: int):
    """Load assets/sprites/<class>_idle<idx>.png as an RGBA surface, or None."""
    fname = f"{class_name.lower()}_idle{idx}.png"
    path  = os.path.join(_SPRITE_DIR, fname)
    if not os.path.isfile(path):
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(surf, (TARGET_PX, TARGET_PX))
    except Exception:
        return None


def _make_variant(base, greyscale: bool, tint):
    surf = pygame.transform.grayscale(base.copy()) if greyscale else base.copy()
    if tint != (255, 255, 255):
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((*tint, 255))
        surf.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


# ── Public API ────────────────────────────────────────────────────────────────

def init_sprites() -> None:
    """
    Load and pre-bake all idle sprites.
    Must be called after pygame.display.set_mode().
    Safe to call multiple times; subsequent calls are no-ops.
    """
    if _cache:
        return

    classes = ["Fighter", "Warrior", "Knight", "Archer", "Mage"]
    for cls in classes:
        frames = []
        ok = True
        for idx in range(1, 4):          # idle1, idle2, idle3
            base = _load_frame(cls, idx)
            if base is None:
                ok = False
                break
            variants = {
                key: _make_variant(base, _GREYSCALE[key], _TINTS[key])
                for key in _TINTS
            }
            frames.append(variants)
        _cache[cls] = frames if ok else None


def get_sprite(class_name: str, team: str, exhausted: bool, frame_index: int):
    """
    Return the pre-baked RGBA surface for (class, team, exhausted, frame 0-2).
    Returns None when sprites are unavailable (caller falls back to shapes).
    """
    frames = _cache.get(class_name)
    if not frames:
        return None
    key = f"{team}{'_ex' if exhausted else ''}"
    return frames[frame_index % 3].get(key)
