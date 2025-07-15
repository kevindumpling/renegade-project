"""
enemy.py

This class defines all the basic types of enemies that can be faced in the game.
Formations are composed of many such enemies.
The boss enemy is contained in boss.py and is not contained in this file.
"""

import pygame
from pygame import Vector2
from typing import Callable
from entity import *
from pattern import *
from ui import AnimatedGIFSprite

class Enemy(Entity):
    """
    Base class for all non-boss enemies (e.g., popcorn enemies, midbosses).

    === Public Attributes ===
    targets: the player sprite group that this enemy can attack

    === Repr. Invariants ===
    self.rect.center == self.position.
    """

    def __init__(self, name: str, health: int, position: Vector2, reward: int, scale: tuple[int, int], *groups):
        super().__init__(name, health, position, Vector2(0, 0), Vector2(0, 0), scale, reward, '', *groups)
        self.targets = players


class PopcornEnemy(Enemy):
    """
    A lightweight, disposable enemy that moves, fires a basic pattern, and dies in one hit.

    === Public Attributes ===
    targets: the targets this enemy will attack

    === Repr. Invariants ===
    self.rect.center == self.position.

    """

    def __init__(self, name: str, scale: tuple[int, int], position: Vector2, movement_fn: Callable[[Enemy], None],
                 pattern_factory: Callable[[Enemy], Pattern], reward: int, fire_delay: int = 0,
                 *groups: pygame.sprite.AbstractGroup):
        """
        movement_fn: function that updates this enemy's position each frame
        pattern: the bullet pattern fired by this enemy
        fire_delay: how long (in ms) after spawn the enemy begins firing
        spawn_time: the time at which this enemy spawned
        """
        super().__init__(name, 1, position, reward, scale, *groups)
        self._movement_fn = movement_fn
        self._pattern = pattern_factory(self)
        self._fire_delay = fire_delay
        self._spawn_time = pygame.time.get_ticks()

    def update(self):
        self._movement_fn(self)

        # Fire after spawn delay.
        if pygame.time.get_ticks() - self._spawn_time > self._fire_delay:
            self._pattern.update()

        super().update()

    def take_damage(self):
        if not self.bomb_immunity:
            ENEMY_DEATH_SOUND.play()
            animated = AnimatedGIFSprite(
                "death",
                (35, 35),
                (self.rect.centerx, self.rect.centery),
                100,
                500,
                ui
            )
            self.kill()

    def _constrain_movement(self):
        # If it leaves the screen, kill it.
        if (self.rect.bottom < 0 or self.rect.top > CANVAS_HEIGHT or
            self.rect.right < 0 or self.rect.left > CANVAS_WIDTH):
            self.kill()

    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        pass  # Can add bullet collisions with the player here later.


class BigEnemy(Enemy):
    """
    A stronger enemy that cycles through multiple bullet patterns over time.

    === Public Attributes ===
    targets: the targets of this enemy.

    === Repr. Invariants ===
    self.rect.center == self.position.
    """


    def __init__(self, name: str, position: Vector2,
                 movement_fn: Callable[[Enemy], None],
                 pattern_factories: list[Callable[[Enemy], Pattern]],
                 pattern_interval: int,
                 health: int,
                 reward: int,
                 *groups):
        """
        movement_fn: function that updates this enemy's position each frame
        patterns: a list of bullet patterns this enemy cycles through
        pattern_interval: how often (in ms) to switch to the next bullet pattern
        current_index: the index of the currently active pattern
        last_switch: the time (in ms) the last pattern switch occurred
        """
        super().__init__(name, health, position, reward, (50, 50), *groups)
        self._movement_fn = movement_fn
        self._patterns: list[Pattern] = [f(self) for f in pattern_factories]
        self._pattern_interval = pattern_interval
        self._current_index = 0
        self._last_switch = pygame.time.get_ticks()
        self.targets = players

    @override
    def update(self):
        self._movement_fn(self)

        if not self._patterns:
            return

        now = pygame.time.get_ticks()
        if now - self._last_switch > self._pattern_interval:
            self._current_index = (self._current_index + 1) % len(self._patterns)
            self._last_switch = now

        self._patterns[self._current_index].update()

        super().update()

    @override
    def take_damage(self):
        if not self.bomb_immunity:
            self.health -= 1
            if self.health <= 0:
                ENEMY_DEATH_SOUND.play()
                animated = AnimatedGIFSprite(
                    "death",
                    (55, 55),
                    (self.rect.centerx, self.rect.centery),
                    100,
                    1000,
                    ui
                )
                self.kill()

    @override
    def _constrain_movement(self):
        if (self.rect.bottom < 0 or self.rect.top > CANVAS_HEIGHT or
            self.rect.right < 0 or self.rect.left > CANVAS_WIDTH):
            self.kill()

    @override
    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        pass
