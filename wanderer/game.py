import pygame, sys, random
from wanderer.constants import *
from wanderer import agents, sprites, particles, timers

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
        # freeware font from http://www.04.jp.org/
        self.font = pygame.font.Font(FONT_FILE, FONT_SIZE)
        self.big_font = pygame.font.Font(FONT_FILE, BIG_FONT_SIZE)
        pygame.key.set_repeat(KEY_DELAY, KEY_INTERVAL)
        print " * interface"

        # Files
        self.TEXT = {}
        self.SPRITES = {}
        self.init_files()

        # Sprites and agents
        self.all_particles = pygame.sprite.RenderPlain()
        self.all_sprites = pygame.sprite.RenderPlain()
        self.all_agents = []
        self.all_npcs = []
        self.player = agents.Player(self, "Player")
        print " * agents"

        # Miscellany
        self.clock = pygame.time.Clock()
        self.init_controls()
        print " * controls & clock"
        print "Done."


    def loop(self):
        "Handle events, check timers, update sprites and particles, and re-render the screen."
        self.clock.tick(40)
        loop_time = self.clock.get_time()

        new_events = pygame.event.get()
        for event in new_events:
            """
            print "Heard", pygame.event.event_name(event.type),
            if event.type in (KEYDOWN, KEYUP):
                print "({})".format(pygame.key.name(event.key))
            else:
                print
            # """
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
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()
        sys.stdout.flush()

    def init_files(self):
        "Internal. Initialize data files."
        text_directory = os.path.join(DATA_DIR, "text")
        text_files = os.listdir(text_directory)
        for filename in text_files:
            name, ext = os.path.splitext(filename)
            self.TEXT[name] = []
            f = open(os.path.join(text_directory, filename))
            for line in f:
                self.TEXT[name].append(line.strip())
            f.close()
        image_directory = os.path.join(DATA_DIR, "images")
        self.SPRITES = os.path.join(image_directory, "lady_sprites.png")

    def init_controls(self):
        "Internal. Initialize the game controls."
        controls = []
        handlers = dict()

        # Quit
        controls.append(Control([QUIT, KEYDOWN], [K_q], self.quit))

        # Speech
        controls.append(Control([KEYDOWN], [K_SPACE], self.player.greet))
        controls.append(Control([KEYDOWN], [K_c], self.player.call))

        # Movement
        controls.append(Control([KEYDOWN], LEFT_KEYS, self.player.walk, LEFT))
        controls.append(Control([KEYDOWN], RIGHT_KEYS, self.player.walk, RIGHT))
        controls.append(Control([KEYDOWN], UP_KEYS, self.player.walk, UP))
        controls.append(Control([KEYDOWN], DOWN_KEYS, self.player.walk, DOWN))
        controls.append(Control([KEYUP], LEFT_KEYS + RIGHT_KEYS + UP_KEYS + DOWN_KEYS, self.player.stand))

        # Appearance
        controls.append(Control([KEYDOWN], [K_1], self.player.set_sprite, 1))
        controls.append(Control([KEYDOWN], [K_2], self.player.set_sprite, 2))
        controls.append(Control([KEYDOWN], [K_3], self.player.set_sprite, 3))
        controls.append(Control([KEYDOWN], [K_4], self.player.set_sprite, 4))
        controls.append(Control([KEYDOWN], [K_5], self.player.set_sprite, 5))
        controls.append(Control([KEYDOWN], [K_6], self.player.set_sprite, 6))
        controls.append(Control([KEYDOWN], [K_7], self.player.set_sprite, 7))
        controls.append(Control([KEYDOWN], [K_8], self.player.set_sprite, 8))

        # NPCs
        controls.append(Control([KEYDOWN], [K_n], agents.Npc, self))

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
