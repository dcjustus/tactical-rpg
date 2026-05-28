"""
Sound effect system. Loads MP3s from assets/sounds/ and plays them on game events.
Falls back silently if files are missing or the mixer is unavailable (e.g. browser).
"""
import os
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
    """Initialise the mixer and pre-load all sound files."""
    global _ready
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _ready = True
        _load_all()
    except Exception:
        _ready = False


def _load_all():
    entries = {
        'slash':    'slash.mp3',
        'strike':   'strike.mp3',
        'swing':    'swing.mp3',
        'magic':    'magic.mp3',
        'movement': 'movement.mp3',
        'arrow':    'arrow.mp3',
    }
    for key, filename in entries.items():
        path = os.path.join(_SOUNDS_DIR, filename)
        if os.path.isfile(path):
            try:
                _sounds[key] = pygame.mixer.Sound(path)
            except Exception:
                pass  # placeholder or corrupt file — skip silently


def play(name: str):
    """Play a sound by key name. No-ops if the sound is absent or mixer failed."""
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
