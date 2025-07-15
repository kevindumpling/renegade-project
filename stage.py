from dataclasses import dataclass
from typing import Callable, List
import pygame
from help import *

@dataclass
class StageEvent:
    """
    Represents an event occuring in a stage.

    === Public Attributes ===
    time: the time this event should be triggered, in ms
    action: the action to be taken when this event occurs
    triggered: whether this event has already activated
    """
    time: int
    action: Callable[[], None]
    triggered: bool = False


class StageHandler:
    """
    A StageHandler organizes the various StageEvents that occur in a Stage.
    All stages are represented by StageHandler instances.
    NOTE: reccomended to use lambda or partials on existing spawn functions when passing events for ease of use.

    === Public Attributes ===
    events: list of StageEvents that are contained within this stage.
    conditional_events: list of those StageEvents that activate upon a conditional.
    start_time: the time at which this StageHandler stage was initialized.

    === Repr. Invariants ===
    self.start_time >= 0
    """

    # == Implementation Details ==
    # _waves_done: whether all the waves in this stage have been spawned.

    events: list[StageEvent]
    conditional_events: list[tuple[Callable[[], bool], Callable]]
    start_time: int
    _waves_done: bool

    def __init__(self):
        self.events: list[StageEvent] = []
        self.conditional_events: list[tuple[Callable[[], bool], Callable]] = []
        self.start_time = pygame.time.get_ticks()
        self._waves_done = False

    def schedule(self, delay_ms: int, action: Callable):
        """Schedule <action> to occur after <delay_ms>."""
        self.events.append(StageEvent(time=delay_ms, action=action))

    def wait_until(self, condition: Callable[[], bool], action: Callable):
        """Execute <action> once <condition()> becomes True."""
        self.conditional_events.append((condition, action))

    def update(self):
        current_time = pygame.time.get_ticks() - self.start_time

        for event in self.events:
            if not event.triggered and current_time >= event.time:
                event.action()
                event.triggered = True

        for condition, action in self.conditional_events[:]:
            if condition():
                action()
                self.conditional_events.remove((condition, action))

    def reset(self):
        """Reset this stage to an empty StageHandler."""
        self.start_time = pygame.time.get_ticks()
        for e in self.events:
            e.triggered = False
        self.conditional_events.clear()
        self.events.clear()

    def mark_waves_done(self):
        """Signal that all enemy waves have been scheduled."""
        self._waves_done = True

    def all_waves_scheduled(self) -> bool:
        """Return true iff self._waves_done."""
        return self._waves_done
