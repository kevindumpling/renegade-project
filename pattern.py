"""
pattern.py

All base attack patterns and their variations are in this file.
"""
import math
from typing import override
from entity import Entity
from bullet import *
import pygame
from pygame import Vector2
from help import *
from player import Player


class Pattern:
    """A Pattern represents a certain shape of bullets that can be used by
    an enemy.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    aimed: whether the pattern is directed toward the direction of the player or not
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """

    bullet_type: str
    bullet_scale: tuple[int, int]
    owner: Entity
    delay: int
    previous_fire_time: int
    bullets_per_shot: int
    speed: int
    accel: int
    aimed: bool
    player: Player

    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, bullets_per_shot: int, delay: int, speed: int, accel: int, aimed: bool=False):
        self.player = player
        self.bullet_type = bullet_type
        self.bullet_scale = bullet_scale
        self.owner = owner
        self.bullets_per_shot = bullets_per_shot
        self.delay = delay
        self.previous_fire_time = 0
        self.speed = speed
        self.accel = accel
        self.aimed = aimed

        self.projectiles: list[pygame.sprite.Sprite] = []
        self.active = True

    def update(self) -> None:
        """Public facing behavior of this pattern."""
        raise NotImplementedError

    def _check_fire(self) -> bool:
        """Check if firing is possible."""
        return pygame.time.get_ticks() - self.previous_fire_time >= self.delay

    def _fire(self) -> None:
        """Create the bullets needed for this pattern."""
        raise NotImplementedError

    def kill_projectiles(self):
        for p in self.projectiles:
            p.kill()
        self.projectiles.clear()

# == BULLET PATTERNS ==
class FanPattern(Pattern):
    """
    A FanPattern implements Pattern and is a conical attack pattern.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    spread_angle: the angle, in degrees, between the first and last bullet in the fan
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """

    spread_angle: int
    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, angles: list[int], delay: int, speed: int, accel: int, aimed: bool=False):
        super().__init__(player, bullet_type, bullet_scale, owner, len(angles), delay, speed, accel, aimed=aimed)
        self.angles = angles

    @override
    def update(self) -> None:
        if not self.active:
            return

        if self._check_fire():
            self._fire()

    @override
    def _fire(self) -> None:
        firing_position = Vector2(self.owner.rect.center)

        if self.aimed:
            to_player = Vector2(self.player.rect.center) - firing_position
            base_angle = math.degrees(math.atan2(to_player.y, to_player.x)) - 90
        else:
            base_angle = 0

        accel_vector = Vector2(self.accel, self.accel)
        center_offset = sum(self.angles) / len(self.angles)

        for angle in self.angles:
            relative_angle = angle - center_offset
            absolute_angle = base_angle + relative_angle

            direction = Vector2(0, 1).rotate(absolute_angle).normalize()
            velocity = direction * self.speed

            spawn_offset = direction * 10 if abs(relative_angle) > 1e-3 else Vector2(0, 0)
            position = firing_position + spawn_offset

            b = Bullet(
                self.bullet_type,
                position,
                velocity,
                accel_vector,
                self.owner,
                self.bullet_scale,
                bullets,
                targets=players
            )

            self.projectiles.append(b)
            ENEMY_FIRE_SOUND.play()

        pygame.draw.line(
            pygame.display.get_surface(),
            (255, 255, 255),
            firing_position,
            firing_position + Vector2(0, 1).rotate(base_angle) * 1000,
            1
        )

        pygame.draw.circle(
            pygame.display.get_surface(),
            (0, 255, 0),
            self.player.rect.center,
            3
        )

        self.previous_fire_time = pygame.time.get_ticks()


class SpiralPattern(Pattern):
    """
    A SpiralPattern implements Pattern and is a spiral attack pattern.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    spread_angle: the angle at which each shot should be spread
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """
    # == Implementation Details ==
    # _current_angle: the current angle at which the next bullet should be drawn in degrees.

    spread_angle: int
    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, bullets_per_shot: int, delay: int, spread_angle: int, speed: int, accel: int, aimed: bool=False):
        super().__init__(player, bullet_type, bullet_scale, owner, bullets_per_shot, delay, speed, accel, aimed)
        self._current_angle = 0
        self.spread_angle = spread_angle

    @override
    def update(self) -> None:
        if not self.active:
            return

        if self._check_fire():
            self._fire()

    @override
    def _fire(self) -> None:
        firing_position = Vector2(self.owner.rect.centerx, self.owner.rect.centery)

        # Aim at the player if needed.
        if self.aimed:
            UNIT_Y_DOWN = Vector2(self.player.rect.center) - Vector2(self.owner.rect.center)
            UNIT_Y_DOWN = UNIT_Y_DOWN.normalize()
        else:
            UNIT_Y_DOWN = Vector2(0, 1)

        for i in range(self.bullets_per_shot):
            direction = UNIT_Y_DOWN.rotate(self._current_angle).normalize()
            firing_velocity = direction * self.speed

            center_x, center_y = int(self.owner.rect.centerx), int(self.owner.rect.centery)
            # Wave of bullets.
            b = Bullet(self.bullet_type, Vector2(center_x - 8, center_y), firing_velocity, Vector2(self.accel, self.accel), self.owner, self.bullet_scale, bullets,
                   targets=players)
            self.projectiles.append(b)
            ENEMY_FIRE_SOUND.play()

            self._current_angle = (self._current_angle + self.spread_angle) % 360

        # Record that this shot was made.
        self.previous_fire_time = pygame.time.get_ticks()

class SinglePattern(Pattern):
    """
    A SinglePattern implements Pattern and is a straight line.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """

    spread_angle: int
    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, bullets_per_shot: int, delay: int, speed: int, accel: int, aimed: bool=False):
        super().__init__(player, bullet_type, bullet_scale, owner, bullets_per_shot, delay, speed, accel, aimed)

    @override
    def update(self) -> None:
        if not self.active:
            return

        if self._check_fire():
            self._fire()

    @override
    def _fire(self) -> None:
        firing_position = Vector2(self.owner.rect.centerx, self.owner.rect.bottom)

        # Aim at the player if needed.
        if self.aimed:
            UNIT_Y_DOWN = Vector2(self.player.rect.center) - Vector2(self.owner.rect.center)
            UNIT_Y_DOWN = UNIT_Y_DOWN.normalize()
        else:
            UNIT_Y_DOWN = Vector2(0, 1)

        for i in range(self.bullets_per_shot):
            firing_velocity = UNIT_Y_DOWN * self.speed

            center_x, center_y = int(self.owner.rect.centerx), int(self.owner.rect.centery)

            # Wave of bullets.
            b = Bullet(self.bullet_type, Vector2(center_x - 8, center_y - 0.2*i*self.bullet_scale[1]), firing_velocity, Vector2(self.accel, self.accel), self.owner, self.bullet_scale, bullets,
                   targets=players)
            self.projectiles.append(b)
            ENEMY_FIRE_SOUND.play()

        # Record that this shot was made.
        self.previous_fire_time = pygame.time.get_ticks()

class SnowflakePattern(Pattern):
    """
    A SnowflakePattern implements Pattern and is a snowflake-shaped attack pattern.
    NOTE: use SHORTER DELAYS or it ends up looking like a circle.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    spin_speed: the speed at which this snowflake pattern spins, in degrees per bullet.
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """
    # == Implementation Details ==
    # _offset: the offset of this spinning snowflake in degrees

    spread_angle: int
    spin_speed: int
    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, bullets_per_shot: int, delay: int, speed: int, accel: int, aimed: bool=False, spin_speed = 0):
        super().__init__(player, bullet_type, bullet_scale, owner, bullets_per_shot, delay, speed, accel, aimed)
        self.spin_speed = spin_speed
        self._offset = 0

    @override
    def update(self) -> None:
        if not self.active:
            return

        if self._check_fire():
            self._fire()

    @override
    def _fire(self) -> None:
        firing_position = Vector2(self.owner.rect.centerx, self.owner.rect.bottom)

        if self.aimed:
            UNIT_Y_DOWN = Vector2(self.player.rect.center) - Vector2(self.owner.rect.center)
            UNIT_Y_DOWN = UNIT_Y_DOWN.normalize()
        else:
            UNIT_Y_DOWN = Vector2(0, 1)

        for i in range(self.bullets_per_shot):
            angle = self._offset + 360 / self.bullets_per_shot * i
            direction = UNIT_Y_DOWN.rotate(angle).normalize()
            firing_velocity = direction * self.speed

            center_x, center_y = int(self.owner.rect.centerx), int(self.owner.rect.centery)
            # Wave of bullets.
            b = Bullet(self.bullet_type, Vector2(center_x - 8, center_y), firing_velocity, Vector2(self.accel, self.accel), self.owner, self.bullet_scale, bullets,
                   targets=players)
            self.projectiles.append(b)
            ENEMY_FIRE_SOUND.play()

        self._offset = (self._offset + self.spin_speed) % 360
        # Record that this shot was made.
        self.previous_fire_time = pygame.time.get_ticks()

class CirclePattern(Pattern):
    """
    A CirclePattern implements Pattern and is a circle-shaped attack pattern.
    NOTE: Use LONGER DELAYS or it ends up looking like a snowflake.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    bullet_scale: the scale at which this pattern's bullets are fired
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    delay: the delay between distinct shots in this pattern in ms
    speed: the y-speed of the bullets
    accel: the y-acceleration of the bullets
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """

    spread_angle: int
    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int], owner: Entity, bullets_per_shot: int, delay: int, speed: int, accel: int, aimed: bool=False):
        super().__init__(player, bullet_type, bullet_scale, owner, bullets_per_shot, delay, speed, accel, aimed)

    @override
    def update(self) -> None:
        if not self.active:
            return

        if self._check_fire():
            self._fire()

    @override
    def _fire(self) -> None:
        firing_position = Vector2(self.owner.rect.centerx, self.owner.rect.centery)

        if self.aimed:
            UNIT_Y_DOWN = Vector2(self.player.rect.center) - Vector2(self.owner.rect.center)
            UNIT_Y_DOWN = UNIT_Y_DOWN.normalize()
        else:
            UNIT_Y_DOWN = Vector2(0, 1)

        for i in range(self.bullets_per_shot):
            angle = 360 / self.bullets_per_shot * i
            direction = UNIT_Y_DOWN.rotate(angle).normalize()
            firing_velocity = direction * self.speed

            center_x, center_y = int(self.owner.rect.centerx), int(self.owner.rect.centery)
            # Wave of bullets.
            b = Bullet(self.bullet_type, Vector2(center_x - 8, center_y), firing_velocity, Vector2(self.accel, self.accel), self.owner, self.bullet_scale, bullets,
                   targets=players)
            self.projectiles.append(b)
            ENEMY_FIRE_SOUND.play()

        # Record that this shot was made.
        self.previous_fire_time = pygame.time.get_ticks()

class BurstPattern(Pattern):
    """
    A BurstPattern fires a burst of bullets one after another (like a rifle burst).

    === Additional Attributes ===
    spread: total angle across the burst
    intra_delay: time in ms between bullets in the same burst
    """

    spread: float
    intra_delay: int
    _burst_queue: list[float]
    _last_burst_bullet_time: int
    _bursting: bool

    def __init__(self, player: Player, bullet_type: str, bullet_scale: tuple[int, int],
                 owner: Entity, bullets_per_shot: int, delay: int, speed: int, accel: int,
                 spread: float, intra_delay: int, aimed: bool = False):
        super().__init__(player, bullet_type, bullet_scale, owner,
                         bullets_per_shot, delay, speed, accel, aimed)
        self.spread = spread
        self.intra_delay = intra_delay
        self._burst_queue = []
        self._last_burst_bullet_time = 0
        self._bursting = False

    @override
    def update(self) -> None:
        if not self.active:
            return

        current_time = pygame.time.get_ticks()

        if not self._bursting and self._check_fire():
            self._prepare_burst()
            self._bursting = True
            self._last_burst_bullet_time = current_time - self.intra_delay  # fire immediately

        if self._bursting and current_time - self._last_burst_bullet_time >= self.intra_delay:
            self._fire_next_burst_bullet()
            self._last_burst_bullet_time = current_time

    def _prepare_burst(self) -> None:
        firing_position = Vector2(self.owner.rect.center)

        # Determine base angle.
        if self.aimed:
            to_player = Vector2(self.player.rect.center) - firing_position
            base_angle = Vector2(0, 1).angle_to(to_player) if to_player.length() > 0 else 0
        else:
            base_angle = 0

        if self.bullets_per_shot > 1:
            step = self.spread / (self.bullets_per_shot - 1)
        else:
            step = 0

        start_angle = base_angle - self.spread / 2
        self._burst_queue = [start_angle + i * step for i in range(self.bullets_per_shot)]

    def _fire_next_burst_bullet(self) -> None:
        if not self._burst_queue:
            self._bursting = False
            self.previous_fire_time = pygame.time.get_ticks()
            return

        firing_position = Vector2(self.owner.rect.center)
        angle = self._burst_queue.pop(0)
        direction = Vector2(0, 1).rotate(angle).normalize()
        velocity = direction * self.speed
        accel_vector = Vector2(self.accel, self.accel)

        b = Bullet(
            self.bullet_type,
            firing_position,
            velocity,
            accel_vector,
            self.owner,
            self.bullet_scale,
            bullets,
            targets=players
        )
        self.projectiles.append(b)
        ENEMY_FIRE_SOUND.play()


# == MISSILE PATTERNS ===
class MissileBurstPattern(Pattern):
    """
    A MissileBurstPattern fires a burst of missiles one at a time in a spread.

    === Additional Attributes ===
    spread: total angle across the burst
    intra_delay: time in ms between missiles in the same burst
    homing_speed: how quickly the missiles turn (deg/frame)
    effect_length: how long the missiles last (ms)
    """
    spread: float
    intra_delay: int
    homing_speed: float
    effect_length: int
    _burst_queue: list[float]
    _last_burst_missile_time: int
    _bursting: bool

    def __init__(self, player, bullet_type: str, bullet_scale: tuple[int, int],
                 owner, bullets_per_shot: int, delay: int, speed: int, accel: int,
                 spread: float, intra_delay: int, homing_speed: float, effect_length: int):
        super().__init__(player, bullet_type, bullet_scale, owner, bullets_per_shot, delay, speed, accel, aimed=True)
        self.spread = spread
        self.intra_delay = intra_delay
        self.homing_speed = homing_speed
        self.effect_length = effect_length
        self._burst_queue = []
        self._last_burst_missile_time = 0
        self._bursting = False

    def update(self) -> None:
        if not self.active:
            return

        current_time = pygame.time.get_ticks()

        if not self._bursting and self._check_fire():
            self._prepare_burst()
            self._bursting = True
            self._last_burst_missile_time = current_time - self.intra_delay

        if self._bursting and current_time - self._last_burst_missile_time >= self.intra_delay:
            self._fire_next_missile()
            self._last_burst_missile_time = current_time

    def _prepare_burst(self) -> None:
        firing_position = Vector2(self.owner.rect.center)

        to_player = Vector2(self.player.rect.center) - firing_position
        base_angle = Vector2(0, 1).angle_to(to_player) if to_player.length() > 0 else 0

        if self.bullets_per_shot > 1:
            step = self.spread / (self.bullets_per_shot - 1)
        else:
            step = 0

        start_angle = base_angle - self.spread / 2
        self._burst_queue = [start_angle + i * step for i in range(self.bullets_per_shot)]

    def _fire_next_missile(self) -> None:
        if not self._burst_queue:
            self._bursting = False
            self.previous_fire_time = pygame.time.get_ticks()
            return

        firing_position = Vector2(self.owner.rect.center)
        angle = self._burst_queue.pop(0)
        direction = Vector2(0, 1).rotate(angle).normalize()
        velocity = direction * self.speed
        accel_vector = Vector2(self.accel, self.accel)

        missile = Missile(
            self.bullet_type,
            firing_position,
            velocity,
            accel_vector,
            self.owner,
            self.player,
            self.homing_speed,
            self.effect_length,
            self.bullet_scale,
            bullets,
            targets=players
        )

        self.projectiles.append(missile)
        ENEMY_FIRE_SOUND.play()

# == LASER PATTERNS ==
class RotatingLaserPattern(Pattern):
    """
    A RotatingLaserPattern implements Pattern and is a snowflake-shaped attack pattern.

    === Public Attributes ===
    bullet_type: the string name of this type of bullet used in the pattern
    width: the width of this laser
    owner: the entity from which this pattern originated
    bullets_per_shot: the number of bullets per shot in this pattern
    effect_length: how long the lasers stay activated
    delay: the delay between distinct shots in this pattern in ms
    spin_speed: the speed at which this snowflake pattern spins, in degrees per bullet.
    previous_fire_time: the last time a shot was fired in this pattern in ms

    === Repr. Invariants ===
    previous_fire_time >= 0
    delay >= 0
    """
    # == Implementation Details ==
    # _offset: the offset of this spinning snowflake in degrees

    spin_speed: int
    effect_length: int
    _offset: int

    spin_speed: int
    effect_length: int
    _offset: int

    def __init__(self, player, laser_type: str, width: int, owner, laser_count: int, delay: int, effect_length: int,
                 spin_speed=0):
        super().__init__(player, laser_type, (width, 300), owner, laser_count, delay, 0, 0, False)
        self.spin_speed = spin_speed
        self.width = width
        self.effect_length = effect_length
        self._offset = 0
        self.lasers = []
        self.spawned = False

    def update(self) -> None:
        if not self.active:
            return

        self._offset = (self._offset + self.spin_speed) % 360
        center = Vector2(self.owner.rect.center)

        if not self.spawned:
            self._fire()
            self.spawned = True

        LASER_WIDTH = self.width

        orbit_center = Vector2(self.owner.rect.center)

        for laser, base_angle in self.lasers:
            angle = round((base_angle + self._offset)) % 360
            direction = Vector2(0, -1).rotate(angle).normalize()

            laser.image, laser.mask = LaserCache.get(
                laser.name + "_" + laser.state,
                (LASER_WIDTH, help.LASER_STANDARD_LENGTH),
                angle
            )
            laser.rect = laser.image.get_rect(center=orbit_center)
            laser.position = Vector2(laser.rect.center)


    def _fire(self) -> None:
        center = Vector2(self.owner.rect.center)

        for i in range(self.bullets_per_shot):
            angle = (360 / self.bullets_per_shot) * i
            direction = Vector2(0, -1).rotate(angle).normalize()
            position = center + direction * 150

            l = laser = Laser(
                self.bullet_type,
                position,
                self.owner,
                self.width,
                self.effect_length,
                self.delay,
                lasers,
                targets=players
            )
            self.projectiles.append(l)
            self.lasers.append((laser, angle))
            print(self.lasers)

class SingleLaserPattern(Pattern):
    """
    A SingleLaserPattern spawns and optionally rotates a single laser beam.

    === Public Attributes ===
    angle: the initial angle (degrees) of the laser beam.
    spin_speed: how fast the laser rotates per frame, in degrees.
    """

    def __init__(self, player: Player, laser_type: str, width: int, owner: Entity,
                 angle: float, delay: int, effect_length: int,
                 spin_speed: float = 0):
        super().__init__(player, laser_type, (width, 300), owner, 1, delay, 0, 0, aimed=False)
        self.width = width
        self.effect_length = effect_length
        self.angle = angle
        self.spin_speed = spin_speed
        self.laser = None
        self.spawned = False

    @override
    def update(self) -> None:
        if not self.active:
            return

        # Update rotation.
        self.angle = round((self.angle + self.spin_speed)) % 360

        if not self.spawned:
            self._fire()
            self.spawned = True

        # Update laser position and rotation.
        laser = self.laser
        orbit_center = Vector2(self.owner.rect.center)

        laser.image, laser.mask = LaserCache.get(
            laser.name + "_" + laser.state,
            (self.width, help.LASER_STANDARD_LENGTH ),  # or help.LASER_STANDARD_LENGTH if defined
            self.angle
        )

        laser.rect = laser.image.get_rect(center=orbit_center)
        laser.position = Vector2(laser.rect.center)

    def _fire(self) -> None:
        center = Vector2(self.owner.rect.center)
        direction = Vector2(0, -1).rotate(self.angle).normalize()
        position = center + direction * 150

        laser = Laser(
            self.bullet_type,
            position,
            self.owner,
            self.width,
            self.effect_length,
            self.delay,
            lasers,
            targets=players
        )

        self.laser = laser
        self.projectiles.append(laser)


class MultiLaserPattern(Pattern):
    """
    A MultiLaserPattern fires multiple lasers arranged radially, each with optional rotation.

    === Public Attributes ===
    angles: list of base angles in degrees (e.g. [0, 90, 180, 270])
    spin_speed: how fast all lasers rotate per frame, in degrees
    """

    def __init__(self, player: Player, laser_type: str, width: int, owner: Entity,
                 angles: list[float], delay: int, effect_length: int,
                 spin_speed: float = 0):
        super().__init__(player, laser_type, (width, 300), owner, len(angles), delay, 0, 0, aimed=False)
        self.width = width
        self.effect_length = effect_length
        self.angles = angles
        self.spin_speed = spin_speed
        self.lasers: list[tuple[Laser, float]] = []
        self.spawned = False
        self._rotation_offset = 0.0

    @override
    def update(self) -> None:
        if not self.active:
            return

        self._rotation_offset = (self._rotation_offset + self.spin_speed) % 360
        if not self.spawned:
            self._fire()
            self.spawned = True

        if not self.owner.alive:
            for laser, _ in self.lasers:
                laser.kill()
            return

        orbit_center = Vector2(self.owner.rect.center)

        for laser, base_angle in self.lasers:
            angle = round((base_angle + self._rotation_offset)) % 360
            direction = Vector2(0, -1).rotate(angle)

            laser.image, laser.mask = LaserCache.get(laser.name + "_" + laser.state, (self.width, help.LASER_STANDARD_LENGTH), angle)
            laser.rect = laser.image.get_rect(center=orbit_center)
            laser.position = Vector2(laser.rect.center)


    def _fire(self) -> None:
        center = Vector2(self.owner.rect.center)

        for angle in self.angles:
            direction = Vector2(0, -1).rotate(angle)
            position = center + direction * 150  # Start slightly away from center.

            laser = Laser(
                self.bullet_type,
                position,
                self.owner,
                self.width,
                self.effect_length,
                self.delay,
                lasers,
                targets=players
            )

            self.lasers.append((laser, angle))
            self.projectiles.append(laser)


class FanLaserPattern(Pattern):
    """
    A FanLaserPattern is a fan of lasers that can optionally aim at the player.

    === Public Attributes ===
    fan_angle: total angle (in degrees) of the spread
    width: width of each laser
    effect_length: how long each laser fires when deadly
    delay: how long each laser stays in warning mode
    lasers: list of (Laser, relative_angle) tuples
    aimed: whether this fan follows the player
    aim_speed: how fast this fan can turn to follow the player, in degrees/frame

    == Repr. Invariants ==
    self.aim_speed == 0 iff self.aimed == False
    """
    aimed: bool
    aim_speed: float

    def __init__(self, player: Player, laser_type: str, width: int, owner: Entity,
                 laser_count: int, delay: int, effect_length: int, fan_angle: float, aimed: bool=False, aim_speed: float=0):
        super().__init__(player, laser_type, (width, 300), owner, laser_count, delay, 0, 0, aimed=aimed)
        self.width = width
        self.effect_length = effect_length
        self.fan_angle = fan_angle
        self.lasers: list[tuple[Laser, float]] = []
        self.spawned = False
        self._offset = 0
        self.aim_speed = aim_speed
    @override
    def update(self) -> None:
        if not self.active:
            return

        center = Vector2(self.owner.rect.center)

        if self.aimed:
            # Find the angle to the player.
            target_vector = (Vector2(self.player.rect.center) - center).normalize()
            target_angle = Vector2(0, -1).angle_to(target_vector)

            # Smooth turning toward the target.
            delta = (target_angle - self._offset + 180) % 360 - 180
            delta = max(-self.aim_speed, min(self.aim_speed, delta))
            self._offset = (self._offset + delta) % 360
        else:
            self._offset = 0

        if not self.spawned:
            self._fire()
            self.spawned = True

        angle_step = self.fan_angle / (self.bullets_per_shot - 1) if self.bullets_per_shot > 1 else 0
        start_angle = self._offset - self.fan_angle / 2

        if not self.spawned:
            self._fire()
            self.spawned = True

        angle_step = self.fan_angle / (self.bullets_per_shot - 1) if self.bullets_per_shot > 1 else 0
        start_angle = self._offset - self.fan_angle / 2

        for i, (laser, _) in enumerate(self.lasers):
            raw_angle = start_angle + i * angle_step
            angle = round(raw_angle) % 360  # use this throughout

            # Only reassign image if necessary
            if not hasattr(laser, "_last_angle") or laser._last_angle != angle:
                laser.image, laser.mask = LaserCache.get(
                    laser.name + "_" + laser.state,
                    (self.width, help.LASER_STANDARD_LENGTH),
                    angle
                )
                laser._last_angle = angle

            laser.rect = laser.image.get_rect(center=center)
            laser.position = Vector2(laser.rect.center)

    def _fire(self) -> None:
        """Store all lasers to be fired."""
        center = Vector2(self.owner.rect.center)
        target_vector = Vector2(self.player.rect.center) - center
        if target_vector.length() != 0:
            self._offset = Vector2(0, -1).angle_to(target_vector.normalize())
        else:
            self._offset = 0

        for i in range(self.bullets_per_shot):
            laser = Laser(
                self.bullet_type,
                Vector2(self.owner.rect.center),
                self.owner,
                self.width,
                self.effect_length,
                self.delay,
                lasers,
                targets=players
            )
            self.lasers.append((laser, 0))  # Relative angle stored but recalculated every frame.
            self.projectiles.append(laser)

class CompoundPattern:
    """
    A CompoundPattern contains and manages multiple bullet patterns as a unit.

    === Public Attributes ===
    patterns: a list of active bullet patterns this compound contains
    active: whether the compound pattern is currently active
    """

    patterns: list[Pattern]
    active: bool

    def __init__(self, patterns: list[Pattern]) -> None:
        self.patterns = patterns
        self.active = True

    def update(self) -> None:
        """Activate all patterns part of this compound pattern."""
        if not self.active:
            return

        for pattern in self.patterns:
            pattern.update()

    def kill_projectiles(self) -> None:
        for pattern in self.patterns:
            pattern.active = False
            pattern.kill_projectiles()
