import pygame, numpy, random, os, math
from pytmx import tmxloader
from wanderer.constants import *

TILE_SIZE = 32
COLOR_KEY = (0, 0, 0)


class Map(object):
    "Stores data about the map. Initialize with the location of a map to load."

    def __init__(self, px_width, px_height):
        self.surface = pygame.Surface((px_width, px_height))
        self.surface.set_colorkey(COLOR_KEY)
        self.width = int(math.ceil(px_width/TILE_SIZE))
        self.height = int(math.ceil(px_height/TILE_SIZE))
        self.dirty = True

        self.layers = []
        self.layers.append(Layer(self.width, self.height).fill(Tile, "water", True))
        dirt = Layer(self.width, self.height).fill(Tile, "dirt")
        dirt.set_row(0, None)
        dirt.set_row(self.height-1, None)
        dirt.set_column(0, None)
        dirt.set_column(self.width-1, None)
        self.layers.append(dirt)
        # self.layers.append(Layer(self.width-4, self.height-4, 2, 2).fill(Tile, "grass"))
        self.player_modified = Layer(self.width, self.height)
        self.layers.append(self.player_modified)

        self.tile_masks = {} # to store masks cached by get_tile_mask
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((px_width, px_height))
        self.walk_mask.image.set_colorkey(COLOR_KEY)
        self.walk_mask.rect = self.surface.get_rect()

        self.update()

    def update(self):
        "Redraw the map surface and walk mask."
        for index, layer in enumerate(self.layers):
            while layer.update():
                # keep updating until it stops having sprites to update
                pass
                self.dirty = True
            self.surface.blit(layer.surface, layer.rect)
            # everybody gets blitted, in case a
            # higher layer updated to transparent
        for x in xrange(self.width):
            for y in xrange(self.height):
                mask = self.get_tile_mask(x, y)
                self.walk_mask.image.blit(mask, (x*TILE_SIZE, y*TILE_SIZE))

    def walkable_rect(self, position):
        "Takes a pygame.Rect, returns True iff all corners are on walkable points."
        for corner in (position.topleft, position.bottomleft, position.topright, position.bottomright):
            if not self.walkable_coords(*corner):
                return False
        return True

    def walkable_coords(self, px_x, px_y):
        "Returns True if the pixel at the coordinates given is walkable, False otherwise."
        pixel = self.walk_mask.image.get_at((px_x, px_y))[0:3]
        if pixel == COLOR_KEY:
            return True
        return False

    def walkable_mask(self, sprite):
        "Takes a sprite (with .image and .rect attributes), and returns True unless any non-alpha part of that sprite is on top of any visible part of a nowalk tile."
        if pygame.sprite.collide_mask(sprite, self.walk_mask):
            return False
        return True

    def get_tile_mask(self, x, y, force = False):
        "Returns a pygame.Surface whose colorkey transparency values match the walkable status of the terrain at the given tile location. Caches these masks."
        if force or not self.tile_masks.has_key((x, y)):
            if COLOR_KEY == (0, 0, 0):
                new_color_key = (255, 255, 255)
            else:
                new_color_key = (0, 0, 0)
            tile_mask = pygame.Surface((TILE_SIZE, TILE_SIZE))
            tile_mask.set_colorkey(COLOR_KEY)
            for tile in self.tiles_under(x, y):
                if tile:
                    if tile.nowalk:
                        tile_mask.fill(COLOR_KEY)
                    else:
                        tile_mask.blit(tile.image, (0,0))
            # modified from source of pygame.surfarray.array_color_key
            # which turned out to be easier than just using it
            key_int = tile_mask.map_rgb(COLOR_KEY)
            new_key_int = tile_mask.map_rgb(new_color_key)
            mask_array = pygame.surfarray.pixels2d(tile_mask)
            mask_array = numpy.choose(numpy.equal(mask_array, key_int), (key_int, new_key_int))
            mask_array.shape = TILE_SIZE, TILE_SIZE
            tile_mask = pygame.surfarray.make_surface(mask_array)
            tile_mask.set_colorkey(COLOR_KEY)
            self.tile_masks[(x, y)] = tile_mask
        return self.tile_masks[(x, y)]

    def tiles_under(self, x, y):
        "Returns a list of tiles under the coordinates given, from bottom layer to top."
        tiles = []
        for index, layer in enumerate(self.layers):
            tile = layer.get_tile(x, y)
            tiles.append(tile)
        return tiles

    def dig(self, px_x, px_y):
        "Attempts to dig away a tile under the coordinates given."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        for layer in reversed(self.layers):
            # not using tiles_under because we need the layer info
            tile = layer.get_tile(x, y)
            if not tile:
                continue
            if tile.name == "grass":
                tile.health -= 4
                if tile.health < 0:
                    layer.set_tile(x, y, None)
                else:
                    layer.dirty_tiles.append((x, y))
                return True
            else:
                # we hit a non-grass tile
                return False
        # went all the way through the tile stack
        return False

    def seed(self, px_x, px_y):
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        self.player_modified.set_tile(x, y, Tile("grass"))


class Layer(object):
    "Stores a grid of tile objects and a surface which depicts them. Initialize with width and height in tiles."

    def __init__(self, width, height, top=0, left=0):
        super(Layer, self).__init__()
        self.width = width
        self.height = height
        self.top = top
        self.left = left
        self.tiles = {}
        px_size = (width*TILE_SIZE, height*TILE_SIZE)
        px_topleft = (left*TILE_SIZE, top*TILE_SIZE)
        self.rect = pygame.Rect(px_topleft, px_size)
        self.surface = pygame.Surface(px_size)
        self.surface.set_colorkey(COLOR_KEY)
        self.dirty_tiles = []

    def get_tile(self, x, y):
        "Return the tile at position x, y or None if there is none."
        if self.tiles.has_key((x, y)):
            return self.tiles[(x, y)]
        return None

    def set_tile(self, x, y, tile):
        "Set the tile at x, y to the given tile, or None (destroy it)."
        destroy_tile = False
        if tile:
            new_tile = tile
            self.tiles[(x, y)] = new_tile
        else:
            if self.get_tile(x, y):
                # unsetting a tile which did exist
                # clear its neighbors first
                new_tile = self.get_tile(x, y)
                new_tile.bitmask = 0
                destroy_tile = True
            else:
                # unsetting a tile which didn't exist
                return

        bit_changes = []
        bit_changes.append(((0, -1), 0b1100, lambda x: x >> 2))
        bit_changes.append(((0, 1), 0b0011, lambda x: x << 2))
        bit_changes.append(((-1, 0), 0b1010, lambda x: x >> 1))
        bit_changes.append(((1, 0), 0b0101, lambda x: x << 1))

        def debug(*args):
            return
            if new_tile.name == "grass":
                for arg in args:
                    print arg,
                print

        debug("\nplacing grass tile at", (x, y), "with bitmask {:b}".format(new_tile.bitmask))
        for transformation, mask, shift in bit_changes:
            dx, dy = transformation
            debug("checking for neighbor tile at", (x+dx, y+dy))
            if x+dx not in xrange(self.left, self.left+self.width)\
              or y+dy not in xrange(self.top, self.top+self.height):
                debug("out of range")
                continue
            neighbor = self.get_tile(x+dx, y+dy)
            debug("in range. transformation is {}, mask is {:b}".format(transformation, mask))
            if neighbor:
                old_mask = neighbor.bitmask
                debug("tile exists already, its mask is {:b}".format(old_mask))
            else:
                neighbor = Tile(new_tile.name, mask = 0)
                old_mask = 0
                debug("no tile there, creating one with a blank mask")
            new_mask = shift(new_tile.bitmask & mask) | (old_mask & mask)
            debug("new mask is", new_mask)
            if new_mask != old_mask:
                debug("it's changed, so replacing the tile")
                neighbor.bitmask = new_mask
                self.set_tile(x+dx, y+dy, neighbor)

        if destroy_tile:
            self.tiles.pop((x, y))
        self.dirty_tiles.append((x, y))

    def update(self):
        "Redraw tiles at any changed locations."
        if not self.dirty_tiles:
            return False
        blank = pygame.Surface((TILE_SIZE, TILE_SIZE))
        blank.fill(COLOR_KEY)
        for location in self.dirty_tiles:
            x, y = location
            px_x = (x - self.left) * TILE_SIZE
            px_y = (y - self.top) * TILE_SIZE
            tile = self.get_tile(x, y)
            self.surface.blit(blank, (px_x, px_y))
            if tile:
                self.surface.blit(tile.image, (px_x, px_y))
        self.dirty_tiles = []
        return True

    def fill(self, tile, *args):
        "Fill the layer with instances of a Tile callable."
        for x in xrange(self.left, self.left + self.width):
            for y in xrange(self.top, self.top + self.height):
                self.set_tile(x, y, tile(*args))
        return self
        # ^ so we can initialize with layer = Layer(x, y).fill(tile)

    def set_row(self, y, tile, *args):
        "Fill a row with instances of a Tile callable."
        for x in xrange(self.width):
            if tile:
                tile = tile(*args)
                # as opposed to None to clear the spot
            self.set_tile(x, y, tile)

    def set_column(self, x, tile, *args):
        "Fill a column with instances of a Tile callable."
        for y in xrange(self.height):
            if tile:
                tile = tile(*args)
            self.set_tile(x, y, tile)


class Tile(object):
    "Information about a specific tile."

    def __init__(self, name, nowalk = False, mask = 0b1111):
        super(Tile, self).__init__()
        self.name = name
        self.nowalk = nowalk
        self.bitmask = mask
        self.health = 3.0

        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        tile_locations = {}

        # center
        tile_locations[0b1111] = (1, 3)
        # center variants in descending density: (0-2, 5)

        # corner
        tile_locations[0b0001] = (0, 2)
        tile_locations[0b0010] = (2, 2)
        tile_locations[0b0100] = (0, 4)
        tile_locations[0b1000] = (2, 4)
        
        # anticorner
        tile_locations[0b1110] = (1, 0)
        tile_locations[0b1101] = (2, 0)
        tile_locations[0b1011] = (1, 1)
        tile_locations[0b0111] = (2, 1)

        # edge
        tile_locations[0b0011] = (1, 2)
        tile_locations[0b1010] = (2, 3)
        tile_locations[0b0101] = (0, 3)
        tile_locations[0b1100] = (1, 4)


        self.variants = {}
        cursor = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        for mask, location in tile_locations.items():
            x, y = location
            x *= TILE_SIZE
            y *= TILE_SIZE
            cursor.topleft = (x, y)
            self.variants[mask] = tile_sheet.subsurface(cursor)
            self.variants[mask].set_colorkey(COLOR_KEY)

        # double corners
        nw_se = pygame.Surface((TILE_SIZE, TILE_SIZE))
        nw_se.set_colorkey(COLOR_KEY)
        nw_se.blit(self.variants[0b1000], (0, 0))
        nw_se.blit(self.variants[0b0001], (0, 0))
        self.variants[0b1001] = nw_se

        ne_sw = pygame.Surface((TILE_SIZE, TILE_SIZE))
        ne_sw.set_colorkey(COLOR_KEY)
        ne_sw.blit(self.variants[0b0100], (0, 0))
        ne_sw.blit(self.variants[0b0010], (0, 0))
        self.variants[0b0110] = ne_sw

        self.spot = {}
        cursor.topleft = (0, 0)
        self.spot[2] = tile_sheet.subsurface(cursor)
        self.spot[2].set_colorkey((COLOR_KEY))
        cursor.topleft = (0, TILE_SIZE)
        self.spot[1] = tile_sheet.subsurface(cursor)
        self.spot[1].set_colorkey((COLOR_KEY))

        self.variants[0] = self.spot[2]

    def __repr__(self):
        return '<Tile object "{}">'.format(self.name)

    @property
    def image(self):
        """
        if neighbor_mask == (0, 0, 0, 0):
            self.health = min(self.health, 2)
        else:
            self.health = max(self.health, 3)

        if self.health > 2:
            self.image = self.variants[neighbor_mask]
        else:
            self.image = self.spot[math.ceil(self.health)]
            neighbor_mask = (0, 0, 0, 0)
        """

        image = self.variants[self.bitmask]

        if self.name == "grass":
            font = pygame.font.Font(os.path.join(DATA_DIR, "04B_11__.TTF"), 8)
            string_mask = "{:04b}".format(self.bitmask)
            line1 = font.render(string_mask[:2], False, (100, 0, 0))
            line2 = font.render(string_mask[2:], False, (100, 0, 0))
            image.blit(line1, (14, 6))
            image.blit(line2, (14, 16))

        image.set_colorkey(COLOR_KEY)
        return image
