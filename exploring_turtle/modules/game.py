import pygame, sys
from modules.constants import *
from modules import player, sprites, particles

class Game(object):
    def __init__(self):
        print "Initializing game ..."
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
        self.player = player.Player(sprites.Turtle(self.screen), self.font)
        self.all_sprites = pygame.sprite.RenderPlain((self.player.sprite,))
        self.all_particles = particles.ParticleGroup()
        print " * sprites"

        # Miscellany
        self.keys_down = dict()
        self.clock = pygame.time.Clock()
        self.controls = self.init_controls()
        print " * controls & clock"


    def loop(self):
        self.clock.tick(60)
        loop_time = self.clock.get_time()

        new_events = []
        for event in pygame.event.get():
            if event.type is KEYDOWN:
                self.keys_down[event.key] = True
            elif event.type is KEYUP:
                self.keys_down[event.key] = False
            else:
                new_events.append(event)

        for control in self.controls:
            control.check(loop_time, self.keys_down, new_events)

        self.player.update()
        self.all_sprites.update()
        self.all_particles.update(loop_time)

        self.screen.blit(self.background, (0,0))
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()

    def init_controls(self):
        controls = []
        controls.append(Control([QUIT], [K_q], 0, sys.exit, 0))
        controls.append(Control([], [K_SPACE], 200, self.player.greet, self.all_particles))
        controls.append(Control([], LEFT_KEYS, 0, self.player.sprite.move, LEFT))
        controls.append(Control([], RIGHT_KEYS, 0, self.player.sprite.move, RIGHT))
        controls.append(Control([], UP_KEYS, 0, self.player.sprite.move, UP))
        controls.append(Control([], DOWN_KEYS, 0, self.player.sprite.move, DOWN))
        return controls


class Control(object):
    def __init__(self, events, keys, timeout, act, *act_args):
        super(Control, self).__init__()
        self.events = events
        self.keys = keys
        self.timeout = timeout
        self.countdown = 0
        self.act = act
        self.act_args = act_args

    def check(self, loop_time, keys_down = [], events = []):
        if self.countdown:
            self.countdown -= loop_time
            if self.countdown < 0:
                self.countdown = 0
        else:
            for key in self.keys:
                if keys_down.get(key):
                    self.act(*self.act_args)
                    self.countdown = self.timeout
                    return
            else:
                for event in events:
                    if event in self.events:
                        self.act(*self.act_args)
                        self.countdown = self.timeout
                        return
