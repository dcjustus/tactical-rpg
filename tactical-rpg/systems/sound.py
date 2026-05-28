"""
Sound effect and music system.
SFX use pygame.mixer.Sound (pre-loaded, low latency).
Music uses pygame.mixer.music (streamed, one track at a time).
Everything falls back silently if the mixer is unavailable (e.g. browser).
"""
import os
import random
import pygame

from systems.items import SWORD, AXE, LANCE, BOW, MAGIC

_SOUNDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')

_sounds: dict = {}
_ready = False
_movement_channel = None   # tracks the looping movement sound so it can be stopped

# Map weapon type → sound key
_WEAPON_SOUND = {
    SWORD: 'slash',
    AXE:   'swing',
    LANCE: 'strike',
    BOW:   'arrow',
    MAGIC: 'magic',
}


def init():
    """Initialise the mixer and pre-load all SFX files."""
    global _ready
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _ready = True
        _load_all()
    except Exception:
        _ready = False


def _load_all():
    sfx_files = {
        'slash':     'slash.mp3',
        'strike':    'strike.mp3',
        'swing':     'swing.mp3',
        'magic':     'magic.mp3',
        'movement':  'movement.mp3',
        'arrow':     'arrow.mp3',
        'death':     'death.mp3',
        'grunt_1':   'grunt 1.mp3',
        'grunt_2':   'grunt 2.mp3',
        'ui_button': 'ui button.mp3',
    }
    for key, filename in sfx_files.items():
        path = os.path.join(_SOUNDS_DIR, filename)
        if os.path.isfile(path):
            try:
                _sounds[key] = pygame.mixer.Sound(path)
            except Exception:
                pass  # placeholder or corrupt file — skip silently


# ── SFX ──────────────────────────────────────────────────────────────────────

def play(name: str):
    """Play a sound effect by key name. No-ops if absent or mixer failed."""
    if not _ready:
        return
    snd = _sounds.get(name)
    if snd:
        try:
            snd.play()
        except Exception:
            pass


def play_for_weapon(weapon: str):
    """Play the combat sound appropriate for the given weapon type."""
    play(_WEAPON_SOUND.get(weapon, 'slash'))


def play_grunt():
    """Play a random grunt SFX (grunt_1 or grunt_2) for the attacking unit."""
    play(random.choice(['grunt_1', 'grunt_2']))


def play_movement():
    """Start the movement sound looping. Call stop_movement() when the unit arrives."""
    global _movement_channel
    if not _ready:
        return
    snd = _sounds.get('movement')
    if snd:
        try:
            _movement_channel = snd.play(loops=-1)
        except Exception:
            pass


def stop_movement():
    """Stop the looping movement sound."""
    global _movement_channel
    if _movement_channel is not None:
        try:
            _movement_channel.stop()
        except Exception:
            pass
        _movement_channel = None


# ── Music ─────────────────────────────────────────────────────────────────────

def play_music(name: str, loops: int = -1):
    """
    Load and play a music track from assets/sounds/.
    loops=-1 loops indefinitely; loops=0 plays once.
    Silently no-ops if the file is missing or unreadable.
    """
    if not _ready:
        return
    path = os.path.join(_SOUNDS_DIR, f'{name}.mp3')
    if not os.path.isfile(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(loops)
    except Exception:
        pass


def stop_music():
    """Stop any currently playing music track."""
    if not _ready:
        return
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
