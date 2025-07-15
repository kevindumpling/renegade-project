"""
background.py

This file contains the ScrollingBackground and StaticBackground classes.
"""

import pygame
from help import *

class ScrollingBackground(pygame.sprite.Sprite):
    """
    A vertical-scrolling background that loops continuously to simulate motion.

    === Public Attributes ===
    image: the visible portion of the background displayed to the screen
    rect: the positioning rectangle of the background
    """

    _full_image: pygame.Surface
    _speed: int
    _offset: int
    image: pygame.Surface
    rect: pygame.Rect

    def __init__(self, name: str, *groups: pygame.sprite.Group):
        super().__init__()
        self._full_image = load_image(name, (CANVAS_WIDTH, CANVAS_HEIGHT * 2))
        self._speed = STAGE_SCROLL_SPEED
        self._offset = 0  # Vertical offset.

        self.image = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.rect = self.image.get_rect(topleft=(0, 0))

        for group in groups:
            group.add(self)

    def update(self):
        # Scroll down.
        self._offset = (self._offset - self._speed) % CANVAS_HEIGHT
        self.image.blit(self._full_image, (0, -self._offset))
        self.image.blit(self._full_image, (0, CANVAS_HEIGHT - self._offset))


class StaticBackground(pygame.sprite.Sprite):
    """
    A static background image that does not scroll, used for non-moving scenes.

    === Public Attributes ===
    image: the visible portion of the background
    rect: the positioning rectangle of the background
    """

    _full_image: pygame.Surface
    _offset: int
    image: pygame.Surface
    rect: pygame.Rect

    def __init__(self, name: str, *groups: pygame.sprite.Group):
        super().__init__()
        self._full_image = load_image(name, (CANVAS_WIDTH, CANVAS_HEIGHT))
        self._offset = 0  # vertical offset

        self.image = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.rect = self.image.get_rect(topleft=(0, 0))

        for group in groups:
            group.add(self)

    def update(self):
        self.image.blit(self._full_image, (0, -self._offset))
        self.image.blit(self._full_image, (0, CANVAS_HEIGHT - self._offset))
