"""
Entry point. Pygbag-compatible: uses asyncio + await asyncio.sleep(0) each frame.
Run locally:  python main.py
Build web:    python -m pygbag --title "FE:Lite" --disable-sound-format-error --build .
              (run from inside the project folder, then open http://localhost:8000)
              Note: audio is disabled in the web build (MP3 unsupported by Pygbag bundler).
"""
import asyncio
import pygame
from core.constants import SCREEN_W, SCREEN_H, FPS, TITLE, load_fonts
from core.game import Game
import systems.sound as sound
import systems.sprites as sprites


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()
    load_fonts()
    sound.init()
    sprites.init_sprites()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # seconds since last frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

        await asyncio.sleep(0)   # yield to browser event loop (required by Pygbag)

    pygame.quit()


asyncio.run(main())
