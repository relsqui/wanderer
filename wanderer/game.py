import pygame, sys, random, jsonpickle, json
from wanderer.constants import *
from wanderer import agents, sprites, particles, timers, world

FONT_SIZE = 8       # point
BIG_FONT_SIZE = 16  # point
TITLE_SIZE = 32     # point

SPLASH_FILL_COLOR = (0, 160, 175)
SPLASH_TEXT_COLOR = (235, 180, 215)

WINDOW_HEIGHT = 640 # pixels (starting)
WINDOW_WIDTH = 640  # pixels (starting)
WINDOW_TITLE = "Wanderer"

KEY_DELAY = 200     # ms before keys start repeating
KEY_INTERVAL = 10   # ms between key repeats
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)

SAVEFILE = "wanderer.sav" 


class Game(object):
    """
    Game manager for display, timers, controls, etc.

    No arguments.
    """

    def __init__(self):
        super(Game, self).__init__()
        self.finished = False

        # Interface
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.get_surface()
        pygame.key.set_repeat(KEY_DELAY, KEY_INTERVAL)

        # Font. Freeware font from http://www.04.jp.org/
        font_file = os.path.join(DATA_DIR, "fonts", "04B_11__.TTF")
        self.font = pygame.font.Font(font_file, FONT_SIZE)
        self.big_font = pygame.font.Font(font_file, BIG_FONT_SIZE)
        title_file = os.path.join(DATA_DIR, "fonts", "04B_20__.TTF")
        self.title_font = pygame.font.Font(title_file, TITLE_SIZE)
        self.subtitle_font = pygame.font.Font(title_file, BIG_FONT_SIZE)

        # (this is the earliest we can display the splash screen)
        self.display_splash("Loading ...")

        # Files
        self.texts = {}
        self.sprites = {}
        self.init_files()

        # Sprites and agents
        self.all_particles = pygame.sprite.RenderUpdates()
        self.all_sprites = pygame.sprite.RenderUpdates()
        self.all_agents = []
        self.all_npcs = []

        # Miscellany
        self.clock = pygame.time.Clock()

    def confirm_start(self):
        self.display_splash("Ready!", "(hit enter)")
        while True:
            event = pygame.event.wait()
            if event.type in [KEYDOWN, KEYUP]:
                if event.key is K_RETURN:
                    break
                if event.key is K_q:
                    self.quit()
                    break

    def new(self):
        self.map = world.Map(pygame.Rect(0, 0, 20, 20))
        self.player = agents.Player(self, "Player")

    def display_splash(self, message = None, small_message = None):
        def centered(surface):
            return self.screen.get_rect().width/2 - surface.get_rect().width/2
        title_color = SPLASH_TEXT_COLOR
        self.screen.fill(SPLASH_FILL_COLOR)
        title = self.title_font.render("Wanderer", False, title_color)
        subtitle = self.subtitle_font.render("in a simple world", False, title_color)
        self.screen.blit(title, (centered(title), 100))
        self.screen.blit(subtitle, (centered(subtitle), 200))

        if message:
            text = self.big_font.render(message, False, title_color)
            self.screen.blit(text, (centered(text), 500))

        if small_message:
            text = self.font.render(small_message, False, title_color)
            self.screen.blit(text, (centered(text), 530))

        pygame.display.flip()

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

        self.map.update()
        if self.map.dirty:
            self.screen.blit(self.map.surface, (0, 0))
            self.map.dirty = False
        else:
            self.all_sprites.clear(self.screen, self.map.surface)
            self.all_particles.clear(self.screen, self.map.surface)
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()

    def init_files(self):
        "Internal. Initialize data files."
        text_directory = os.path.join(DATA_DIR, "text")
        text_files = os.listdir(text_directory)
        for filename in text_files:
            name, ext = os.path.splitext(filename)
            self.texts[name] = []
            f = open(os.path.join(text_directory, filename))
            for line in f:
                self.texts[name].append(line.strip())
            f.close()
        image_directory = os.path.join(DATA_DIR, "images")
        self.sprites = os.path.join(image_directory, "lady_sprites.png")

    def init_controls(self):
        "Internal. Initialize the game controls."
        controls = []
        handlers = dict()

        # Speech
        controls.append(Control([KEYDOWN], [K_SPACE], self.player.greet))
        controls.append(Control([KEYDOWN], [K_c], self.player.call))

        # Inventory
        controls.append(Control([KEYDOWN], [K_p], self.player.place))
        controls.append(Control([KEYDOWN], [K_u], self.player.pick_up))
        controls.append(Control([KEYDOWN], [K_i], self.player.inventory))

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

        # Miscellaneous
        controls.append(Control([QUIT, KEYDOWN], [K_q], self.quit))
        controls.append(Control([KEYDOWN], [K_n], agents.Npc, self))

        # Debug
        def p(*args):
            # cheeeeeats
            # if I were using py3 print, I wouldn't have to do this
            # but I'm not
            for arg in args:
                print arg,
            print
        controls.append(Control([KEYDOWN], [K_t], lambda: p(self.map.tiles_under(self.player.sprite.rect.centerx/32, self.player.sprite.rect.centery/32))))

        for control in controls:
            for event in control.events:
                if handlers.get(event):
                    handlers[event].append(control)
                else:
                    handlers[event] = [control]

        self.controls = controls
        self.handlers = handlers

    def save(self):
        savegame = {}
        savegame["map"] = self.map
        savegame["player"] = self.player
        savegame["npcs"] = self.all_npcs
        with open(SAVEFILE, 'w') as savefile:
            json.dump(self.map.to_json(), savefile, sort_keys=True, indent=4)
        print "Game saved."

    def load(self):
        with open(SAVEFILE) as savefile:
            savegame = json.load(savefile)
            print "Loading saved game."
        self.map = world.Map.from_json(savegame)
        self.player = agents.Player(self, "Player")
        self.all_npcs = []

    def quit(self):
        "Exit the game politely."
        self.save()
        self.finished = True


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
