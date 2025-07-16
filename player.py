"""
player.py

This file contains all information related to the player entity.
"""

import pygame
from pygame.math import Vector2
from typing import *
from entity import Entity
from help import *
from bullet import Bullet, Bomb
from ui import AnimatedGIFSprite
import help

ZERO_VECTOR = Vector2(0, 0)

class Player(Entity):
    """
    A controllable player entity in the game.

    The Player responds to keyboard input for movement and inherits core properties
    such as health, position, and sprite rendering from Entity. It can shoot bullets,
    deploy bombs, and temporarily become invulnerable after taking damage.

    === Public Attributes ===
    name: the name of this player
    health: the current health of the player
    position: the position of the player as a Vector2
    velocity: the velocity of the player as a Vector2
    accel: the acceleration of the player as a Vector2
    state: the current orientation ('', 'front', 'left', or 'right')
    speed: the base movement speed of the player
    lives: how many lives the player currently has
    bombs: how many bombs the player currently has
    score: total score accumulated by this player


    === Repr. Invariants ===
    - len(self.name) > 0
    - self.health >= 0
    - self.speed >= 0
    - self.state in {'', 'left', 'right'}
    - self.position.x and self.position.y are valid screen coordinates
    - self.rect.center == self.position.
    """
    # == Implementation Details ==
    # _firing_attempted: tracks whether the player is trying to fire
    # _respawn_position: the location to respawn to
    # _death_animation_occuring: whether the death animation is playing
    # _death_animation_timer: time since last death
    # _death_animation_duration: how long the death animation should last for

    previous_shot_time: int
    previous_bomb_time: int
    shot_delay: int
    bomb_delay: int
    speed: float
    lives: int
    bombs: int
    score: int

    _firing_attempted: bool
    _bomb_attempted: bool
    _respawn_position: Vector2
    _death_animation_occuring: bool
    _death_animation_timer: int
    _death_animation_duration: int
    _damage_inv: bool
    _inv_timer: int
    _inv_duration: int
    _last_blink_time: int
    _blink_interval: int
    _is_visible: bool


    def __init__(self, name: str, health: int, position: Vector2,
                 velocity: Vector2 = ZERO_VECTOR, accel: Vector2 = ZERO_VECTOR,
                 speed: float = 5.0, *groups: pygame.sprite.AbstractGroup) -> None:
        super().__init__(name, health, position, velocity, accel, (35, 55), 0, 'front', *groups)
        self.speed = speed
        self.previous_shot_time = 0
        self.previous_bomb_time = 0
        self.bomb_delay = 1000
        self.shot_delay = 100
        self.targets = enemies
        self._firing_attempted = False
        self._bomb_attempted = False

        self.mask = pygame.mask.from_surface(self.image)
        self.deaths = 0

        self._respawn_position = position
        self._death_animation_occuring = False
        self._death_animation_timer = 0
        self._death_animation_duration = 1000
        self.bullet_type = 'playerbullet'
        self.bomb_type = 'bomb_ring'

        self._damage_inv = True
        self._inv_duration = 2000
        self._inv_timer = 0
        self._last_blink_time = 0
        self._blink_interval = 250
        self._is_visible = True

        self.alive = True

        self.lives = 1
        self.bombs = 999
        self.max_lives = 9
        self.max_bombs = 9
        self.stage_number = 1
        self.bullets_per_shot = 6
        self.stage_name = '...AND THUS TO TYRANTS'

        self.images = {}
        for state in ['', 'left', 'right', 'front']:
            key = f"{self.name}_{state}" if state else self.name
            try:
                self.images[state] = load_image(key, (25, 45))
            except Exception as e:
                print(f"DEBUG, ERROR / FAILED TO LOAD SPRITE {key}")

    def update(self) -> None:
        """Global update."""
        # Check for death.

        # TODO: DEBUG, REMOVE THIS LATER; SET LIVES TO -99 TO TEST THE DEATH SCREEN
        if self.lives == -999:
            self.kill()
            self.alive = False
            help.gamestate = 'game_over'

        current_time = pygame.time.get_ticks()
        if self._death_animation_occuring:
            self.image = load_image('transparent', (55, 55))
            animated = AnimatedGIFSprite(
                "death",
                (55, 55),
                (self.rect.centerx, self.rect.centery),
                100,
                500,
                ui
            )
            if current_time - self._death_animation_timer >= self._death_animation_duration:
                self._death_animation_occuring = False
                if self.lives > 0:
                    self._respawn()
                else:
                    self.alive = False
                    help.gamestate = 'game_over'
                    self.kill()
            return # Don't allow updating when death animation is playing.

        # Behavior.
        self._take_input()
        super().update()

        if self._firing_attempted:
            self._check_fire()

        if self._bomb_attempted:
            self._check_bomb()

        # Play blinking animation if under invulnerability frames.
        if self._damage_inv:
            if current_time - self._inv_timer > self._inv_duration:
                self._damage_inv = False
                self._is_visible = True  # Make sure player becomes visible.
                self.image = self.images[self.state].copy()
                self.image.set_alpha(255)
            else:
                self.image = self.images[self.state].copy()
                if current_time - self._last_blink_time >= self._blink_interval:
                    self._is_visible = not self._is_visible
                    self._last_blink_time = current_time
                self.image.set_alpha(255 if self._is_visible else 100)
        else:
            # Always ensure image is reset when not blinking.
            self.image = self.images[self.state].copy()

    def _take_input(self) -> None:
        inputs = pygame.key.get_pressed()
        self.velocity = Vector2(0, 0)

        if inputs[pygame.K_LEFT] or inputs[pygame.K_a]:
            self.velocity.x = -self.speed
            self.state = 'left'
        elif inputs[pygame.K_RIGHT] or inputs[pygame.K_d]:
            self.velocity.x = self.speed
            self.state = 'right'
        else:
            self.state = 'front'

        if inputs[pygame.K_UP] or inputs[pygame.K_w]:
            self.velocity.y = -self.speed
        elif inputs[pygame.K_DOWN] or inputs[pygame.K_s]:
            self.velocity.y = self.speed

        if inputs[pygame.K_SPACE]:
            self._firing_attempted = True
        else:
            self._firing_attempted = False

        if inputs[pygame.K_b]:
            self._bomb_attempted = True
        else:
            self._bomb_attempted = False

        if inputs[pygame.K_p]:
            help.gamestate = 'paused'



    @override
    def _constrain_movement(self) -> None:
        """Deal with interaction at the screen edges."""
        screen_size = pygame.Rect(0, PANEL_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT - PANEL_SIZE)
        self.rect.clamp_ip(screen_size)
        self.position = Vector2(self.rect.center)

    def _fire(self) -> None:
        """Allow the player to fire bullets."""

        # Bullet properties.
        BULLET_SPEED = 9

        # Add a group of bullets to the bullets active.
        BULLET_AMOUNT = self.bullets_per_shot
        FAN_ANGLE = 27  # Spread of the first to last bullets in degrees.
        UNIT_Y_UP = Vector2(0, -1)
        angle_increment = FAN_ANGLE / BULLET_AMOUNT
        start_angle = -FAN_ANGLE / 2  # The bullets begin at -fan angle /2 and go to fan angle /2 off the central y axis.

        for i in range(BULLET_AMOUNT):
            angle = start_angle + i * angle_increment
            direction = UNIT_Y_UP.rotate(angle).normalize()
            firing_velocity = direction * BULLET_SPEED

            center_x, center_y = int(self.rect.centerx), int(self.rect.centery)
            # Wave of bullets.
            Bullet(self.bullet_type, Vector2(center_x - 4, center_y), firing_velocity, ZERO_VECTOR, self, (20, 15), player_bullets,
                   targets=self.targets)
        PLAYER_FIRE_SOUND.play()

    def _check_fire(self) -> None:
        """Allow the player to fire bullets by holding spacebar."""

        current_time = pygame.time.get_ticks()
        if current_time - self.previous_shot_time >= self.shot_delay:
            self.previous_shot_time = current_time
            self._fire()

        else:
            return  # Don't allow another wave to be fired.


    def _check_bomb(self) -> None:
        """Allow the player to bomb by pressing B."""
        current_time = pygame.time.get_ticks()
        if current_time - self.previous_bomb_time >= self.bomb_delay:
            self.previous_bomb_time = current_time
            self._bomb()

    def _bomb(self) -> None:
        if self.bombs > 0:
            BOMB_SOUND.play()
            Bomb(self.bomb_type, self, self.bomb_delay, player_bullets, targets=bullets)
            self.bombs -= 1

    @override
    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        pass

    @override
    def take_damage(self) -> None:
        if self.bomb_immunity or self._damage_inv or self._death_animation_occuring:
            return  # Don't take damage if immune.

        PLAYER_DEATH_SOUND.play()
        self.lives -= 1
        self.deaths += 1
        self.bombs = min(self.max_bombs, self.bombs + 1)
        self._respawn_position = self.position
        self._death_animation_occuring = True
        self._death_animation_timer = pygame.time.get_ticks()
        self.image.set_alpha(255)

    def _respawn(self) -> None:
        self.name = 'xfa33'
        self.rect.center = self._respawn_position
        self.position = Vector2(self._respawn_position)
        self._allow_inv()

    def _allow_inv(self) -> None:
        self._damage_inv = True
        self._inv_timer = pygame.time.get_ticks()
        self._last_blink_time = self._inv_timer
        self._is_visible = True
        self.image.set_alpha(255)
