import pygame, sys, random
from modules.constants import *
from modules import agents, sprites, particles, timers

class Game(object):
    """
    Game manager for display, timers, controls, etc.

    No arguments.
    """

    def __init__(self):
        print "Welcome! Initializing game ..."
        super(Game, self).__init__()
        pygame.init()
        if not pygame.font:
            print "Couldn't load pygame.font!"
            sys.exit(1)
        print " * pygame"

        # Interface
        self.window = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.get_surface()
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill(BACKGROUND_COLOR)
        self.font = pygame.font.Font(None, FONT_SIZE)
        pygame.key.set_repeat(KEY_DELAY, KEY_INTERVAL)
        print " * interface"

        # Sprites and agents
        self.all_particles = particles.ParticleGroup()
        self.all_sprites = pygame.sprite.RenderPlain()
        self.player = agents.Player(self.screen, self.font, self.all_particles, self.all_sprites, 2, None, "Player")
        buddyx = random.randrange(0, WINDOW_WIDTH - SPRITE_WIDTH)
        buddyy = random.randrange(0, WINDOW_HEIGHT - SPRITE_HEIGHT)
        buddy_location = pygame.Rect(buddyx, buddyy, SPRITE_WIDTH, SPRITE_HEIGHT)
        self.buddy = agents.Agent(self.screen, self.font, self.all_particles, self.all_sprites, None, buddy_location, "Buddy")
        self.all_agents = [self.player]
        print " * sprites & agents"

        # Miscellany
        self.clock = pygame.time.Clock()
        self.init_controls()
        print " * controls & clock"


    def loop(self):
        "Handle events, check timers, update sprites and particles, and re-render the screen."
        self.clock.tick(40)
        loop_time = self.clock.get_time()

        new_events = pygame.event.get()
        for event in new_events:
            """
            print "Heard a", pygame.event.event_name(event.type),
            if event.type in (KEYDOWN, KEYUP):
                print "({})".format(pygame.key.name(event.key))
            else:
                print
            """
            if self.handlers.get(event.type):
                for handler in self.handlers[event.type]:
                    handler.respond(event)

        for agent in self.all_agents:
            agent.update()
        self.all_sprites.update()
        self.all_particles.update()
        for timer in timers.all_timers:
            timer.update(loop_time)

        self.screen.blit(self.background, (0,0))
        for sprite in self.all_sprites:
            self.screen.fill((255, 200, 200), sprite.rect)
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()

    def init_controls(self):
        "Internal. Initialize the game controls."
        controls = []
        handlers = dict()

        # Quit
        controls.append(Control([QUIT, KEYDOWN], [K_q], self.quit))

        # Random greeting
        controls.append(Control([KEYDOWN], [K_SPACE], self.player.greet))

        # Movement
        controls.append(Control([KEYDOWN], LEFT_KEYS, self.player.move, LEFT))
        controls.append(Control([KEYDOWN], RIGHT_KEYS, self.player.move, RIGHT))
        controls.append(Control([KEYDOWN], UP_KEYS, self.player.move, UP))
        controls.append(Control([KEYDOWN], DOWN_KEYS, self.player.move, DOWN))
        controls.append(Control([KEYUP], LEFT_KEYS + RIGHT_KEYS + UP_KEYS + DOWN_KEYS, self.player.stop))

        # Appearance
        controls.append(Control([KEYDOWN], [K_1], self.player.set_sprite, 1))
        controls.append(Control([KEYDOWN], [K_2], self.player.set_sprite, 2))
        controls.append(Control([KEYDOWN], [K_3], self.player.set_sprite, 3))
        controls.append(Control([KEYDOWN], [K_4], self.player.set_sprite, 4))
        controls.append(Control([KEYDOWN], [K_5], self.player.set_sprite, 5))
        controls.append(Control([KEYDOWN], [K_6], self.player.set_sprite, 6))
        controls.append(Control([KEYDOWN], [K_7], self.player.set_sprite, 7))
        controls.append(Control([KEYDOWN], [K_8], self.player.set_sprite, 8))

        for control in controls:
            for event in control.events:
                if handlers.get(event):
                    handlers[event].append(control)
                else:
                    handlers[event] = [control]

        self.controls = controls
        self.handlers = handlers

    def quit(self):
        "Exit the game politely."
        print "Goodbye!"
        sys.exit(0)


class Control(object):
    """
    A piece of the game/player interface. Arguments:
        events      (list of pygame.event.Events to respond to)
        keys        (list of key constants to respond to)
        act         (function to call when invoked)
        *act_args   (arguments to function)
    """

    def __init__(self, events, keys, act, *act_args):
        super(Control, self).__init__()
        self.events = events
        self.keys = keys
        self.act = act
        self.act_args = act_args

    def respond(self, event):
        "Respond to one of our events, checking key if needed."
        if event.type not in (KEYDOWN, KEYUP) or event.key in self.keys:
            self.act(*self.act_args)
