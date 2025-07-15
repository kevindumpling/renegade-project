"""
boss.py

This file contains all behavior and aspects related to bosses with named attacks.
"""

from typing import Callable
import pygame
from pattern import *
import help
from entity import *
from ui import *
from bullet import Bomb

class BossPhase:
    """
    A single phase of a boss fight, containing patterns and optional duration.

    === Public Attributes ===
    name: the name of this phase
    pattern_defs: a list of tuples.
        - The first element of the tuple is a Callable that takes an FiringSite or OffsetFiringSite argument and returns
        a Pattern or CompoundPattern whose owner is that Site. NOTE: When using a FiringSite, HARDCODE one of the
        sides into the pattern INSTEAD of having the Callable take the Site parameter to prevent the site from moving.
            - Recall that an OffsetFiringSite follows the boss and maintains a relative reference to the boss center,
                while a FiringSite does not and remains in the same location always.
        - The second element of the tuple is a Vector2 indicating the absolute or relative position of the FiringSite or
        OffsetFiringSite associated with the Callable in question.
    max_hp: maximum HP for this phase
    duration: how long (in ms) the phase lasts (optional; overrides HP-based transitions)
    current_hp: current remaining HP in this phase
    start_time: timestamp when the phase began
    patterns: the actual instantiated patterns for this phase
    banner: a UI banner object for displaying the attack name

    === Repr. Invariants ===
    self.rect.center == self.position.

    """
    name: str
    pattern_defs: list[tuple[Callable[[OffsetFiringSite | FiringSite], Pattern | CompoundPattern], Vector2]]
    max_hp: int
    duration: int | None
    current_hp: int
    start_time: int | None
    patterns: list[Pattern]
    banner: AttackBanner

    def __init__(self, name: str, pattern_defs: list[tuple[Callable[[OffsetFiringSite | FiringSite], Pattern | CompoundPattern], Vector2]], max_hp: int,
                 duration: int = None):
        self.name = name
        self.pattern_defs = pattern_defs
        self.max_hp = max_hp
        self.duration = duration
        self.current_hp = max_hp
        self.start_time = None
        self.patterns: list[Pattern] = []

        # Attach a unique banner to this phase.
        self.banner = AttackBanner(self.name)  # Don't add to group until needed.

    def start(self, boss: Entity):
        self.start_time = pygame.time.get_ticks()
        self.current_hp = self.max_hp
        self.patterns = []

        for pattern_fn, offset in self.pattern_defs:
            site = OffsetFiringSite(boss, offset, 0, global_sprites)
            pattern = pattern_fn(site)
            self.patterns.append(pattern)

        # Show the banner.
        ui.add(self.banner)
        self.banner.timer = pygame.time.get_ticks()
        self.banner.state = 'showing'
        self.banner.set_alpha(255)

    def update_ui(self, surface: pygame.Surface):
        self.banner.update()


class Boss(Entity):
    """
    A boss enemy that transitions through multiple phases, each with its own patterns and health.

    === Public Attributes ===
    phases: list of all phases the boss will cycle through
    current_phase: the currently active BossPhase object
    movement: function that defines the boss's movement
    active: whether the boss is active on screen
    targets: the group of targets the boss can collide with
    healthbar: visual health bar for the current phase
    """

    phases: list[BossPhase]
    _current_phase_index: int
    current_phase: BossPhase
    _movement: Callable[['Boss'], None]
    active: bool
    _targets: pygame.sprite.Group
    _phase_transitioning: bool
    _healthbar: BossHealthBar

    def __init__(self, name: str, position: Vector2,
                 phases: list[BossPhase], movement: Callable[['Boss'], None], reward: int,
                 *groups):
        super().__init__(name, phases[0].max_hp, position, ZERO_VECTOR, ZERO_VECTOR, (90, 90), reward, '', *groups)
        self.phases = phases
        self._current_phase_index = 0
        self.current_phase = phases[0]
        self._movement = movement
        self.active = True
        self.targets = players
        self._phase_transitioning = False
        self._healthbar = BossHealthBar(self, 800, 5, ui)

        self._start_phase()

    def _start_phase(self):
        Bomb('screen_clear', self, 400, player_bullets, targets=bullets)
        help.STAGE_SCROLL_SPEED = 0
        self.current_phase = self.phases[self._current_phase_index]
        self.current_phase.start(self)
        self.health = self.current_phase.max_hp
        print(f"Entering phase: {self.current_phase.name}")


    def update(self):
        if not self.active:
            return

        self._movement(self)

        for pattern in self.current_phase.patterns:
            pattern.update()

        if self.current_phase.duration:
            elapsed = pygame.time.get_ticks() - self.current_phase.start_time
            if elapsed > self.current_phase.duration:
                self._next_phase()

        super().update()

    def take_damage(self):
        if self.bomb_immunity:
            return

        self.current_phase.current_hp -= 1
        self.health = self.current_phase.current_hp

        if self.current_phase.current_hp <= 0 and not self._phase_transitioning:
            ENEMY_DEATH_SOUND.play()
            self._next_phase()

    def _next_phase(self):
        self._phase_transitioning = True
        self._current_phase_index += 1

        # Clear this pattern.
        Bomb('screen_clear', self, 400, player_bullets, targets=bullets)
        for pattern in self.current_phase.patterns:
            pattern.active = False
            pattern.kill_projectiles()

        if self.current_phase.banner.alive():
            self.current_phase.banner.kill()

        if self._current_phase_index >= len(self.phases):
            ENEMY_DEATH_SOUND.play()
            animated = AnimatedGIFSprite(
                "death",
                (70, 70),
                (self.rect.centerx, self.rect.centery),
                100,
                1500,
                ui
            )
            self.kill()
            help.STAGE_SCROLL_SPEED = ORIGINAL_SCROLL_SPEED
            return

        self._start_phase()
        self._phase_transitioning = False


    @override
    def _constrain_movement(self) -> None:
        pass

    @override
    def check_collisions(self, targets: pygame.sprite.Group | None = None) -> None:
        pass
