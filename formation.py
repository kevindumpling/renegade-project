"""
formation.py

This file contains all information regarding the creation of enemy formations, which are ultimately
the user-facing API of the game engine in stagebuilder.py.
"""

from dataclasses import dataclass

import pygame
from pygame import Vector2
from entity import Entity
from enemy import *
from pattern import Pattern
from typing import Callable

@dataclass
class FormationEntry:
    """
    Configuration for a single popcorn enemy.

    === Public Attributes ===
    offset: offset from formation spawn point to place enemy
    movement_fn: function defining how the enemy moves
    pattern_fn: function that returns the attack pattern
    reward: score given upon contacting the enemy
    delay: time to wait before enemy becomes active (ms)
    """
    offset: Vector2
    movement_fn: Callable[[Entity], None]
    pattern_fn: Callable[[Entity], Pattern]
    reward: int
    delay: int = 0

    def __init__(self, offset: Vector2, movement_fn: Callable[[Entity], None],
                 pattern_fn: Callable[[Entity], Pattern], reward: int, delay: int = 0):
        self.offset = offset
        self.movement_fn = movement_fn
        self.pattern_fn = pattern_fn
        self.delay = delay
        self.reward = reward


@dataclass
class FiringSiteEntry:
    """
    Configuration for a firing site that spawns patterns.

    === Public Attributes ===
    offset: offset from formation spawn point to place the firing site
    pattern_factory: function that produces a Pattern instance
    reward: score value for contacting this site
    """
    offset: Vector2
    pattern_factory: Callable[[Entity], Pattern]
    reward: int

    offset: Vector2
    pattern_factory: Callable[[Entity], Pattern]
    reward: int


@dataclass
class BigEnemyEntry:
    """
    Configuration for a single large enemy.

    === Public Attributes ===
    offset: offset from formation spawn point to place enemy
    movement_fn: function defining how the enemy moves
    pattern_factories: list of factories creating bullet patterns
    interval: time between pattern switches (ms)
    health: total HP of the enemy
    reward: score given upon contact
    """
    offset: Vector2
    movement_fn: Callable[[Entity], None]
    pattern_factories: list[Callable[[Entity], Pattern | CompoundPattern]]
    interval: int
    health: int
    reward: int

    def __init__(self,
                 offset: Vector2,
                 movement_fn: Callable[[Entity], None],
                 pattern_factories: list[Callable[[Entity], Pattern | CompoundPattern]],
                 interval: int,
                 health: int, reward: int):
        self.offset = offset
        self.movement_fn = movement_fn
        self.pattern_factories = pattern_factories
        self.interval = interval
        self.health = health
        self.reward = reward


class Formation(pygame.sprite.Sprite):
    """
    Base class for enemy formations that spawn enemies and fire patterns over time.

    === Public Attributes ===
    name: the name identifier of this formation
    spawn_position: the position where this formation is placed
    scale: the (width, height) scale applied to entities in this formation
    spawn_time: the time (in ms) when this formation should activate
    enemies: list of all enemies spawned by this formation
    patterns: list of firing patterns associated with this formation
    firing_sites: list of firing sites (Entity instances) that control bullet patterns
    """
    name: str
    spawn_position: Vector2
    scale: tuple[int, int]
    spawn_time: int
    enemies: list[Entity]
    patterns: list[Pattern | CompoundPattern]
    firing_sites: list[Entity]

    def __init__(self, name: str, spawn_position: Vector2, scale: tuple[int, int], spawn_time: int, *groups, firing_sites: list[FiringSiteEntry] = None):
        super().__init__(*groups)
        self.spawn_position = spawn_position
        self.spawn_time = spawn_time
        self._spawned = False
        self.scale = scale
        self.name = name

        self._firing_sites_definitions = [] if firing_sites is None else firing_sites
        self.firing_sites = []
        self.patterns = []
        self.enemies = []

        # Required for pygame's sprite system (invisible).
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def update(self):
        if not self._spawned and pygame.time.get_ticks() >= self.spawn_time:
            self._spawned = True
            self.spawn()
            return  # Allow scroll/update to happen next frame.

        if self._spawned:
            # Move the formation and kill it if it is entirely off-screen.
            for site in self.firing_sites:
                site.position.y += STAGE_SCROLL_SPEED
                site.rect.center = site.position
                if site.rect.top > CANVAS_HEIGHT + 300:  # Add some padding just in case.
                    site.kill()
                    for pattern in self.patterns:
                        if pattern.owner == site and 'laser' in pattern.bullet_type:
                            pattern.kill_projectiles()

            # Remove patterns from dead enemies.
            for pattern in self.patterns:
                pattern.update()

                if isinstance(pattern, Pattern):
                    if not pattern.owner.alive:
                        pattern.kill_projectiles()
                        self.patterns.remove(pattern)
                elif isinstance(pattern, CompoundPattern):
                    if all(not p.owner.alive for p in pattern.patterns):
                        pattern.kill_projectiles()
                        self.patterns.remove(pattern)

            # Kill formation if all enemies contained within are dead.
            if all(not site.alive() for site in self.firing_sites) and all(
                    not hasattr(p, 'alive') or getattr(p, 'active', True) for p in self.patterns):
                self.kill()
                for pattern in self.patterns:
                    if 'laser' in pattern.bullet_type:
                        pattern.kill_projectiles()

    def spawn(self):
        raise NotImplementedError


class PopcornFormation(Formation):
    """
    A PopcornFormation spawns lightweight enemies ("popcorn") in configurable positions.

    === Public Attributes ===
    entries: a list of FormationEntry instances defining enemy behavior
    """
    entries: list[FormationEntry]


    def __init__(self, name: str, spawn_position: Vector2, scale: tuple[int, int], entries: list[FormationEntry], spawn_time: int,
*groups, firing_sites: list[FiringSiteEntry] | None = None):
        super().__init__(name, spawn_position, scale, spawn_time, *groups, firing_sites=firing_sites)
        self.entries = entries
        self.scale = scale

    def spawn(self):
        for entry in self.entries:
            pos = self.spawn_position + entry.offset
            self.enemies.append(PopcornEnemy(self.name, self.scale, pos, entry.movement_fn, entry.pattern_fn, entry.reward, entry.delay, enemies))

        for entry in self._firing_sites_definitions:
            site_pos = self.spawn_position + entry.offset
            site = FiringSite(site_pos, entry.reward, global_sprites)
            pattern = entry.pattern_factory(site)
            self.patterns.append(pattern)
            self.firing_sites.append(site)


class BigEnemyFormation(Formation):
    """
    A BigEnemyFormation spawns large enemies with more complex behaviors and the ability to
    change between multiple attack patterns on an interval timer.

    === Public Attributes ===
    entries: a list of BigEnemyEntry instances defining big enemy behavior
    """
    entries: list[BigEnemyEntry]

    def __init__(self, name: str, spawn_position: Vector2,
                 entries: list[BigEnemyEntry], scale: tuple[int, int], spawn_time: int, *groups, firing_sites: list[FiringSiteEntry] | None = None):
        super().__init__(name, spawn_position, scale, spawn_time, *groups, firing_sites=firing_sites)
        self.entries = entries

    def spawn(self):
        for entry in self.entries:
            pos = self.spawn_position + entry.offset
            self.enemies.append(BigEnemy(self.name, pos, entry.movement_fn,
                        entry.pattern_factories, entry.interval,
                        entry.health, entry.reward, enemies, global_sprites))

        for entry in self._firing_sites_definitions:
            site_pos = self.spawn_position + entry.offset
            site = FiringSite(site_pos, entry.reward, global_sprites)
            pattern = entry.pattern_factory(site)
            self.patterns.append(pattern)
            self.firing_sites.append(site)
