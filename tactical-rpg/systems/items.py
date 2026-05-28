import random
import math

# Weapon types
SWORD  = "Sword"
AXE    = "Axe"
LANCE  = "Lance"
BOW    = "Bow"
MAGIC  = "Magic"

# Weapon triangle: key beats value
TRIANGLE = {
    SWORD: AXE,
    AXE:   LANCE,
    LANCE: SWORD,
}

def weapon_triangle_bonus(atk_weapon, def_weapon):
    """Return +bonus, 0, or -bonus to ATK. Magic/Bow are neutral."""
    from core.constants import WEAPON_TRIANGLE_BONUS
    if atk_weapon in (BOW, MAGIC) or def_weapon in (BOW, MAGIC):
        return 0
    if TRIANGLE.get(atk_weapon) == def_weapon:
        return WEAPON_TRIANGLE_BONUS
    if TRIANGLE.get(def_weapon) == atk_weapon:
        return -WEAPON_TRIANGLE_BONUS
    return 0

def weapon_triangle_hit_mod(atk_weapon, def_weapon):
    """Return +10, 0, or -10 hit% modifier based on triangle. Magic/Bow neutral."""
    if atk_weapon in (BOW, MAGIC) or def_weapon in (BOW, MAGIC):
        return 0
    if TRIANGLE.get(atk_weapon) == def_weapon:
        return 10
    if TRIANGLE.get(def_weapon) == atk_weapon:
        return -10
    return 0

def weapon_triangle_crit_mod(atk_weapon, def_weapon):
    """Return +5, 0, or -5 crit% modifier based on triangle. Magic/Bow neutral."""
    if atk_weapon in (BOW, MAGIC) or def_weapon in (BOW, MAGIC):
        return 0
    if TRIANGLE.get(atk_weapon) == def_weapon:
        return 5
    if TRIANGLE.get(def_weapon) == atk_weapon:
        return -5
    return 0

# Attack range definitions: (min_px, max_px)
WEAPON_RANGE = {
    SWORD: (0,  65),
    AXE:   (0,  70),
    LANCE: (0,  75),
    BOW:   (80, 160),   # dead zone: cannot attack within 80 px
    MAGIC: (0,  150),   # full range
}

def in_attack_range(weapon, dist):
    lo, hi = WEAPON_RANGE[weapon]
    return lo <= dist <= hi

# ── Items ────────────────────────────────────────────────────────────────────

class Item:
    """
    Flexible item supporting HP healing and/or a single permanent stat buff.
    Stat buffs are applied directly to the unit for the remainder of the battle.
    """
    def __init__(self, name, heal_pct=0.0, buff_stat=None, buff_amount=0, uses=1):
        self.name        = name
        self.heal_pct    = heal_pct
        self.buff_stat   = buff_stat      # 'strength', 'defense', 'intelligence', 'resistance'
        self.buff_amount = buff_amount
        self.uses        = uses
        self.max_uses    = uses

    def use(self, unit):
        if self.uses <= 0:
            return f"{unit.name} has no {self.name} left!"
        self.uses -= 1
        parts = []
        if self.heal_pct > 0:
            restore = int(unit.max_hp * self.heal_pct)
            unit.hp = min(unit.max_hp, unit.hp + restore)
            parts.append(f"+{restore} HP")
        if self.buff_stat and self.buff_amount:
            cur = getattr(unit, self.buff_stat)
            setattr(unit, self.buff_stat, cur + self.buff_amount)
            parts.append(f"+{self.buff_amount} {self.buff_stat.title()}")
        return f"{unit.name} used {self.name} ({', '.join(parts)})"

    @property
    def depleted(self):
        return self.uses <= 0

    def __repr__(self):
        return f"{self.name} ({self.uses}/{self.max_uses})"

    def clone(self):
        it = Item(self.name, self.heal_pct, self.buff_stat, self.buff_amount, self.uses)
        it.max_uses = self.max_uses
        return it


# Regular consumable pool (starting inventories — healing only)
CONSUMABLE_POOL = [
    lambda: Item("Heal Potion", heal_pct=0.25, uses=1),
    lambda: Item("Elixir",      heal_pct=0.50, uses=1),
    lambda: Item("Vulnerary",   heal_pct=0.15, uses=2),
]

# Special pool (chest rewards — tonics + better heals)
CHEST_POOL = [
    lambda: Item("Str Tonic",  buff_stat="strength",     buff_amount=4, uses=1),
    lambda: Item("Def Tonic",  buff_stat="defense",      buff_amount=4, uses=1),
    lambda: Item("Int Tonic",  buff_stat="intelligence", buff_amount=4, uses=1),
    lambda: Item("Res Tonic",  buff_stat="resistance",   buff_amount=4, uses=1),
    lambda: Item("Mega Potion", heal_pct=0.40, uses=1),
    lambda: Item("Elixir",     heal_pct=0.50, uses=1),
]

def random_inventory(count=None):
    if count is None:
        count = random.randint(0, 2)
    return [random.choice(CONSUMABLE_POOL)() for _ in range(count)]

def random_chest_item():
    return random.choice(CHEST_POOL)()


# ── Ground items (dropped by defeated units / from chests) ────────────────────

class GroundItem:
    PICKUP_RADIUS = 48

    def __init__(self, x, y, item):
        self.x    = float(x)
        self.y    = float(y)
        self.item = item

    def in_pickup_range(self, unit):
        return math.hypot(unit.x - self.x, unit.y - self.y) <= self.PICKUP_RADIUS

    def draw(self, surface):
        import pygame
        ix, iy = int(self.x), int(self.y)
        # Small golden diamond
        size = 8
        pts = [(ix, iy - size), (ix + size, iy), (ix, iy + size), (ix - size, iy)]
        pygame.draw.polygon(surface, (220, 180, 40), pts)
        pygame.draw.polygon(surface, (255, 220, 80), pts, 1)
        import core.constants as C
        if C.FONT_SM:
            lbl = C.FONT_SM.render(self.item.name[0], True, (255, 255, 200))
            surface.blit(lbl, lbl.get_rect(center=(ix, iy)))
