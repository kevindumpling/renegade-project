"""
bullet.py

This file defines all types of projectiles that are used in the game, such as bullets, lasers, and missiles.
"""

from typing import *
import pygame
from pygame import Vector2
from entity import Entity
from help import *
import help

class Bullet(Entity):
    """
     A basic projectile that moves linearly and despawns when it exits the screen
     or hits a target.

     === Public Attributes ===
     owner: the entity that fired this bullet
     targets: the group of entities this bullet can damage
     """

    owner: Entity
    targets: pygame.sprite.Group

    def __init__(self, name: str, position: Vector2, velocity: Vector2, accel: Vector2,
                 owner: Entity = None,
                 scale: Tuple[int, int] = (4, 10),
                 *groups: pygame.sprite.AbstractGroup,targets: Optional[pygame.sprite.AbstractGroup] = None) -> None:

        super().__init__(
            name,
            1,
            position,
            velocity,
            accel,
            scale,
            0,
            '',
            *groups
        )

        self.owner = owner
        self.targets = targets

    def update(self) -> None:
        # DEBUG
        pygame.draw.circle(pygame.display.get_surface(), (255, 0, 0), self.rect.center, 2)
        pygame.draw.circle(pygame.display.get_surface(), (0, 255, 0), self.position, 2)
        super().update()
        # self.rect.center = self.position  # DEBUG: Override topleft.

    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        """Destroy self on collision with targets."""
        if targets is None:
            return

        hits = pygame.sprite.spritecollide(self, targets, dokill=False, collided=pygame.sprite.collide_mask)
        for target in hits:
            if target != self.owner and not target.bomb_immunity:
                target.take_damage()  # Must be implemented by target.
                self.owner.score += int(target.reward * help.difficulty_modifier)
                self.kill()
                break

    @override
    def _constrain_movement(self) -> None:
        """Deal with interaction at the screen edges."""
        if (self.rect.bottom < 0 or self.rect.top > CANVAS_HEIGHT or
                self.rect.right < 0 or self.rect.left > CANVAS_WIDTH):
            self.kill()

    @override
    def take_damage(self) -> None:
        pass

class Missile(Bullet):
    """
    A missile projectile that tracks the player and homes in that self-destructs after a time limit.

    === Public Attributes ===
    owner: the entity that fired the missile
    targets: the group of entities the missile can damage
    """

    owner: Entity
    targets: pygame.sprite.Group
    _spawn_time: int

    def __init__(self, name: str, position: Vector2, velocity: Vector2, accel: Vector2,
                 owner: Optional[pygame.sprite.Sprite], target: Entity,
                 homing_speed: float, effect_length: int,
                 scale: Tuple[int, int] = (20, 20),
                 *groups: pygame.sprite.AbstractGroup,
                 targets: Optional[pygame.sprite.AbstractGroup] = None) -> None:

        super().__init__(name, position, velocity, accel, owner, scale, *groups, targets=targets)
        self.target = target
        self.homing_speed = homing_speed  # degrees/frame
        self.effect_length = effect_length
        self._spawn_time = pygame.time.get_ticks()

    def update(self) -> None:

        self._home_toward_target()
        super().update()

    def _home_toward_target(self) -> None:
        """Rotate the velocity vector toward the target by at most `homing_speed` degrees."""
        if not self.target:
            return

        # Direction vector to target
        to_target = Vector2(self.target.rect.center) - Vector2(self.rect.center)
        if to_target.length_squared() == 0:
            return  # Target is on top of us

        current_angle = self.velocity.angle_to(Vector2(1, 0))
        target_angle = to_target.angle_to(Vector2(1, 0))

        # Shortest angular difference [-180, 180]
        angle_diff = (target_angle - current_angle + 180) % 360 - 180

        # Clamp to max turning speed
        turn = max(-self.homing_speed, min(self.homing_speed, angle_diff))

        # Apply rotation (Pygame rotates CCW with negative angle)
        self.velocity = self.velocity.rotate(-turn)

    @override
    def _constrain_movement(self) -> None:
        """Kill the missile if it leaves the screen."""
        if (self.rect.right < 0 or self.rect.left > CANVAS_WIDTH or
            self.rect.bottom < 0 or self.rect.top > CANVAS_HEIGHT):
            self.kill()

    @override
    def _check_death(self) -> None:
        if pygame.time.get_ticks() - self._spawn_time >= self.effect_length:
            self.kill()
            return


class LaserCache:
    """
    Storage class that contains all of the orientations of the lasers, to a 1 degree level of accuracy.
    ALL used widths of lasers MUST be preloaded in main.py's preload_images.
    """

    _cache: dict[tuple[str, int, int], dict[int, tuple[pygame.Surface, pygame.Mask]]] = {}

    @staticmethod
    def preload(name: str, base_image: pygame.Surface, size: tuple[int, int], angle_step: int = 1):
        key = (name, size[0], size[1])
        if key not in LaserCache._cache:
            scaled = pygame.transform.scale(base_image, size)
            angle_dict = {}
            for angle in range(0, 360, angle_step):
                # Create a surface where the firing point is vertically centered.
                adjusted = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
                adjusted.blit(scaled, (0, -scaled.get_height() // 2 + 1))  # shift up so base is center

                # Rotate.
                rotated = pygame.transform.rotate(adjusted, -angle)
                mask = pygame.mask.from_surface(rotated)
                angle_dict[angle] = (rotated, mask)

            LaserCache._cache[key] = angle_dict

    @staticmethod
    def get(name: str, size: tuple[int, int], angle: float) -> tuple[pygame.Surface, pygame.Mask]:
        key = (name, size[0], size[1])
        angle_bucket = round(angle / 1) * 1 % 360
        return LaserCache._cache[key][angle_bucket]


class Laser(Bullet):
    """

    A laser is a beam that does not die when hitting an enemy, does not have a velocity, and has a FIRING and WARNING state represented
    by its default and front sprites respectfully.

    === Public Attributes ===
    owner: the sprite who fired this laser
    targets: the targets which can be destroyed by this laser
    warning: represents whether this laser is in its warning or deadly stage.
    effect_length: how long this laser lasts for in its deadly state, in ms
    delay: represents the time until this laser becomes deadly, in ms
    previous_started_time: the last time this laser started firing, in ms
    previous_finished_time: the last time this laser finished its deadly cycle, in ms
    original_image: the unrotated version of this laser's image
    === Representation Invariants ==
    self.state == 'left' if in warning mode and == 'right' if in deadly mode.
    """

    def __init__(self, name: str, position: Vector2, owner: Entity, width: int, effect_length: int, delay: int, *groups: pygame.sprite.AbstractGroup, targets: Optional[pygame.sprite.AbstractGroup] = None):
        super().__init__(name, position, ZERO_VECTOR, ZERO_VECTOR, owner, (200, 200), *groups, targets=targets)
        self.warning = True
        self.effect_length = effect_length
        self.delay = delay
        self.previous_finished_time = pygame.time.get_ticks()
        self.previous_started_time = 0
        self.state = 'left'
        self.width = width
        self.mask = pygame.mask.from_surface(self.image)
        self.owner = owner

        self.images = {}
        for state in ['', 'left', 'right', 'front']:
            key = f"{self.name}_{state}" if state else self.name
            try:
                self.images[state] = load_image(key, (200, 200))
            except Exception as e:
                print(f"DEBUG, ERROR / FAILED TO LOAD SPRITE {key}")

        if 'left' in self.images:
            self.original_image = self.images['left'].copy()
        else:
            self.original_image = self.images[''].copy()

    def _update_state(self) -> None:
        """Update the state of this laser."""
        current = pygame.time.get_ticks()

        # Check activation.
        if self.warning and current - self.previous_finished_time >= self.delay:
            self.warning = False
            self.previous_started_time = current
            LASER_FIRE_SOUND.play()

        # Check deactivation.
        if not self.warning and current - self.previous_started_time >= self.effect_length:
            self.warning = True
            self.previous_finished_time = current

        if self.warning:
            self.state = 'left'
        else:
            self.state = 'right'

    def _update_image_from_state(self) -> None:
        """Update self.image based on current state, without rotating or affecting rect."""
        if self.state in self.images:
            self.original_image = self.images[self.state]  # Removed .copy()
        else:
            self.original_image = self.images['']  # Removed .copy()

    @override
    def check_collisions(self, targets: pygame.sprite.Group | None = players) -> None:
        if targets is None:
            return

        hits = pygame.sprite.spritecollide(self, targets, dokill=False, collided=pygame.sprite.collide_mask)
        for target in hits:
            if target != self.owner and not target.bomb_immunity:
                target.take_damage()

    @override
    def _constrain_movement(self) -> None:
        """Deal with interaction at the screen edges. In this case, don't do anything."""
        pass

    @override
    def update(self) -> None:
        if not self.owner.health > 0 and self.owner.health != -1:
            self.kill()
            return

        self._update_state()
        self._update_image_from_state()

        # Avoid super().update() since the state-based image reassignment kills the rotation set in the rotating laser patterns.
        self._constrain_movement()
        if not self.warning and pygame.time.get_ticks() % 2 == 0:
            self.check_collisions(self.targets)

        self._check_death()


class Bomb(Bullet):
    """
    A bomb projectile that emits damaging waves and fades after a delay.

    === Public Attributes ===
    owner: the entity that dropped the bomb
    targets: the group of entities the bomb can damage
    """
    # == Implementation Details ==
    # _fire_time: the last time this bomb went off, in ms
    # _current_scale: the current size of this bomb

    targets: Optional[pygame.sprite.AbstractGroup]
    owner: Entity
    duration: int
    _fire_time: int
    _current_scale: int

    def __init__(self, name: str, owner: Entity, duration: int, *groups: pygame.sprite.AbstractGroup, targets: Optional[pygame.sprite.AbstractGroup] = None) -> None:

        super().__init__(
            name,
            Vector2(owner.rect.center),
            ZERO_VECTOR,
            ZERO_VECTOR,
            owner,
            (200, 200),
            *groups
        )

        self.owner = owner
        self.targets = targets
        self.duration = duration
        self._fire_time = pygame.time.get_ticks()
        self._current_scale = 1

        self.original_image = self.images[''].copy()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=self.position)


    @override
    def update(self) -> None:

        self._update_position()
        self._constrain_movement()
        self.check_collisions(self.targets)
        self._check_death()

    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        """Destroy self on collision with targets."""
        if targets is None:
            return

        hits = pygame.sprite.spritecollide(self, targets, dokill=True, collided=pygame.sprite.collide_rect)
        for target in hits:
            if target != self.owner:
                target.take_damage()  # Must be implemented by target.
                break

    @override
    def _constrain_movement(self) -> None:
        """Deal with interaction at the screen edges."""
        pass

    @override
    def take_damage(self) -> None:
        pass

    @override
    def _check_death(self) -> None:
        """Check if this bomb has reached its duration."""
        if pygame.time.get_ticks() - self._fire_time >= self.duration:
            self.kill()
            self.owner.bomb_immunity = False

    @override
    def _update_position(self) -> None:
        """Expand the bomb. It should expand a total of 200 times in the duration."""
        elapsed   = pygame.time.get_ticks() - self._fire_time
        progress  = min(elapsed / self.duration, 1.0)

        # -- Grow from 1 px to the diameter that covers the screen diagonal
        max_diam  = int((CANVAS_WIDTH**2 + CANVAS_HEIGHT**2) ** 0.5) * 2
        max_diam = min(max_diam, 1500)
        new_size  = max(1, int(progress * max_diam))

        # -- Keep centre fixed
        centre    = self.rect.center

        # -- Always scale from the ORIGINAL image, not the already-scaled one
        self.image = pygame.transform.scale(self.original_image, (new_size, new_size))
        self.rect = self.image.get_rect(center=self.rect.center)

        self.owner.bomb_immunity = True


class MuzzleFlash(pygame.sprite.Sprite):
    """
    A short-lived visual effect rendered at the point of firing.

    === Public Attributes ===
    image: the visual surface of the flash
    rect: the position and size of the flash sprite
    """

    _spawn_time: int
    image: pygame.Surface
    rect: pygame.Rect

    def __init__(self, position: Vector2, scale: tuple[int, int] = (32, 32), duration: int = 2000, *groups: pygame.sprite.AbstractGroup):
        super().__init__(*groups)
        self.image = load_image("muzzle_flash", (50, 50))
        self.rect = self.image.get_rect(center=position)
        self._spawn_time = pygame.time.get_ticks()
        self.duration = duration

    def update(self):
        if pygame.time.get_ticks() - self._spawn_time > self.duration:
            self.kill()
