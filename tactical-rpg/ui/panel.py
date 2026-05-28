"""
Side panel showing selected unit's full stat block and inventory.
"""
import pygame
import core.constants as C
from core.constants import (
    SCREEN_W, SCREEN_H, PANEL_W, PANEL_H,
    UI_BG, UI_BORDER, UI_TEXT, UI_TEXT_DIM, UI_HIGHLIGHT,
    ALLY_COLOR, ENEMY_COLOR, WHITE,
    HP_HIGH, HP_MID, HP_LOW,
    EXP_PER_LEVEL, LEVEL_CAP,
)
from systems.items import MAGIC, BOW

PANEL_X = SCREEN_W - PANEL_W - 8
PANEL_Y = 44
MAX_ITEMS_SHOWN = 4

# Colour for the EXP progress bar
_EXP_BAR_COLOR = (80, 160, 255)


def _range_label(weapon):
    if weapon == BOW:
        return "Ranged only  (no close-range)"
    if weapon == MAGIC:
        return "Any range  (melee & ranged)"
    return "Melee range"


def _mov_label(mov):
    labels = {3: "Short", 4: "Medium", 5: "Long", 6: "Very long"}
    return labels.get(mov, str(mov))


def draw_unit_panel(surface, unit):
    if unit is None:
        return

    rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    pygame.draw.rect(surface, UI_BG, rect, border_radius=6)
    pygame.draw.rect(surface, UI_BORDER, rect, 1, border_radius=6)

    x  = PANEL_X + 10
    y  = PANEL_Y + 9
    rw = PANEL_W - 20

    # Name + team colour
    name_col = ALLY_COLOR if unit.team == "ally" else ENEMY_COLOR
    _blit(surface, C.FONT_MD, unit.name, name_col, x, y);  y += 20

    # Class · Weapon
    _blit(surface, C.FONT_SM, f"{unit.class_name}  ·  {unit.weapon}", UI_TEXT_DIM, x, y); y += 13

    # Level + EXP bar
    if unit.level >= LEVEL_CAP:
        _blit(surface, C.FONT_SM, f"Lv.{unit.level}  (MAX)", UI_TEXT_DIM, x, y); y += 13
    else:
        _blit(surface, C.FONT_SM, f"Lv.{unit.level}  EXP: {unit.exp}/{EXP_PER_LEVEL}", UI_TEXT_DIM, x, y); y += 12
        pygame.draw.rect(surface, (50, 50, 50), (x, y, rw, 4))
        exp_w = int(rw * unit.exp / EXP_PER_LEVEL)
        if exp_w > 0:
            pygame.draw.rect(surface, _EXP_BAR_COLOR, (x, y, exp_w, 4))
        pygame.draw.rect(surface, WHITE, (x, y, rw, 4), 1)
        y += 8

    # Attack range (plain language)
    _blit(surface, C.FONT_SM, _range_label(unit.weapon), UI_TEXT_DIM, x, y); y += 11

    _divider(surface, x, y, rw); y += 7

    # HP bar
    _blit(surface, C.FONT_SM, "HP", UI_TEXT_DIM, x, y)
    _blit(surface, C.FONT_SM, f"{unit.hp} / {unit.max_hp}", UI_TEXT, x + 30, y); y += 13
    bw  = rw
    pct = unit.hp / unit.max_hp
    pygame.draw.rect(surface, (50, 50, 50), (x, y, bw, 6))
    fw  = int(bw * pct)
    col = HP_HIGH if pct > 0.5 else (HP_MID if pct > 0.25 else HP_LOW)
    if fw:
        pygame.draw.rect(surface, col, (x, y, fw, 6))
    pygame.draw.rect(surface, WHITE, (x, y, bw, 6), 1)
    y += 10

    _divider(surface, x, y, rw); y += 7

    # Stats — two columns
    col2 = x + 118
    _blit(surface, C.FONT_SM, "Physical", UI_TEXT_DIM, x,    y)
    _blit(surface, C.FONT_SM, "Magical",  UI_TEXT_DIM, col2, y); y += 13

    phys = [("STR", unit.strength), ("DEF", unit.defense),
            ("SPD", unit.speed),    ("MOV", _mov_label(unit.movement))]
    mag  = [("INT", unit.intelligence), ("RES", unit.resistance)]

    for i, (lbl, val) in enumerate(phys):
        _blit(surface, C.FONT_SM, f"{lbl}:", UI_TEXT_DIM, x,      y + i * 14)
        _blit(surface, C.FONT_SM, str(val),  UI_TEXT,     x + 28, y + i * 14)

    for i, (lbl, val) in enumerate(mag):
        _blit(surface, C.FONT_SM, f"{lbl}:", UI_TEXT_DIM, col2,      y + i * 14)
        _blit(surface, C.FONT_SM, str(val),  UI_TEXT,     col2 + 28, y + i * 14)

    y += max(len(phys), len(mag)) * 14 + 3

    _divider(surface, x, y, rw); y += 7

    # Inventory
    _blit(surface, C.FONT_SM, "Inventory:", UI_TEXT_DIM, x, y); y += 13
    items = unit.inventory
    shown = items[:MAX_ITEMS_SHOWN]
    extra = len(items) - MAX_ITEMS_SHOWN

    if not items:
        _blit(surface, C.FONT_SM, "  (none)", UI_TEXT_DIM, x, y)
    else:
        for it in shown:
            col_t = UI_TEXT if not it.depleted else UI_TEXT_DIM
            if it.buff_stat:
                label = f"  {it.name}  +{it.buff_amount} {it.buff_stat[:3].title()}"
            elif it.heal_pct > 0:
                label = f"  {it.name}  [{it.uses}/{it.max_uses}]"
            else:
                label = f"  {it.name}"
            _blit(surface, C.FONT_SM, label, col_t, x, y); y += 13
        if extra > 0:
            _blit(surface, C.FONT_SM, f"  +{extra} more...", UI_TEXT_DIM, x, y)


def _blit(surface, font, text, color, x, y):
    surface.blit(font.render(text, True, color), (x, y))

def _divider(surface, x, y, w):
    pygame.draw.line(surface, UI_BORDER, (x, y), (x + w, y))
