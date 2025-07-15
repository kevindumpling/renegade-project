"""
===========================================================

"RENEGADE"
version: 0.27 (Last updated: 2025-07-15, 1:23PM)
Made by Kevin Ding, with love.
Created using Pygame.

===========================================================

Copyright Kevin Ding, 2025. All rights reserved.
All music assets, code, and game design elements
belong to Kevin Ding. Unauthorized distribution or reproduction is strictly prohibited.

All sprites were created by Kevin Ding using OpenAI ChatGPT.

===========================================================

TODO:
- acceleration on bullets breaks the aiming (we need to incorporate the sign of the corresponding velocity)

===========================================================

main.py

This is the driver of the program and contains the main loop.

===========================================================
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pygame import Vector2
from player import Player
from help import *
from bullet import Bullet, Bomb, Missile
from pattern import *
from entity import FiringSite
from formation import *
import random
from boss import *
from spawner import *
from stage import *
from background import *
import stagebuilder
from bullet import *

# == INITIALIZE ==
pygame.init()

# == UTILITY ==
def show_loading_screen(screen):
    """
    Display a simple loading message on the provided screen surface.

    === Parameters ===
    screen: the pygame surface to draw the loading screen onto
    """

    screen.fill((0, 0, 0))  # Black background
    font = pygame.font.SysFont("Courier New", 40)
    text_surface = font.render("Loading...", True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2))
    screen.blit(text_surface, text_rect)
    pygame.display.flip()  # Push to screen immediately

def preload_images():
    """
    Preloads a set of commonly used images into memory to reduce lag during gameplay.
    """

    show_loading_screen(CANVAS)

    bullet_sizes = [(20, 20), (30, 30), (40, 40), (50, 50), (60, 60), (70, 70), (80, 80), (90, 90), (100, 100)]
    bullet_names = ["smallbullet", "bigbullet"]
    for name in bullet_names:
        for size in bullet_sizes:
            load_image(name, size)

    sprite_sizes = [(35, 35), (55, 55), (25, 45), (50, 50)]
    sprite_names = [
        "popcorn", "xfa47", "mech_boss", "bomb_ring", "bomb_ring_green", "bomb_ring_purple",
        "bomb_ring_yellow", "bomb_ring_lightgreen", "death", ]
    for name in sprite_names:
        for size in sprite_sizes:
            load_image(name, size)

    playerbullet_sizes = [(20, 15)]
    playerbullet_names = ["playerbullet", "playerbullet_green", "playerbullet_purple", "playerbullet_yellow"]
    for name in playerbullet_names:
        for size in playerbullet_sizes:
            load_image(name, size)

    for laser_name in ["laser_left", "laser_right"]:
        base_img = load_image(laser_name, (20, LASER_STANDARD_LENGTH))
        for size in [(20, LASER_STANDARD_LENGTH), (50, LASER_STANDARD_LENGTH)]:  # NOTE: ALL used widths MUST go here.
            LaserCache.preload(laser_name, base_img, size)

        LaserCache.preload(laser_name, base_img, (100, 1000))

    preload_laser_assets()


def preload_laser_assets():
    """
    Warm up the laser sprite pipeline.
    """
    laser_img = load_image("laser", (8, 200)).convert_alpha()
    dummy_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
    dummy_surface.blit(laser_img, (0, 0))

    laser_mask = pygame.mask.from_surface(laser_img)
    laser_mask.get_at((0, 0))

    dummy = Laser("laser", Vector2(100, 100), help.player, 20, 500, 1000, bullets)
    dummy.kill()

    snd = pygame.mixer.Sound(help.resource_path("sounds/sound_laseron.wav"))
    snd.play()
    snd.stop()

# == UTILITIES ==
ZERO_VECTOR = Vector2(0, 0)

# == FRAMERATE ==
clock = pygame.time.Clock()
FPS = 60

# == GAME WINDOW ==
CANVAS = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
pygame.display.set_caption('RENEGADE - MAIN WINDOW')
preload_images()

# == CURRENT STAGE ==
current_stage = None

# === MENU AND SELECT UI ELEMENTS ===
def _start_game_template(model: Player):
    """
    Starts the game using the provided Player model.

    === Parameters ===
    model: the configured Player object to initialize gameplay with
    """

    # Clear the previous menu.
    for sprite in help.global_sprites:
        sprite.kill()

    for group in [players, ui, player_bullets, bullets, lasers, enemies, formations, banners, overlay]:
        for sprite in group:
            sprite.kill()

    # Set the player, HUD, and build the first stage.
    if help.stage1:
        help.stage1.reset()
    help.stage1 = StageHandler()
    hud = PlayerHUD(help.player, ui)
    stagebuilder.build_stage1(help.stage1, help.player)


    global current_stage
    current_stage = help.stage1

    # Reset the gamestate. NOTE: this MUST go last.
    help.gamestate = 'stage1'
    help.previous_gamestate = 'stage1'

def default_start_game():
    """
    Starts the game using the default player configuration from `help`.
    """

    # Clear the previous menu.
    for sprite in help.global_sprites:
        sprite.kill()
    for group in [players, ui, player_bullets, bullets, lasers, enemies, formations, banners, overlay]:
        for sprite in group:
            sprite.kill()

    # Set the player, HUD, and build the first stage.
    help.player = Player(help.player_plane_type, help.player_lives_type, Vector2(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2 + 100), Vector2(CANVAS_WIDTH // 2, CANVAS_HEIGHT - 200), ZERO_VECTOR, help.player_speed_type,
           players)
    help.player.lives = help.player_lives_type
    help.player.max_lives = help.player.lives
    help.player.bombs = help.player_bombs_type
    help.player.max_bombs = help.player.bombs
    help.player.shot_delay = help.player_shot_delay_type
    help.player.bullets_per_shot = help.player_bullets_per_shot_type
    help.player.bullet_type = help.player_bullet_type
    help.player.bomb_type = help.player_bomb_type

    if help.stage1:
        help.stage1.reset()
    hud = PlayerHUD(help.player, ui)
    stagebuilder.build_stage1(help.stage1, help.player)

    global current_stage
    current_stage = help.stage1

    # Reset the gamestate. NOTE: this MUST go last.
    help.gamestate = 'stage1'
    help.previous_gamestate = 'stage1'


def button_quit_game():
    """On click, end the game."""
    pygame.quit()
    exit()


# == PREPARE TITLE SCREEN ==
menu_manager = MenuManager(CANVAS, default_start_game)
menu_manager.show_menu('title')

help.highscore = help.load_highscore()


"""==== GAME LOOP ===="""


def main() -> None:
    """Main game loop."""
    global current_stage

    while help.GAME_RUNNING:
        clock.tick(FPS)
        # print("EFFECTIVE TIME:", pygame.time.get_ticks() - 6000)

        # == KEEP THE GLOBAL GROUP UPDATED ==
        forward_group(player_bullets, global_sprites, 1)
        forward_group(bullets, global_sprites, 2)
        forward_group(lasers, global_sprites, 2)
        forward_group(enemies, global_sprites, 3)
        forward_group(formations, global_sprites, 3)
        forward_group(players, global_sprites, 4)
        forward_group(ui, global_sprites, 5)
        forward_group(background, global_sprites, 0)
        forward_group(banners, global_sprites, 6)
        forward_group(overlay, global_sprites, 7)

        # == HANDLE STAGES ==
        match help.gamestate:
            case 'stage1':
                if not current_stage == help.stage1:
                    current_stage = help.stage1
                current_stage.update()

            case 'stage2':
                if not current_stage == help.stage2:
                    current_stage = help.stage2
                current_stage.update()

            case 'stage3':
                if not current_stage == help.stage3:
                    current_stage = help.stage3
                current_stage.update()

            case 'stage4':
                if not current_stage == help.stage4:
                    current_stage = help.stage4
                current_stage.update()

            case 'stage5':
                if not current_stage == help.stage5:
                    current_stage = help.stage5
                current_stage.update()

        # == HANDLE MENUS ==
        if help.gamestate != help.previous_gamestate:
            match help.gamestate:
                case 'title':
                    menu_manager.show_menu('title')
                case 'game_over':
                    menu_manager.show_menu('game_over')
                case 'mission_select':
                    menu_manager.show_menu('mission_select')
                case 'end_screen':
                    menu_manager.show_menu('end_screen')
                case 'paused':
                    menu_manager.show_menu('paused')
                case 'help':
                    menu_manager.show_menu('help')

            help.previous_gamestate = help.gamestate

        # == OTHER ==

        # Check for 'close game' event.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GAME_RUNNING_FLAG = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_TAB:
                    help.skip_banners = not help.skip_banners
                    help.BUTTON_PRESSED_SOUND.play()

        # == UPDATE DRAWING ON THE DISPLAY ==
        CANVAS.fill((0, 0, 0))
        global_sprites.update()
        global_sprites.draw(CANVAS)
        pygame.display.update()

        # == DEBUGGING ==


    # == END OF MAIN LOOP ==
    pygame.quit()


if __name__ == "__main__":
    main()
