"""
spawner.py

This is a utility file containing useful movement patterns for enemies.
TODO: refactor this into a more convenient location.
"""

from formation import *
from enemy import *
import math
import random
from ui import *

# == MOVEMENT PATTERNS ==
def straight_down_slow(enemy: Entity):
    enemy.velocity = Vector2(0, STAGE_SCROLL_SPEED + 2)

def swoop_in_left(enemy: Entity):
    if not hasattr(enemy, "_init"):
        enemy.velocity = Vector2(2.5, STAGE_SCROLL_SPEED + 2)
        enemy._init = True

def swoop_in_right(enemy: Entity):
    if not hasattr(enemy, "_init"):
        enemy.velocity = Vector2(-2.5, 2)
        enemy._init = True

def sine_wave(enemy: Entity):
    if not hasattr(enemy, "_spawn_x"):
        enemy._spawn_x = enemy.position.x
        enemy._start_time = pygame.time.get_ticks()

    t = (pygame.time.get_ticks() - enemy._start_time) / 1000.0  # seconds
    enemy.position.x = enemy._spawn_x + 40 * math.sin(t * 3)     # 3 Hz wiggle
    enemy.velocity.y = 1.8

def bezier_point(t: float, p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2) -> Vector2:
    """Return the point on the cubic Bezier curve at time t ∈ [0,1]."""
    return ((1 - t) ** 3) * p0 + \
           3 * ((1 - t) ** 2) * t * p1 + \
           3 * (1 - t) * (t ** 2) * p2 + \
           (t ** 3) * p3

def make_bezier_curve(p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2, duration: float = 2.0):
    """
    Returns a movement_fn that causes an enemy to follow the cubic Bezier path
    over `duration` seconds.
    """
    def bezier_move(enemy: Entity):
        if not hasattr(enemy, "_bezier_t"):
            enemy._bezier_start = pygame.time.get_ticks()
            enemy._bezier_t = 0

        elapsed = (pygame.time.get_ticks() - enemy._bezier_start) / 1000.0
        t = min(elapsed / duration, 1.0)
        enemy._bezier_t = t

        pos = bezier_point(t, p1, p2, p3, p4)
        enemy.position = pos
        enemy.rect.center = pos

        # Kill once curve is done.
        if t >= 1.0:
            enemy.kill()

    return bezier_move

def boss_random_wander(enemy: Entity):
    if not hasattr(enemy, "_next_target"):
        enemy._next_target = Vector2(400, 150)
        enemy._move_timer = pygame.time.get_ticks()

    now = pygame.time.get_ticks()
    if now - enemy._move_timer > 3000:  # Pick a new location every 3s.
        x = random.randint(100, CANVAS_WIDTH - 100)
        y = random.randint(100, 300)
        enemy._next_target = Vector2(x, y)
        enemy._move_timer = now

    direction = (enemy._next_target - enemy.position)
    if direction.length() > 1:
        direction = direction.normalize()
        enemy.velocity = direction * 1.5
    else:
        enemy.velocity = Vector2(0, 0)

def stationary(enemy: Entity):
    enemy.velocity = Vector2(0, 0)
