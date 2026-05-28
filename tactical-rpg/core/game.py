"""
Main game class. Manages state machine, input routing, rendering.
"""
import math
import random
import pygame
import core.constants as C
from core.constants import (
    SCREEN_W, SCREEN_H, FPS, UI_BG, WHITE, BLACK, DARK_GRAY,
    ALLY_COLOR, ENEMY_COLOR, MOVE_CIRCLE_COLOR,
)
from battlefield.battlefield import generate_battlefield
from systems.combat import resolve_combat
from systems.movement import clamp_to_radius, point_in_circle
from systems.ai import ai_move
from systems.items import GroundItem
from systems.effects import create_combat_effects
import systems.sound as sound
from entities import names as _names
from ui.hud import HUD
from ui.panel import draw_unit_panel
from ui.action_menu import ActionMenu, ItemMenu

# ── Player turn sub-states ────────────────────────────────────────────────────
S_SELECT    = "select"
S_MOVE      = "move"
S_MOVING    = "moving"   # unit animating to destination; input blocked
S_ACTION    = "action"
S_ATTACK    = "attack"
S_ITEM_MENU = "item_menu"


class Game:
    def __init__(self, surface):
        self.surface = surface
        self.state   = "title"
        self._reset()

    def _reset(self):
        _names.reset()
        self.allies, self.enemies, self.terrain, self.chests = generate_battlefield()
        self.ground_items = []
        self.effects      = []
        self.hud          = HUD()
        self.turn_num     = 1
        self.phase        = "player"
        self.selected     = None
        self.inspected    = None      # enemy being viewed (no control)
        self.sub_state    = S_SELECT
        self.action_menu  = None
        self.item_menu    = None
        self._pre_move_pos  = None
        self._pending_extra = []      # chest options stored during S_MOVING
        self._ai_queue          = []
        self._ai_timer          = 0.0
        self._ai_delay          = 0.5   # seconds between enemies after animation+combat finish
        self._ai_pending_attack = None  # (enemy, target) waiting for move anim to complete
        self._ai_moving_unit    = None  # enemy currently animating (no pending attack)
        self._bg_color    = (22, 28, 18)
        sound.stop_movement()
        sound.play_music('menu_music')

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        # Tick all visual effects
        self.effects = [e for e in self.effects if not e.done]
        for e in self.effects:
            e.update(dt)

        # Advance unit movement animations
        for unit in self.allies + self.enemies:
            unit.update_anim(dt)

        # Decay unit hit-flash timers
        for unit in self.allies + self.enemies:
            if unit.flash_timer > 0:
                unit.flash_timer = max(0.0, unit.flash_timer - dt)

        # When the player's unit finishes moving, open the action menu
        if (self.state == "battle" and self.phase == "player"
                and self.sub_state == S_MOVING and self.selected):
            if not self.selected.is_moving:
                sound.stop_movement()
                unit = self.selected
                self._pickup_ground_items(unit)
                self.action_menu = ActionMenu(unit, int(unit.x), int(unit.y),
                                              extra=self._pending_extra)
                self._pending_extra = []
                self.sub_state = S_ACTION

        if self.state == "battle" and self.phase == "enemy":
            self._update_ai(dt)
        self._check_win_loss()

    def _update_ai(self, dt):
        # Stop movement sound when a non-attacking enemy finishes its animation
        if self._ai_moving_unit is not None and not self._ai_moving_unit.is_moving:
            sound.stop_movement()
            self._ai_moving_unit = None

        # ── Phase 2: resolve combat once movement animation has finished ────────
        if self._ai_pending_attack is not None:
            enemy, target = self._ai_pending_attack
            if enemy.is_moving:
                return  # still animating — wait
            sound.stop_movement()
            self._ai_pending_attack = None
            # Resolve combat at the unit's arrived position
            if target.alive and enemy.can_attack(target):
                log = resolve_combat(enemy, target)
                for line in log:
                    self.hud.push_log(line)
                self.effects.extend(create_combat_effects(enemy, target))
            dead_allies = [a for a in self.allies if not a.alive]
            if dead_allies or not enemy.alive:
                sound.play('death')
            for a in dead_allies:
                self._drop_items_from(a, killer=enemy)
            self.allies = [a for a in self.allies if a.alive]
            self._pickup_ground_items(enemy)
            enemy.exhaust()
            return  # timer resets from 0 after this — _ai_delay before next enemy

        # ── Phase 1: wait for delay, then move the next enemy ─────────────────
        if not self._ai_queue:
            self._begin_player_phase()
            return
        self._ai_timer += dt
        if self._ai_timer < self._ai_delay:
            return
        self._ai_timer = 0.0

        enemy = self._ai_queue.pop(0)
        if not enemy.alive:
            return

        log, attack_target = ai_move(enemy, self.allies)
        for line in log:
            self.hud.push_log(line)

        if attack_target is not None:
            if enemy.is_moving:
                # Unit animated toward target — defer combat until arrival
                sound.play_movement()
                self._ai_pending_attack = (enemy, attack_target)
            else:
                # Already in range, no movement needed — attack right away
                if attack_target.alive:
                    log = resolve_combat(enemy, attack_target)
                    for line in log:
                        self.hud.push_log(line)
                    self.effects.extend(create_combat_effects(enemy, attack_target))
                dead_allies = [a for a in self.allies if not a.alive]
                if dead_allies or not enemy.alive:
                    sound.play('death')
                for a in dead_allies:
                    self._drop_items_from(a, killer=enemy)
                self.allies = [a for a in self.allies if a.alive]
                self._pickup_ground_items(enemy)
                enemy.exhaust()
        elif enemy.is_moving:
            # Enemy moved but couldn't reach a target — track for sound stop
            sound.play_movement()
            self._ai_moving_unit = enemy

    def _check_win_loss(self):
        if self.state != "battle":
            return
        if not any(e.alive for e in self.enemies):
            sound.stop_music()
            sound.play_music('victory', loops=0)
            self.state = "victory"
        elif not any(a.alive for a in self.allies):
            sound.stop_music()
            sound.play_music('defeat', loops=0)
            self.state = "defeat"

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.state == "title":
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.state = "battle"
                sound.play_music('battle_music')
            return

        if self.state in ("victory", "defeat"):
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._reset()
                self.state = "title"
            return

        if self.state == "battle" and self.phase == "player":
            self._handle_player_input(event)

    def _handle_player_input(self, event):
        if self.sub_state == S_MOVING:
            return  # block all input while unit is animating

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            if self.sub_state == S_ACTION and self.action_menu:
                result = self.action_menu.handle_event(event)
                self._process_action_choice(result)
            elif self.sub_state == S_ITEM_MENU and self.item_menu:
                result = self.item_menu.handle_event(event)
                self._process_item_choice(result)
            return

        mx, my = event.pos

        if self.sub_state == S_SELECT:
            self._try_select(mx, my)
        elif self.sub_state == S_MOVE:
            self._try_move(mx, my)
        elif self.sub_state == S_ACTION:
            if self.action_menu:
                result = self.action_menu.handle_event(event)
                self._process_action_choice(result)
        elif self.sub_state == S_ITEM_MENU:
            if self.item_menu:
                result = self.item_menu.handle_event(event)
                self._process_item_choice(result)
        elif self.sub_state == S_ATTACK:
            self._try_attack(mx, my)

    def _try_select(self, mx, my):
        # Try to select a ready ally first
        for unit in self.allies:
            if not unit.alive or unit.exhausted:
                continue
            if point_in_circle(mx, my, unit.x, unit.y, 24):
                self.selected  = unit
                self.inspected = None
                self.sub_state = S_MOVE
                return
        # Try to inspect an enemy (view-only — no control)
        for unit in self.enemies:
            if not unit.alive:
                continue
            if point_in_circle(mx, my, unit.x, unit.y, 24):
                self.inspected = unit
                return
        # Click on empty space — deselect / stop inspecting
        self.selected  = None
        self.inspected = None

    def _try_move(self, mx, my):
        unit = self.selected
        if unit is None:
            self.sub_state = S_SELECT
            return

        # Click another idle ally → re-select
        for other in self.allies:
            if other is unit or not other.alive or other.exhausted:
                continue
            if point_in_circle(mx, my, other.x, other.y, 24):
                self.selected  = other
                self.sub_state = S_MOVE
                return

        # Click outside move range → deselect
        if not point_in_circle(mx, my, unit.x, unit.y, unit.mov_radius):
            self.selected  = None
            self.sub_state = S_SELECT
            return

        # Save position for potential undo
        self._pre_move_pos = (unit.x, unit.y)

        # Update logical position (visual position animates to match in update())
        nx, ny = clamp_to_radius(unit.x, unit.y, mx, my, unit.mov_radius)
        unit.x, unit.y = nx, ny
        unit.moved = True
        sound.play_movement()

        # Check for nearby chests at destination (ground pickup deferred to after anim)
        extra = []
        for chest in self.chests:
            if not chest.opened and chest.in_range(unit):
                extra = ["Open Chest"]
                break
        self._pending_extra = extra

        self.sub_state = S_MOVING

    def _process_action_choice(self, result):
        if result is None:
            return
        unit = self.selected

        if result == "Attack":
            self.action_menu = None
            self.sub_state   = S_ATTACK

        elif result == "Item":
            self.action_menu = None
            self.item_menu   = ItemMenu(unit, int(unit.x), int(unit.y))
            self.sub_state   = S_ITEM_MENU

        elif result == "Open Chest":
            for chest in self.chests:
                if not chest.opened and chest.in_range(unit):
                    chest.opened = True
                    unit.inventory.append(chest.item)
                    self.hud.push_log(f"{unit.name} opens a chest — found {chest.item.name}!")
                    break
            unit.exhaust()
            self._finish_turn()

        elif result == "Back":
            # Undo the move — snap back instantly (no animation)
            if self._pre_move_pos:
                unit.teleport_to(*self._pre_move_pos)
                unit.moved = False
            self.action_menu   = None
            self._pre_move_pos = None
            self.sub_state     = S_MOVE

        elif result == "Wait":
            unit.exhaust()
            self._finish_turn()

        elif result == "close":
            # Clicked outside menu — keep menu open
            pass

    def _process_item_choice(self, result):
        unit = self.selected
        if result is None:
            return  # unhandled key — keep item menu open
        if result == "back":
            self.item_menu   = None
            self.action_menu = self._build_action_menu(unit)
            self.sub_state   = S_ACTION
            return
        msg = result.use(unit)
        self.hud.push_log(msg)
        self.item_menu = None
        unit.exhaust()
        self._finish_turn()

    def _try_attack(self, mx, my):
        unit = self.selected
        if unit is None:
            self.sub_state = S_SELECT
            return

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if point_in_circle(mx, my, enemy.x, enemy.y, 24):
                if unit.can_attack(enemy):
                    self.effects.extend(create_combat_effects(unit, enemy))
                    log = resolve_combat(unit, enemy)
                    for line in log:
                        self.hud.push_log(line)
                    dead_enemies = [e for e in self.enemies if not e.alive]
                    dead_allies  = [a for a in self.allies  if not a.alive]
                    if dead_enemies or dead_allies:
                        sound.play('death')
                    for e in dead_enemies:
                        self._drop_items_from(e, killer=unit)
                    self.enemies = [e for e in self.enemies if e.alive]
                    # Drop items for any ally killed by counter-attack
                    for a in dead_allies:
                        self._drop_items_from(a, killer=enemy)
                    self.allies = [a for a in self.allies if a.alive]
                    unit.exhaust()
                    self._finish_turn()
                    return
                else:
                    self.hud.push_log(f"{enemy.name} is out of range.")
                    return

        # Clicked empty space → cancel attack, reopen menu
        self.sub_state   = S_ACTION
        self.action_menu = self._build_action_menu(unit)

    def _build_action_menu(self, unit):
        """Build an ActionMenu for unit, including Open Chest if one is in range."""
        extra = []
        for chest in self.chests:
            if not chest.opened and chest.in_range(unit):
                extra = ["Open Chest"]
                break
        return ActionMenu(unit, int(unit.x), int(unit.y), extra=extra)

    def _finish_turn(self):
        self.selected      = None
        self.action_menu   = None
        self.item_menu     = None
        self._pre_move_pos = None
        self.sub_state     = S_SELECT

        if all(not a.alive or a.exhausted for a in self.allies):
            self._begin_enemy_phase()

    def _begin_enemy_phase(self):
        self.phase     = "enemy"
        self.hud.push_log("--- Enemy Phase ---")
        self._ai_queue = [e for e in self.enemies if e.alive]
        self._ai_timer = 0.0

    def _begin_player_phase(self):
        sound.stop_movement()   # safety: catches the last-enemy-still-moving bug
        self.phase    = "player"
        self.turn_num += 1
        for unit in self.allies + self.enemies:
            unit.refresh()
        self.sub_state = S_SELECT
        self.hud.push_log(f"--- Player Phase (Turn {self.turn_num}) ---")

    # ── Loot helpers ──────────────────────────────────────────────────────────

    def _drop_items_from(self, unit, killer=None):
        """Scatter unit's non-depleted items; 30% chance each goes straight to killer."""
        for it in unit.drop_items():
            if killer is not None and random.random() < 0.30:
                killer.inventory.append(it)
                self.hud.push_log(f"  {it.name} claimed by {killer.name}!")
            else:
                self.ground_items.append(GroundItem(unit.x, unit.y, it))
                self.hud.push_log(f"  {it.name} dropped!")

    def _pickup_ground_items(self, unit):
        remaining = []
        for gi in self.ground_items:
            if gi.in_pickup_range(unit):
                unit.inventory.append(gi.item)
                self.hud.push_log(f"{unit.name} picks up {gi.item.name}!")
            else:
                remaining.append(gi)
        self.ground_items = remaining

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self):
        self.surface.fill(self._bg_color)

        if self.state == "title":
            self._draw_title()
            return
        if self.state == "victory":
            self._draw_end("VICTORY!", ALLY_COLOR)
            return
        if self.state == "defeat":
            self._draw_end("DEFEAT", ENEMY_COLOR)
            return

        # Terrain
        for piece in self.terrain:
            piece.draw(self.surface)

        # Chests
        for chest in self.chests:
            chest.draw(self.surface)

        # Ground items
        for gi in self.ground_items:
            gi.draw(self.surface)

        # Range overlays
        if self.selected and self.sub_state == S_MOVE:
            self.selected.draw_move_range(self.surface)
        if self.selected:
            # Show attack range whenever a unit is selected
            self.selected.draw_attack_range(self.surface)
        # Show inspected enemy's attack range so the player can see their threat
        if self.inspected and self.inspected.alive and self.sub_state == S_SELECT:
            self.inspected.draw_attack_range(self.surface)

        # Units
        for unit in self.allies + self.enemies:
            if unit.alive:
                is_inspected = (unit is self.inspected and self.sub_state == S_SELECT)
                unit.draw(self.surface, selected=(unit is self.selected),
                          inspected=is_inspected)

        # Visual effects drawn on top of units
        for e in self.effects:
            e.draw(self.surface)

        # UI — show inspected enemy in panel when no ally is selected
        panel_unit = self.selected if self.selected is not None else self.inspected
        draw_unit_panel(self.surface, panel_unit)

        # Hint shown inside the log box
        if self.phase == "enemy":
            hint = "Enemy is acting..."
        else:
            if self.sub_state == S_SELECT:
                if self.inspected:
                    hint = "Viewing enemy details.  Click an ally to select.  Click elsewhere to dismiss."
                else:
                    hint = "Click an ally to select.  Click an enemy to view their details."
            else:
                hint = {
                    S_MOVE:      "Click inside the blue circle to move.  Click another ally to switch.",
                    S_MOVING:    "Moving...",
                    S_ACTION:    "Choose an action.  Back = undo your move.",
                    S_ATTACK:    "Click an enemy in the red zone.  Click empty space to cancel.",
                    S_ITEM_MENU: "Choose an item to use.",
                }.get(self.sub_state, "")

        self.hud.draw(self.surface, self.phase, self.turn_num,
                      self.allies, self.enemies, hint=hint)

        if self.sub_state == S_ACTION and self.action_menu:
            self.action_menu.draw(self.surface)
        if self.sub_state == S_ITEM_MENU and self.item_menu:
            self.item_menu.draw(self.surface)

    def _draw_title(self):
        self.surface.fill((10, 12, 20))
        cx = SCREEN_W // 2

        title  = C.FONT_XL.render("TACTICAL RPG", True, (180, 200, 255))
        sub    = C.FONT_LG.render("A Fantasy Battle", True, (120, 140, 180))
        prompt = C.FONT_MD.render("Press any key or click to begin", True, (90, 110, 150))
        self.surface.blit(title, title.get_rect(centerx=cx, centery=220))
        self.surface.blit(sub,   sub.get_rect(centerx=cx,   centery=278))

        sections = [
            # (header, color, [(line, color), ...])
            ("HOW TO PLAY", (200, 200, 120), [
                ("Click one of your blue units to select them.",         (190, 190, 160)),
                ("Click inside the glowing ring to move them.",          (190, 190, 160)),
                ("Then choose: Attack, use an Item, or Wait.",           (190, 190, 160)),
                ("When all your units have acted, the enemies take their turn.", (190, 190, 160)),
            ]),
            ("WEAPONS & WEAKNESSES", (200, 180, 100), [
                ("S Sword  beats  Axe  —  A Axe  beats  Lance  —  L Lance  beats  Sword",
                 (210, 200, 140)),
                ("Strong weapons hit more reliably and deal more damage.",  (190, 190, 160)),
                ("B Bow  attacks from a distance but can't hit nearby enemies.", (200, 160, 80)),
                ("M Magic  attacks at any range but the caster is very fragile.", (180, 120, 255)),
            ]),
            ("COMBAT STATS", (180, 200, 180), [
                ("Strength & Defense govern physical combat.",  (190, 190, 160)),
                ("Intelligence & Resistance govern magic.",     (190, 190, 160)),
                ("A much faster unit strikes twice in one exchange.", (190, 190, 160)),
            ]),
            ("LOOT", (140, 210, 140), [
                ("Golden chests appear on the battlefield — move a unit next to one to open it.", (190, 190, 160)),
                ("Defeated enemies drop their items.  Walk over them to pick up.",  (190, 190, 160)),
                ("Tonics permanently boost a stat for the rest of the battle.",     (190, 190, 160)),
            ]),
        ]

        y = 318
        for header, hcol, lines in sections:
            h = C.FONT_SM.render(f"— {header} —", True, hcol)
            self.surface.blit(h, h.get_rect(centerx=cx, y=y)); y += 16
            for line, lcol in lines:
                t = C.FONT_SM.render(line, True, lcol)
                self.surface.blit(t, t.get_rect(centerx=cx, y=y)); y += 14
            y += 5

        self.surface.blit(prompt, prompt.get_rect(centerx=cx, centery=y + 6))

    def _draw_end(self, label, color):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surface.blit(overlay, (0, 0))
        txt = C.FONT_XL.render(label, True, color)
        sub = C.FONT_MD.render("Press any key to return to title", True, (200, 200, 200))
        self.surface.blit(txt, txt.get_rect(centerx=SCREEN_W // 2, centery=300))
        self.surface.blit(sub, sub.get_rect(centerx=SCREEN_W // 2, centery=380))
