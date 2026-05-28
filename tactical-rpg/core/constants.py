import pygame
import pygame.freetype as _ft

# --- Screen ---
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "Tactical RPG Demo"

# --- Colors ---
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_GRAY   = (40,  40,  40)
MID_GRAY    = (90,  90,  90)
LIGHT_GRAY  = (180, 180, 180)

ALLY_COLOR        = (70,  130, 200)
ALLY_DARK         = (30,  70,  130)
ENEMY_COLOR       = (200, 60,  60)
ENEMY_DARK        = (120, 20,  20)
EXHAUSTED_TINT    = (100, 100, 110)

MOVE_CIRCLE_COLOR = (80,  140, 220, 60)   # blue, semi-transparent
ATTACK_RING_COLOR = (220, 60,  60,  60)   # red, semi-transparent
DEAD_ZONE_COLOR   = (60,  60,  60,  80)   # dark, dead zone overlay

HP_HIGH   = (50,  200, 80)
HP_MID    = (220, 200, 40)
HP_LOW    = (220, 50,  50)

UI_BG         = (20,  20,  30)
UI_BORDER     = (80,  80,  100)
UI_HIGHLIGHT  = (60,  80,  140)
UI_TEXT       = (230, 230, 230)
UI_TEXT_DIM   = (140, 140, 160)

PANEL_W = 240
PANEL_H = 330

# --- Unit sizing ---
UNIT_RADIUS = 20   # base draw radius

# --- Movement ---
MOV_SCALE = 50     # pixels per 1 point of MOV stat  (MOV 5 = 250 px)

# --- Combat ---
WEAPON_TRIANGLE_BONUS   = 3    # ATK bonus for advantage / penalty for disadvantage
WEAPON_TRIANGLE_HIT_MOD = 10   # hit% modifier for advantage / disadvantage
BASE_HIT_RATE           = 90   # base accuracy %
DOUBLE_ATTACK_THRESHOLD = 1.4  # attacker.speed >= defender.speed * this → double hit
BASE_CRIT_CHANCE        = 10   # base crit % (all classes except Mage; Mage = 0)
CRIT_TRIANGLE_MOD       = 5    # crit% ±modifier for weapon triangle advantage/disadvantage

# --- Unit animation ---
UNIT_ANIM_SPEED    = 500.0   # pixels per second for movement glide
HIT_FLASH_DURATION = 0.28    # seconds the red hit flash remains visible

# --- AI ---
AI_HEAL_THRESHOLD   = 0.30   # heal if HP/max_HP falls below this fraction
AI_ATTACK_MARGIN    = 5      # px inside weapon range the AI targets when repositioning

# --- Loot ---
ITEM_DROP_CHANCE = 0.30      # probability each dropped item goes directly to the killer

# --- Level & EXP system ---
EXP_PER_LEVEL    = 100   # EXP required for each level up
EXP_FOR_HIT      = 10    # EXP awarded to attacker for each successful hit
EXP_FOR_KILL     = 40    # bonus EXP awarded on top of EXP_FOR_HIT when a kill occurs
SPAWN_LEVEL_MIN  = 1     # minimum unit level at the start of a battle
SPAWN_LEVEL_MAX  = 10    # maximum unit level at the start of a battle
LEVEL_CAP        = 20    # units stop gaining EXP / levels at this point

# --- Stat modifier on spawn ---
# Each stat gets an independent flat random offset in [-STAT_MODIFIER_RANGE, +STAT_MODIFIER_RANGE].
# This replaces the old ±15% percentage variance with a tighter, flat spread.
STAT_MODIFIER_RANGE = 3

# --- Terrain gameplay ---
# Trees count as Forest; rocks count as Hills.
# evasion: % subtracted from attacker's hit chance when defender is in this terrain.
# move_cost: extra pixels consumed from movement budget when path crosses this terrain.
# Mages are exempt from move_cost penalties.
TERRAIN_DEFS = {
    "tree": {"evasion": 15, "move_cost": 50, "label": "Forest"},
    "rock": {"evasion": 10, "move_cost": 25, "label": "Hills"},
}
MAX_TERRAIN_EVASION = 30     # cap so stacked terrain never makes a unit unhittable

# --- Enemy AI ---
AI_STEP_DELAY = 0.45        # seconds between each enemy acting

# --- Fonts (loaded at runtime) ---
FONT_SM         = None
FONT_MD         = None
FONT_LG         = None
FONT_XL         = None
FONT_UNIT_BADGE = None   # pygame.font.SysFont for unit weapon-class badges


class _FTFont:
    """
    Wraps pygame.freetype.Font to match the pygame.font.Font.render() interface.
    freetype renders against a transparent background, eliminating the dark-halo
    blurriness that pygame.font produces at small sizes.
    """
    def __init__(self, ft_font):
        self._f = ft_font

    def render(self, text, antialias, color):
        self._f.antialiased = bool(antialias)
        surf, _ = self._f.render(str(text), color)
        return surf


def _make_ft(size, bold=False):
    _ft.init()
    for name in ["calibri", "segoeui", "tahoma", "arial"]:
        try:
            return _FTFont(_ft.SysFont(name, size, bold=bold))
        except Exception:
            pass
    return _FTFont(_ft.Font(None, size))


def load_fonts():
    global FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_UNIT_BADGE
    FONT_SM = _make_ft(13)
    FONT_MD = _make_ft(16)
    FONT_LG = _make_ft(22, bold=True)
    FONT_XL = _make_ft(52, bold=True)
    pygame.font.init()
    FONT_UNIT_BADGE = pygame.font.SysFont("calibri", 13, bold=True)
