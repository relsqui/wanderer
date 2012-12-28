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

        ocean = Layer(self.width, self.height).fill(Tile, "water", True)
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

        # ocean doesn't need settling because we haven't changed it since the fill
        dirt.settle_tiles()
        grass.settle_tiles()
        for layer in [ocean, dirt, grass]:
            self.layers.append(layer)
            self.surface.blit(layer.surface, (0, 0))

        self.tile_masks = {}
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((px_width, px_height))
        self.walk_mask.image.set_colorkey(COLOR_KEY)
        self.walk_mask.rect = self.surface.get_rect()
        self.walk_mask.image.fill(COLOR_KEY)
        # ^ temporary, while we're getting the map working at all

    def walkable_rect(self, position):
        "Takes a pygame.Rect, returns True iff all corners are on walkable points."
        for corner in (position.topleft, position.bottomleft, position.topright, position.bottomright):
            if not self.walkable_coords(*corner):
                return False
        return True

    def walkable_coords(self, px_x, px_y):
        "Returns True if the pixel at the coordinates given is walkable, False otherwise."
        pixel = self.walk_mask.image.get_at(px_x, px_y)[0:3]
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
            new_color_key = (255, 255, 255)
            tile_mask = pygame.Surface((TILE_SIZE, TILE_SIZE))
            for tile in self.tiles_under(x, y):
                if tile:
                    if tile.nowalk:
                        tile_mask.fill(COLOR_KEY)
                    else:
                        tile_mask.blit(tile.image, (0, 0))
            mask_array = pygame.surfarray.pixels3d(tile_mask)
            key_array = numpy.array(COLOR_KEY)
            new_key_array = numpy.array(new_color_key)
            for x in xrange(32):
                for y in xrange(32):
                    if numpy.equal(mask_array[x][y], key_array).all():
                        mask_array[x][y] = new_key_array
                    else:
                        mask_array[x][y] = key_array
            self.tile_masks[(x, y)] = tile_mask
        return self.tile_masks[(x, y)]

    def tiles_under(self, x, y):
        "Returns a list of tiles under the coordinates given, from bottom layer to top."
        tiles = []
        for layer in self.layers:
            tiles.append(layer.get_tile(x, y))
        return tiles


class Layer(object):
    "Stores a grid of tile objects and a surface which depicts them. Initialize with width and height in tiles."

    def __init__(self, width, height):
        super(Layer, self).__init__()
        self.width = width
        self.height = height
        self.tiles = {}

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

    def settle_tiles(self):
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
        for x in xrange(self.width):
            for y in xrange(self.height):
                if self.tiles.has_key((x, y)):
                    tile = self.tiles[(x, y)]
                    if tile:
                        tile.make_image()

    def fill(self, tile, *args):
        for x in xrange(self.width):
            for y in xrange(self.height):
                self.set_tile(x, y, tile, *args)
        self.settle_tiles()
        return self
        # ^ so we can initialize with layer = Layer(x, y).fill(tile)

    def set_row(self, y, tile, *args):
        for x in xrange(self.width):
            self.set_tile(x, y, tile, *args)
        self.settle_tiles()

    def set_column(self, x, tile, *args):
        for y in xrange(self.height):
            self.set_tile(x, y, tile, *args)
        self.settle_tiles()

    @property
    def surface(self):
        surface = pygame.Surface((self.width*TILE_SIZE, self.height*TILE_SIZE))
        for x in xrange(self.width):
            for y in xrange(self.height):
                tile = self.get_tile(x, y)
                if tile:
                    surface.blit(tile.image, (x*TILE_SIZE, y*TILE_SIZE))
        surface.set_colorkey(COLOR_KEY)
        return surface


class Tile(object):
    "Information about a specific tile."
    NORTH = 1
    SOUTH = 2
    EAST = 4
    WEST = 8

    def __init__(self, name, nowalk = False):
        super(Tile, self).__init__()
        self.name = name
        self.nowalk = nowalk
        self.image = None
        self.neighbors = {}

        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        cursor = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.spot = [tile_sheet.subsurface(cursor)]
        cursor.top += TILE_SIZE
        self.spot.append(tile_sheet.subsurface(cursor))
        cursor.left += 2 * TILE_SIZE
        self.anticorner = [tile_sheet.subsurface(cursor)]
        cursor.left -= 2 * TILE_SIZE
        cursor.top += TILE_SIZE
        self.corner = [tile_sheet.subsurface(cursor)]
        cursor.left += TILE_SIZE
        self.edge = [tile_sheet.subsurface(cursor)]
        cursor.top += TILE_SIZE
        self.center = [tile_sheet.subsurface(cursor)]
        cursor.top += 2 * TILE_SIZE
        self.center.append(tile_sheet.subsurface(cursor))
        cursor.left -= TILE_SIZE
        self.center.append(tile_sheet.subsurface(cursor))
        cursor.left += 2 * TILE_SIZE
        self.center.append(tile_sheet.subsurface(cursor))

    def set_neighbors(self, layer, x, y):
        # one is for iterating, one is for quick/readable accessing
        self.neighbors[self.NORTH] = self.north = layer.get_tile(x, y-1)
        self.neighbors[self.SOUTH] = self.south = layer.get_tile(x, y+1)
        self.neighbors[self.EAST] = self.east = layer.get_tile(x+1, y)
        self.neighbors[self.WEST] = self.west = layer.get_tile(x-1, y)

    def make_image(self):
        NORTH, SOUTH, EAST, WEST = (self.NORTH, self.SOUTH, self.EAST, self.WEST)
        ALL = NORTH + SOUTH + EAST + WEST
        image = None
        like_neighbors = 0
        for direction, neighbor in self.neighbors.items():
            if neighbor and neighbor.name == self.name:
                like_neighbors += direction

        spot = [0]
        center = [ALL]
        corner = [NORTH+WEST, SOUTH+WEST, SOUTH+EAST, NORTH+EAST]
        edge = [ALL-WEST, ALL-SOUTH, ALL-EAST, ALL-NORTH]
        if like_neighbors not in spot + center + corner + edge:
            # i.e. only one adjacent like tile, or two opposites
            # neither of which should occur in terrain generation
            like_neighbors = 0

        rotation = 0
        if like_neighbors in spot:
            image = random.choice(self.spot)
        elif like_neighbors in center:
            diagonals = [self.north.west, self.south.west, self.south.east, self.north.east]
            for index, neighbor in enumerate(diagonals):
                if neighbor and neighbor.name != self.name:
                    image = random.choice(self.anticorner)
                    rotation = 90 * index
                    break
                    # we're only accounting for one mismatched diagonal
                    # because any other possibility requires an illegal board
            else:
                # for-else: rarely useful, but when it is nothing else will do
                image = random.choice(self.center)
        else:
            if like_neighbors in corner:
                pattern_list = corner
            else:
                pattern_list = edge
            for index, neighbor_pattern in enumerate(pattern_list):
                if neighbor_pattern == like_neighbors:
                    image = random.choice(self.edge)

        if rotation:
            image = pygame.transform.rotate(image, rotation)
        self.image = image
