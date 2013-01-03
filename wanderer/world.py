import pygame, numpy, random, os, math
from pytmx import tmxloader
from wanderer.constants import *

TILE_SIZE = 32
COLOR_KEY = (0, 0, 0)


class Map(object):
    "Stores data about the map. Initialize with pixel width and height."

    def __init__(self, px_width, px_height, left=0, top=0):
        self.surface = pygame.Surface((px_width, px_height))
        self.surface.set_colorkey(COLOR_KEY)
        self.width = int(math.ceil(px_width/TILE_SIZE))
        self.height = int(math.ceil(px_height/TILE_SIZE))
        self.left = 0
        self.top = 0
        self.dirty = True

        self.tiers = [Tier(self.height, self.width, self.left, self.top)]

        self.tile_masks = {}
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((px_width, px_height))
        self.walk_mask.image.set_colorkey(COLOR_KEY)
        self.walk_mask.rect = self.surface.get_rect()

        self.update()

    def update(self):
        for tier in self.tiers:
            tier.update()
            if tier.dirty:
                self.dirty = True
                tier.dirty = False
            self.surface.blit(tier.surface, (0,0))
            # blit all of them, in case a higher tier updated to transparent
        for x in xrange(self.width):
            for y in xrange(self.height):
                mask = self.get_tile_mask(x, y)
                self.walk_mask.image.blit(mask, (x*TILE_SIZE, y*TILE_SIZE))
        # self.walk_mask.image.set_alpha(100)
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
        "Returns a list of tiles on the top tier under the coordinates given, from bottom layer to top."
        tiles = []
        top_tier = None
        for tier in self.tiers:
            if tier.exists_at(x, y):
                top_tier = tier
        if top_tier:
            for name in top_tier.layer_names:
                tile = top_tier.layers[name].get_tile(x, y)
                tiles.append(tile)
        return tiles

    def top_tile(self, x, y):
        "Returns the top tile which exists under the coordinates given, or None if there aren't any."
        for tile in reversed(self.tiles_under(x, y)):
            if tile:
                break
        return tile
        # if the loop runs out, we'll return None

    def place(self, px_x, px_y, item):
        "Attempt to place the given item on the top tile at the given coordinates."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        tile = self.top_tile(x, y)
        if tile:
            return tile.place(item)
        return False

    def pick_up(self, px_x, px_y):
        "Attempt to pick up the top tile at the given coordinates."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        tile = self.top_tile(x, y)
        if tile:
            return tile.pick_up()
        return None


class Tier(object):
    "Stores information about a height level on the map. Initialize with width and height in tiles."

    def __init__(self, width, height, left, top):
        super(Tier, self).__init__()
        self.width = width
        self.height = height
        self.top = top
        self.left = left
        px_width, px_height = (self.width*TILE_SIZE, self.height*TILE_SIZE)
        self.surface = pygame.Surface((px_width, px_height))
        self.dirty = True

        self.layer_names = ["dirt", "hole", "grass", "water", "items"]
        # the name list also provides the order
        self.layers = {}
        for name in self.layer_names:
            self.layers[name] = Layer(self.width, self.height, self.left, self.top)
        self.layers["dirt"].fill(Dirt)
        self.layers["hole"].fill(Hole)
        self.layers["grass"].set_rect((2, 2), (self.width-2, self.height-2), Diggable, "grass")
        self.layers["water"].set_rect((5, 5), (self.width-5, self.width-5), Diggable, "water")

    def update(self):
        "Redraw the tier surface."
        for name in self.layer_names:
            layer = self.layers[name]
            layer.update()
            if layer.dirty:
                self.dirty = True
                layer.dirty = False
            self.surface.blit(layer.surface, layer.rect)

    def exists_at(self, x, y):
        "Return True if the tier has contents at the given coordinates."
        exists = False
        for layer in self.layers.values():
            if layer.get_tile(x, y):
                exists = True
        return exists


class Layer(object):
    "Stores a grid of tile objects and a surface which depicts them. Initialize with width and height in tiles."

    def __init__(self, width, height, left, top):
        super(Layer, self).__init__()
        self.width = width
        self.height = height
        self.top = top
        self.left = left
        self.tiles = {}
        px_size = (self.width*TILE_SIZE, self.height*TILE_SIZE)
        px_topleft = (self.left*TILE_SIZE, self.top*TILE_SIZE)
        self.rect = pygame.Rect(px_topleft, px_size)
        self.surface = pygame.Surface(px_size)
        self.surface.set_colorkey(COLOR_KEY)
        self.dirty = False
        # unlike Map and Tile, a fresh Layer is actually empty

    def get_tile(self, x, y):
        "Return the tile at position x, y or None if there is none."
        if self.tiles.has_key((x, y)):
            return self.tiles[(x, y)]
        return None

    def set_tile(self, x, y, tile):
        "Change x, y to the given tile or None (remove it)."
        if tile:
            new_tile = tile
            self.tiles[(x, y)] = new_tile
        else:
            if self.get_tile(x, y):
                # unsetting a tile, clear its neighbors
                new_tile = self.get_tile(x, y)
                new_tile.bitmask = 0
                new_tile.kill = True
            else:
                # unsetting a tile which didn't exist
                return
        self.dirty = True

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
            if x+dx < self.left or x+dx > self.left+self.width\
             or y+dy < self.top or y+dy > self.top+self.height:
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
            # update the tile, remove if it disappeared
            if neighbor.update(bitmask = new_mask) and not neighbor.bitmask:
                neighbor.update(health = 0)
            else:
                # place our maybe-newly-created tile
                self.tiles[(x+dx, y+dy)] = neighbor

    def update(self):
        "Redraw tiles at any changed locations."
        blank = pygame.Surface((TILE_SIZE, TILE_SIZE))
        blank.fill(COLOR_KEY)
        for location, tile in self.tiles.items():
            if not (tile.dirty or tile.kill):
                continue
            self.dirty = True
            x, y = location
            px_x = (x - self.left) * TILE_SIZE
            px_y = (y - self.top) * TILE_SIZE
            self.surface.blit(blank, (px_x, px_y))
            if tile.kill and not tile.immortal:
                self.tiles.pop((x, y))
            else:
                # update its neighbors
                self.set_tile(x, y, tile)
                self.surface.blit(tile.image, (px_x, px_y))
                tile.dirty = False

    def fill(self, tile_type, *args):
        "Fill the layer with instances of a Tile callable, or None (clear it)."
        self.set_rect((self.left, self.top), (self.left+self.width, self.top+self.height), tile_type, *args)
        return self

    def set_row(self, y, tile_type, *args):
        "Fill a row with instances of a Tile callable, or None (clear it)."
        tile = None
        for x in xrange(self.width):
            if tile_type:
                tile = tile_type(*args)
            self.set_tile(x, y, tile)
        return self

    def set_column(self, x, tile_type, *args):
        "Fill a column with instances of a Tile callable, or None (clear it)."
        tile = None
        for y in xrange(self.height):
            if tile_type:
                tile = tile_type(*args)
            self.set_tile(x, y, tile)
        return self

    def set_rect(self, topleft, bottomright, tile_type, *args):
        "Fill a rectangle with instances of a Tile callable, or None (clear it)."
        left, top = topleft
        right, bottom = bottomright
        tile = None
        for x in xrange(left, right):
            for y in xrange(top, bottom):
                if tile_type:
                    tile = tile_type(*args)
                self.set_tile(x, y, tile)
        return self


class Tile(object):
    "Generic class for map tile information. Takes a string name which should match the base name of a file in the tile images directory."

    def __init__(self, name):
        super(Tile, self).__init__()
        self.name = name
        self.bitmask = 0b1111
        self.health_min = 0
        self.health_max = 7
        self.health = random.randrange(3, self.health_max)
        self.walkable = True
        # if True, the opaque parts of the tile are walkable
        self.superwalkable = False
        # if True, the whole tile is walkable regardless of opacity
        self.immortal = False
        # if True, don't remove this tile when you otherwise would
        self.kill = False
        # if True, remove this tile from its layer
        self.dirty = True
        # if True, redraw this tile onto its layer

        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        tile_locations = {}

        # center
        tile_locations[0b1111] = (1, 3)

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

        # double corners
        nw_se = pygame.Surface((TILE_SIZE, TILE_SIZE))
        nw_se.blit(self.variants[0b1000], (0, 0))
        nw_se.blit(self.variants[0b0001], (0, 0))
        self.variants[0b1001] = nw_se

        ne_sw = pygame.Surface((TILE_SIZE, TILE_SIZE))
        ne_sw.blit(self.variants[0b0100], (0, 0))
        ne_sw.blit(self.variants[0b0010], (0, 0))
        self.variants[0b0110] = ne_sw

        blank = pygame.Surface((TILE_SIZE, TILE_SIZE))
        blank.fill(COLOR_KEY)
        self.variants[0] = blank

        self.health_variants = []
        self.health_variants.append(blank)
        # these are small, non-connecting (0b0000)
        cursor.topleft = (0, TILE_SIZE)
        self.health_variants.append(tile_sheet.subsurface(cursor))
        cursor.topleft = (0, 0)
        self.health_variants.append(tile_sheet.subsurface(cursor))

        # these are dense and fully connecting (0b1111)
        self.health_variants.append(self.variants[0b1111])
        cursor.topleft = (2*TILE_SIZE, 5*TILE_SIZE)
        self.health_variants.append(tile_sheet.subsurface(cursor))
        cursor.topleft = (TILE_SIZE, 5*TILE_SIZE)
        self.health_variants.append(tile_sheet.subsurface(cursor))
        cursor.topleft = (0, 5*TILE_SIZE)
        self.health_variants.append(tile_sheet.subsurface(cursor))

    def get_another(self):
        "Return another instance of this class (not a full copy)."
        return Tile(self.name)

    def pick_up(self):
        "Returns an object to be given to the player when this tile is picked up."
        return None

    def place(self, item):
        "Defines behavior when an object is placed here; returns True if the placement was successful, False otherwise."
        return False

    def update(self, bitmask = None, health = None):
        "Sets tile data which affect rendering. Returns True if a net change was made, False otherwise."
        old_mask, old_health = (self.bitmask, self.health)

        if bitmask is not None:
            self.bitmask = bitmask
            if self.bitmask == 0b1111:
                self.health = max(self.health, 3)
            else:
                self.health = min(self.health, 2)

        if health is not None:
            self.health = health
            if self.health < self.health_min:
                self.health = self.health_min
            elif self.health > self.health_max:
                self.health = self.health_max

            if self.health < 3 and self.bitmask:
                self.bitmask = 0
            elif self.health >= 3:
                self.bitmask = 0b1111

            if not self.health and not self.immortal:
                self.kill = True

        if self.bitmask == old_mask and self.health == old_health:
            return False
        else:
            self.dirty = True
            return True

    @property
    def image(self):
        "Returns the tile's current image, defined by its bitmask and health."
        font = pygame.font.Font(os.path.join(DATA_DIR, "fonts", "04B_11__.TTF"), 8)
        color = (250, 200, 200)

        # these blit useful debug data on top of tiles

        def debug_bitmask(name=None):
            if not name or self.name == name:
                string_mask = "{:04b}".format(self.bitmask)
                line1 = font.render(string_mask[:2], False, color)
                line2 = font.render(string_mask[2:], False, color)
                image.blit(line1, (14, 6))
                image.blit(line2, (14, 16))

        def debug_health(name=None):
            if not name or self.name == name:
                health_text = font.render(str(self.health), False, color)
                index_text = font.render(str(health_index), False, color)
                image.blit(health_text, (14, 6))
                image.blit(index_text, (14, 16))

        if self.bitmask == 0b1111 or self.bitmask == 0b0000:
            health_index = min(int(math.floor(self.health)), len(self.health_variants)-1)
            image = self.health_variants[health_index]
        else:
            image = self.variants[self.bitmask]
            health_index = "-" # for debug printing

        # put debug calls here

        return image


class Diggable(Tile):
    "A Tile which deteriorates when dug (same arguments as Tile)."

    def get_another(self):
        return Diggable(self.name)

    def pick_up(self):
        "When picked up, deteriorate and return another instance of self."
        if self.update(health=self.health-1):
            return self.get_another()
        else:
            return None

    def place(self, item):
        "When another of the same tile is placed here, get healthier."
        if item.name == self.name:
            return self.update(health=self.health+1)
        return False


class Blocking(Tile):
    "A Tile which can't be walked over (same arguments as Tile)."
    def __init__(self, name):
        super(Blocking, self).__init__(name)
        self.walkable = False

    def get_another(self):
        return Blocking(self.name)


class Dirt(Tile):
    def __init__(self):
        super(Dirt, self).__init__("dirt")
        self.health_variants.pop(6)
        # this one is too conspicuous
        self.health_max = 6
        # because we have one fewer tile for it

    def get_another(self):
        return Dirt()


class Hole(Tile):
    "A Tile which starts invisible and becomes a hole when dug. No arguments."
    def __init__(self):
        super(Hole, self).__init__("hole")
        self.bitmask = 0
        self.health = 0
        self.health_max = 3
        self.superwalkable = True
        self.immortal = True

    def get_another(self):
        return Hole()

    def pick_up(self):
        "When the hole is 'picked up,' it gets deeper and yields dirt."
        if self.bitmask == 0 or self.bitmask == 0b1111:
            new_health = self.health + 1
        else:
            # we're already half-dug, skip the incremental
            new_health = self.health_max
        if self.update(health = new_health):
            return Dirt()
        else:
            return False

    def place(self, item):
        "When dirt is placed in the hole, it goes away."
        if item.name == "dirt":
            return self.update(health = self.health_min)
        return False
