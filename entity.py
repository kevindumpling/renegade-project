"""
entity.py

This file defines the framework for all entities in the game with a hitbox, velocity, and collisions,
as well as the FiringSite and OffsetFiringSite for firing independent of an enemy.
"""

import pygame
from typing import *
from pygame.math import Vector2
from help import *

class Entity(pygame.sprite.Sprite):
    """
    A base class for any game object with a hitbox, velocity, and collision logic.

    === Public Attributes ===
    name: the name of this entity.
    health: current health of the entity.
    position: current position vector.
    velocity: current velocity vector.
    accel: acceleration vector applied to this entity.
    state: facing direction; '', 'left', 'right', or 'front'.
    targets: sprite group this entity can collide with.
    bomb_immunity: whether this entity is currently immune to bomb damage.

    === Repr. Invariants ===
    self.rect.center == self.position.

    """

    name: str
    health: int
    position: Vector2
    velocity: Vector2
    accel: Vector2
    state: str
    targets: Optional[pygame.sprite.AbstractGroup]
    bomb_immunity: bool

    def __init__(self, name: str, health: int, position: Vector2, velocity: Vector2, accel: Vector2, scale: tuple[int, int], reward: int, state: str = '', *groups: pygame.sprite.AbstractGroup, targets: Optional[pygame.sprite.AbstractGroup] = None) -> None:
        super().__init__(*groups)
        self.name = name
        self._max_health = health
        self.health = health
        self.position = position
        self.velocity = velocity
        self.accel = accel
        self.state = state
        self.targets = targets
        self.bomb_immunity = False

        self.images = {}
        for state in ['']:
            key = f"{self.name}_{state}" if state else self.name
            try:
                self.images[state] = load_image(key, scale)
            except Exception as e:
                print(f"DEBUG, ERROR / FAILED TO LOAD SPRITE {key}")

        self.image = self.images.get(self.state, self.images[''])
        self.rect = self.image.get_rect(center=self.position)
        self.mask = pygame.mask.from_surface(self.image)
        self.score = 0
        self.reward = reward

    def update(self) -> None:
        self._update_position()
        self._constrain_movement()
        self.check_collisions(self.targets)
        self._check_death()
        self.image = self.images.get(self.state, self.images[''])
        self.mask = pygame.mask.from_surface(self.image)

    def _update_position(self) -> None:
        self.velocity += self.accel
        self.position += self.velocity
        self.rect.center = self.position

        # Update sprite based on velocity.
        if self.velocity.x > 0:
            self.state = 'right'
        elif self.velocity.x < 0:
            self.state = 'left'
        else:
            self.state = ''


    def _update_health(self, damage_amount: int) -> None:
        self.health -= damage_amount
        self.health = max(0, self.health)
        self._check_death()

    def _check_death(self) -> None:
        if self.health <= 0:
            ENEMY_DEATH_SOUND.play()
            self.kill()

    def _constrain_movement(self) -> None:
        """Deal with interaction at the screen edges."""
        raise NotImplementedError

    def take_damage(self) -> None:
        raise NotImplementedError

    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        raise NotImplementedError


class FiringSite(Entity):
    """
    A placeholder Entity used to define positions for bullet firing logic.
    It does not render or collide with anything.

    Used for: boss weapon sites or ghost emitters.
    """

    def __init__(self, position: Vector2, reward: int, *groups: pygame.sprite.AbstractGroup,
                 targets: Optional[pygame.sprite.AbstractGroup] = None) -> None:
        super().__init__('transparent', -1, position, ZERO_VECTOR, ZERO_VECTOR, (1, 1), reward, '', *groups, targets=targets)

    @override
    def update(self) -> None:
        pass

class OffsetFiringSite(FiringSite):
    """
    A firing site attached to a parent entity (e.g. a boss) with an offset.
    Follows the parent as it moves.

    === Public Attributes ===
    """

    def __init__(self, parent: Entity, offset: Vector2, reward: int, *groups):
        self._parent = parent
        self._offset = offset
        super().__init__(self._parent.position + self._offset, reward, *groups)

    @override
    def update(self):
        self.position = self._parent.position + self._offset
        self.rect.center = self.position

    @property
    def health(self):
        return self._parent.health

    @health.setter
    def health(self, value):
        self._parent.health = value
