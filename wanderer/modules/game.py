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
        sprite_sheet = pygame.image.load(os.path.join("images", "lady_sprites.png")).convert()
        char_cursor = pygame.Rect(CHAR_WIDTH, 0, CHAR_WIDTH, CHAR_HEIGHT)
        char_sheet = sprite_sheet.subsurface(char_cursor)
        self.player = player.Player(sprites.Character(self.screen, char_sheet), self.font)
        self.all_sprites = pygame.sprite.RenderPlain((self.player.sprite,))
        self.all_particles = particles.ParticleGroup()
        print " * sprites"

        # Miscellany
        self.clock = pygame.time.Clock()
        self.controls = self.init_controls()
        print " * controls & clock"


    def loop(self):
        self.clock.tick(60)
        loop_time = self.clock.get_time()

        new_events = pygame.event.get()

        for control in self.controls:
            control.check(loop_time, new_events)

        self.player.update()
        self.all_sprites.update()
        self.all_particles.update(loop_time)

        self.screen.blit(self.background, (0,0))
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()

    def init_controls(self):
        controls = []
        controls.append(Control([QUIT, KEYDOWN], [K_q], 0, self.quit))
        controls.append(Control([KEYDOWN], [K_SPACE], 200, self.player.greet, self.all_particles))
        controls.append(Control([KEYDOWN], LEFT_KEYS, 0, self.player.sprite.accelerate, LEFT))
        controls.append(Control([KEYDOWN], RIGHT_KEYS, 0, self.player.sprite.accelerate, RIGHT))
        controls.append(Control([KEYDOWN], UP_KEYS, 0, self.player.sprite.accelerate, UP))
        controls.append(Control([KEYDOWN], DOWN_KEYS, 0, self.player.sprite.accelerate, DOWN))
        return controls

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

    def check(self, loop_time, events = []):
        if self.countdown:
            self.countdown -= loop_time
            if self.countdown < 0:
                self.countdown = 0
        else:
            for event in events:
                if event.type in self.events:
                    if event.type not in (KEYDOWN, KEYUP) or event.key in self.keys:
                        self.act(*self.act_args)
                        self.countdown = self.timeout
