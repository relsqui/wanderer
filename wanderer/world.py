import pygame, numpy, random, os, math
from pytmx import tmxloader
from wanderer.constants import *

TILE_SIZE = 32
COLOR_KEY = (0, 0, 0)


class Map(object):
    "Stores data about the map. Initialize with pixel width and height."

    def __init__(self, px_width, px_height):
        self.surface = pygame.Surface((px_width, px_height))
        self.surface.set_colorkey(COLOR_KEY)
        self.width = int(math.ceil(px_width/TILE_SIZE))
        self.height = int(math.ceil(px_height/TILE_SIZE))
        self.dirty = True

        self.layers = []
        self.layers.append(Layer("water", self.width, self.height).fill(Blocking, "water"))
        self.layers.append(Layer("dirt", self.width, self.height).set_rect((2, 2), (self.width-2, self.height-2), Tile, "dirt"))
        self.layers.append(Layer("dirt", self.width, self.height).set_rect((2, 2), (self.width-2, self.height-2), Hole))
        self.layers.append(Layer("grass", self.width, self.height).set_rect((4, 4), (self.width-4, self.height-4), Diggable, "grass"))

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
        # self.surface.blit(self.walk_mask.image, (0, 0))
        # ^ extremely useful for collision debugging

    def walkable_coords(self, px_x, px_y):
        "Returns True if the pixel at the coordinates given is walkable, False otherwise."
        pixel = self.walk_mask.image.get_at((px_x, px_y))[0:3]
        if pixel == COLOR_KEY:
            return True
        return False

    def walkable_mask(self, sprite):
        "Takes a sprite (with .image and .rect attributes), and returns True if all opaque parts of the sprite are over walkable map areas."
        if pygame.sprite.collide_mask(sprite, self.walk_mask):
            return False
        return True

    def get_tile_mask(self, x, y):
        "Returns a pygame.Surface whose colorkey transparency values match the walkable status of the terrain at the given tile location. Caches these masks."
        if not self.tile_masks.has_key((x, y)):
            if COLOR_KEY == (0, 0, 0):
                new_color_key = (255, 255, 255)
            else:
                new_color_key = (0, 0, 0)
            tile_mask = pygame.Surface((TILE_SIZE, TILE_SIZE))
            tile_mask.set_colorkey(COLOR_KEY)
            for tile in self.tiles_under(x, y):
                if tile and not tile.superwalkable:
                    if tile.walkable:
                        tile_mask.blit(tile.image, (0,0))
                    else:
                        tile_mask.fill(COLOR_KEY)
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

    @property
    def top_tile(self, x, y):
        "Returns the top tile which exists under the coordinates given, or None if there aren't any."
        for tile in reversed(self.tiles_under(x, y)):
            if tile:
                break
        return tile
        # if the loop runs out, we'll return None

    def dig(self, px_x, px_y):
        "Attempts to dig away a tile under the coordinates given."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        diggable = False
        for layer in reversed(self.layers):
            # not using tiles_under because we need the layer info
            tile = layer.get_tile(x, y)
            if tile:
                diggable = tile.dig()
                if diggable:
                    layer.dirty_tiles.append((x, y))
                break
        return diggable

    def seed(self, px_x, px_y):
        "Seeds some grass at the given coordinates."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        grass_layer = None
        for index, layer in enumerate(self.layers):
            if layer.name == "grass":
                grass_layer = index
                # not breaking, so we'll overwrite
                # if for some reason there's more than one
        if grass_layer:
            self.layers[index].set_tile(x, y, Diggable("grass"))


class Layer(object):
    "Stores a grid of tile objects and a surface which depicts them. Initialize with width and height in tiles."

    def __init__(self, name, width, height, top=0, left=0):
        super(Layer, self).__init__()
        self.name = name
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
        "Change x, y to the given tile or None (remove it)."
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
        # the elements of a tuple in bit_changes are:
        # - the translation needed to get to the neighbor tile
        # - the bitmask of the bit(s) facing that direction
        # - a function which shifts that mask
        #   to the mask for the opposite direction

        # cardinal directions
        bit_changes.append(((0, -1), 0b1100, lambda x: x >> 2))
        bit_changes.append(((0, 1), 0b0011, lambda x: x << 2))
        bit_changes.append(((-1, 0), 0b1010, lambda x: x >> 1))
        bit_changes.append(((1, 0), 0b0101, lambda x: x << 1))

        # diagonals
        bit_changes.append(((-1, -1), 0b1000, lambda x: x >> 3))
        bit_changes.append(((1, -1), 0b0100, lambda x: x >> 1))
        bit_changes.append(((-1, 1), 0b0010, lambda x: x << 1))
        bit_changes.append(((1, 1), 0b0001, lambda x: x << 3))

        for translation, mask, shift in bit_changes:
            dx, dy = translation
            if x+dx not in xrange(self.left, self.left+self.width)\
              or y+dy not in xrange(self.top, self.top+self.height):
                # the neighboring tile is off the edge of the layer
                continue

            neighbor = self.get_tile(x+dx, y+dy)
            if not neighbor:
                # there isn't already a tile there; start one
                neighbor = new_tile.get_another()
                neighbor.bitmask = 0
            old_mask = neighbor.bitmask

            # copy the neighbor-facing bits from the tile we're placing
            # into the new-tile-facing bits in the neighbor
            new_mask = shift(new_tile.bitmask & mask) | (old_mask & ~shift(mask))
            if new_mask != old_mask:
                neighbor.bitmask = new_mask
                if new_mask:
                    self.tiles[(x+dx, y+dy)] = neighbor
                else:
                    # that tile was depending on this edge
                    # and we removed it. destroy the tile, if it exists
                    if self.get_tile(x+dx, y+dy):
                        self.tiles.pop((x+dx, y+dy))
                self.dirty_tiles.append((x+dx, y+dy))

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
                if tile.health <= 0:
                    self.set_tile(x, y, None)
                elif tile.dirty:
                    tile.dirty = False
                    self.set_tile(x, y, tile)
                else:
                    self.surface.blit(tile.image, (px_x, px_y))
        self.dirty_tiles = []
        return True

    def fill(self, tile_type, *args):
        "Fill the layer with instances of a Tile callable, or None (clear it)."
        self.set_rect((self.left, self.top), (self.left+self.width, self.top+self.height), tile_type, *args)
        return self
        # ^ so we can initialize with layer = Layer(x, y).fill(tile)

    def set_row(self, y, tile_type, *args):
        "Fill a row with instances of a Tile callable, or None (clear it)."
        for x in xrange(self.width):
            if tile_type:
                tile = tile_type(*args)
            else:
                tile = None
            self.set_tile(x, y, tile)
        return self

    def set_column(self, x, tile_type, *args):
        "Fill a column with instances of a Tile callable, or None (clear it)."
        for y in xrange(self.height):
            if tile_type:
                tile = tile_type(*args)
            else:
                tile = None
            self.set_tile(x, y, tile)
        return self

    def set_rect(self, topleft, bottomright, tile_type, *args):
        "Fill a rectangle with instances of a Tile callable, or None (clear it)."
        left, top = topleft
        right, bottom = bottomright
        for x in xrange(left, right):
            for y in xrange(top, bottom):
                if tile_type:
                    tile = tile_type(*args)
                else:
                    tile = None
                self.set_tile(x, y, tile)
        return self


class Tile(object):
    "Generic class for map tile information. Takes a string name which should match the base name of a file in the tile images directory."

    def __init__(self, name):
        super(Tile, self).__init__()
        self.name = name
        self.walkable = True
        self.superwalkable = False
        # superwalkable skips collision checking entirely
        # instead of using a mask for this tile.
        # useful for invisible tiles, which otherwise block
        # even when they're set walkable (because they look like holes)
        self.bitmask = 0b1111
        self.health = 3.0
        self.dirty = True
        # this is a little different from a layer or map being dirty.
        # if a tile is dirty, the layer will set_tile it again
        # (i.e. recalculate its neighbors' bitmasks to match)

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

        blank = pygame.Surface((TILE_SIZE, TILE_SIZE))
        blank.fill(COLOR_KEY)
        self.variants[0] = blank

    def get_another(self):
        "Return another instance of this class (not a full copy)."
        return Tile(self.name)

    def dig(self):
        "Defines dig behavior. To make a diggable tile class, override and return True."
        return False

    @property
    def image(self):
        "Returns the tile's current image, defined by its bitmask and health."
        image = self.variants[self.bitmask]
        """
        font = pygame.font.Font(os.path.join(DATA_DIR, "04B_11__.TTF"), 8)
        string_mask = "{:04b}".format(self.bitmask)
        line1 = font.render(string_mask[:2], False, (100, 0, 0))
        line2 = font.render(string_mask[2:], False, (100, 0, 0))
        image.blit(line1, (14, 6))
        image.blit(line2, (14, 16))
        """
        return image


class Diggable(Tile):
    "A Tile which deteriorates when dug (same arguments as Tile)."
    def get_another(self):
        return Diggable(self.name)

    def dig(self):
        self.health -= 1
        if self.health <= 2:
            self.bitmask = 0
            self.dirty = True
        return True

    @property
    def image(self):
        if self.bitmask == 0:
            image = self.spot[math.ceil(self.health)]
        else:
            image = super(Diggable, self).image
        return image


class Blocking(Tile):
    "A Tile which can't be walked over (same arguments as Tile)."
    def __init__(self, name):
        super(Blocking, self).__init__(name)
        self.walkable = False

    def get_another(self):
        return Blocking(self.name)


class Hole(Tile):
    "A Tile which starts invisible and becomes a hole when dug. No arguments."
    def __init__(self):
        super(Hole, self).__init__("hole")
        self.bitmask = 0
        self.health = 0.5
        # not 0 so we don't get erased
        self.superwalkable = True

    def get_another(self):
        return Hole()

    def dig(self):
        if not self.bitmask:
            # if we have a bitmask, we've already been dug
            self.health += 1
            # we gain health when dug, because we're a hole
            if self.health >= 3:
                self.bitmask = 0b1111
            self.dirty = True
            return True
        return False

    @property
    def image(self):
        if not self.bitmask and self.health > 1 and self.health < 3:
            return self.spot[math.floor(self.health)]
        else:
            return super(Hole, self).image
