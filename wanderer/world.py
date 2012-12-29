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
        self.layers.append(Layer(self.width, self.height).fill(Ocean))
        self.layers.append(Layer(self.width-2, self.height-2, 1, 1).fill(Tile, "dirt"))
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
                tile.health -= 1
                if tile.health > 0:
                    tile.make_image(tile.neighbor_mask, force = True)
                else:
                    layer.set_tile(x, y, None)
                layer.dirty_tiles.append((x, y))
                return True
            else:
                # we hit a non-grass tile
                return False
        # went all the way through the tile stack
        return False

    def seed(self, px_x, px_y):
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        self.player_modified.set_tile(x, y, Tile, "grass")


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

    def set_tile(self, x, y, tile, *args):
        "Set the tile at x, y to the given Tile callable with the arguments supplied, or None"
        destroy_tile = False
        if tile:
            # setting a new tile, do the whole shebang
            new_tile = tile(*args)
        else:
            if self.get_tile(x, y):
                # unsetting a tile which did exist
                # clear its neighbors first
                new_tile = self.get_tile(x, y)
                new_tile.neighbor_mask = (0, 0, 0, 0)
                destroy_tile = True
            else:
                # unsetting a tile which didn't exist
                return

        # neighbors[translation] = (bits to change), (replacement bits)
        neighbors = {}
        neighbors[(0, -1)] = (2, 3), (0, 1)     # north
        neighbors[(0, 1)] = (0, 1), (2, 3)      # south
        neighbors[(-1, 0)] = (1, 3), (0, 2)     # west
        neighbors[(1, 0)] = (0, 2), (1, 3)      # east
        neighbors[(-1, -1)] = (3,), (0,)        # northwest
        neighbors[(1, -1)] = (2,), (1,)         # northeast
        neighbors[(-1, 1)] = (1,), (2,)         # southwest
        neighbors[(1, 1)] = (0,), (3,)          # southeast
        used_bits = [0, 0, 0, 0]

        def copy_bits(to_list, from_list):
            for index, old_bit in enumerate(to_list):
                new_bit = from_list[index]
                mask[old_bit] = new_tile.neighbor_mask[new_bit]
                used_bits[new_bit] = 1

        for transformation, bit_lists in neighbors.items():
            dx, dy = transformation
            neighbor = self.get_tile(x+dx, y+dy)
            if neighbor and neighbor.name == new_tile.name:
                self.dirty_tiles.append((x+dx, y+dy))
                mask = list(neighbor.neighbor_mask)
                copy_bits(*bit_lists)
                neighbor.make_image(tuple(mask))

        if destroy_tile:
            self.tiles.pop((x, y))
        else:
            new_tile.make_image(tuple(used_bits))
            # that is, set any bits which DIDN'T have neighbors to 0
            self.tiles[(x, y)] = new_tile
        self.dirty_tiles.append((x, y))

    def update(self):
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
        for x in xrange(self.left, self.left + self.width):
            for y in xrange(self.top, self.top + self.height):
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
        self.neighbor_mask = (1, 1, 1, 1)
        self.health = 3.0

        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        tile_locations = {}

        # center
        tile_locations[(1, 1, 1, 1)] = (1, 3)
        # center variants in descending density: (0-2, 5)

        # corner
        tile_locations[(0, 0, 0, 1)] = (0, 2)
        tile_locations[(0, 0, 1, 0)] = (2, 2)
        tile_locations[(0, 1, 0, 0)] = (0, 4)
        tile_locations[(1, 0, 0, 0)] = (2, 4)
        
        # anticorner
        tile_locations[(1, 1, 1, 0)] = (1, 0)
        tile_locations[(1, 1, 0, 1)] = (2, 0)
        tile_locations[(1, 0, 1, 1)] = (1, 1)
        tile_locations[(0, 1, 1, 1)] = (2, 1)

        # edge
        tile_locations[(0, 0, 1, 1)] = (1, 2)
        tile_locations[(1, 0, 1, 0)] = (2, 3)
        tile_locations[(0, 1, 0, 1)] = (0, 3)
        tile_locations[(1, 1, 0, 0)] = (1, 4)


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
        nw_se.blit(self.variants[(1, 0, 0, 0)], (0, 0))
        nw_se.blit(self.variants[(0, 0, 0, 1)], (0, 0))
        self.variants[(1, 0, 0, 1)] = nw_se

        ne_sw = pygame.Surface((TILE_SIZE, TILE_SIZE))
        ne_sw.set_colorkey(COLOR_KEY)
        ne_sw.blit(self.variants[(0, 1, 0, 0)], (0, 0))
        ne_sw.blit(self.variants[(0, 0, 1, 0)], (0, 0))
        self.variants[(0, 1, 1, 0)] = ne_sw

        self.spot = {}
        cursor.topleft = (0, 0)
        self.spot[2] = tile_sheet.subsurface(cursor)
        self.spot[2].set_colorkey((COLOR_KEY))
        cursor.topleft = (0, TILE_SIZE)
        self.spot[1] = tile_sheet.subsurface(cursor)
        self.spot[1].set_colorkey((COLOR_KEY))

        self.variants[(0, 0, 0, 0)] = self.spot[2]

    def __repr__(self):
        return '<Tile object "{}">'.format(self.name)

    def make_image(self, neighbor_mask, force = False):
        if not self.image:
            force = True

        if neighbor_mask == self.neighbor_mask and not force:
            return neighbor_mask

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

        self.image = self.variants[neighbor_mask]

        if self.name == "grass":
            font = pygame.font.Font(os.path.join(DATA_DIR, "04B_11__.TTF"), 8)
            line1 = font.render(str(neighbor_mask[0:2]), False, (100, 0, 0))
            line2 = font.render(str(neighbor_mask[2:4]), False, (100, 0, 0))
            self.image.blit(line1, (2, 2))
            self.image.blit(line2, (2, 18))

        self.neighbor_mask = neighbor_mask
        self.image.set_colorkey(COLOR_KEY)


class Ocean(Tile):
    "Water tiles that are only ever center tiles, to use as a backdrop."
    def __init__(self):
        super(Ocean, self).__init__("water", True)
        self.image = self.variants[(1, 1, 1, 1)]
        self.name = "ocean"

    def make_image(self, force = False):
        return (1, 1, 1, 1)
