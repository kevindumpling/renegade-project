"""
stagebuilder.py

This is the game engine of the program.
Here, methods named build_stageN: Callable[[StageHandler, player], None] contain the information
needed to build the relevant Nth stage of the game.

=== DEVELOPMENT PROCESS GUIDANCE ===

    1. First, define a stagebuilding method: Callable[[StageHandler, player], None] that will build the <stage>.
    2. Within these stagebuilders, define attack patterns as a Callable[[Entity], Pattern | CompoundPattern].
    3. Then, define 'spawner' methods in the stagebuilders to be scheduled to the <stage>.
        3.1. These are Callable[[None], None].
        3.2. They contain any of PopcornFormation, BigEnemyFormation, or Boss.
    4. Once all of the 'waves' are defined through the 'spawner' methods in step 3, schedule them to <stage.>
        4.1. The utility methods provided in each stage between the line indicated # == UTILITY == are important.
        4.2. Ensure to kill_static_sites and then mark_waves_done at the end of the stage.
        4.3. Then, wait_until no_more_enemies_and_formations to spawn_boss.
        4.4. Then, wait_until no_more_enemies_and_formations to end_stage.
        4.5. end_stage must:
            4.5.1. Change the gamestate to the next stage.
            4.5.2. Change player.stage_name and stage_number.
            4.5.3. (Optional) Turn off the music and kill the background.
            4.5.4. (Optional) Provide a bonus number of lives and bombs to the player.
            4.5.5. Make the next stage, contained in help.py, into a new StageHandler.
            4.5.6. Call the relevant stagebuilder method on the next stage (i.e, build_stageN(help.stageN, player)
        4.6. start_mission must:
            4.6.1. Set the gamestate to this stage's gamestate.
            4.6.2. Initialize the mixer and play this stage's music.
            4.6.3. (Optional) Display this stage's title with a TypingBanner.

"""


from pygame import Vector2
from formation import *
from pattern import *
from boss import *
from spawner import *
from entity import FiringSite
from enemy import *
import random
from stage import StageHandler
from background import ScrollingBackground

def build_stage1(stage: StageHandler, player: Player):
    RIGHT_UPPER = FiringSite(Vector2(0, 200), 0, enemies)
    LEFT_LOWER = FiringSite(Vector2(790, 600), 0, enemies)
    STATIC_SITES = [RIGHT_UPPER, LEFT_LOWER]
    boss_spawned = False

    # === REGULAR PATTERNS ===
    def popcorn_bursts_1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [0, 20, 40], int(1500 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, aimed=True)

    def popcorn_circles1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, 3, int(1500 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, aimed=False)

    def popcorn_bursts2(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (90, 90), site, 2, int(1500 + 500*(1-help.difficulty_modifier)), int(8 * help.difficulty_modifier), 0, 10, 50, True)

    def popcorn_fan_1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60, 80, 100, 120], int(700 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, aimed=False)

    def popcorn_circles2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(10 * help.difficulty_modifier), int(1000 + 500*(1-help.difficulty_modifier)), 5, 0, aimed=False)

    def midboss_circles1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(20 * help.difficulty_modifier), int(1000 + 500*(1-help.difficulty_modifier)), int(4 * help.difficulty_modifier), 0, aimed=False)

    def midboss_fan1(site: Entity) -> CompoundPattern:
        a = FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60, 80, 100, 120], int(500 + 500*(1-help.difficulty_modifier)), int(7 * help.difficulty_modifier), 0, aimed=True)
        b = midboss_circles1(RIGHT_UPPER)
        return CompoundPattern([a, b])

    def midboss_spiral1(site: Entity) -> CompoundPattern:
        a = SpiralPattern(player, 'smallbullet', (40, 40), site, int(20 * help.difficulty_modifier), int(500 + 500*(1-help.difficulty_modifier)), 7, int(4 * help.difficulty_modifier), 0, aimed=False)
        b = midboss_circles1(LEFT_LOWER)
        return CompoundPattern([a, b])

    def midboss_missile1(site: Entity) -> CompoundPattern:
        a = MissileBurstPattern(player, 'smallbullet', (90, 90), site, 2, 2000, 2, 0, 0, 50, 1.2, int(5000 * help.difficulty_modifier))
        b = midboss_circles1(RIGHT_UPPER)
        c = midboss_circles1(LEFT_LOWER)
        return CompoundPattern([a, b, c])

    # === BOSS PATTERNS ===
    def boss_snowflake(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (40, 40), site, int(6 * help.difficulty_modifier), int(50 + 500*(1-help.difficulty_modifier)), int(6 * help.difficulty_modifier), 0, spin_speed=10, aimed=False)

    def boss_circle(site: Entity) -> CompoundPattern:
        a = BurstPattern(player, 'smallbullet', (90, 90), site, 2, 1000, int(8 * help.difficulty_modifier), 0, 10, 50, True)
        b = CirclePattern(player, 'smallbullet', (40, 40), site, int(20 * help.difficulty_modifier), int(300 + 500*(1-help.difficulty_modifier)), 6, 0, aimed=False)
        return CompoundPattern([a, b])

    def boss_fan(site: Entity) -> CompoundPattern:
        a = FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60, 80, 100, 120], int(500 + 500*(1-help.difficulty_modifier)), int(7 * help.difficulty_modifier), 0, aimed=True)
        b = RotatingLaserPattern(player, 'laser', 20, site, 5, 500, int(500 * help.difficulty_modifier), 0.4)
        return CompoundPattern([a, b])

    def boss_cage(site: Entity) -> CompoundPattern:
        a = CirclePattern(player, 'smallbullet', (40, 40), site, int(20 * help.difficulty_modifier), int(400 + 500*(1-help.difficulty_modifier)), 6, 0, aimed=False)
        b = MultiLaserPattern(player, 'laser', 20, site, [10, 30, 50, 70, 90, 120, 160, 190, 220, 240, 280, 310, 340, 350], int(500 + 500*(1-help.difficulty_modifier)), int(500 * help.difficulty_modifier), 0)
        return CompoundPattern([a, b])

    def boss_blasts(site: Entity) -> CompoundPattern:
        a = CirclePattern(player, 'smallbullet', (90, 90), site, int(8 * help.difficulty_modifier), int(500 + 500*(1-help.difficulty_modifier)), 10, 0, aimed=False)
        b = BurstPattern(player, 'smallbullet', (90, 90), site, 3, int(500 + 500*(1-help.difficulty_modifier)), 8, 0, 10, 50, True)
        return CompoundPattern([a, b])

    # === WAVE SPAWNERS ===
    def intro_w1():
        PopcornFormation(
            'f14',
            Vector2(200, 50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), straight_down_slow, popcorn_bursts_1, 2),
                FormationEntry(Vector2(100, 50), straight_down_slow, popcorn_bursts_1, 2),
                FormationEntry(Vector2(200, 0), straight_down_slow, popcorn_bursts_1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
            ]
        )
    def intro_w2():
        PopcornFormation(
            'f14',
            Vector2(600, 50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), straight_down_slow, popcorn_bursts_1, 2),
                FormationEntry(Vector2(100, 100), straight_down_slow, popcorn_bursts_1, 2),
                FormationEntry(Vector2(200, 0), straight_down_slow, popcorn_bursts_1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
            ]
        )
    def intro_w3():
        PopcornFormation(
            'f14',
            Vector2(300, 20),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(600, 100), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(50, 50), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(110, 50), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(210, 60), straight_down_slow, popcorn_fan_1, 2),
                FormationEntry(Vector2(98, 80), straight_down_slow, popcorn_fan_1, 2),
                FormationEntry(Vector2(435, 10), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(512, 100), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(588, 20), straight_down_slow, popcorn_fan_1, 2),
                FormationEntry(Vector2(700, 300), straight_down_slow, popcorn_circles1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
            ]
        )
    def intro_w4():
        PopcornFormation(
            'f14',
            Vector2(300, 20),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200), 6), popcorn_bursts2, 2),
                FormationEntry(Vector2(100, 60), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200),6), popcorn_bursts2, 2),
                FormationEntry(Vector2(200, 110), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200),6), popcorn_bursts2, 2),
                FormationEntry(Vector2(100, 50), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(200, 220), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(300, 80), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(400, 10), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(500, 100), straight_down_slow, popcorn_circles1, 2),
                FormationEntry(Vector2(600, 20), straight_down_slow, popcorn_circles1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
            ]
        )
    def bomb_w1():
        BigEnemyFormation(
            'f16',
            Vector2(400, -40),
            [
                BigEnemyEntry(Vector2(0, 0), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200), 10),[popcorn_bursts2], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(100, 142), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200), 10),[popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(600, 165), make_bezier_curve(Vector2(800, 0), Vector2(100, 0), Vector2(400, 200), Vector2(0, 200),10), [popcorn_bursts2], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(600, 215), make_bezier_curve(Vector2(800, 100), Vector2(100, 100), Vector2(400, 200), Vector2(0, 200),10), [popcorn_fan_1], interval=4000, health=10, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def bomb_w2():
        BigEnemyFormation(
            'f16',
            Vector2(400, -40),
            [
                BigEnemyEntry(Vector2(0, 0), sine_wave,[popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(100, 150), sine_wave,[popcorn_fan_1], interval=4000, health=5, reward=10),
                BigEnemyEntry(Vector2(600, 210), sine_wave, [popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(240, 78), swoop_in_left, [popcorn_circles2], interval=4000, health=5, reward=10),
                BigEnemyEntry(Vector2(240, 78), swoop_in_left, [popcorn_circles1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(367, 146), swoop_in_left, [popcorn_circles2], interval=4000, health=5, reward=10),
                BigEnemyEntry(Vector2(240, 78), swoop_in_left, [popcorn_circles1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(240, 178), swoop_in_right, [popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(240, 99), swoop_in_right, [popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(600, 300),make_bezier_curve(Vector2(800, 0), Vector2(100, 0), Vector2(400, 200), Vector2(0, 200),10), [popcorn_bursts2], interval=4000, health=10, reward=10),

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def midboss_w1():
        BigEnemyFormation(
            'neonyf23',
            Vector2(400, 100),
            [
                BigEnemyEntry(Vector2(0, 0), boss_random_wander,[midboss_fan1, midboss_spiral1, midboss_missile1], interval=6000, health=100, reward=10),  # health = 100
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(-400, 0), midboss_circles1, 0),
                FiringSiteEntry(Vector2(800, 0), midboss_circles1, 0)

            ]
        )

    def spawn_boss():
        nonlocal boss_spawned
        if boss_spawned:
            return
        boss_spawned = True

        boss = Boss(
            "boss_carrier",
            Vector2(400, 100),
            [
                BossPhase("Furious Inquiry of Invader's Intent", [(boss_snowflake, Vector2(70, 50))], max_hp=100),  # 100
                BossPhase("Realization of The Renegade's Danger", [(boss_circle, Vector2(10, 50))], max_hp=100),
                BossPhase("Attempted Containment of the Incoming Threat", [(boss_fan, Vector2(10, 50))], max_hp=100),
                BossPhase("Further Containment of the Incoming Threat", [(boss_cage, Vector2(10, 50))], max_hp=100),
                BossPhase("Desperate Attempt to Remove the Enemy", [(boss_blasts, Vector2(10, 50))], max_hp=100),
            ],
            boss_random_wander,
            20,
            enemies
        )

    # == UTILITY ==
    def kill_static_sites():
        for site in STATIC_SITES:
            site.kill()

    def no_more_enemies_and_formations():
        return stage.all_waves_scheduled() and len(enemies) == 0 and len(formations) == 0

    end_banner = None
    def show_end_banner():
        nonlocal end_banner
        end_banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name} ... COMPLETE', 20,
                        Vector2(CANVAS_WIDTH // 2, 200), duration_ms=7000, start_delay=1000)

    def end_banner_done():
        return end_banner.done if end_banner is not None else False

    def always_true():
        """DEBUGGING: ALWAYS RETURNS TRUE"""
        return True

    def end_stage():
        help.gamestate = 'stage2'
        player.stage_name = 'SILENT NIGHT, ALL IS BRIGHT'
        player.stage_number = 2
        bg.kill()
        pygame.mixer.music.pause()

        bonus_lives = 0
        bonus_bombs = 0
        match help.difficulty:
            case 'NOVICE':
                bonus_lives = 1
                bonus_bombs = 2
            case 'PILOT':
                bonus_lives = 1
                bonus_bombs = 1
            case 'VETERAN':
                bonus_lives = 1
                bonus_bombs = 1
            case 'ACE':
                bonus_lives = 0
                bonus_bombs = 1
        player.lives = min(player.max_lives, player.lives + player.max_lives // 5 + bonus_lives)
        player.bombs = min(player.max_bombs, player.bombs + player.max_bombs // 5 + bonus_bombs)

        help.stage2 = StageHandler()
        build_stage2(help.stage2, player)

    def start_mission():
        help.gamestate = 'stage1'

        pygame.mixer.init()
        pygame.mixer.music.load(resource_path('sounds/RENEGADE.mp3'))
        pygame.mixer.music.play(-1, fade_ms=1000)

        if not help.skip_banners:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=13000)

            intro1 = TypingBanner('DIRECTIVE: Take the plane from them and run.', 20, Vector2(300, 300), start_delay=1000)
            intro2 = TypingBanner('STATUS REPORT: You are...', 20, Vector2(500, 500), start_delay=6000)
            intro3 = TypingBanner('...a RENEGADE.', 30, Vector2(200, 600), start_delay=8000)
        else:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=0)

    # === SCHEUDLE EVENTS ===
    START_TIME = 17000 if not help.skip_banners else 0 # 17000
    ONE_SECOND = 1000

    bg = ScrollingBackground('stage1background', background)

    # BEGIN MISSION
    stage.schedule(0, start_mission)

    # STAGE ENEMIES
    stage.schedule(START_TIME + 1*ONE_SECOND, intro_w1)
    stage.schedule(START_TIME + 1*ONE_SECOND, intro_w2)
    stage.schedule(START_TIME + 3*ONE_SECOND, intro_w1)
    stage.schedule(START_TIME + 5*ONE_SECOND, intro_w3)
    stage.schedule(START_TIME + 5*ONE_SECOND, intro_w4)
    stage.schedule(START_TIME + 6*ONE_SECOND, bomb_w1)
    stage.schedule(START_TIME + 12*ONE_SECOND, bomb_w2)
    stage.schedule(START_TIME + 12*ONE_SECOND, intro_w2)
    stage.schedule(START_TIME + 20*ONE_SECOND, intro_w2)
    stage.schedule(START_TIME + 20*ONE_SECOND, intro_w1)
    stage.schedule(START_TIME + 25*ONE_SECOND, midboss_w1)

    # PREPARE BOSS
    stage.schedule(START_TIME +  40*ONE_SECOND, kill_static_sites) # 40
    stage.schedule(START_TIME +  46*ONE_SECOND, stage.mark_waves_done)  # 46*ONE_SECOND
    stage.wait_until(no_more_enemies_and_formations, spawn_boss)

    # END LEVEL
    stage.wait_until(no_more_enemies_and_formations, show_end_banner)
    stage.wait_until(end_banner_done, end_stage)


def build_stage2(stage: StageHandler, player: Player):
    RIGHT_UPPER = FiringSite(Vector2(0, 200), 0, enemies)
    LEFT_LOWER = FiringSite(Vector2(790, 600), 0, enemies)
    STATIC_SITES = [RIGHT_UPPER, LEFT_LOWER]
    previous_stage_end = pygame.time.get_ticks()
    boss_spawned = False

    # === REGULAR PATTERNS ===
    def air_circles1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(15 * help.difficulty_modifier), int(1000 + 500*(1-help.difficulty_modifier)), 4, 0, aimed=False)

    def air_circles2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (40, 40), site, int(10 * help.difficulty_modifier), int(1500 + 500*(1-help.difficulty_modifier)), 6, 0, aimed=False)

    def air_lasers1(site: Entity) -> Pattern:
        return FanLaserPattern(player, 'laser', 20, site, 2, 1000, 500, 35, True, 1)

    def air_lasers2(site: Entity) -> Pattern:
        return FanLaserPattern(player, 'laser', 20, site, 4, int(1000 + 500*(1-help.difficulty_modifier)), int(200 * help.difficulty_modifier), 60, True, 0.2)

    def air_lasers3(site: Entity) -> Pattern:
        return RotatingLaserPattern(player, 'laser', 20, site, 3, int(1000 + 500*(1-help.difficulty_modifier)), 500, 0.5)

    def air_lasers4(site: Entity) -> Pattern:
        return RotatingLaserPattern(player, 'laser', 20, site, 3, int(1000 + 500*(1-help.difficulty_modifier)), 500, 0.5)

    def bomb_raid1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (70, 70), site, [0, 20, 40], int(1000 + 500*(1-help.difficulty_modifier)), int(12 * help.difficulty_modifier), 0, True)

    def popcorn_fan_1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60, 80, 100, 120], int(700 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, aimed=False)
    # === BOSS PATTERNS ===
    def boss_spinning(site: Entity) -> Pattern:
        return RotatingLaserPattern(player, 'laser', 20, site, 3, int(1000 + 500*(1-help.difficulty_modifier)), 500, 0.5)

    def boss_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60, 80, 100, 120], int(400 + 500*(1-help.difficulty_modifier)), int(7 * help.difficulty_modifier), 0, aimed=True)

    def boss_vertical(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, -180, int(1000 + 500*(1-help.difficulty_modifier)), 500, 0)

    def boss_machine_gun(site: Entity) -> CompoundPattern:
        a = BurstPattern(player, 'smallbullet', (90, 90), site, 3, int(100 + 500*(1-help.difficulty_modifier)), int(12 * help.difficulty_modifier), 0, 0, 50, True)
        return CompoundPattern([a])

    def boss_sprinkles(site: Entity) -> CompoundPattern:
        a = SpiralPattern(player, 'smallbullet', (20, 20), site, int(20 * help.difficulty_modifier), int(500 + 500*(1-help.difficulty_modifier)), 10, 4, 0)
        return CompoundPattern([a])

    def boss_missile(site: Entity) -> CompoundPattern:
        a = MissileBurstPattern(player, 'smallbullet', (90, 90), site, 3, 800, 4, 0, 60, 100, 0.5, int(7000 * help.difficulty_modifier))
        b = CirclePattern(player, 'smallbullet', (20, 20), site, int(20 * help.difficulty_modifier), 1000, 4, 0, False)
        return CompoundPattern([a, b])

    # === WAVE SPAWNERS ===
    def antiair1():
        BigEnemyFormation(
            'xfa33',
            Vector2(400, 0),
            [

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(-400, 0), air_circles2, 0),
                FiringSiteEntry(Vector2(200, 110), air_circles1, 0),
                FiringSiteEntry(Vector2(250, 520), air_circles1, 0),
            ]
        )
    def antiair2():
        BigEnemyFormation(
            'xfa33',
            Vector2(400, 0),
            [

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(256, 0), air_circles2, 0),
                FiringSiteEntry(Vector2(-112, 89), air_circles1, 0),
                FiringSiteEntry(Vector2(-2, 129), air_circles1, 0),
            ]
        )
    def antiair3():
        BigEnemyFormation(
            'neonb2',
            Vector2(400, 0),
            [

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(278, 0), air_lasers2, 0),
                FiringSiteEntry(Vector2(-250, -400), air_lasers2, 0),
            ]
        )
    def antiair4():
        BigEnemyFormation(
                'xfa33',
                Vector2(400, -20),
                [

                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations,
                firing_sites=[
                    FiringSiteEntry(Vector2(278, 0), air_lasers1, 0),
                    FiringSiteEntry(Vector2(-322, -92), air_lasers1, 0),
                ]
            )
    def antiair5():
        BigEnemyFormation(
                'xfa33',
                Vector2(400, -20),
                [

                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations,
                firing_sites=[
                    FiringSiteEntry(Vector2(-300, 0), air_lasers3, 0),
                ]
            )
    def antiair6():
        BigEnemyFormation(
                'xfa33',
                Vector2(400, -20),
                [

                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations,
                firing_sites=[
                    FiringSiteEntry(Vector2(300, -75), air_lasers4, 0),
                ]
            )
    def bomb_w1():
        BigEnemyFormation(
            'neonb2',
            Vector2(400, -40),
            [
                BigEnemyEntry(Vector2(0, 0), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200), 10),[bomb_raid1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(100, 142), make_bezier_curve(Vector2(0, 0), Vector2(100, 0), Vector2(400, 300), Vector2(800, 200), 10),[popcorn_fan_1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(600, 165), make_bezier_curve(Vector2(800, 0), Vector2(100, 0), Vector2(400, 200), Vector2(0, 200),10), [bomb_raid1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(600, 215), make_bezier_curve(Vector2(800, 100), Vector2(100, 100), Vector2(400, 200), Vector2(0, 200),10), [popcorn_fan_1], interval=4000, health=10, reward=10),

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def bomb_w2():
        BigEnemyFormation(
                'neonb2',
                Vector2(400, -40),
                [

                    BigEnemyEntry(Vector2(0, 0),
                                  make_bezier_curve(Vector2(0, 0), Vector2(200, 100), Vector2(400, 500),
                                                    Vector2(800, 600),
                                                    3), [bomb_raid1], interval=4000, health=10, reward=10),
                    BigEnemyEntry(Vector2(100, 142),
                                  make_bezier_curve(Vector2(0, 0), Vector2(200, 100), Vector2(400, 500),
                                                    Vector2(800, 600),
                                                    3), [bomb_raid1], interval=4000, health=10, reward=10),
                    BigEnemyEntry(Vector2(600, 100),
                                  make_bezier_curve(Vector2(0, 0), Vector2(200, 100), Vector2(400, 500),
                                                    Vector2(800, 600),
                                                    3), [bomb_raid1], interval=4000, health=10, reward=10),
                    BigEnemyEntry(Vector2(600, 56),
                                  make_bezier_curve(Vector2(0, 0), Vector2(200, 100), Vector2(400, 500),
                                                    Vector2(800, 600),
                                                    3), [bomb_raid1], interval=4000, health=10, reward=10)
                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations
            )
    def spawn_boss():
        nonlocal boss_spawned
        if boss_spawned:
            return
        boss_spawned = True

        boss = Boss(
            "boss_antiair",
            Vector2(400, 100),
            [
                BossPhase("RADARS SCANNING...", [(boss_spinning, Vector2(200, 300)), (boss_spinning, Vector2(-200, 300)), (boss_fan1, Vector2(0, 0))], max_hp=100),  # 100
                BossPhase("MACHINE GUN FIRING...", [(boss_vertical, Vector2(-100, -100)), (boss_vertical, Vector2(100, -100)), (boss_vertical, Vector2(-300, -100)), (boss_vertical, Vector2(300, -100)), (boss_vertical, Vector2(350, -100)), (boss_vertical, Vector2(-350, -100)), (boss_machine_gun, Vector2(0, 0))], max_hp=100),
                BossPhase("WARNING: MISSILE LOCK ENGAGED", [(boss_spinning, Vector2(200, -100)), (boss_spinning, Vector2(-200, -100)), (boss_spinning, Vector2(0, 300)), (boss_missile, Vector2(0, 0))], max_hp=100),
                BossPhase("WARNING: ANTI-AIRCRAFT TURRETS ONLINE", [(boss_machine_gun, Vector2(10, 50)), (boss_machine_gun, Vector2(70, 50)), (boss_sprinkles, Vector2(10, 50))], max_hp=100),
            ],
            stationary,
            20,
            enemies
        )

    # == UTILITY ==
    def kill_all():
        for site in STATIC_SITES:
            site.kill()
        for enemy in enemies:
            enemy.kill()

    def no_more_enemies_and_formations():
        return stage.all_waves_scheduled() and len(enemies) == 0 and len(formations) == 0

    end_banner = None
    def show_end_banner():
        nonlocal end_banner
        end_banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name} ... COMPLETE', 20,
                        Vector2(CANVAS_WIDTH // 2, 200), duration_ms=7000, start_delay=1000)

    def end_banner_done():
        return end_banner.done if end_banner is not None else False

    def always_true():
        """DEBUGGING: ALWAYS RETURNS TRUE"""
        return True

    def end_stage():
        help.gamestate = 'stage3'
        player.stage_name = 'CITIES DREAM OF ETERNAL SLEEP'
        player.stage_number += 1
        bg.kill()
        pygame.mixer.music.pause()

        bonus_lives = 0
        bonus_bombs = 0
        match help.difficulty:
            case 'NOVICE':
                bonus_lives = 1
                bonus_bombs = 2
            case 'PILOT':
                bonus_lives = 1
                bonus_bombs = 1
            case 'VETERAN':
                bonus_lives = 1
                bonus_bombs = 1
            case 'ACE':
                bonus_lives = 1
                bonus_bombs = 1
        player.lives = min(player.max_lives, player.lives + player.max_lives // 5 + bonus_lives)
        player.bombs = min(player.max_bombs, player.bombs + player.max_bombs // 5 + bonus_bombs)

        help.stage3 = StageHandler()
        build_stage3(help.stage3, player)

    def start_mission():
        help.gamestate = 'stage2'

        pygame.mixer.init()
        pygame.mixer.music.load(resource_path('sounds/Canyon Lullaby.mp3'))
        pygame.mixer.music.play(-1, fade_ms=1000)

        if not help.skip_banners:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=1000)
            banner2 = TypingBanner(f"...YOU'VE MADE IT OUT OF THE OUTPOST.", 20, Vector2(300, 200),
                                  start_delay=6000)
            banner3 = TypingBanner(f"THEY'RE HUNTING YOU IN THE CANYON.", 20, Vector2(400, 300),
                                   start_delay=11000)
            banner4 = TypingBanner(f"STAY LOW. AVOID ANTI-AIR SHELLS.", 20, Vector2(400, 400),
                                   start_delay=16000)
        else:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=0)

    # === SCHEUDLE EVENTS ===
    START_TIME = 21000 if not help.skip_banners else 0 # 16000, 1000
    ONE_SECOND = 1000

    bg = ScrollingBackground('stage2background', background)

    # BEGIN MISSION

    stage.schedule(0, start_mission)

    # STAGE ENEMIES
    stage.schedule(START_TIME + 1*ONE_SECOND, antiair3)
    stage.schedule(START_TIME + 10*ONE_SECOND, antiair1)

    stage.schedule(START_TIME + 18*ONE_SECOND, antiair2)
    stage.schedule(START_TIME + 25*ONE_SECOND, antiair1)
    stage.schedule(START_TIME + 25*ONE_SECOND, antiair4)
    stage.schedule(START_TIME + 35*ONE_SECOND, antiair5)
    stage.schedule(START_TIME + 38*ONE_SECOND, bomb_w1)
    stage.schedule(START_TIME + 48*ONE_SECOND, bomb_w2)
    stage.schedule(START_TIME + 48*ONE_SECOND, antiair5)
    stage.schedule(START_TIME + 52*ONE_SECOND, antiair6)
    stage.schedule(START_TIME + 52*ONE_SECOND, antiair1)
    stage.schedule(START_TIME + 58*ONE_SECOND, bomb_w1)

    # PREPARE BOSS
    stage.schedule(START_TIME +  67*ONE_SECOND, kill_all)  # 67
    stage.schedule(START_TIME +  68*ONE_SECOND, stage.mark_waves_done)  # 74*ONE_SECOND
    stage.wait_until(no_more_enemies_and_formations, spawn_boss)

    # END LEVEL
    stage.wait_until(no_more_enemies_and_formations, show_end_banner)
    stage.wait_until(end_banner_done, end_stage)


def build_stage3(stage: StageHandler, player: Player):
    RIGHT_UPPER = FiringSite(Vector2(0, 200), 0, enemies)
    LEFT_LOWER = FiringSite(Vector2(790, 600), 0, enemies)
    STATIC_SITES = [RIGHT_UPPER, LEFT_LOWER]
    previous_stage_end = pygame.time.get_ticks()
    boss_spawned = False

    # === REGULAR PATTERNS ===
    def fast_popcorn1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (90, 90), site, [0, 80, 120], 1500, int(12 * help.difficulty_modifier), 0, aimed=True)
    def fast_popcorn2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (120, 120), site, int(10 * help.difficulty_modifier), 500, int(12 * help.difficulty_modifier), 0, aimed=False)
    def fast_popcorn3(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (40, 40), site, int(10 * help.difficulty_modifier), 500, int(12 * help.difficulty_modifier), 0, aimed=True)
    def fast_popcorn4(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (80, 80), site, [0, 2, 5], 500, int(12 * help.difficulty_modifier), 0, aimed=True)

    def aimed_burst1(site: Entity) -> CompoundPattern:
        a = BurstPattern(player, 'smallbullet', (80, 80), site, 5, 400, int(20 * help.difficulty_modifier), 0, 5, 150, aimed=True)
        b = CirclePattern(player, 'smallbullet', (60, 60), site, int(20 * help.difficulty_modifier), 2000, int(12 * help.difficulty_modifier), 0, aimed=True)
        return CompoundPattern([a, b])
    def blast_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (40, 40), site, [0, 20, 40, 60], 300, int(12 * help.difficulty_modifier), 0, aimed=True)
    def blast_circles1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (110, 110), site, int(20 * help.difficulty_modifier), 2000, int(13 * help.difficulty_modifier), 0, aimed=True)
    def blast_combo1(site: Entity) -> CompoundPattern:
        a = blast_fan1(site)
        b = blast_circles1(site)
        return CompoundPattern([a, b])

    def bombs1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (70, 70), site, [0, 40, 80], 500, int(12 * help.difficulty_modifier), 0, aimed=False)
    def trickle1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [0, 20, 40, 60, 80, 100], 100, int(6 * help.difficulty_modifier), 0, aimed=True)

    def sky_lasers1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [10, 80], 1000, 500, 1)

    # === BOSS PATTERNS ===
    def boss_circle(site: Entity) -> CompoundPattern:
        a = MultiLaserPattern(player, 'laser', 20, site, [0, 90, 180, 270], 0, 9999, 0.8 * help.difficulty_modifier)
        b = CirclePattern(player, 'smallbullet', (60, 60), site, int(20 * help.difficulty_modifier), 1000, int(15 * help.difficulty_modifier), 0, False)
        return CompoundPattern([a, b])

    def boss_blasts(site: Entity) -> CompoundPattern:
        a = MultiLaserPattern(player, 'laser', 20, site, [0, 90, 180, 270], 0, 9999, -0.5)
        b = blast_circles1(site)
        c = FanPattern(player, 'smallbullet', (120, 120), site, [0, 2, 5], 400, int(15 * help.difficulty_modifier), 0, aimed=True)  # 0, 2, 5
        return CompoundPattern([a, b, c])

    def boss_fan(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (60, 60), site, [0, 30, 60, 90], 300, int(15 * help.difficulty_modifier), 0, aimed=True)
    def boss_fastcircles(site: Entity) -> CompoundPattern:
        a = CirclePattern(player, 'smallbullet', (110, 110), site, int(20 * help.difficulty_modifier), 1900, int(13 * help.difficulty_modifier), 0, aimed=True)
        c = CirclePattern(player, 'smallbullet', (60, 60), site, int(20 * help.difficulty_modifier), 1900, int(15 * help.difficulty_modifier), 0, aimed=True)
        # b = FanLaserPattern(player, 'laser', 30, site, 1, 1000, 500, 1, True, 0.1)
        return CompoundPattern([a, c])

    def boss_selfcircles(site: Entity) -> CompoundPattern:
        b = CirclePattern(player, 'smallbullet', (60, 60), site, int(10 * help.difficulty_modifier), 3000, 6, 0, aimed=False)
        return CompoundPattern([b])
    def boss_repeatcircles(site: Entity) -> CompoundPattern:
        a = FanPattern(player, 'smallbullet', (30, 30), site, [0, 40, 80, 120], 100, 6, 0, aimed=True)
        b = CirclePattern(player, 'smallbullet', (60, 60), site, 10, 500, int(15 * help.difficulty_modifier), 0, aimed=True)
        return CompoundPattern([a, b])

    def boss_burst1(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (80, 80), site, 3, 1500, int(15 * help.difficulty_modifier), 0, 5, 100, aimed=True)
    def boss_lasers(site: Entity) -> CompoundPattern:
        a = MultiLaserPattern(player, 'laser', 20, site, [0, 90, 180, 270], 0, 9999, -0.5)
        b = MultiLaserPattern(player, 'laser', 50, site, [0], 1000, 500, 1.5)
        return CompoundPattern([a, b])
    def boss_seizure(site: Entity) -> CompoundPattern:
        a = FanPattern(player, 'smallbullet', (60, 60), site, [0, 40, 80, 120], 2000, int(11 * help.difficulty_modifier), 0, aimed=True)
        b = FanPattern(player, 'smallbullet', (90, 90), site, [0, 20, 40, 60, 80], 2100, int(12 * help.difficulty_modifier), 0, aimed=True)
        c = CirclePattern(player, 'smallbullet', (60, 60), site, int(30 * help.difficulty_modifier), 2200, int(11 * help.difficulty_modifier), 0, aimed=False)
        return CompoundPattern([a, b, c])

    # === WAVE SPAWNERS ===
    def popcorn_w1():
        PopcornFormation(
            'popcorn',
            Vector2(0, 20),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), straight_down_slow, fast_popcorn1, 2),
                FormationEntry(Vector2(600, 100), straight_down_slow, fast_popcorn4, 2),
                FormationEntry(Vector2(50, 50), straight_down_slow, fast_popcorn1, 2),
                FormationEntry(Vector2(110, 50), straight_down_slow, fast_popcorn4, 2),
                FormationEntry(Vector2(210, 60), straight_down_slow, fast_popcorn1, 2),
                FormationEntry(Vector2(98, 80), straight_down_slow, fast_popcorn4, 2),
                FormationEntry(Vector2(435, 10), straight_down_slow, fast_popcorn1, 2),
                FormationEntry(Vector2(512, 100), straight_down_slow, fast_popcorn1, 2),
                FormationEntry(Vector2(588, 20), straight_down_slow, fast_popcorn4, 2),
                FormationEntry(Vector2(700, 300), straight_down_slow, fast_popcorn1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
            ]
        )
    def lasers_w1():
        BigEnemyFormation(
            'xfa33',
            Vector2(400, 0),
            [

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(-400, 0), sky_lasers1, 0),
                FiringSiteEntry(Vector2(200, 110), sky_lasers1, 0),
                FiringSiteEntry(Vector2(250, 520), sky_lasers1, 0),
            ]
        )
    def raid_w1():
        BigEnemyFormation(
            'neonyf23',
            Vector2(400, -40),
            [

                BigEnemyEntry(Vector2(0, 0),
                              straight_down_slow,
                                                 [fast_popcorn1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(100, 142),
                              straight_down_slow, [fast_popcorn1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(185, 22),
                              straight_down_slow, [fast_popcorn1], interval=4000, health=10, reward=10),
                BigEnemyEntry(Vector2(-188, 23),
                              straight_down_slow, [fast_popcorn1], interval=4000, health=10, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def bomb_w1():
        BigEnemyFormation(
            'neonb2',
            Vector2(400, -100),
            [

                BigEnemyEntry(Vector2(-213, 78),
                              boss_random_wander,
                                                 [trickle1, bombs1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(198, 122),
                              boss_random_wander, [bombs1, trickle1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(256, 0),
                              boss_random_wander, [trickle1, bombs1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(-312, 244),
                              boss_random_wander, [trickle1, bombs1], interval=4000, health=20, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def raid_w2():
        BigEnemyFormation(
            'neonyf23',
            Vector2(400, -40),
            [

                BigEnemyEntry(Vector2(-312, 0),
                              boss_random_wander,
                                                 [fast_popcorn2, fast_popcorn3], interval=3000, health=20, reward=10),
                BigEnemyEntry(Vector2(12, 142),
                              boss_random_wander, [fast_popcorn2], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(185, 22),
                              boss_random_wander, [fast_popcorn3, fast_popcorn2], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(362, 23),
                              boss_random_wander, [fast_popcorn2], interval=1500, health=20, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def bomb_w2():
        BigEnemyFormation(
            'neonb2',
            Vector2(400, -100),
            [

                BigEnemyEntry(Vector2(-213, 78),
                              boss_random_wander,
                                                 [aimed_burst1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(198, 122),
                              boss_random_wander, [aimed_burst1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(256, 0),
                              boss_random_wander, [aimed_burst1], interval=2000, health=20, reward=10),
                BigEnemyEntry(Vector2(-312, 244),
                              boss_random_wander, [aimed_burst1], interval=4000, health=20, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def raid_w3():
        BigEnemyFormation(
            'neonyf23',
            Vector2(0, 0),
            [

                BigEnemyEntry(Vector2(112, 0),
                              make_bezier_curve(Vector2(0, 50), Vector2(210, 255), Vector2(423, 600), Vector2(800, 300), 2),
                                                 [fast_popcorn4], interval=3000, health=20, reward=10),
                BigEnemyEntry(Vector2(322, 142),
                              make_bezier_curve(Vector2(122, 76), Vector2(255, 287), Vector2(522, 687), Vector2(800, 300), 2), [fast_popcorn4], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(5, 22),
                              make_bezier_curve(Vector2(147, 123), Vector2(197, 316), Vector2(469, 598), Vector2(800, 300), 2), [fast_popcorn4, fast_popcorn4], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(25, 23),
                              make_bezier_curve(Vector2(233, 50), Vector2(365, 122), Vector2(587, 677), Vector2(800, 300), 2), [fast_popcorn4], interval=1500, health=20, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def raid_w4():
        BigEnemyFormation(
            'neonyf23',
            Vector2(800, 0),
            [

                BigEnemyEntry(Vector2(0, 0),
                              make_bezier_curve(Vector2(812, 350), Vector2(210, 255), Vector2(423, 600), Vector2(0, 300), 2),
                                                 [fast_popcorn4], interval=3000, health=20, reward=10),
                BigEnemyEntry(Vector2(0, 0),
                              make_bezier_curve(Vector2(822, 285), Vector2(255, 287), Vector2(522, 687), Vector2(0, 300), 2), [fast_popcorn4], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(0, 0),
                              make_bezier_curve(Vector2(782, 255), Vector2(197, 316), Vector2(469, 598), Vector2(0, 300), 2), [fast_popcorn4, fast_popcorn4], interval=1500, health=20, reward=10),
                BigEnemyEntry(Vector2(0, 0),
                              make_bezier_curve(Vector2(766, 328), Vector2(365, 122), Vector2(587, 677), Vector2(0, 300), 2), [fast_popcorn4], interval=1500, health=20, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def bomb_w3():
        BigEnemyFormation(
            'neonb2',
            Vector2(400, -100),
            [

                BigEnemyEntry(Vector2(-213, 78),
                              boss_random_wander,
                                                 [blast_combo1], interval=4000, health=25, reward=10),
                BigEnemyEntry(Vector2(198, 122),
                              boss_random_wander, [blast_combo1], interval=2000, health=25, reward=10),
                BigEnemyEntry(Vector2(256, 0),
                              boss_random_wander, [blast_combo1], interval=2000, health=25, reward=10),
                BigEnemyEntry(Vector2(-312, 244),
                              boss_random_wander, [blast_combo1], interval=4000, health=25, reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )
    def raid_w5():
        BigEnemyFormation(
            'neonyf23',
            Vector2(0, 0),
            [

                BigEnemyEntry(Vector2(112, 0),
                              make_bezier_curve(Vector2(0, 50), Vector2(210, 255), Vector2(423, 600), Vector2(800, 300),
                                                2),
                              [blast_circles1], interval=3000, health=20, reward=10),
                BigEnemyEntry(Vector2(322, 142),
                              make_bezier_curve(Vector2(122, 76), Vector2(255, 287), Vector2(522, 687),
                                                Vector2(800, 300), 2), [aimed_burst1], interval=1500, health=20,
                              reward=10),
                BigEnemyEntry(Vector2(5, 22),
                              make_bezier_curve(Vector2(147, 123), Vector2(197, 316), Vector2(469, 598),
                                                Vector2(800, 300), 2), [blast_circles1], interval=1500,
                              health=20, reward=10),
                BigEnemyEntry(Vector2(25, 23),
                              make_bezier_curve(Vector2(233, 50), Vector2(365, 122), Vector2(587, 677),
                                                Vector2(800, 300), 2), [fast_popcorn4], interval=1500, health=20,
                              reward=10)
            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations
        )

    def spawn_boss():
        nonlocal boss_spawned
        if boss_spawned:
            return
        boss_spawned = True

        boss = Boss(
            "boss_disco",
            Vector2(400, 400),
            [
                BossPhase("They Say The Disco Never Dies",
                          [(boss_circle, Vector2(0, 0))], max_hp=40),
                BossPhase("They Say The Disco Never Dies (REWIND)",
                          [(boss_blasts, Vector2(0, 0))], max_hp=40),
                BossPhase("City Slicking for Dirt Cheap",
                          [(boss_fan, Vector2(0, 0)), (boss_fastcircles, Vector2(200, -300)), (boss_fastcircles, Vector2(-200, -300))], max_hp=100),
                BossPhase("City Slicking for Dirt Cheap (FAST FORWARD)",
                          [(boss_burst1, Vector2(0, 0)), (boss_burst1, Vector2(10, 0)), (boss_burst1, Vector2(-10, 0)), (boss_fastcircles, Vector2(200, -300)),
                           (boss_fastcircles, Vector2(-200, -300)), (boss_selfcircles, Vector2(0, 0))], max_hp=100),
                BossPhase("A Hunt on the Sleeping Skyline",
                          [(boss_repeatcircles, Vector2(0, 0)), (boss_repeatcircles, Vector2(10, 0)), (boss_repeatcircles, Vector2(-10, 0)),
                           (boss_fastcircles, Vector2(-200, -300)), (boss_selfcircles, Vector2(200, -300))], max_hp=100),
                BossPhase("The Dancing Fever, Dancing Queen",
                          [(boss_lasers, Vector2(0, 0)), (boss_seizure, Vector2(0, 0))], max_hp=100)
            ],
            stationary,
            20,
            enemies
        )

    # == UTILITY ==
    def kill_all():
        for site in STATIC_SITES:
            site.kill()
        for enemy in enemies:
            enemy.kill()

    def no_more_enemies_and_formations():
        return stage.all_waves_scheduled() and len(enemies) == 0 and len(formations) == 0

    end_banner = None
    def show_end_banner():
        nonlocal end_banner
        end_banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name} ... COMPLETE', 20,
                                  Vector2(CANVAS_WIDTH // 2, 200), duration_ms=7000, start_delay=1000)

    def end_banner_done():
        return end_banner.done if end_banner is not None else False

    def always_true():
        """DEBUGGING: ALWAYS RETURNS TRUE"""
        return True

    def end_stage():
        help.gamestate = 'stage4'
        player.stage_name = 'RAGE ABOVE THOSE MOUNTAINS'
        player.stage_number = 4
        bg.kill()
        pygame.mixer.music.pause()
        pygame.mixer.music.unload()

        bonus_lives = 0
        bonus_bombs = 0
        match help.difficulty:
            case 'NOVICE':
                bonus_lives = 2
                bonus_bombs = 2
            case 'PILOT':
                bonus_lives = 1
                bonus_bombs = 1
            case 'VETERAN':
                bonus_lives = 1
                bonus_bombs = 1
            case 'ACE':
                bonus_lives = 0
                bonus_bombs = 1
        player.lives = min(player.max_lives, player.lives + player.max_lives // 5 + bonus_lives)
        player.bombs = min(player.max_bombs, player.bombs + player.max_bombs // 5 + bonus_bombs)

        help.stage4 = StageHandler()
        build_stage4(help.stage4, player)


    def start_mission():
        help.gamestate = 'stage3'

        pygame.mixer.init()
        pygame.mixer.music.load(resource_path('sounds/Murder, Murder on the Floor.mp3'))
        pygame.mixer.music.play(-1, fade_ms=1000)

        if not help.skip_banners:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30,
                                  Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=1000)
            banner2 = TypingBanner(f"THEY'VE CHASED YOU OUT OF THE CANYON.", 20, Vector2(300, 200),
                                  start_delay=6000)
            banner3 = TypingBanner(f"YOU'VE TAKEN REFUGE OVER THE CITY.", 20, Vector2(350, 300),
                                  start_delay=11000)
            banner3 = TypingBanner(f"...THEY WON'T STOP. KEEP FIGHTING.", 20, Vector2(400, 400),
                                  start_delay=16000)
        else:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30,
                                  Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=0)
    # === SCHEUDLE EVENTS ===
    START_TIME = 21000 if not help.skip_banners else 0 # 12000, 1000
    ONE_SECOND = 1000

    bg = ScrollingBackground('stage3background', background)

    # BEGIN MISSION
    stage.schedule(0, start_mission)

    # STAGE ENEMIES

    stage.schedule(START_TIME, lasers_w1)
    stage.schedule(START_TIME + 7000, raid_w1)  # 7000
    stage.schedule(START_TIME + 9000, bomb_w1)  # 7000
    stage.schedule(START_TIME + 15000, raid_w2)  # 7000
    stage.schedule(START_TIME + 25000, bomb_w2)  # 7000
    stage.schedule(START_TIME + 30000, popcorn_w1)  # 7000
    stage.schedule(START_TIME + 35000, raid_w3)  # 7000
    stage.schedule(START_TIME + 37000, raid_w4)  # 7000
    stage.schedule(START_TIME + 39000, raid_w3)  # 7000
    stage.schedule(START_TIME + 40000, raid_w4)  # 7000
    stage.schedule(START_TIME + 40000, popcorn_w1)  # 7000
    stage.schedule(START_TIME + 43000, bomb_w3)  # 7000
    stage.schedule(START_TIME + 48000, raid_w5)  # 7000

    # PREPARE BOSS
    stage.schedule(START_TIME + 52 * ONE_SECOND, kill_all)  # 52
    stage.schedule(START_TIME + 53 * ONE_SECOND, stage.mark_waves_done)  # 53
    stage.wait_until(no_more_enemies_and_formations, spawn_boss)

    # END LEVEL
    stage.wait_until(no_more_enemies_and_formations, show_end_banner)
    stage.wait_until(end_banner_done, end_stage)


def build_stage4(stage: StageHandler, player: Player):
    LEFT_UPPER_1 = FiringSite(Vector2(100, 50), 0, enemies)
    LEFT_UPPER_2 = FiringSite(Vector2(200, 50), 0, enemies)
    RIGHT_UPPER_1 = FiringSite(Vector2(700, 50), 0, enemies)
    RIGHT_UPPER_2 = FiringSite(Vector2(600, 50), 0, enemies)
    LEFT_LOWER_1 = FiringSite(Vector2(300, 790), 0, enemies)
    RIGHT_LOWER_1 = FiringSite(Vector2(500, 790), 0, enemies)

    STATIC_SITES = [LEFT_UPPER_1, LEFT_UPPER_2, RIGHT_UPPER_1, RIGHT_UPPER_2, LEFT_LOWER_1, RIGHT_LOWER_1]
    previous_stage_end = pygame.time.get_ticks()
    boss_spawned = False

    # === REGULAR PATTERNS ===
    def air_circles1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(30 * help.difficulty_modifier), int(1000 + 300*(1-help.difficulty_modifier)), 3, 0, aimed=False)
    def laser_fan1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [150, 180, 210], int(1000 + 300*(1-help.difficulty_modifier)), 500, 0)
    def laser_wheel1(site: Entity) -> Pattern:
        return RotatingLaserPattern(player, 'laser', 20, site, 3, 1000, 500, 2)
    def big_spiral1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, int(10 * help.difficulty_modifier), int(400 + 500*(1-help.difficulty_modifier)), 7, 5, False)
    def big_spiral2(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, int(30 * help.difficulty_modifier), int(400 + 500*(1-help.difficulty_modifier)), 7, 5, False)
    def fast_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (50, 50), site, [0, 40, 80, 120], int(2000 + 500*(1-help.difficulty_modifier)), 10, 0, False)
    def big_wheel1(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (40, 40), site, 6, int(100 + 500*(1-help.difficulty_modifier)), 5, 0, spin_speed=10, aimed=False)
    def big_blast1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (90, 90), site, 6, int(150 + 500*(1-help.difficulty_modifier)), 6, 5, 0, True)

    def popcorn_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (20, 20), site, [0, 30, 60], int(200 + 500*(1-help.difficulty_modifier)), int(7 * help.difficulty_modifier), 0, False)
    def popcorn_fan2(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (50, 50), site, [0, 40, 80, 120], int(1000 + 500*(1-help.difficulty_modifier)), int(7 * help.difficulty_modifier), 0, False)
    def aimed_burst1(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (40, 40), site, 3, int(1000 + 500*(1-help.difficulty_modifier)), int(8 * help.difficulty_modifier), 0, 0, 500, True)
    def popcorn_sprinkle1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [0, 20, 40, 60, 80, 100, 120, 140], int(300 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, False)

    def boss_tightcircle1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(80 * help.difficulty_modifier), int(780 + 500*(1-help.difficulty_modifier)), 3, 0, aimed=False)
    def boss_tightcircle2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (50, 50), site, int(40 * help.difficulty_modifier), 1000, 3, 0, aimed=True)
    def boss_tightcircle3(site: Entity) -> Pattern:
        return CirclePattern(player, 'bigbullet', (90, 90), site, int(20 * help.difficulty_modifier), 1000, 3, 0, aimed=True)
    def boss_laserzone1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 80, 160, 240, 300], 1000, 500, -0.1)
    def boss_laserzone2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 120, 240], 1000, 500, 0.2)
    def boss_fastblast1(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (50, 50), site, 9, int(500 + 500*(1-help.difficulty_modifier)), int(8 * help.difficulty_modifier), 0, 0, 300, True)
    def boss_laserzone3(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 90, 180, 270], 1000, 500, 0)
    def boss_trickle(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [0, 20, 40, 60, 80, 100, 120, 140], int(300 + 500*(1-help.difficulty_modifier)), 3, 0, False)

    def boss_tightfan1(site: Entity) -> Pattern:
        return FanPattern(player, 'bigbullet', (95, 95), site, [0, 10, 20, 30, 40, 50], int(1000 + 500*(1-help.difficulty_modifier)), 3, 0, True)
    def boss_zonefan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [0, 60], 100, int(15 * help.difficulty_modifier), 0, True)
    def boss_wheel1(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (40, 40), site, int(6 * help.difficulty_modifier), int(150 + 500*(1-help.difficulty_modifier)), 2, 0, spin_speed=10, aimed=False)
    def boss_wheel2(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'bigbullet', (95, 95), site, int(8 * help.difficulty_modifier), int(600 + 500*(1-help.difficulty_modifier)), 4, 0, spin_speed=15, aimed=True)
    # == SPAWN ==
    def popcorn_w1():

        PopcornFormation(
            'f14',
            Vector2(50, -50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), boss_random_wander, popcorn_fan1, 2),
                FormationEntry(Vector2(80, 60), straight_down_slow, popcorn_fan2, 2),
                FormationEntry(Vector2(160, 20), boss_random_wander, popcorn_fan1, 2),
                FormationEntry(Vector2(240, 80), straight_down_slow, popcorn_fan2, 2),
                FormationEntry(Vector2(320, 40), straight_down_slow, popcorn_fan1, 2),
                FormationEntry(Vector2(400, 100), boss_random_wander, popcorn_fan2, 2),
                FormationEntry(Vector2(480, 20), straight_down_slow, popcorn_fan1, 2),
                FormationEntry(Vector2(560, 70), boss_random_wander, popcorn_fan2, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[]
        )
    def popcorn_w2():
        PopcornFormation(
            'f14',
            Vector2(50, -50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), boss_random_wander, popcorn_fan1, 2),
                FormationEntry(Vector2(80, 60), boss_random_wander, air_circles1, 2),
                FormationEntry(Vector2(160, 20), boss_random_wander, popcorn_fan2, 2),
                FormationEntry(Vector2(240, 80), boss_random_wander, air_circles1, 2),
                FormationEntry(Vector2(320, 40), boss_random_wander, popcorn_fan1, 2),
                FormationEntry(Vector2(400, 100), boss_random_wander, air_circles1, 2),
                FormationEntry(Vector2(480, 20), boss_random_wander, popcorn_fan2, 2),
                FormationEntry(Vector2(560, 70), boss_random_wander, popcorn_fan1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[]
        )
    def popcorn_w3():
        PopcornFormation(
            'f14',
            Vector2(50, -50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), swoop_in_left, aimed_burst1, 2),
                FormationEntry(Vector2(80, 60), swoop_in_left, aimed_burst1, 2),
                FormationEntry(Vector2(160, 20), swoop_in_left, aimed_burst1, 2),
                FormationEntry(Vector2(240, 80), swoop_in_left, aimed_burst1, 2),
                FormationEntry(Vector2(320, 40), swoop_in_right, aimed_burst1, 2),
                FormationEntry(Vector2(400, 100), swoop_in_right, aimed_burst1, 2),
                FormationEntry(Vector2(480, 20), swoop_in_right, aimed_burst1, 2),
                FormationEntry(Vector2(560, 70), swoop_in_right, aimed_burst1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[]
        )
    def popcorn_w4():
        PopcornFormation(
            'f14',
            Vector2(50, -50),
            (50, 50),
            [
                FormationEntry(Vector2(0, 0), sine_wave, popcorn_sprinkle1, 2),
                FormationEntry(Vector2(160, 20), sine_wave, popcorn_sprinkle1, 2),
                FormationEntry(Vector2(240, 80), sine_wave, popcorn_sprinkle1, 2),
                FormationEntry(Vector2(320, 40), sine_wave, popcorn_sprinkle1, 2),
                FormationEntry(Vector2(480, 20), sine_wave, popcorn_sprinkle1, 2),
                FormationEntry(Vector2(560, 70), sine_wave, popcorn_sprinkle1, 2),
            ],
            pygame.time.get_ticks(),
            formations,
            firing_sites=[]
        )

    def antiair2():
        BigEnemyFormation(
            'xfa33',
            Vector2(400, 0),
            [

            ],
            (50, 50),
            pygame.time.get_ticks(),
            formations,
            firing_sites=[
                FiringSiteEntry(Vector2(256, 0), air_circles1, 0),
                FiringSiteEntry(Vector2(-256, -500), air_circles1, 0),

            ]
        )
    def spread_w1():
        BigEnemyFormation(
                'neonb2',
                Vector2(400, 0),
                [

                    BigEnemyEntry(Vector2(0, 0),
                                  boss_random_wander, [air_circles1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-120, 142),
                                  boss_random_wander, [air_circles1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(210, 100),
                                  boss_random_wander, [air_circles1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-250, 56),
                                  boss_random_wander, [air_circles1], interval=4000, health=100, reward=10)
                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations
            )
    def spread_w2():
        BigEnemyFormation(
                'neonb2',
                Vector2(400, 0),
                [

                    BigEnemyEntry(Vector2(0, 0),
                                  boss_random_wander, [big_spiral1, popcorn_fan1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-120, 142),
                                  boss_random_wander, [laser_fan1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(210, 100),
                                  boss_random_wander, [laser_fan1], interval=4000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-250, 56),
                                  boss_random_wander, [big_spiral1, popcorn_fan1], interval=4000, health=100, reward=10)
                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations
            )
    def spread_w3():
        BigEnemyFormation(
                'neonb2',
                Vector2(400, 0),
                [

                    BigEnemyEntry(Vector2(0, 0),
                                  boss_random_wander, [big_spiral2, popcorn_fan1], interval=2000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-120, 142),
                                  boss_random_wander, [aimed_burst1, fast_fan1], interval=2000, health=100, reward=10),
                    BigEnemyEntry(Vector2(210, 100),
                                  boss_random_wander, [fast_fan1, aimed_burst1], interval=2000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-250, 56),
                                  boss_random_wander, [big_spiral2, popcorn_fan1], interval=2000, health=100, reward=10)
                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations
            )
    def spread_w4():
        BigEnemyFormation(
                'neonb2',
                Vector2(400, 0),
                [

                    BigEnemyEntry(Vector2(-120, 142),
                                  boss_random_wander, [big_wheel1, big_blast1], interval=1000, health=100, reward=10),
                    BigEnemyEntry(Vector2(210, 100),
                                  boss_random_wander, [big_wheel1], interval=2000, health=100, reward=10),
                    BigEnemyEntry(Vector2(-250, 56),
                                  boss_random_wander, [big_blast1, popcorn_fan1], interval=2000, health=100, reward=10)
                ],
                (50, 50),
                pygame.time.get_ticks(),
                formations
            )

    def spawn_boss():
        nonlocal boss_spawned
        if boss_spawned:
            return
        boss_spawned = True

        boss = Boss(
            "ace_boss",
            Vector2(400, 100),
            [
                BossPhase("Ruthless Precision of an Ace", [(boss_tightcircle1, Vector2(0, 0)), (boss_tightcircle2, Vector2(0, 0))], max_hp=150),
                BossPhase("Unending Chase of Overwhelming Glory",
                          [(boss_tightcircle3, Vector2(0, 0)), (boss_laserzone1, Vector2(-400, 200)), (boss_laserzone2, Vector2(400, 200)), ], max_hp=150),
                BossPhase("Deep Chasm of Obsessive Pursuit",
                          [(boss_tightcircle2, Vector2(-300, -100)), (boss_tightcircle2, Vector2(300, -100)),
                           (air_circles1, Vector2(400, 650)),(air_circles1, Vector2(-400, 650)) ], max_hp=150),
                BossPhase("Relentless Anger and Righteousness",
                          [(boss_fastblast1, Vector2(-300, -150)), (boss_fastblast1, Vector2(300, -150)),
                           (boss_fastblast1, Vector2(300, 700)), (boss_fastblast1, Vector2(-300, 700)), (boss_laserzone3, Vector2(0, 300)), (boss_laserzone3, Vector2(-300, 0)),
                           (boss_trickle, Vector2(0, 0))], max_hp=150),
                BossPhase("An Unreasonable Demand for Perfection",
                          [
                           (boss_tightcircle2, Vector2(300, 100)), (boss_tightcircle2, Vector2(-300, 100)), (boss_tightcircle3, Vector2(0, 0)),
                           ], max_hp=150),
                BossPhase("Reprise of a Demand for Perfection",
                          [
                              (boss_tightfan1, Vector2(0, 0)), (boss_zonefan1, Vector2(300, 0)), (boss_zonefan1, Vector2(-300, 0)), (boss_zonefan1, Vector2(0, 0))
                          ], max_hp=150),
                BossPhase("Desperation to Complete Destiny",
                          [
                              (boss_wheel1, Vector2(150, 0)), (boss_wheel1, Vector2(-150, 0)), (boss_wheel2, Vector2(0, 0))
                          ], max_hp=150),
                # 100
            ],
            boss_random_wander,
            20,
            enemies
        )

    # == UTILITY ==
    def kill_all():
        for site in STATIC_SITES:
            site.kill()
        for enemy in enemies:
            enemy.kill()

    def no_more_enemies_and_formations():
        return stage.all_waves_scheduled() and len(enemies) == 0 and len(formations) == 0

    end_banner = None
    def show_end_banner():
        nonlocal end_banner
        end_banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name} ... COMPLETE', 20,
                        Vector2(CANVAS_WIDTH // 2, 200), duration_ms=7000, start_delay=1000)

    def end_banner_done():
        return end_banner.done if end_banner is not None else False

    def always_true():
        """DEBUGGING: ALWAYS RETURNS TRUE"""
        return True

    def end_stage():
        help.gamestate = 'stage5'
        player.stage_name = 'SI VIS PACEM... PARA BELLUM'
        player.stage_number += 1
        bg.kill()
        pygame.mixer.music.pause()

        bonus_lives = 0
        bonus_bombs = 0
        match help.difficulty:
            case 'NOVICE':
                bonus_lives = 2
                bonus_bombs = 2
            case 'PILOT':
                bonus_lives = 1
                bonus_bombs = 1
            case 'VETERAN':
                bonus_lives = 1
                bonus_bombs = 1
            case 'ACE':
                bonus_lives = 1
                bonus_bombs = 1
        player.lives = min(player.max_lives, player.lives + player.max_lives // 5 + bonus_lives)
        player.bombs = min(player.max_bombs, player.bombs + player.max_bombs // 5 + bonus_bombs)
        help.stage5 = StageHandler()
        build_stage5(help.stage5, player)

    def start_mission():
        help.gamestate = 'stage4'

        pygame.mixer.init()
        pygame.mixer.music.load(resource_path('sounds/Rage Beneath Those Mountains.mp3'))
        pygame.mixer.music.play(-1, fade_ms=1000)

        if not help.skip_banners:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=1000)
            banner2 = TypingBanner(f"THEIR BASE IS HIDDEN IN THESE MOUNTAINS.", 20, Vector2(350, 200),
                                  start_delay=6000)
            banner3 = TypingBanner(f"THEY'LL SEND AN ACE AFTER YOU.", 20, Vector2(400, 300),
                                  start_delay=11000)
            banner4 = TypingBanner(f"...LET THEM.", 20, Vector2(400, 350),
                                  start_delay=16000)
        else:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=0)

    # === SCHEUDLE EVENTS ===
    START_TIME = 21000 if not help.skip_banners else 0 # 4000
    ONE_SECOND = 1000

    bg = ScrollingBackground('stage4background', background)

    # BEGIN MISSION
    stage.schedule(0, start_mission)

    # STAGE ENEMIES

    stage.schedule(START_TIME + 0*ONE_SECOND, popcorn_w1)
    stage.schedule(START_TIME + 4*ONE_SECOND, spread_w1)
    stage.schedule(START_TIME + 10*ONE_SECOND, popcorn_w2)
    stage.schedule(START_TIME + 15*ONE_SECOND, popcorn_w2)
    stage.schedule(START_TIME + 20*ONE_SECOND, popcorn_w2)
    stage.schedule(START_TIME + 25*ONE_SECOND, popcorn_w3)
    stage.schedule(START_TIME + 35*ONE_SECOND, popcorn_w3)
    stage.schedule(START_TIME + 35*ONE_SECOND, spread_w2)
    stage.schedule(START_TIME + 45*ONE_SECOND, popcorn_w3)
    stage.schedule(START_TIME + 55*ONE_SECOND, popcorn_w2)
    stage.schedule(START_TIME + 70*ONE_SECOND, spread_w3)
    stage.schedule(START_TIME + 75*ONE_SECOND, popcorn_w3)
    stage.schedule(START_TIME + 75*ONE_SECOND, popcorn_w2)
    stage.schedule(START_TIME + 80*ONE_SECOND, popcorn_w1)
    stage.schedule(START_TIME + 85*ONE_SECOND, popcorn_w4)
    stage.schedule(START_TIME + 95*ONE_SECOND, spread_w4)


    # PREPARE BOSS
    stage.schedule(START_TIME + 115 * ONE_SECOND, kill_all)  # 115
    stage.schedule(START_TIME + 116 * ONE_SECOND, stage.mark_waves_done)  # 116
    stage.wait_until(no_more_enemies_and_formations, spawn_boss)

    # END LEVEL
    stage.wait_until(no_more_enemies_and_formations, show_end_banner)
    stage.wait_until(end_banner_done, end_stage)


def build_stage5(stage: StageHandler, player: Player):
    LEFT_UPPER_1 = FiringSite(Vector2(100, 50), 0, enemies)
    LEFT_UPPER_2 = FiringSite(Vector2(200, 50), 0, enemies)
    RIGHT_UPPER_1 = FiringSite(Vector2(700, 50), 0, enemies)
    RIGHT_UPPER_2 = FiringSite(Vector2(600, 50), 0, enemies)
    LEFT_LOWER_1 = FiringSite(Vector2(300, 790), 0, enemies)
    RIGHT_LOWER_1 = FiringSite(Vector2(500, 790), 0, enemies)

    STATIC_SITES = [LEFT_UPPER_1, LEFT_UPPER_2, RIGHT_UPPER_1, RIGHT_UPPER_2, LEFT_LOWER_1, RIGHT_LOWER_1]
    previous_stage_end = pygame.time.get_ticks()
    boss_spawned = False
    boss_phase2_spawned = False

    # === REGULAR PATTERNS ===
    def laser_activation1(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 0, 1000, 500)
    def laser_activation2(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 0, 1500, 500)
    def laser_activation3(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 0, 2000, 500)
    def laser_activation1h(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 90, 1000, 500)
    def laser_activation2h(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 90, 1500, 500)
    def laser_activation3h(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 90, 2000, 500)
    def laser_activation1d1(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 45, 1000, 500)
    def laser_activation1d2(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, -45, 1000, 500)
    def laser_activation2d1(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 45, 1500, 500)
    def laser_activation2d2(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, -45, 1500, 500)
    def laser_activation3d1(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, 45, 2000, 500)
    def laser_activation3d2(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 20, site, -45, 2000, 500)
    def laser_circle1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], 1000, 500, 0)
    def laser_wheel1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], 1000, 500, 0.4)
    def laser_wheel2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], 1000, 500, -0.2)
    def perma_wheel1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 60,  60*2, 60*3, 60*4, 60*5], 0, 9999, -0.2)
    def perma_wheel2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 60,  60*2, 60*3, 60*4, 60*5], 0, 9999, 0.2)
    def fast_permasweep1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 20], 0, 9999, 1.2 * help.difficulty_modifier)
    def fast_permasweep2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 20], 0, 9999, -1.2 * help.difficulty_modifier)
    def fast_sweep1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 30], 1000, 400, 1.2 * help.difficulty_modifier)
    def fast_sweep2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 30], 1000, 400, -1.2 * help.difficulty_modifier)
    def zone_fan1(site: Entity) -> Pattern:
        return FanLaserPattern(player, 'laser', 20, site, 5, 800, 450, 40, True, 0.15)
    def zone_fan2(site: Entity) -> Pattern:
        return FanLaserPattern(player, 'laser', 20, site, 5, 800, 450, 60, True, 0.15)
    def static_fan1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [140, 160, 180, 200, 220], 1000, 500, 0)
    def static_fan2(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [120, 180, 240], 1000, 500, 0)
    def laser_mill1(site: Entity) -> Pattern:
        return MultiLaserPattern(player, 'laser', 20, site, [0, 120, 240], 1000, 500, 0.8 * help.difficulty_modifier)
    def big_laser1(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 100, site, 0, 500, 300, 0)
    def big_laser2(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 100, site, 90, 500, 300, 0)
    def big_laser3(site: Entity) -> Pattern:
        return SingleLaserPattern(player, 'laser', 100, site, 45, 500, 300, 0)

    def aimed_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [25*x for x in range(5)] + [25*x + 5 for x in range(5)], int(800 + 500*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, True)
    def aimed_fan2(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (50, 50), site, [10*x for x in range(5)] + [10*x + 5 for x in range(5)], int(300 + 500*(1-help.difficulty_modifier)), int(8 * help.difficulty_modifier), 0, True)
    def aimed_fan3(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (50, 50), site, [20*x for x in range(int(7 * help.difficulty_modifier))] +[20*x + 5 for x in range(int(7 * help.difficulty_modifier))], int(200 + 500*(1-help.difficulty_modifier)), int(10 * help.difficulty_modifier), 0, True)
    def big_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'bigbullet', (200, 200), site, [30*x for x in range(5)], 900, 4, 0, True)
    def swoop_fan1(site: Entity) -> Pattern:
        return FanPattern(player, 'smallbullet', (30, 30), site, [x for x in range(int(25 * help.difficulty_modifier))], int(300 +  500*(1-help.difficulty_modifier)), 5, 0, True)

    def missile_burst1(site: Entity) -> Pattern:
        return MissileBurstPattern(player, 'smallbullet', (70, 70), site, 3, int(1500 + 500*(1-help.difficulty_modifier)) , 5, 0, 20, 300, 0.5, 5000)
    def missile_burst2(site: Entity) -> Pattern:
        return MissileBurstPattern(player, 'smallbullet', (70, 70), site, 2, int(1000 + 500*(1-help.difficulty_modifier)), 4, 0, 50, 400, 1.5 * help.difficulty_modifier, 5000)
    def aimed_burst1(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (50, 50), site, 2, int(570+ 500*(1-help.difficulty_modifier)), int(18 * help.difficulty_modifier), 0, 0, 150, True)
    def aimed_burst2(site: Entity) -> Pattern:
        return BurstPattern(player, 'smallbullet', (80, 80), site, 4, int(570 + 500*(1-help.difficulty_modifier)), int(20 * help.difficulty_modifier), 0, 0, 150, True)

    def blast_ring1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (40, 40), site, int(20 * help.difficulty_modifier), int(800 + 500*(1-help.difficulty_modifier)), int(9 * help.difficulty_modifier), 0, True)
    def blast_ring2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (90, 90), site, int(10 * help.difficulty_modifier), int(500 + 500*(1-help.difficulty_modifier)), int(12 * help.difficulty_modifier), 0, True)
    def blast_ring3(site: Entity) -> Pattern:
        return CirclePattern(player, 'bigbullet', (100, 100), site, 10, 800, int(9 * help.difficulty_modifier), 0, True)
    def slow_ring1(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (30, 30), site, int(30 * help.difficulty_modifier), 1200, 3, 0, True)
    def slow_ring2(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (50, 50), site, int(75 * help.difficulty_modifier), 1700, 4, 0, True)
    def slow_ring3(site: Entity) -> Pattern:
        return CirclePattern(player, 'smallbullet', (90, 90), site, int(60 * help.difficulty_modifier), 1700, 5, 0, False)
    def big_ring1(site: Entity) -> Pattern:
        return CirclePattern(player, 'bigbullet', (120, 120), site, int(30 * help.difficulty_modifier), 1500, 5, 0, False)

    def partial_spiral1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, int(9 * help.difficulty_modifier), int(200 + 200*(1-help.difficulty_modifier)), 4, 4, 0)
    def partial_spiral2(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, int(20 * help.difficulty_modifier), int(200 + 500*(1-help.difficulty_modifier)), 6, 5, 0, aimed=True)
    def slow_spiral1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, 2, int(50 + 200*(1-help.difficulty_modifier)), 4, 4, 0)
    def slow_spiral2(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, 2, int(50 + 200 *(1-help.difficulty_modifier)), 4, 4, 0)
    def fast_spiral1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'smallbullet', (40, 40), site, 1, int(50 + 200*(1-help.difficulty_modifier)), 6, int(8 * help.difficulty_modifier), 0)
    def big_spiral1(site: Entity) -> Pattern:
        return SpiralPattern(player, 'bigbullet', (95, 95), site, 4, 100 + 300*(1-help.difficulty_modifier), 17, 7, 0)

    def spread_snowflake1(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (30, 30), site, int(15 * help.difficulty_modifier), int(100 + 300*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, False, spin_speed=5)
    def spread_snowflake2(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (30, 30), site, int(20 * help.difficulty_modifier), int(200 + 300*(1-help.difficulty_modifier)), int(5 * help.difficulty_modifier), 0, False, spin_speed=8)
    def normal_snowflake1(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (30, 30), site, int(5 * help.difficulty_modifier), int(100 + 300*(1-help.difficulty_modifier)), 5, 0, False, spin_speed=10)
    def normal_snowflake2(site: Entity) -> Pattern:
        return SnowflakePattern(player, 'smallbullet', (30, 30), site, int(7 * help.difficulty_modifier), 50 + 50*(1-help.difficulty_modifier), 5, 0, False, spin_speed=15)


    # == SPAWN ==
    def spawn_boss():
        nonlocal boss_spawned
        if boss_spawned:
            return
        boss_spawned = True

        boss = Boss(
            "mech_boss",
            Vector2(400, 100),
            [
                BossPhase("1.0", [(slow_spiral1, Vector2(-200, 0)), (slow_spiral1, Vector2(200, 0)), (spread_snowflake2, Vector2(0, -50))], max_hp=100),
                BossPhase("1.1", [(slow_spiral2, Vector2(-200, 0)), (normal_snowflake1, Vector2(-200, 0)), (slow_spiral1, Vector2(200, 0)), (normal_snowflake1, Vector2(200, 0)),
                            ], max_hp=100),
                BossPhase("1.2", [(slow_ring2, Vector2(0, 0)), (big_ring1, Vector2(-200, 0)),(slow_ring3, Vector2(-200, 0))
                                  ], max_hp=100),
                BossPhase("1.3",
                          [(big_ring1, Vector2(350, -50)), (big_ring1, Vector2(-350, -50))
                           ], max_hp=100),
                BossPhase("1.4",
                          [(aimed_fan2, Vector2(0, 0)), (static_fan1, Vector2(-350, -50)), (static_fan1, Vector2(350, -50))
                           ], max_hp=100),
                BossPhase("2.0", [(laser_activation1, Vector2(0, 800)),
                                                  (laser_activation2, Vector2(100, 800)),
                                                  (laser_activation2, Vector2(-100, 800)),
                                                  (laser_activation3, Vector2(200, 800)),
                                                  (laser_activation3, Vector2(-200, 800)),
                                                  (laser_activation1, Vector2(300, 800)),
                                                  (laser_activation1, Vector2(-300, 800)),
                                                  (laser_activation2, Vector2(380, 800)),
                                                  (laser_activation2, Vector2(-380, 800)),
                                (blast_ring3, Vector2(-300, -50)), (aimed_burst2, Vector2(0, 0)), (aimed_burst2, Vector2(200, 0)), (aimed_burst2, Vector2(-200, 0)),
                                (blast_ring2, Vector2(300, -50))], max_hp=100),
                BossPhase("2.1", [
                                (laser_activation2, Vector2(100, 800)),
                                (laser_activation2, Vector2(-100, 800)),
                                (laser_activation2, Vector2(300, 800)),
                                (laser_activation2, Vector2(-300, 800)),
                                (swoop_fan1, Vector2(0, -50))], max_hp=100),
                BossPhase("2.2", [
                    (laser_activation1h, Vector2(-400, 50)),
                    (laser_activation1h, Vector2(-400, 100)),
                    (laser_activation1h, Vector2(-400, 300)),
                    (laser_activation1h, Vector2(-400, 500)),
                    (laser_activation1h, Vector2(-400, 700)),
                    (laser_activation1h, Vector2(-400, 750)),
                    (swoop_fan1, Vector2(0, 750))], max_hp=100),
                BossPhase("2.3", [
                    (laser_activation1h, Vector2(-400, 50)),
                    (laser_activation1h, Vector2(-400, 100)),
                    (laser_activation1h, Vector2(-400, 300)),
                    (laser_activation1h, Vector2(-400, 500)),
                    (laser_activation1h, Vector2(-400, 700)),
                    (laser_activation1h, Vector2(-400, 750)),
                    (laser_activation1, Vector2(100, 800)),
                    (laser_activation1, Vector2(-100, 800)),
                    (laser_activation1, Vector2(300, 800)),
                    (laser_activation1, Vector2(-300, 800)),  (aimed_burst1, Vector2(350, 300)),
                    (aimed_burst2, Vector2(380, 200)), (aimed_burst2, Vector2(380, 350)), (aimed_burst1, Vector2(-200, 680)), (aimed_burst2, Vector2(-250, 680))], max_hp=100),
                BossPhase("2.4", [
                    (laser_activation1h, Vector2(-400, 50)),
                    (laser_activation1h, Vector2(-400, 100)),
                    (laser_activation1h, Vector2(-400, 300)),
                    (laser_activation1h, Vector2(-400, 500)),
                    (laser_activation1h, Vector2(-400, 700)),
                    (laser_activation1h, Vector2(-400, 750)),
                    (laser_activation1, Vector2(100, 800)),
                    (laser_activation1, Vector2(-100, 800)),
                    (laser_activation1, Vector2(300, 800)),
                    (laser_activation1, Vector2(-300, 800)),
                    (fast_permasweep2, Vector2(-150, 350)), (fast_permasweep2, Vector2(150, 350))
                ], max_hp=100),
                BossPhase("2.5",
                          [(laser_activation1d1, Vector2(-400, 700)), (laser_activation1d1, Vector2(-400, 400)),
                           (laser_activation1d1, Vector2(-400, 200)),
                           (laser_activation1d1, Vector2(-200, 900)), (laser_activation1d1, Vector2(-100, 1100)),
                           (laser_activation1d2, Vector2(400, 500)),
                           (laser_activation1d2, Vector2(200, 800)),
                           (missile_burst2, Vector2(-300, 300)), (missile_burst1, Vector2(300, -50)),
                           (slow_ring1, Vector2(0, 0))], max_hp=100),
                BossPhase("3.0", [(missile_burst2, Vector2(300, 300)),
                                (big_fan1, Vector2(0, 0))], max_hp=100),
                BossPhase("3.1", [(missile_burst2, Vector2(300, 300)),
                                  (big_spiral1, Vector2(0, 0))], max_hp=100),
                BossPhase("3.2", [(perma_wheel1, Vector2(0, 300)),
                                  (missile_burst2, Vector2(-300, 0)), (missile_burst2, Vector2(300, 600))], max_hp=100),
                BossPhase("3.3", [(laser_mill1, Vector2(-200, 300)), (laser_mill1, Vector2(200, 300)),
                                  (blast_ring3, Vector2(0, 0)), (big_fan1, Vector2(0, 0))], max_hp=100),
                BossPhase("3.4", [(blast_ring2, Vector2(-350, 300)), (blast_ring2, Vector2(350, 300)),
                                  (blast_ring1, Vector2(0, 0))], max_hp=100),
                BossPhase("4.0",
                          [(fast_sweep1, Vector2(-200, 300)), (fast_sweep2, Vector2(200, 300)),
                           (partial_spiral1, Vector2(-250, 0)),
                           (partial_spiral1, Vector2(250, 0))
                           ], max_hp=100),
                BossPhase("4.1",
                          [(fast_sweep2, Vector2(-200, 300)), (fast_sweep1, Vector2(200, 300)),
                           (aimed_fan1, Vector2(-250, 0)),
                           (aimed_fan1, Vector2(250, 0))
                           ], max_hp=100),
                BossPhase("4.2",
                          [(fast_spiral1, Vector2(-250, 0)), (fast_spiral1, Vector2(250, 0)),
                           (slow_ring1, Vector2(-250, 0)),
                           (slow_ring1, Vector2(250, 0))
                           ], max_hp=100),
                BossPhase("4.3",
                          [(big_spiral1, Vector2(-250, 0)),
                           (zone_fan2, Vector2(250, 0)),
                           ], max_hp=100),
                BossPhase("4.4",
                          [(big_spiral1, Vector2(250, 0)),
                           (zone_fan1, Vector2(-250, 0)),
                           ], max_hp=100),
            ],
            stationary,
            20,
            enemies
        )
    def spawn_boss2():
        nonlocal boss_phase2_spawned
        if boss_phase2_spawned:
            return
        boss_phase2_spawned = True

        boss = Boss(
            "mech_boss",
            Vector2(400, 100),
            [
                BossPhase("5.0",
                          [(big_laser1, Vector2(0, 700)),
                           (big_laser1, Vector2(300, 700)),
                           (big_laser1, Vector2(-300, 700)),
                           (big_laser1, Vector2(500, 700)),
                           (big_laser1, Vector2(-500, 700)),
                (spread_snowflake1, Vector2(0, 0))], max_hp=100),
                BossPhase("5.1",
                          [(big_laser1, Vector2(0, 700)),
                           (big_laser1, Vector2(200, 700)),
                           (big_laser1, Vector2(-200, 700)),
                           (big_laser1, Vector2(400, 700)),
                           (big_laser1, Vector2(-400, 700)),
                           (blast_ring1, Vector2(0, 0))

                           ], max_hp=100),
                BossPhase("5.2",
                          [
                              (big_laser1, Vector2(0, 700)),
                              (big_laser1, Vector2(300, 700)),
                              (big_laser1, Vector2(-300, 700)),
                              (big_laser1, Vector2(500, 700)),
                              (big_laser1, Vector2(-500, 700)),
                              (big_ring1, Vector2(0, 0)),
                              (slow_ring2, Vector2(0, 0)),
                              (slow_ring1, Vector2(0, 0)),

                          ], max_hp=100),
                BossPhase("5.3",
                          [

                              (aimed_fan3, Vector2(-150, 0)),
                              (aimed_fan3, Vector2(150, 0)),
                              (normal_snowflake2, Vector2(150, 0)),
                              (partial_spiral2, Vector2(-150, 0)),

                          ], max_hp=100),
                BossPhase("5.4",
                          [

                              (partial_spiral2, Vector2(0, 0)),
                              (big_spiral1, Vector2(0, 0)),
                              (big_laser1, Vector2(0, 800)),
                              (big_laser1, Vector2(300, 800)),
                              (big_laser1, Vector2(-300, 800)),
                              (big_laser1, Vector2(500, 800)),
                              (big_laser1, Vector2(-500, 800)),

                          ], max_hp=100),
            ],
            boss_random_wander,
            20,
            enemies
        )

    # == UTILITY ==
    def kill_all():
        for site in STATIC_SITES:
            site.kill()
        for enemy in enemies:
            enemy.kill()

    def no_more_enemies_and_formations():
        return stage.all_waves_scheduled() and len(enemies) == 0 and len(formations) == 0

    end_banner = None
    def show_end_banner():
        nonlocal end_banner
        end_banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name} ... COMPLETE', 20,
                        Vector2(CANVAS_WIDTH // 2, 200), duration_ms=7000, start_delay=1000)

    def end_banner_done():
        return end_banner.done if end_banner is not None else False

    def always_true():
        """DEBUGGING: ALWAYS RETURNS TRUE"""
        return True

    def end_stage():
        help.gamestate = 'end_screen'
        bg.kill()
        pygame.mixer.music.pause()

    def start_mission():
        help.gamestate = 'stage5'

        pygame.mixer.init()
        pygame.mixer.music.load(resource_path('sounds/NO SOUND, NO MERCY.mp3'))
        pygame.mixer.music.play(-1, fade_ms=1000)

        if not help.skip_banners:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=1000)
            banner2 = TypingBanner(f"THEIR LEADER AWAITS YOUR ARRIVAL.", 20, Vector2(300, 200),
                                  start_delay=6000)
            banner3 = TypingBanner(f"HE WON'T FORGIVE YOUR BETRAYAL.", 20, Vector2(300, 300),
                                  start_delay=11000)
            banner4 = TypingBanner(f"...NEITHER WILL YOU.", 20, Vector2(300, 400),
                                  start_delay=16000)
        else:
            banner = TypingBanner(f'MISSION {player.stage_number} // {player.stage_name}', 30, Vector2(CANVAS_WIDTH // 2, 200),
                                  start_delay=0)

    # === SCHEUDLE EVENTS ===
    START_TIME = 21000 if not help.skip_banners else 4000  # 15000
    ONE_SECOND = 1000

    bg = ScrollingBackground('stage5background', background)

    # BEGIN MISSION
    stage.schedule(0, start_mission)

    # STAGE ENEMIES

    # PREPARE BOSS
    stage.schedule(START_TIME + 0 * ONE_SECOND, kill_all)
    stage.schedule(START_TIME + 0 * ONE_SECOND, stage.mark_waves_done)
    stage.wait_until(no_more_enemies_and_formations, spawn_boss)
    stage.wait_until(no_more_enemies_and_formations, spawn_boss2)

    # END LEVEL
    stage.wait_until(no_more_enemies_and_formations, show_end_banner)
    stage.wait_until(end_banner_done, end_stage)
