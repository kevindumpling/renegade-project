"""
ui.py

This file contains all UI and GUI-related classes, as well as text-display classes.
"""

from dataclasses import dataclass
from time import struct_time
from typing import List, Callable

import pygame
from help import *
import help
from background import StaticBackground

class UISprite(pygame.sprite.Sprite):
    """
    A UISprite is the parent class for any element appearing as part of the game's UI.
    This includes player HUDs and menus.

    === Public Attributes ===
    image: a pygame.Surface containing the appearance of this sprite
    rect: The rectangle on which self.image is placed
    position: the x and y position of this UISprite

    === Repr. Invariants ===
    self.rect is determined by self.image.
    """

    size: tuple[int, int]
    position: tuple[int, int]
    image: pygame.Surface
    rect: pygame.rect

    def __init__(self, size: tuple[int, int], position: tuple[int, int], *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=position)
        self._alpha = 255  # Default fully visible
        self.position = position

    def set_alpha(self, alpha: int):
        """Set transparency (0 = invisible, 255 = fully visible)."""
        self._alpha = max(0, min(255, alpha))
        self.image.set_alpha(self._alpha)

    def set_center(self, x: int, y: int):
        """Set the center of this sprite's rect."""
        self.rect.center = (x, y)

    def clear(self):
        """Clear this image from the screen by drawing a black overlay on it."""
        self.image.fill((0, 0, 0, 0))  # Clear with transparency


class BossHealthBar(UISprite):
    """
    A BossHealthBar displays the amount of health remaining on the boss' current phase.

    === Public Attributes ===
    boss: the boss of which this bar belongs to
    width: the width of this bar
    height: the height of this bar

    === Repr. Invariants ===
    self.boss must be an instance of Entity or a subclass of Entity
    """

    width: int
    height: int

    def __init__(self, boss, width: int, height: int, *groups):
        super().__init__((width, height), (800 // 2, 90), *groups)
        self._boss = boss
        self._width = width
        self._height = height
        self._bar_color = (120, 61, 10)
        self._font = pygame.font.SysFont('Arial', 20, bold=True)

    def update(self):
        if not self._boss or not self._boss.active:
            return
        if not self._boss.alive():
            self.kill()

        # Do not show if the phase is over.
        phase = self._boss.current_phase
        if not phase:
            return

        self.clear()

        # Calculate and display the bar.
        hp_ratio = phase.current_hp / phase.max_hp
        hp_width = int(self._width * hp_ratio)
        pygame.draw.rect(self.image, self._bar_color, (0, 0, hp_width, self._height))


class AttackBanner(UISprite):
    """
    An AttackBanner displays the attack name of the boss' current phase on the screen.
    Set duration to -1 to last it indefinitely.

    === Public Attributes ===
    attack_name: the name of this attack
    duration: the duration of this banner.

    === Repr. Invariants ===
    self.duration >= 0 or self.duration == -1.
    """
    def __init__(self, attack_name: str, duration: int = -1, *groups):
        super().__init__((800, 60), (40, 100), *groups)
        self._font = pygame.font.SysFont('Courier New', 15, bold=True)
        self.attack_name = attack_name
        self._text = f"{attack_name}"
        self._alpha = 255
        self._timer = pygame.time.get_ticks()
        self.duration = duration
        self._state = 'showing'
        self.set_alpha(self._alpha)

    def update(self):
        self.clear()

        if self._state == 'showing':
            # Kill when duration reached.
            elapsed = pygame.time.get_ticks() - self._timer
            if self.duration >= 0 and elapsed > self.duration:
                self._state = 'idle'
                self.set_alpha(0)
                self.kill()

        if self._alpha > 0:
            # Show.
            label = self._font.render(self._text, True, (255, 255, 255))
            label.set_alpha(self._alpha)
            rect = label.get_rect(topleft=(self.rect.width // 2, self.rect.height // 2))
            self.image.blit(label, rect)


class PlayerHUD(UISprite):
    """
    A PlayerHUD displays the relevant information about a player at the top of the screen. It typically contains:
        - number of lives
        - number of bombs
        - current mission and difficulty
        - current reward.

    === Public Attributes ===
    player: the player this HUD is describing
    """
    def __init__(self, player, *groups):
        super().__init__((800, 80), (400, 50), *groups)  # Positioned top-right, slightly lower
        self.player = player
        self._font = pygame.font.SysFont('Courier New', 18, bold=True)
        self._small_font = pygame.font.SysFont('Courier New', 15, bold=True)
        self._smaller_font = pygame.font.SysFont('Courier New', 10, bold=False)

        self._life_icon = load_image(help.player_plane_type, (15, 15))
        self._bomb_icon = load_image(help.player_bomb_type, (15, 15))


    def update(self):
        self.clear()
        bg_color = (40, 40, 40, 100)  # Dark blue-gray with some transparency
        pygame.draw.rect(self.image, bg_color, self.image.get_rect())

        # Draw lives in top row
        for i in range(self.player.lives):
            self.image.blit(self._life_icon, (520 + i * 14, 33 + 8))

        # Draw bombs in bottom row
        for i in range(self.player.bombs):
            self.image.blit(self._bomb_icon, (520 + i * 14, 10 + 8))

        lives_text = self._font.render(str(self.player.lives), True, (255, 255, 255))
        bombs_text = self._font.render(str(self.player.bombs), True, (255, 255, 255))
        self.image.blit(lives_text, (520 + self.player.lives * 14 + 5, 33 + 10))
        self.image.blit(bombs_text, (520 + self.player.bombs * 14 + 5, 10 + 10))

        stage_text = self._small_font.render(f'MISSION {self.player.stage_number} // {self.player.stage_name} ({help.difficulty})', True, (255, 255, 255))
        self.image.blit(stage_text, (70, 25))
        reward_text = self._smaller_font.render(f'REWARD: {self.player.score} (HIGHEST: {help.highscore})', True, (255, 255, 255))
        self.image.blit(reward_text, (70, 45))


class TypingBanner(pygame.sprite.Sprite):
    """
    A TypingBanner displays text in the help.banners layer and types it out one letter at a time,
    like a typewriter.

    === Public Attributes ===
    text: the text contained on this banner
    text_size: the size of the text on this banner
    position: the location of this banner
    duration_ms: the duration of this banner, in ms
    type_speed: the delay between characters, in ms
    fade_time: the time it takes for this banner to fade out, in ms
    start_delay: the time until this banner should be activated, in ms
    done: whether this banner is done.
    """

    text: str
    text_size: int
    position: Vector2
    duration_ms: int
    type_speed: int
    fade_time: int
    start_delay: int

    def __init__(self, text: str, text_size: int, position: Vector2, duration_ms: int = 5000, type_speed: int = 100,
                 fade_time: int = 500, start_delay: int = 0):
        super().__init__(help.banners)
        self.text = text
        self.text_size = text_size
        self.position = position
        self.type_speed = type_speed
        self.total_duration = duration_ms
        self.fade_time = fade_time
        self.start_delay = start_delay
        self._start_time = pygame.time.get_ticks()
        self._active_start = 0
        self._activated = False
        self.done = False

        self._font = pygame.font.SysFont("Courier New", text_size)
        self._full_surface = self._font.render(text, True, (255, 255, 255))
        self._current_display = ""
        self.image = pygame.Surface(self._full_surface.get_size(), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=position)

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self._start_time

        if not self._activated:
            if elapsed >= self.start_delay:
                self._activated = True
                self._active_start = now
            else:
                self.image.set_alpha(0)
                return

        active_elapsed = now - self._active_start

        if active_elapsed >= self.total_duration:
            self.kill()
            self.done = True
            return

        # Type characters individually.
        num_chars = min(len(self.text), active_elapsed // self.type_speed)
        self._current_display = self.text[:num_chars]

        typed_surface = self._font.render(self._current_display, True, (255, 255, 255))
        self.image.fill((0, 0, 0, 0))  # Fully transparent
        self.image.blit(typed_surface, (0, 0))

        # Fade out when done.
        if active_elapsed > self.total_duration - self.fade_time:
            alpha = int(255 * ((self.total_duration - active_elapsed) / self.fade_time))
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)


class AnimatedGIFSprite(pygame.sprite.Sprite):
    """
    An AnimatedGIFSprite cycles through four directional frames (base, left, right, front)
    in a loop to create a simple animation. Used for effects like explosions.

    === Public Attributes ===
    image: the current surface being displayed
    rect: the position and size of the sprite
    """

    _frame_duration: int
    _lifetime_ms: int | None
    _start_time: int
    _frames: list[pygame.Surface]
    image: pygame.Surface
    rect: pygame.Rect

    def __init__(self, base_name: str, size: tuple[int, int], position: tuple[int, int],
                 frame_duration: int = 200, lifetime_ms: int | None = None,
                 *groups: pygame.sprite.Group):
        super().__init__(*groups)
        self._frame_duration = frame_duration
        self._lifetime_ms = lifetime_ms
        self._start_time = pygame.time.get_ticks()

        suffixes = ['', '_left', '_right', '_front']
        self._frames: List[pygame.Surface] = [
            load_image(base_name + s, size) for s in suffixes
        ]
        self.image = self._frames[0]
        self.rect = self.image.get_rect(center=position)

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self._start_time

        # Kill after lifetime expires.
        if self._lifetime_ms is not None and elapsed >= self._lifetime_ms:
            self.kill()
            return

        index = (elapsed // self._frame_duration) % len(self._frames)
        self.image = self._frames[index]


class FadeOverlay(pygame.sprite.Sprite):
    """
    A FadeOverlay is a full-screen black rectangle that fades in or out,
    useful for transitions between menus or scenes.

    === Public Attributes ===
    fade_in: whether this overlay fades in (True) or out (False)
    duration: how long the fade lasts (in ms)
    image: the black surface being drawn
    rect: the area it covers (full screen)
    """

    def __init__(self, fade_in: bool, duration: int = 1000, on_complete: Callable = None, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.fade_in = fade_in
        self.duration = duration
        self._start_time = pygame.time.get_ticks()
        self._done = False
        self._alpha = 255 if fade_in else 0
        self.image.set_alpha(self._alpha)
        self._on_complete = on_complete

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self._start_time

        # Fade.
        progress = min(1.0, elapsed / self.duration)
        self._alpha = int(255 * (1 - progress)) if self.fade_in else int(255 * progress)
        self.image.set_alpha(self._alpha)

        # End when done.
        if progress >= 1.0 and not self._done:
            self._done = True
            if self._on_complete:
                self._on_complete()
            self.kill()


class MenuButton(UISprite):
    """
    A MenuButton is an interactive button that can be hovered and clicked,
    triggering a callback and playing sounds based on state.

    === Public Attributes ===
    text: the label displayed on the button
    callback: function to call when the button is clicked
    color: RGBA background color of the button
    font: font used to render text
    hovered: whether the mouse is currently over the button
    """

    text: str
    callback: Callable
    color: tuple[int, int, int, int]
    font: pygame.font.Font
    hovered: bool
    _was_pressed: bool
    _sound_played: bool


    def __init__(self, text: str, position: tuple[int, int], callback: Callable, width: int, height: int, color: tuple[int, int, int, int],
                 *groups):
        super().__init__((width, height), position, *groups)
        self.text = text
        self.callback = callback
        self.color = color
        self.font = pygame.font.SysFont('Courier New', 25, bold=True)
        self.hovered = False
        self._was_pressed = False
        self._sound_played = False

    def update(self):
        self.clear()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.hovered = self.rect.collidepoint(mouse_pos)
        bg_color = self.color if self.hovered else (self.color[0]*0.7, self.color[1]*0.7, self.color[2]*0.7, self.color[3]*0.7)
        if self.hovered:
            if not self._sound_played:
                help.BUTTON_HOVER_SOUND.play()
                self._sound_played = True
        else:
            self._sound_played = False

        pygame.draw.rect(self.image, bg_color, self.image.get_rect(), border_radius=8)

        label = self.font.render(self.text, True, (255, 255, 255))
        rect = label.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(label, rect)

        # Trigger on click release.
        if self._was_pressed and not mouse_pressed and self.hovered:
            FadeOverlay(False, 700, self.callback, help.overlay)
            help.BUTTON_PRESSED_SOUND.play()

        # Update was_pressed state every frame.
        self._was_pressed = mouse_pressed


@dataclass
class ButtonEntry:
    """
    A ButtonEntry represents a clickable UI button and its behavior.

    === Public Attributes ===
    label: the button label text
    position: the (x, y) position of the button center
    size: the (width, height) of the button
    color: the RGBA background color of the button
    callback: the function to call when this button is pressed
    """

    label: str
    position: tuple[int, int]
    size: tuple[int, int]
    color: tuple[int, int, int, int]
    callback: Callable[[], None]  # Must change help.gamestate on press.

@dataclass
class TextEntry:
    """
    A TextEntry represents static text to be displayed on a menu screen.

    === Public Attributes ===
    text: the text content to display
    position: the (x, y) position of the text's center
    size: the font size
    color: the RGB color of the text
    bold: whether the text should be bold
    """

    text: str
    position: tuple[int, int]
    size: int
    color: tuple[int, int, int]
    bold: bool = False


class Menu(UISprite):
    """
    A Menu represents a full-screen interactive interface containing buttons and text elements,
    such as title screens, pause menus, or end-of-game summaries.

    === Public Attributes ===
    entries: a list of button configuration entries (label, size, color, callback, etc.)
    text_entries: static text to be rendered on the menu screen
    bg: path to this menu's background.

    === Representation Invariants ===
    NOTE: Don't add menu items to groups through their constructors.
    Add them manually in MenuManager.
    """

    entries: list[ButtonEntry]
    _buttons: list[MenuButton]
    text_entries: list[TextEntry]
    _font_name: str
    bg: str
    _music: str

    def __init__(self, button_entries: list[ButtonEntry], text_entries: list[TextEntry], bg: str, font: str = 'Courier New', music: str = 'RENEGADE (Quiet).mp3'):
        super().__init__((CANVAS_WIDTH, CANVAS_HEIGHT), (CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2), )

        self.entries = button_entries
        self.bg = bg
        self._buttons = []
        self.text_entries = text_entries
        self._font_name = font
        self._music = resource_path(f'sounds/{music}')
        pygame.mixer.init()
        pygame.mixer.music.load(self._music)
        pygame.mixer.music.play(-1)

    def activate(self, group: pygame.sprite.Group):
        """Creates interface and adds them to the sprite group."""
        for entry in self.entries:
            self._buttons.append(MenuButton(entry.label, entry.position, entry.callback,
                       entry.size[0], entry.size[1], entry.color, group))

    def update(self):
        self.clear()

        for entry in self.text_entries:
            font = pygame.font.SysFont(self._font_name, entry.size, bold=entry.bold)
            label = font.render(entry.text, True, entry.color)
            rect = label.get_rect(center=entry.position)
            self.image.blit(label, rect)


# ====== CONSTRUCTION BEGINS HERE ========

class MenuManager:
    """
       A MenuManager controls the visibility and transitions between different menus
       (title, pause, mission select, etc.) and handles state restoration and menu-based logic.

       === Public Attributes ===
       canvas: the main game canvas used for rendering
       active_menu: the currently visible Menu (if any)
       start_game: callback to begin the game from the menu
       paused: whether the game is currently paused
       """

    canvas: pygame.Surface
    active_menu: Menu | None
    start_game: Callable
    paused: bool
    _menus: dict[str, Menu]

    def __init__(self, canvas: pygame.Surface, start_game: Callable):
        self.canvas = canvas
        self.active_menu: Menu | None = None
        self.start_game = start_game
        self.paused = False

        self._menus: dict[str, Menu] = {
            "title": Menu([
                ButtonEntry("MISSION SELECT", (400, 710), (600, 50), (51, 59, 102, 180), self.show_mission_select),
                ButtonEntry("HOW-TO", (400, 770), (600, 50), (28, 34, 59, 180), self.show_help),
                ButtonEntry("QUIT", (400, 830), (600, 50),(28, 34, 59, 180) , self.quit_game)
            ],
                [
                    TextEntry('RENEGADE', (400, 200), 100, (230, 230, 230), bold=True),
                    TextEntry('V. 0.27', (400, 260), 25, (230, 230, 230)),
                    TextEntry('© KEVIN DING 2025, ALL RIGHTS RESERVED', (400, 290), 20, (230, 230, 230)),
                    TextEntry("TAKE THE PLANE AND DON'T LOOK BACK.", (400, 350), 20, (230, 230, 230)),

                ],
                'title_background'),
            "game_over": Menu([
                ButtonEntry("RESTART", (400, 640), (600, 50), (51, 59, 102, 180), self.show_mission_select),
                ButtonEntry("RETURN TO TITLE", (400, 720), (600, 50), (28, 34, 59, 180), self.return_to_title),
                ButtonEntry("QUIT", (400, 780), (600, 50), (28, 34, 59, 180), self.quit_game)
            ],
                [
                    TextEntry('MISSION FAILED', (400, 200), 70, (230, 230, 230), bold=True)
                ],
                'title_background'),
            "help": Menu([
                ButtonEntry("RETURN TO TITLE", (400, 720 + 30), (600, 50), (51, 59, 102, 180), self.return_to_title),
                ButtonEntry("QUIT", (400, 780 + 30), (600, 50), (28, 34, 59, 180), self.quit_game)
            ],
                [
                    TextEntry('HELP MENU', (400, 100), 70, (230, 230, 230), bold=True),
                    TextEntry(f'LIFETIME HIGHEST REWARD: {help.highscore}', (400, 150), 15, (230, 230, 230)),
                    TextEntry('CONTROLS', (400, 170 + 40), 30, (230, 230, 230), bold=True),
                    TextEntry('MOVEMENT: [WASD] OR [ARROW KEYS]', (400, 220 + 30), 20, (230, 230, 230)),
                    TextEntry('FIRE: [SPACE]', (400, 260 + 30), 20, (230, 230, 230)),
                    TextEntry('BOMB (TO CLEAR BULLETS): [B]', (400, 300 + 30), 20, (230, 230, 230)),

                    TextEntry('UTILITY', (400, 370 + 30), 30, (230, 230, 230), bold=True),
                    TextEntry('TERMINATE (PAUSING FORCES RESTART MISSION): [P]', (400, 410 + 30), 20, (230, 230, 230)),
                    TextEntry('DISABLE PRE-MISSION DIALOGUE: [TAB] (TOGGLE)', (400, 450 + 30), 20, (230, 230, 230)),

                    TextEntry('OTHER', (400, 510 + 30), 30, (230, 230, 230), bold=True),
                    TextEntry('REMEMBER THAT PAUSING FORCES YOU TO RESTART THE WHOLE ATTEMPT!', (400, 550 + 30), 15, (230, 230, 230)),
                    TextEntry('SCORE REDUCTIONS ARE APPLIED FOR NOVICE AND PILOT DIFFICULTIES.', (400, 590 + 30), 15, (230, 230, 230)),
                    TextEntry('EXTRA POINTS FOR ALL-CLEARS AND ANY LIVES/BOMBS REMAINING AT THE END!', (400, 630 + 30), 15,
                              (230, 230, 230)),

                ],
                'title_background'),
            "mission_select": Menu([
                ButtonEntry("F16", (150, 300), (100, 40), (28, 34, 59, 180), self._make_player_f16),
                ButtonEntry("YF23", (150, 350), (100, 40), (28, 34, 59, 180), self._make_player_yf23),
                ButtonEntry("B2", (150, 400), (100, 40), (28, 34, 59, 180), self._make_player_b2),
                ButtonEntry("XFA47", (150, 450), (100, 40), (28, 34, 59, 180), self._make_player_xfa47),
                ButtonEntry("F4", (150, 500), (100, 40), (28, 34, 59, 180), self._make_player_f4),

                ButtonEntry("NOVICE", (200, 640), (120, 50), (51, 59, 102, 200), self._start_novice),
                ButtonEntry("PILOT", (340, 640), (120, 50), (51, 59, 102, 200), self._start_pilot),
                ButtonEntry("VETERAN", (500, 640), (120, 50), (51, 59, 102, 200), self._start_veteran),
                ButtonEntry("ACE", (640, 640), (120, 50), (51, 59, 102, 200), self._start_ace),

                ButtonEntry("RETURN TO TITLE", (400, 750), (600, 50), (28, 34, 59, 180), self.return_to_title),
                ButtonEntry("QUIT", (400, 810), (600, 50), (28, 34, 59, 180), self.quit_game)
            ],
                [
                    TextEntry('MISSION SELECT', (400, 100), 80, (230, 230, 230), bold=True),
                    TextEntry('WHICH PLANE WILL YOU TAKE FROM THEIR HANGER?', (400, 150), 20, (230, 230, 230)),
                    TextEntry('ROBUST AND WELL-BALANCED. BEST FOR THE INEXPERIENCED.', (470, 300), 15, (230, 230, 230)),
                    TextEntry('SUPERMANOEUVRABLE ATTACK-BASED PLATFORM. HARD TO CONTROL.', (470, 350), 15, (230, 230, 230)),
                    TextEntry('STEALTHY DEFENSIVE BOMBER. WEAKER ATTACK AND SPEED.', (470, 400), 15,(230, 230, 230)),
                    TextEntry('THEIR EXPERIMENTAL PLANE. WELL-ROUNDED, SHARP HANDLING.', (470, 450), 15, (230, 230, 230)),
                    TextEntry('A PLANE FROM A DIFFERENT TIME. A CHALLENGE FOR EXPERIENCED PILOTS.', (470, 500), 15, (230, 230, 230)),
                    TextEntry('SELECT YOUR CAMPAIGN TYPE.', (400, 580), 20, (230, 230, 230), bold=True),

                ],
                'mission_select_background'),

            "end_screen": Menu([
                ButtonEntry("PLAY AGAIN", (400, 640), (600, 50), (51, 59, 102, 180), self.start_game),
                ButtonEntry("RETURN TO TITLE", (400, 720), (600, 50), (28, 34, 59, 180), self.return_to_title),
                ButtonEntry("QUIT", (400, 780), (600, 50), (28, 34, 59, 180), self.quit_game)
            ],
                [
                    TextEntry('CLEAR', (400, 200), 100, (230, 230, 230), bold=True)
                ],
                'victory_background'),
            "paused": Menu([
                ButtonEntry("RESTART", (400, 640), (600, 50), (51, 59, 102, 180), self.show_mission_select),
                ButtonEntry("RETURN TO MENU", (400, 720), (600, 50), (28, 34, 59, 180), self.return_to_title),
                ButtonEntry("QUIT", (400, 780), (600, 50), (28, 34, 59, 180), self.quit_game)
            ],
                [
                    TextEntry('PAUSED', (400, 200), 100, (230, 230, 230), bold=True)
                ],
                'title_background')
        }

    def _start_novice(self) -> None:
        help.difficulty_modifier = 0.25
        help.difficulty = 'NOVICE'
        self.clear_all()
        self.start_game()

    def _start_pilot(self) -> None:
        help.difficulty_modifier = 0.5
        help.difficulty = 'PILOT'
        self.clear_all()
        self.start_game()

    def _start_veteran(self) -> None:
        help.difficulty_modifier = 0.75
        help.difficulty = 'VETERAN'
        self.clear_all()
        self.start_game()

    def _start_ace(self) -> None:
        help.difficulty_modifier = 1
        help.difficulty = 'ACE'
        self.clear_all()
        self.start_game()

    @staticmethod
    def _change_player_type(plane_type: str, lives: int, bombs: int, speed: int, shot_delay: int, bullets_per_shot: int, bullet_type: str, bomb_type: str) -> None:
        help.player_plane_type = plane_type
        help.player_lives_type = lives
        help.player_bombs_type = bombs
        help.player_speed_type = speed
        help.player_shot_delay_type = shot_delay
        help.player_bullets_per_shot_type = bullets_per_shot
        help.player_bullet_type = bullet_type
        help.player_bomb_type = bomb_type

    def _make_player_f16(self):
        MenuManager._change_player_type('f16', 10, 12, 4, 150, 5, 'playerbullet_green', 'bomb_ring_green')
        self.clear_menu()
        self.show_menu('mission_select')

    def _make_player_yf23(self):
        self._change_player_type('yf23', 8, 9, 6, 70, 6, 'playerbullet_purple', 'bomb_ring_purple')
        self.clear_menu()
        self.show_menu('mission_select')

    def _make_player_b2(self):
        self._change_player_type('b2', 14, 16, 3.5, 200, 4, 'playerbullet_yellow', 'bomb_ring_yellow')
        self.clear_menu()
        self.show_menu('mission_select')

    def _make_player_xfa47(self):
        self._change_player_type('xfa47', 9, 9, 5, 100, 6, 'playerbullet', 'bomb_ring')
        self.clear_menu()
        self.show_menu('mission_select')

    def _make_player_f4(self):
        self._change_player_type('f4', 5, 5, 4, 300, 4, 'playerbullet_green', 'bomb_ring_lightgreen')
        self.clear_menu()
        self.show_menu('mission_select')

    def _transition(self) -> None:
        self.clear_all()
        self.clear_menu()

        help.previous_gamestate = help.gamestate

    def return_after_pause(self) -> None:
        self.clear_all()
        self.show_mission_select()

    def show_mission_select(self) -> None:
        self.clear_menu()
        pygame.mixer.music.load(resource_path('sounds/RENEGADE (Quiet).mp3'))
        pygame.mixer.music.play(-1)

        help.gamestate = 'mission_select'


    def show_help(self) -> None:
        self.clear_menu()
        help.gamestate = 'help'

    def show_menu(self, name: str):
        if help.previous_gamestate != help.gamestate:
            self._transition()

        menu = self._menus.get(name)

        if not menu:
            print(f"Menu {name} not found.")
            return

        # == Check for special screens. ==

        match name:
            case 'game_over':
                if help.player.score > help.highscore:
                    menu.text_entries = [
                        TextEntry('MISSION FAILED', (400, 200), 70, (230, 230, 230), bold=True),
                        TextEntry(f'FINAL REWARD: {help.player.score}', (400, 250), 20, (200, 200, 200)),
                        TextEntry(f'(HIGHEST REWARD: {help.highscore})', (400, 270), 15, (200, 200, 200)),
                        TextEntry(f'NEW RECORD ACHIEVED!', (400, 290), 15, (200, 200, 200)),
                        TextEntry(f'FAILED TO COMPLETE MISSION {help.player.stage_number}: {help.player.stage_name} ({help.difficulty})',
                                            (400, 580), 15, (200, 200, 200))

                    ]
                    help.highscore = help.player.score

                else:
                    menu.text_entries = [
                        TextEntry('MISSION FAILED', (400, 200), 70, (230, 230, 230), bold=True),
                        TextEntry(f'FINAL REWARD: {help.player.score}', (400, 250), 20, (200, 200, 200)),
                        TextEntry(f'(HIGHEST REWARD: {help.highscore})', (400, 270), 15, (200, 200, 200)),
                        TextEntry(
                            f'FAILED TO COMPLETE MISSION {help.player.stage_number}: {help.player.stage_name} ({help.difficulty})',
                            (400, 580), 15, (200, 200, 200))

                    ]

                help.save_highscore()

            case 'end_screen':
                # Calculate any bonuses that may be needed.
                lives_bonus = help.player.lives * int(10000 * help.difficulty_modifier)
                bombs_bonus = help.player.bombs * int(4000 * help.difficulty_modifier)
                all_clear_bonus = 0
                all_clear = False
                if help.player.deaths == 0:
                    all_clear = True
                    all_clear_bonus = 10 ** 6
                final_score = help.player.score + lives_bonus + bombs_bonus + all_clear_bonus

                if help.player.score > help.highscore:
                    menu.text_entries = [
                        TextEntry('CLEAR', (400, 200), 100, (230, 230, 230), bold=True),
                        TextEntry(f'REWARD: {help.player.score}', (400, 270), 20, (200, 200, 200)),
                        TextEntry(f'LIVES BONUS: {help.player.lives} * 10000 * {help.difficulty_modifier} ({help.difficulty}) = {lives_bonus}', (400, 290), 15, (200, 200, 200)),
                        TextEntry(f'BOMBS BONUS: {help.player.bombs} * 4000 * {help.difficulty_modifier} ({help.difficulty}) = {bombs_bonus}', (400, 310), 15, (200, 200, 200)),
                        TextEntry(f'FULL CLEAR BONUS: {all_clear_bonus}', (400, 330), 15, (200, 200, 200)),
                        TextEntry(f'FINAL REWARD: {final_score}', (400, 350 + 10), 20, (200, 200, 200)),
                        TextEntry(f'(HIGHEST REWARD: {help.highscore})', (400, 370 + 10), 15, (200, 200, 200)),
                        TextEntry(f'NEW RECORD ACHIEVED!', (400, 390 + 10), 15, (200, 200, 200)),
                        TextEntry(f'CONGRATULATIONS!', (400, 450), 40, (200, 200, 200)),
                        TextEntry(f'LEGENDARY PILOT, YOU ARE A TRUE RENEGADE.',
                                  (400, 580), 15, (200, 200, 200))
                    ]
                    help.highscore = final_score

                else:
                    menu.text_entries = [
                        TextEntry('CLEAR', (400, 200), 100, (230, 230, 230), bold=True),
                        TextEntry(f'REWARD: {help.player.score}', (400, 270), 20, (200, 200, 200)),
                        TextEntry(f'LIVES BONUS: {help.player.lives} * 10000 * {help.difficulty_modifier} ({help.difficulty}) = {lives_bonus}', (400, 290), 15, (200, 200, 200)),
                        TextEntry(f'BOMBS BONUS: {help.player.bombs} * 4000 * {help.difficulty_modifier} ({help.difficulty}) = {bombs_bonus}', (400, 310), 15, (200, 200, 200)),
                        TextEntry(f'FULL CLEAR BONUS: {all_clear_bonus}', (400, 330), 15, (200, 200, 200)),
                        TextEntry(f'FINAL REWARD: {final_score}', (400, 350 + 10), 20, (200, 200, 200)),
                        TextEntry(f'(HIGHEST REWARD: {help.highscore})', (400, 370 + 10), 15, (200, 200, 200)),
                        TextEntry(f'CONGRATULATIONS!', (400, 450), 40, (200, 200, 200)),
                        TextEntry(f'LEGENDARY PILOT, YOU ARE A TRUE RENEGADE.',
                                  (400, 580), 15, (200, 200, 200))
                    ]

                help.player.score = final_score
                help.save_highscore()

            case 'paused':
                menu.text_entries = [
                    TextEntry('TERMINATED', (400, 200), 100, (230, 230, 230), bold=True),
                    TextEntry(f'CURRENT REWARD: {help.player.score}', (400, 270), 20, (200, 200, 200)),
                    TextEntry(f'(HIGHEST REWARD: {help.highscore})', (400, 290), 15, (200, 200, 200)),
                    TextEntry(f'YOU MUST RESTART ON TERMINATION. YOU STOPPED AT:', (400, 560), 20, (230, 230, 230), bold=True),
                    TextEntry(f'MISSION {help.player.stage_number}: {help.player.stage_name} ({help.difficulty})',
                              (400, 580), 15, (200, 200, 200))
                ]

            case 'mission_select':
                menu.text_entries = [
                    TextEntry('MISSION SELECT', (400, 100), 80, (230, 230, 230), bold=True),

                    TextEntry('WHICH PLANE WILL YOU TAKE FROM THEIR HANGER?', (400, 150), 20, (230, 230, 230)),
                    TextEntry(f'SELECTED: {help.player_plane_type.upper()}', (400, 240), 25, (230, 230, 230), bold=True),

                    TextEntry('ROBUST AND WELL-BALANCED. BEST FOR THE INEXPERIENCED.', (470, 300), 15, (230, 230, 230)),
                    TextEntry('SUPERMANOEUVRABLE ATTACK-BASED PLATFORM. HARD TO CONTROL.', (470, 350), 15,
                              (230, 230, 230)),
                    TextEntry('STEALTHY DEFENSIVE BOMBER. WEAKER ATTACK AND SPEED.', (470, 400), 15, (230, 230, 230)),
                    TextEntry('THEIR EXPERIMENTAL PLANE. WELL-ROUNDED, SHARPER HANDLING.', (470, 450), 15,
                              (230, 230, 230)),
                    TextEntry('AN OLD LEGEND. A CHALLENGE FOR EXPERIENCED PILOTS.', (470, 500), 15,
                              (230, 230, 230)),
                    TextEntry('SELECT YOUR CAMPAIGN TYPE', (400, 580), 20,
                              (230, 230, 230), bold=True),
                    TextEntry('CHOOSING AN OPTION WILL LAUNCH YOUR PLANE!', (400, 690), 15,
                              (230, 230, 230)),
                ]

            case 'help':
                menu.text_entries = [
                        TextEntry('HELP MENU', (400, 100), 70, (230, 230, 230), bold=True),
                        TextEntry(f'LIFETIME HIGHEST REWARD: {help.highscore}', (400, 150), 15, (230, 230, 230)),

                        TextEntry('CONTROLS', (400, 170 + 40), 30, (230, 230, 230), bold=True),
                        TextEntry('MOVEMENT: [WASD] OR [ARROW KEYS]', (400, 220 + 30), 20, (230, 230, 230)),
                        TextEntry('FIRE: [SPACE]', (400, 260 + 30), 20, (230, 230, 230)),
                        TextEntry('BOMB (TO CLEAR BULLETS): [B]', (400, 300 + 30), 20, (230, 230, 230)),

                        TextEntry('UTILITY', (400, 370 + 30), 30, (230, 230, 230), bold=True),
                        TextEntry('TERMINATE (PAUSING FORCES RESTART MISSION): [P]', (400, 410 + 30), 20, (230, 230, 230)),
                        TextEntry('DISABLE PRE-MISSION DIALOGUE (TOGGLE): [TAB]', (400, 450 + 30), 20, (230, 230, 230)),

                    TextEntry('DIFFICULTIES', (400, 510 + 30), 30, (230, 230, 230), bold=True),
                        TextEntry('NOVICE: FOR INEXPERIENCED PLAYERS. GOOD TO LEARN THE ROPES.' , (400, 540 + 30), 15, (230, 230, 230)),
                        TextEntry('PILOT: A MODERATE CHALLENGE. A GOOD STEP AFTER NOVICE.', (400, 560 + 30), 15, (230, 230, 230)),
                        TextEntry('VETERAN: A SERIOUS COMMITMENT. DESIGNED FOR ADVANCED PLAYERS.', (400, 580 + 30), 15, (230, 230, 230)),
                    TextEntry('ACE: IMPOSSIBLE. THE FINAL FRONTIER.', (400, 600 + 30), 15,
                                  (230, 230, 230)),
                    TextEntry('REMEMBER: PAUSING WITH [P] FORCES YOU TO RESTART!', (400, 640 + 30), 15,
                              (230, 230, 230)),
                    TextEntry('PICK A GOOD PLANE FOR YOUR DIFFICULTY!', (400, 660 + 30), 15,
                              (230, 230, 230)),
                    ]

        # == Core behavior. ==
        help.ui.add(menu)
        self.active_menu = menu

        StaticBackground(menu.bg, help.background)

        help.ui.add(menu)  # Add the menu now, so it will update and draw each frame.
        menu.activate(help.ui)

    def clear_menu(self):
        for sprite in help.background:
            sprite.kill()

        for sprite in help.ui.sprites():
            sprite.kill()

        help.ui.empty()
        help.banners.empty()
        self.active_menu = None

    @staticmethod
    def clear_all() -> None:
        for sprite in help.global_sprites:
            sprite.kill()

        for group in [players, ui, player_bullets, bullets, lasers, enemies, formations, banners, overlay]:
            for sprite in group:
                sprite.kill()

    @staticmethod
    def quit_game():
        help.GAME_RUNNING = False

    def return_to_title(self) -> None:
        self.clear_menu()
        help.gamestate = 'title'
        pygame.mixer.music.load(resource_path('sounds/RENEGADE (Quiet).mp3'))
        pygame.mixer.music.play(-1)
