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
        self.layers = []
        self.dirty = False

        ocean = Layer(self.width, self.height).fill(Ocean)
        dirt = Layer(self.width, self.height).fill(Tile, "dirt")
        grass = Layer(self.width, self.height).fill(Tile, "grass")

        dirt.set_row(0, None)
        dirt.set_row(self.height-1, None)
        dirt.set_column(0, None)
        dirt.set_column(self.width-1, None)

        grass.set_row(0, None)
        grass.set_row(1, None)
        grass.set_row(self.height-2, None)
        grass.set_row(self.height-1, None)
        grass.set_column(0, None)
        grass.set_column(1, None)
        grass.set_column(self.width-2, None)
        grass.set_column(self.width-1, None)

        for layer in [ocean, dirt, grass]:
            layer.update()
            self.layers.append(layer)

        self.tile_masks = {} # to store masks cached by get_tile_mask
        layer.update()
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((px_width, px_height))
        self.walk_mask.image.set_colorkey(COLOR_KEY)
        self.walk_mask.rect = self.surface.get_rect()

        self.update()

    def update(self):
        "Redraw the map surface and walk mask."
        for layer in self.layers:
            self.surface.blit(layer.surface, (0, 0))
        for x in xrange(self.width):
            for y in xrange(self.height):
                mask = self.get_tile_mask(x, y)
                self.walk_mask.image.blit(mask, (x*TILE_SIZE, y*TILE_SIZE))
        self.dirty = True

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
        for layer in self.layers:
            tiles.append(layer.get_tile(x, y))
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
                layer.set_tile(x, y, None)
                layer.update()
                self.update()
                return True
            else:
                # we hit a non-grass tile
                return False
        # went all the way through the tile stack
        return False



class Layer(object):
    "Stores a grid of tile objects and a surface which depicts them. Initialize with width and height in tiles."

    def __init__(self, width, height):
        super(Layer, self).__init__()
        self.width = width
        self.height = height
        self.tiles = {}
        # surface will be set by update() after we get some tiles

    def get_tile(self, x, y):
        "Return the tile at position x, y or None if there is none."
        if self.tiles.has_key((x, y)):
            return self.tiles[(x, y)]
        return None

    def set_tile(self, x, y, tile, *args):
        "Set the tile at x, y to the given Tile callable with the arguments supplied, or None"
        if tile:
            new_tile = tile(*args)
            new_tile.set_neighbors(self, x, y)
            self.tiles[(x, y)] = new_tile
        else:
            self.tiles[(x, y)] = None

    def update(self):
        "Update neighbors and images for all tiles on the layer."
        for x in xrange(self.width):
            for y in xrange(self.height):
                if self.tiles.has_key((x, y)):
                    tile = self.tiles[(x, y)]
                    if tile:
                        tile.set_neighbors(self, x, y)
        # yes, we're doing the WHOLE LOOP twice
        # because we need to set all the neighbors
        # before we can make all the images
        self.surface = pygame.Surface((self.width*TILE_SIZE, self.height*TILE_SIZE))
        self.surface.set_colorkey(COLOR_KEY)
        for x in xrange(self.width):
            for y in xrange(self.height):
                if self.tiles.has_key((x, y)):
                    tile = self.tiles[(x, y)]
                    if tile:
                        tile.make_image()
                        self.surface.blit(tile.image, (x*TILE_SIZE, y*TILE_SIZE))

    def fill(self, tile, *args):
        for x in xrange(self.width):
            for y in xrange(self.height):
                self.set_tile(x, y, tile, *args)
        return self
        # ^ so we can initialize with layer = Layer(x, y).fill(tile)

    def set_row(self, y, tile, *args):
        for x in xrange(self.width):
            self.set_tile(x, y, tile, *args)

    def set_column(self, x, tile, *args):
        for y in xrange(self.height):
            self.set_tile(x, y, tile, *args)


class Tile(object):
    "Information about a specific tile."

    def __init__(self, name, nowalk = False):
        super(Tile, self).__init__()
        self.name = name
        self.nowalk = nowalk
        self.image = None
        self.neighbors = {}

        NORTH, SOUTH, EAST, WEST = (1, 2, 4, 8)
        ALL = NORTH + SOUTH + EAST + WEST
        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        tile_locations = {}

        # spot
        tile_locations[0] = [(0, 0), (0, 1)]

        # center
        tile_locations[15] = [(1, 3), (0, 5), (1, 5), (2, 5)]

        # corner
        # note that the directions used as indices are where neighbor tiles ARE
        # i.e. NORTH+EAST is for the SOUTHWEST corner tile variant
        tile_locations[SOUTH+EAST] = [(0, 2)]
        tile_locations[SOUTH+WEST] = [(2, 2)]
        tile_locations[NORTH+EAST] = [(0, 4)]
        tile_locations[NORTH+WEST] = [(2, 4)]

        # edge
        # unlike the above, ALL-NORTH is actually the north edge, etc.
        tile_locations[ALL-NORTH] = [(1, 2)]
        tile_locations[ALL-WEST] = [(0, 3)]
        tile_locations[ALL-EAST] = [(2, 3)]
        tile_locations[ALL-SOUTH] = [(1, 4)]

        # ignoring anticorner tiles for now, but they're at (1, 0) through (2, 1)

        self.variants = {}
        cursor = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        for shape, locations in tile_locations.items():
            self.variants[shape] = []
            for location in locations:
                x, y = location
                x *= TILE_SIZE
                y *= TILE_SIZE
                cursor.topleft = (x, y)
                self.variants[shape].append(tile_sheet.subsurface(cursor))

    def set_neighbors(self, layer, x, y):
        NORTH, SOUTH, EAST, WEST = (1, 2, 4, 8)
        self.neighbors[NORTH] = layer.get_tile(x, y-1)
        self.neighbors[SOUTH] = layer.get_tile(x, y+1)
        self.neighbors[EAST] = layer.get_tile(x+1, y)
        self.neighbors[WEST] = layer.get_tile(x-1, y)

    def make_image(self):
        NORTH, SOUTH, EAST, WEST = (1, 2, 4, 8)
        ALL = NORTH + SOUTH + EAST + WEST

        like_neighbors = 0
        for direction, neighbor in self.neighbors.items():
            if neighbor and neighbor.name == self.name:
                like_neighbors += direction

        if not self.variants.has_key(like_neighbors):
            like_neighbors = 0
            # this makes it nice and conspicuous so we can figure out what went wrong
            # (also, a known default lets us do tricky things like Ocean)

        self.image = random.choice(self.variants[like_neighbors])
        self.image.set_colorkey(COLOR_KEY)


class Ocean(Tile):
    "Water tiles that are only ever center tiles, to use as a backdrop."
    def __init__(self):
        super(Ocean, self).__init__("water", True)
        centers = self.variants[15]
        del(self.variants)
        self.variants = {0: centers}
