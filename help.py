"""
help.py

This is a storage file. It contains the majority of the global constants and
globally-referenced variables, such as the gamestate and stages as well as the
sprite groups.
"""
import json
from typing import overload
import pygame
from pygame import Vector2
from stage import StageHandler
import os
import sys

"""==== IMAGES AND DRAWING ===="""
@overload
def draw(path: str, x: int, y: int, screen: pygame.display) -> None: ...
@overload
def draw(path: str, x: int, y: int, scalex: int, scaley: int, screen: pygame.display) -> None: ...

def draw(path: str, x: int, y: int, *args) -> None:
    """Draw the image file to the screen, optionally scaling it."""
    image = pygame.image.load(resource_path(path)).convert_alpha()

    if len(args) == 1:
        screen = args[0]
    elif len(args) == 3:
        scalex, scaley, screen = args
        image = pygame.transform.scale(image, (scalex, scaley))
    else:
        raise TypeError("Invalid arguments for draw()")

    screen.blit(image, (x, y))

global_images: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}

def load_image(name: str, scale: tuple[int, int]) -> pygame.Surface:
    """
    Load a scaled image from the sprites folder into the global cache and return a copy.

    === Parameters ===
    name: the sprite filename without extension
    scale: the (width, height) to scale the image to

    === Returns ===
    A copy of the loaded and scaled pygame.Surface
    """

    key = (name, scale)
    if key not in global_images:
        img = pygame.image.load(resource_path(f"sprites/{name}.png")).convert_alpha()
        img = pygame.transform.scale(img, scale)
        global_images[key] = img
    return global_images[key].copy()

"""=== UTILITY ==="""
def resource_path(relative_path: str) -> str:
    """Get absolute path to resource (for PyInstaller or direct run)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


"""=== PHYSICS AND MECHANICS ==="""
ZERO_VECTOR = Vector2(0, 0)
ORIGINAL_SCROLL_SPEED = 2.0
STAGE_SCROLL_SPEED = ORIGINAL_SCROLL_SPEED  # pixels/frame

pygame.mixer.init()
pygame.mixer.set_num_channels(999)  # Default is 8

ENEMY_FIRE_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_enemyfire.wav"))
PLAYER_FIRE_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_playerfire.wav"))
PLAYER_DEATH_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_death.wav"))
ENEMY_DEATH_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_enemydestroyed.wav"))
BOMB_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_bombdeployed.wav"))
LASER_FIRE_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_laseron.wav"))
BUTTON_HOVER_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_button_hover.wav"))
BUTTON_PRESSED_SOUND = pygame.mixer.Sound(resource_path("sounds/sound_button_pressed.wav"))

loud_sounds = [ENEMY_FIRE_SOUND, LASER_FIRE_SOUND]
for sound in loud_sounds:
    sound.set_volume(0.1)
PLAYER_FIRE_SOUND.set_volume(0.2)
BOMB_SOUND.set_volume(2)
BUTTON_HOVER_SOUND.set_volume(0.2)
BUTTON_PRESSED_SOUND.set_volume(0.2)

"""=== OTHER CONSTANTS ==="""
GAME_RUNNING = True
PANEL_SIZE = 100
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 800 + PANEL_SIZE
gamestate = 'title'
previous_gamestate = gamestate
player = None
LASER_STANDARD_LENGTH = 2000

"""=== GAME ELEMENTS ==="""
player_plane_type = 'f16'
player_lives_type = 10
player_speed_type = 4
player_bombs_type = 12
player_shot_delay_type = 100
player_bullet_type = 'playerbullet_green'
player_bomb_type = 'bomb_ring_green'
player_bullets_per_shot_type = 5
difficulty_modifier = 1  # default for ace difficulty
difficulty = 'ACE'
DIFFICULTY_DELAY_INCREASE = 500


"""=== SETTINGS ==="""
highscore = 0
skip_banners = False

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".renegade_save")
HIGHSCORE_FILE = os.path.join(SAVE_DIR, "save.json")

def save_highscore() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump({"highscore": player.score}, f)

def load_highscore() -> int:
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f).get("highscore", 0)
    except FileNotFoundError:
        return 0

"""=== STAGES ==="""
stage1 = StageHandler()
stage2 = None
stage3 = None
stage4 = None
stage5 = None

"""=== GROUPS ==="""
global_sprites = pygame.sprite.LayeredUpdates()  # This is the group from which all things are drawn in main.py.
players = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
lasers = pygame.sprite.Group()
ui = pygame.sprite.Group()
banners = pygame.sprite.Group()
background = pygame.sprite.Group()
formations = pygame.sprite.Group()
overlay = pygame.sprite.Group()

def forward_group(source: pygame.sprite.Group, target: pygame.sprite.LayeredUpdates, layer: int):
    """
    Add sprites from one group into another LayeredUpdates group, assigning them to a specific draw layer.

    === Parameters ===
    source: the group containing source sprites
    target: the destination LayeredUpdates group
    layer: the draw layer priority
    """

    for sprite in source:
        if sprite not in target:
            target.add(sprite, layer=layer)
