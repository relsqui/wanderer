import pygame, sys, random
from pytmx import tmxloader
from wanderer.constants import *
from wanderer import agents, sprites, particles, timers

class Game(object):
    """
    Game manager for display, timers, controls, etc.

    No arguments.
    """

    FONT_SIZE = 8       # point
    BIG_FONT_SIZE = 16  # point
    # color setting is in particles.TextParticle

    WINDOW_HEIGHT = 640 # pixels (starting)
    WINDOW_WIDTH = 640  # pixels (starting)
    WINDOW_TITLE = "Wanderer"

    KEY_DELAY = 200     # ms before keys start repeating
    KEY_INTERVAL = 10   # ms between key repeats
    LEFT_KEYS = (K_h, K_LEFT, K_a)
    RIGHT_KEYS = (K_l, K_RIGHT, K_d)    # these define three control options:
    UP_KEYS = (K_k, K_UP, K_w)          # wasd, hjkl, and arrow keys
    DOWN_KEYS = (K_j, K_DOWN, K_s)

    def __init__(self):
        print "Welcome! Initializing game ..."
        super(Game, self).__init__()
        pygame.init()
        if not pygame.font:
            print "Couldn't load pygame.font!"
            sys.exit(1)
        print " * pygame"

        if getattr(sys, 'frozen', None):
            BASEDIR = sys._MEIPASS
        else:
            BASEDIR = os.path.dirname(__file__)
        self.data_dir = os.path.join(BASEDIR, "data")

        # Interface
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption(self.WINDOW_TITLE)
        self.screen = pygame.display.get_surface()
        pygame.key.set_repeat(self.KEY_DELAY, self.KEY_INTERVAL)

        # Font. Freeware font from http://www.04.jp.org/
        font_file = os.path.join(self.data_dir, "04B_11__.TTF")
        self.font = pygame.font.Font(font_file, self.FONT_SIZE)
        self.big_font = pygame.font.Font(font_file, self.BIG_FONT_SIZE)
        print " * interface"

        island_map = os.path.join(self.data_dir, "maps", "island.tmx")
        self.map = Map(island_map)
        self.screen.blit(self.map.surface, (0,0))
        print " * map"

        # Files
        self.TEXT = {}
        self.SPRITES = {}
        self.init_files()

        # Sprites and agents
        self.all_particles = pygame.sprite.RenderUpdates()
        self.all_sprites = pygame.sprite.RenderUpdates()
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

        self.all_sprites.clear(self.screen, self.map.surface)
        self.all_particles.clear(self.screen, self.map.surface)
        self.all_sprites.draw(self.screen)
        self.all_particles.draw(self.screen)
        pygame.display.flip()
        sys.stdout.flush()

    def init_files(self):
        "Internal. Initialize data files."
        text_directory = os.path.join(self.data_dir, "text")
        text_files = os.listdir(text_directory)
        for filename in text_files:
            name, ext = os.path.splitext(filename)
            self.TEXT[name] = []
            f = open(os.path.join(text_directory, filename))
            for line in f:
                self.TEXT[name].append(line.strip())
            f.close()
        image_directory = os.path.join(self.data_dir, "images")
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
        controls.append(Control([KEYDOWN], self.LEFT_KEYS, self.player.walk, LEFT))
        controls.append(Control([KEYDOWN], self.RIGHT_KEYS, self.player.walk, RIGHT))
        controls.append(Control([KEYDOWN], self.UP_KEYS, self.player.walk, UP))
        controls.append(Control([KEYDOWN], self.DOWN_KEYS, self.player.walk, DOWN))
        controls.append(Control([KEYUP], self.LEFT_KEYS + self.RIGHT_KEYS + self.UP_KEYS + self.DOWN_KEYS, self.player.stand))

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


class Map(object):
    "Stores data about the map. Initialize with the location of a map to load."

    def __init__(self, map_location):
        self.data = tmxloader.load_pygame(map_location)
        pxwidth, pxheight = self.tile2px(self.data.width, self.data.height)
        self.surface = pygame.Surface((pxwidth, pxheight))
        for l in xrange(len(self.data.tilelayers)):
            for y in xrange(self.data.height):
                for x in xrange(self.data.width):
                    tile = self.data.getTileImage(x, y, l)
                    if tile:
                        self.surface.blit(tile, self.tile2px(x, y))

    def walkable_rect(self, position):
        "Takes a pygame.Rect, returns True iff all corners are on walkable tiles."
        for corner in (position.topleft, position.bottomleft, position.topright, position.bottomright):
            if not self.walkable_coords(*corner):
                return False
        return True

    def walkable_coords(self, x, y):
        """
        Given x, y pixel coordinates, returns:
            False if there are no tiles under those coordinates
            False if the topmost tile present is set to nowalk
            True otherwise, i.e. there are tiles and the topmost is walkable
        """
        walkable = True
        for gid in self.tiles_under(x, y):
            if gid:
                # there's a tile present
                try:
                    properties = self.data.tile_properties[gid]
                    if properties["nowalk"]:
                        walkable = False
                except KeyError:
                    # it has no properties
                    walkable = True
        return walkable

    def tiles_under(self, x, y):
        x, y = self.px2tile(x, y)
        tiles = []
        for layer in self.data.tilelayers:
            tiles.append(layer.data[y][x])
        return tiles

    def walkable_mask(self, image):
        pass

    def px2tile(self, x, y):
        "Converts an x, y position from real (pixel) position to tile location."
        return (x / self.data.tilewidth, y / self.data.tileheight)

    def tile2px(self, x, y):
        "Converts an x, y position from tile location to real (pixel) position."
        return (x * self.data.tilewidth, y * self.data.tileheight)
