import pygame, sys
from modules.constants import *
from modules import player, sprites, particles, timers

class Game(object):
    def __init__(self):
        print "Welcome! Initializing game ..."
        super(Game, self).__init__()
        pygame.init()
        if not pygame.font:
            print "Couldn't load pygame.font!"
            sys.exit(1)
        print " * pygame"

        # Display and screen
        self.window = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.get_surface()
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill(BACKGROUND_COLOR)
        self.font = pygame.font.Font(None, FONT_SIZE)
        print " * display"

        # Sprites and player
        self.all_particles = particles.ParticleGroup()
        sprite_sheet = pygame.image.load(os.path.join("images", "lady_sprites.png")).convert()
        char_cursor = pygame.Rect(CHAR_WIDTH, 0, CHAR_WIDTH, CHAR_HEIGHT)
        char_sheet = sprite_sheet.subsurface(char_cursor)
        self.player = player.Player(sprites.Character(self.screen, char_sheet, self.font, self.all_particles))
        self.all_sprites = pygame.sprite.RenderPlain((self.player.sprite,))
        print " * sprites"

        # Miscellany
        self.clock = pygame.time.Clock()
        self.init_controls()
        print " * controls & clock"


    def loop(self):
        self.clock.tick(60)
        loop_time = self.clock.get_time()

        new_events = pygame.event.get()
        for event in new_events:
            if self.handlers.get(event.type):
                for handler in self.handlers[event.type]:
                    handler.check(event)

        self.player.update()
        self.all_sprites.update()
        self.all_particles.update(loop_time)
        for control in self.controls:
            control.update(loop_time)
        for timer in timers.all_timers:
            timer.update(loop_time)

        self.screen.blit(self.background, (0,0))
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()

    def init_controls(self):
        controls = []
        handlers = dict()

        # Quit
        controls.append(Control([QUIT, KEYDOWN], [K_q], 0, self.quit))

        # Random greeting
        controls.append(Control([KEYDOWN], [K_SPACE], 200, self.player.greet))

        # Movement
        controls.append(Control([KEYDOWN], LEFT_KEYS, 0, self.player.sprite.move, LEFT))
        controls.append(Control([KEYUP], LEFT_KEYS, 0, self.player.sprite.accelerate, RIGHT, True))
        controls.append(Control([KEYDOWN], RIGHT_KEYS, 0, self.player.sprite.move, RIGHT))
        controls.append(Control([KEYUP], RIGHT_KEYS, 0, self.player.sprite.accelerate, LEFT, True))
        controls.append(Control([KEYDOWN], UP_KEYS, 0, self.player.sprite.move, UP))
        controls.append(Control([KEYUP], UP_KEYS, 0, self.player.sprite.accelerate, DOWN, True))
        controls.append(Control([KEYDOWN], DOWN_KEYS, 0, self.player.sprite.move, DOWN))
        controls.append(Control([KEYUP], DOWN_KEYS, 0, self.player.sprite.accelerate, UP, True))

        for control in controls:
            for event in control.events:
                if handlers.get(event):
                    handlers[event].append(control)
                else:
                    handlers[event] = [control]

        self.controls = controls
        self.handlers = handlers

    def quit(self):
        print "Goodbye!"
        sys.exit(0)


class Control(object):
    def __init__(self, events, keys, timeout, act, *act_args):
        super(Control, self).__init__()
        self.events = events
        self.keys = keys
        self.timeout = timeout
        self.countdown = 0
        self.act = act
        self.act_args = act_args

    def update(self, loop_time):
        if self.countdown:
            self.countdown -= loop_time
            if self.countdown < 0:
                self.countdown = 0

    def check(self, event):
        if not self.countdown:
                if event.type not in (KEYDOWN, KEYUP) or event.key in self.keys:
                    self.act(*self.act_args)
                    self.countdown = self.timeout
