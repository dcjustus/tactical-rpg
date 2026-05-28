"""
Visual combat effects: slash, arrow, magic orb + impact flash.
All effects are cosmetic — combat is already resolved before they play.
"""
import math
import random
import pygame
from systems.items import BOW, MAGIC
import systems.sound as sound


class Effect:
    def __init__(self, duration: float):
        self.timer = float(duration)
        self.total = float(duration)
        self.done  = False

    @property
    def t(self) -> float:
        """Progress 0.0 → 1.0"""
        return 1.0 - self.timer / self.total

    def update(self, dt: float):
        self.timer = max(0.0, self.timer - dt)
        if self.timer == 0.0:
            self.done = True

    def draw(self, surface):
        pass


class SlashEffect(Effect):
    """Expanding slash lines radiating from impact point (melee weapons)."""

    def __init__(self, x, y):
        super().__init__(0.38)
        self.x, self.y = float(x), float(y)
        base = random.uniform(0, math.pi)
        self.angles = [base, base + math.pi * 0.4, base - math.pi * 0.4]

    def draw(self, surface):
        p    = self.t
        fade = 1.0 - p
        for i, angle in enumerate(self.angles):
            # Lines start slightly inward and expand outward
            inner = 4 + int(10 * p)
            outer = 12 + int(26 * p)
            x1 = int(self.x + math.cos(angle) * inner)
            y1 = int(self.y + math.sin(angle) * inner)
            x2 = int(self.x + math.cos(angle) * outer)
            y2 = int(self.y + math.sin(angle) * outer)
            thickness = max(1, int(3 * fade))
            bright = int(255 * fade)
            pygame.draw.line(surface, (bright, int(bright * 0.9), 60),
                             (x1, y1), (x2, y2), thickness)


class ArrowEffect(Effect):
    """Arrow projectile flying from attacker to defender."""

    def __init__(self, x1, y1, x2, y2):
        super().__init__(0.38)
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy) or 1.0
        self.ux = dx / dist
        self.uy = dy / dist

    def draw(self, surface):
        p  = self.t
        cx = self.x1 + (self.x2 - self.x1) * p
        cy = self.y1 + (self.y2 - self.y1) * p

        # Shaft
        tail_x = int(cx - self.ux * 14)
        tail_y = int(cy - self.uy * 14)
        pygame.draw.line(surface, (160, 120, 50),
                         (tail_x, tail_y), (int(cx), int(cy)), 2)

        # Arrowhead triangle
        tip   = (int(cx + self.ux * 7),  int(cy + self.uy * 7))
        left  = (int(cx - self.uy * 3 - self.ux * 5),
                 int(cy + self.ux * 3 - self.uy * 5))
        right = (int(cx + self.uy * 3 - self.ux * 5),
                 int(cy - self.ux * 3 - self.uy * 5))
        pygame.draw.polygon(surface, (200, 160, 60), [tip, left, right])


class MagicEffect(Effect):
    """Glowing orb travels from caster, then bursts into particles + ring."""
    TRAVEL = 0.45   # fraction of total duration spent traveling

    def __init__(self, x1, y1, x2, y2):
        super().__init__(0.60)
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        self.particles = [
            (random.uniform(0, 2 * math.pi), random.uniform(0.6, 1.3))
            for _ in range(12)
        ]

    def draw(self, surface):
        p = self.t
        if p < self.TRAVEL:
            # Traveling orb
            tp = p / self.TRAVEL
            cx = int(self.x1 + (self.x2 - self.x1) * tp)
            cy = int(self.y1 + (self.y2 - self.y1) * tp)
            for radius, alpha in ((14, 35), (9, 90), (5, 200)):
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (160, 80, 255, alpha), (radius, radius), radius)
                surface.blit(s, (cx - radius, cy - radius))
        else:
            # Impact burst
            ip   = (p - self.TRAVEL) / (1.0 - self.TRAVEL)
            fade = max(0.0, 1.0 - ip)
            cx, cy = int(self.x2), int(self.y2)

            ring_r = int(45 * ip)
            if ring_r > 1:
                pygame.draw.circle(surface, (180, 100, 255), (cx, cy), ring_r, 2)
                pygame.draw.circle(surface, (220, 160, 255), (cx, cy), max(1, ring_r - 4), 1)

            for angle, speed in self.particles:
                dist = speed * 38 * ip
                px   = int(cx + math.cos(angle) * dist)
                py   = int(cy + math.sin(angle) * dist)
                size = max(1, int(4 * fade))
                pygame.draw.circle(surface, (200, 130, 255), (px, py), size)


class ImpactFlash(Effect):
    """White burst at the defender's position."""

    def __init__(self, x, y, delay=0.0):
        super().__init__(0.22)
        self.x, self.y = int(x), int(y)
        self._delay = delay
        self._started = delay == 0.0

    def update(self, dt):
        if not self._started:
            self._delay -= dt
            if self._delay <= 0:
                self._started = True
            return
        super().update(dt)

    def draw(self, surface):
        if not self._started:
            return
        fade = max(0.0, 1.0 - self.t)
        size = max(1, int(24 * fade + 4))
        a    = int(200 * fade)
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 210, a), (size, size), size)
        surface.blit(s, (self.x - size, self.y - size))


def create_combat_effects(attacker, defender) -> list:
    """Return Effect list for a combat exchange."""
    ax, ay = int(attacker.x), int(attacker.y)
    dx, dy = int(defender.x), int(defender.y)
    effects = []

    if attacker.weapon == BOW:
        effects.append(ArrowEffect(ax, ay, dx, dy))
        effects.append(ImpactFlash(dx, dy, delay=0.32))
    elif attacker.weapon == MAGIC:
        effects.append(MagicEffect(ax, ay, dx, dy))
        effects.append(ImpactFlash(dx, dy, delay=0.28))
    else:
        effects.append(SlashEffect(dx, dy))
        effects.append(ImpactFlash(dx, dy, delay=0.0))

    sound.play_for_weapon(attacker.weapon)
    sound.play_grunt()
    return effects
