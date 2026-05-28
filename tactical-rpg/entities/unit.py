import math
import random
import pygame
from core.constants import (
    UNIT_RADIUS, ALLY_COLOR, ALLY_DARK, ENEMY_COLOR, ENEMY_DARK,
    EXHAUSTED_TINT, HP_HIGH, HP_MID, HP_LOW, WHITE, BLACK, DARK_GRAY,
    MOVE_CIRCLE_COLOR, ATTACK_RING_COLOR, DEAD_ZONE_COLOR, MOV_SCALE,
)
from entities.unit_classes import CLASS_DEFS
from entities.names import get_name
from systems.items import (
    SWORD, AXE, LANCE, BOW, MAGIC,
    WEAPON_RANGE, random_inventory,
)
import systems.sprites as _sprites


def _vary(base, pct=0.15):
    """Apply ±pct random variance to a stat, returning an int (min 1)."""
    lo = base * (1 - pct)
    hi = base * (1 + pct)
    return max(1, round(random.uniform(lo, hi)))


class Unit:
    _id_counter = 0

    def __init__(self, class_name, team, x, y):
        Unit._id_counter += 1
        self.uid        = Unit._id_counter
        self.class_name = class_name
        self.team       = team          # "ally" or "enemy"
        self.x          = float(x)
        self.y          = float(y)

        defn = CLASS_DEFS[class_name]
        self.weapon       = defn["weapon"]
        self.max_hp       = _vary(defn["max_hp"])
        self.hp           = self.max_hp

        # Core stats (all vary ±15% except movement)
        self.strength     = _vary(defn["strength"])
        self.defense      = _vary(defn["defense"])
        self.intelligence = _vary(defn["intelligence"])
        self.resistance   = _vary(defn["resistance"])
        self.speed        = _vary(defn["speed"])
        self.movement     = defn["movement"]          # raw MOV stat, no variance
        self.mov_radius   = self.movement * MOV_SCALE # pixel movement radius

        self.inventory    = random_inventory()
        self.name         = get_name(team)
        self.exhausted    = False
        self.moved        = False
        self.alive        = True
        self.flash_timer  = 0.0    # hit flash countdown

        # Idle animation state
        self._idle_timer  = 0.0    # seconds within current frame
        self._idle_frame  = 0      # 0, 1, or 2

        # Visual animation state — _draw_x/_draw_y trail behind x/y
        self._draw_x     = float(x)
        self._draw_y     = float(y)
        self._anim_speed = 500.0   # pixels per second

    # ── Animation ────────────────────────────────────────────────────────────

    @property
    def is_moving(self):
        return math.hypot(self._draw_x - self.x, self._draw_y - self.y) > 0.5

    def update_anim(self, dt):
        """Step the visual position toward the logical position and advance idle animation."""
        dx = self.x - self._draw_x
        dy = self.y - self._draw_y
        dist = math.hypot(dx, dy)
        if dist <= 0.5:
            self._draw_x = self.x
            self._draw_y = self.y
        else:
            step = min(self._anim_speed * dt, dist)
            self._draw_x += dx / dist * step
            self._draw_y += dy / dist * step
            if math.hypot(self.x - self._draw_x, self.y - self._draw_y) <= 0.5:
                self._draw_x = self.x
                self._draw_y = self.y

        # Advance idle frame cycle
        self._idle_timer += dt
        if self._idle_timer >= _sprites.FRAME_DURATION:
            self._idle_timer -= _sprites.FRAME_DURATION
            self._idle_frame = (self._idle_frame + 1) % 3

    def teleport_to(self, x, y):
        """Instantly reposition with no animation (used for undo)."""
        self.x = float(x)
        self.y = float(y)
        self._draw_x = self.x
        self._draw_y = self.y

    # ── Geometry helpers ─────────────────────────────────────────────────────

    @property
    def pos(self):
        return (self.x, self.y)

    def dist_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def dist_to_point(self, px, py):
        return math.hypot(self.x - px, self.y - py)

    def can_attack(self, target):
        d = self.dist_to(target)
        lo, hi = WEAPON_RANGE[self.weapon]
        return lo <= d <= hi

    # ── Rendering ────────────────────────────────────────────────────────────

    def _base_color(self):
        if self.team == "ally":
            return ALLY_COLOR if not self.exhausted else EXHAUSTED_TINT
        return ENEMY_COLOR if not self.exhausted else EXHAUSTED_TINT

    def _dark_color(self):
        if self.exhausted:
            return (60, 60, 65)
        return ALLY_DARK if self.team == "ally" else ENEMY_DARK

    def draw(self, surface, selected=False, inspected=False):
        ix, iy = int(self._draw_x), int(self._draw_y)
        r      = UNIT_RADIUS

        if selected:
            pygame.draw.aacircle(surface, WHITE, (ix, iy), r + 5, 3)
        elif inspected:
            pygame.draw.aacircle(surface, (255, 200, 80), (ix, iy), r + 5, 2)

        sprite = _sprites.get_sprite(self.class_name, self.team, self.exhausted, self._idle_frame)
        if sprite is not None:
            sw, sh = sprite.get_size()
            surface.blit(sprite, (ix - sw // 2, iy - sh // 2))
        else:
            base = self._base_color()
            dark = self._dark_color()
            self._draw_shape(surface, ix, iy, r, base, dark)

        self._draw_hp_bar(surface, ix, iy, r)

        # Hit flash overlay
        if self.flash_timer > 0:
            fade = self.flash_timer / 0.28
            size = r + 4
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 80, 80, int(160 * fade)), (size, size), size)
            surface.blit(s, (ix - size, iy - size))

    def _draw_shape(self, surface, ix, iy, r, base, dark):
        w = self.weapon
        if w == SWORD:
            pygame.draw.aacircle(surface, base, (ix, iy), r)
            pygame.draw.aacircle(surface, dark, (ix, iy), r, 2)
        elif w == AXE:
            pygame.draw.aacircle(surface, base, (ix, iy), r + 3)
            pygame.draw.aacircle(surface, dark, (ix, iy), r + 3, 2)
        elif w == LANCE:
            rect = pygame.Rect(ix - r, iy - r, r * 2, r * 2)
            pygame.draw.rect(surface, base, rect, border_radius=6)
            pygame.draw.rect(surface, dark, rect, 2, border_radius=6)
        elif w == BOW:
            pygame.draw.aacircle(surface, base, (ix, iy), r - 3)
            pygame.draw.aacircle(surface, dark, (ix, iy), r - 3, 2)
            arc_rect = pygame.Rect(ix - r + 4, iy - r + 4, (r - 4) * 2, (r - 4) * 2)
            pygame.draw.arc(surface, dark, arc_rect, math.pi * 0.2, math.pi * 0.8, 2)
        elif w == MAGIC:
            pts = [(ix, iy - r - 2), (ix + r, iy), (ix, iy + r + 2), (ix - r, iy)]
            pygame.draw.polygon(surface, base, pts)
            pygame.draw.aalines(surface, dark, True, pts)

    def _draw_hp_bar(self, surface, ix, iy, r):
        bar_w = r * 2 + 6
        bar_h = 5
        bx = ix - bar_w // 2
        by = iy - r - 12
        pct = self.hp / self.max_hp

        pygame.draw.rect(surface, (50, 50, 50), (bx, by, bar_w, bar_h))
        fill_w = int(bar_w * pct)
        if fill_w > 0:
            col = HP_HIGH if pct > 0.5 else (HP_MID if pct > 0.25 else HP_LOW)
            pygame.draw.rect(surface, col, (bx, by, fill_w, bar_h))
        pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)

    # ── Range overlays ───────────────────────────────────────────────────────

    def draw_move_range(self, surface):
        _draw_filled_circle(surface, int(self._draw_x), int(self._draw_y), self.mov_radius, MOVE_CIRCLE_COLOR)

    def draw_attack_range(self, surface):
        lo, hi = WEAPON_RANGE[self.weapon]
        ix, iy = int(self._draw_x), int(self._draw_y)
        _draw_filled_circle(surface, ix, iy, hi, ATTACK_RING_COLOR)
        if lo > 0:
            _draw_filled_circle(surface, ix, iy, lo, DEAD_ZONE_COLOR)

    # ── State ────────────────────────────────────────────────────────────────

    def exhaust(self):
        self.exhausted = True
        self.moved     = True

    def refresh(self):
        self.exhausted = False
        self.moved     = False

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        if self.hp == 0:
            self.alive = False
        self.flash_timer = 0.28

    def usable_items(self):
        return [it for it in self.inventory if not it.depleted]

    def drop_items(self):
        """Return non-depleted items to be left on the ground when this unit dies."""
        return [it for it in self.inventory if not it.depleted]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _draw_filled_circle(surface, cx, cy, radius, color):
    if radius <= 0:
        return
    size = radius * 2 + 4
    tmp  = pygame.Surface((size, size), pygame.SRCALPHA)
    tmp.fill((0, 0, 0, 0))
    pygame.draw.circle(tmp, color, (size // 2, size // 2), radius)
    surface.blit(tmp, (cx - size // 2, cy - size // 2))
