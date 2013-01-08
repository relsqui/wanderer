import pygame, numpy, random, os, math
from pytmx import tmxloader
from wanderer.constants import *

TILE_SIZE = 32
COLOR_KEY = (0, 0, 0)


class Map(object):
    "Stores data about the map. Initialize with pygame.Rect defining size/offset in tiles."

    def __init__(self, rect, tiers=None):
        self.rect = rect
        self.left, self.top, self.width, self.height = self.rect
        px_width, px_height = (self.width*TILE_SIZE, self.height*TILE_SIZE)
        self.surface = pygame.Surface((px_width, px_height))
        self.surface.set_colorkey(COLOR_KEY)
        self.dirty = True

        if tiers:
            self.tiers = tiers
        else:
            self.tiers = [Tier(self.rect)]

        self.tile_masks = {}
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((px_width, px_height))
        self.walk_mask.image.set_colorkey(COLOR_KEY)
        self.walk_mask.rect = self.surface.get_rect()

        self.update()

    def to_json(self):
        return {'rect': tuple(self.rect), 'tiers': [t.to_json() for t in self.tiers]}

    @classmethod
    def from_json(self, json_map):
        return Map(pygame.Rect(*json_map["rect"]), [Tier.from_json(t) for t in json_map["tiers"]])

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
                if tile and not tile.flags.get("superwalkable"):
                    if tile.flags.get("walkable"):
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

    def top_tier(self, x, y):
        for tier in reversed(self.tiers):
            if tier.exists_at(x, y):
                return tier
        return None

    def tiles_under(self, x, y):
        "Returns a list of tiles on the top tier under the coordinates given, from bottom layer to top."
        tiles = []
        tier = self.top_tier(x, y)
        if tier:
            for name in tier.layer_names:
                tile = tier.layers[name].get_tile(x, y)
                tiles.append(tile)
        return tiles

    def top_tile(self, x, y):
        "Returns the top tile which exists under the coordinates given, or None if there aren't any."
        tile = None
        for tile in reversed(self.tiles_under(x, y)):
            if tile:
                break
        return tile

    def place(self, px_x, px_y, item):
        "Attempt to place the given item on the top tile at the given coordinates."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        return item.alter_tiles(self.top_tier(x, y), x, y)

    def pick_up(self, px_x, px_y):
        "Attempt to pick up the top tile at the given coordinates."
        x, y = (px_x/TILE_SIZE, px_y/TILE_SIZE)
        tile = self.top_tile(x, y)
        if tile:
            return tile.pick_up()
        return None


class Tier(object):
    "Stores information about a height level on the map. Initialize with width and height in tiles."

    def __init__(self, rect, layers = None):
        super(Tier, self).__init__()
        self.rect = rect
        self.left, self.top, self.width, self.height = self.rect
        px_width, px_height = (self.width*TILE_SIZE, self.height*TILE_SIZE)
        self.surface = pygame.Surface((px_width, px_height))
        self.dirty = True

        # the name list defines the order of the layers, bottom-up
        self.layer_names = ["dirt", "grass", "water"]
        if layers is None:
            layers = {}
            layers["dirt"] = Layer(self.rect).fill(DirtTile)
            layers["grass"] = Layer(self.rect).set_rect((2, 2), (self.width-2, self.height-2), GrassTile)
            layers["water"] = Layer(self.rect).set_rect((4, 4), (self.width-4, self.height-4), WaterTile)
        self.layers = layers
        for name in self.layer_names:
            if not self.layers.get(name):
                self.layers[name] = Layer(self.rect)

    def __repr__(self):
        layers = []
        for name in self.layer_names:
            layers.append("{}({})".format(name, len(self.layers[name].tiles)))
        layer_text = ",".join(layers)
        return "<Tier:{}>".format(layer_text)

    def to_json(self):
        layers = {}
        for name, layer in self.layers.items():
            layers[name] = layer.to_json()
        return {'rect': tuple(self.rect), 'layers': layers}

    @classmethod
    def from_json(self, json_tier):
        layers = {}
        for name, layer in json_tier["layers"].items():
            layers[name] = Layer.from_json(layer)
        return Tier(pygame.Rect(*json_tier["rect"]), layers)


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

    def __init__(self, rect, tiles = None):
        super(Layer, self).__init__()
        self.rect = rect
        self.left, self.top, self.width, self.height = self.rect
        if tiles is None:
            tiles = {}
        self.tiles = tiles
        px_size = (self.width*TILE_SIZE, self.height*TILE_SIZE)
        px_topleft = (self.left*TILE_SIZE, self.top*TILE_SIZE)
        self.surface = pygame.Surface(px_size)
        self.surface.set_colorkey(COLOR_KEY)
        self.dirty = False

    def to_json(self):
        tiles = []
        for location, tile in self.tiles.items():
            x, y = location
            tiles.append((x, y, tile.to_json()))
        return {'rect': tuple(self.rect), 'tiles': tiles}

    @classmethod
    def from_json(self, json_layer):
        tiles = {}
        for tile_tuple in json_layer["tiles"]:
            x, y, tile_json = tile_tuple
            tile_type = tile_json["type"]
            tiles[(int(x), int(y))] = globals()[tile_type].from_json(tile_json)
        return Layer(pygame.Rect(*json_layer["rect"]), tiles)

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
                neighbor = new_tile.get_another(bitmask = 0)
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
            if tile.kill and not tile.flags.get("immortal"):
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

    def __init__(self, name, bitmask = 0b1111, health = None, flags = None):
        super(Tile, self).__init__()
        self.name = name
        self.bitmask = bitmask
        self.health_min = 0
        self.health_max = 7
        if health is None:
            self.health = random.randrange(3, self.health_max)
        else:
            self.health = health
        if flags is None:
            flags = {"walkable": True, "superwalkable": False, "immortal": False}
            # walkable: opaque parts of tile can be walked on
            # superwalkable: whole tile can be walked on, regardless of opacity
            # immortal: don't kill the tile while this flags is set
        self.flags = flags
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

    def __repr__(self):
        return '<{} tile ("{}")>'.format(self.__class__.__name__, self.name)

    def to_json(self):
        return {'type': self.__class__.__name__, 'name': self.name, 'bitmask': self.bitmask, 'health': self.health, 'flags': self.flags}

    @classmethod
    def from_json(self, tile_json):
        tile_type = tile_json.pop("type")
        return globals()[tile_type](**tile_json)

    def get_another(self, **kwargs):
        "Return another instance of this class (not a full copy)."
        kwargs["name"] = self.name
        return self.__class__(**kwargs)

    def pick_up(self):
        "Returns an object to be given to the player when this tile is picked up."
        return None

    def empty(self):
        "Clear bitmask and return self; used for starting new tiles when placed."
        self.bitmask = 0
        return self

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

            if not self.health and not self.flags.get("immortal"):
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


class Item(object):
    "An item which can be on the map or in an agent's inventory. Initialize with name and, optionally, associated tile type and/or layer name."

    def __init__(self, name, tile = None, layer = None):
        self.name = name
        self.tile = tile
        if layer is None:
            layer = self.name
        self.layer = layer

    def __repr__(self):
        return '<Item "{}">'.format(self.tile, self.name)

    def to_json(self):
        return {'name': self.name, 'tile': self.tile, 'layer': self.layer}

    @classmethod
    def from_json(self, json_item):
        return Item(json_item["name"], json_item["tile"], json_item["layer"])

    def tile_available(self, tier, x, y, tile_type = None):
        if tile_type is None:
            tile_type = self.tile
        for layer_name in reversed(tier.layer_names):
            tile = tier.layers[layer_name].get_tile(x, y)
            if tile:
                break
        if tile.__class__ == tile_type:
            return tile
        return None

    def layer_available(self, tier, x, y, layer_name = None):
        if layer_name is None:
            layer_name = self.layer
        for name in reversed(tier.layer_names):
            layer = tier.layers[name]
            if name == layer_name:
                return layer
            if layer.get_tile(x, y):
                break
        return None

    def alter_tiles(self, tier, x, y):
        "What should the item do when placed on the map? Takes an ordered list of layer names and a dict of layer names to tiles, which should be equal length."
        pass


class DiggableTile(Tile):
    "A Tile which deteriorates when dug (same arguments as Tile)."
    def item(self):
        return DiggableItem(self.name, self.__class__)

    def pick_up(self):
        "When picked up, deteriorate and return an item."
        if self.update(health=self.health-1):
            return self.item()
        else:
            return None


class DiggableItem(Item):
    def alter_tiles(self, tier, x, y):
        "Attempt to update the top relevant tile, or place one."
        tile = self.tile_available(tier, x, y)
        layer = self.layer_available(tier, x, y)
        if layer and not tile:
            layer = tier.layers[self.layer]
            layer.set_tile(x, y, self.tile().empty())
            tile = layer.get_tile(x, y)
        if tile:
            return tile.update(health = tile.health + 1)
        return False


class GrassTile(DiggableTile):
    def __init__(self, **kwargs):
        kwargs["name"] = "grass"
        super(GrassTile, self).__init__(**kwargs)


class WaterTile(DiggableTile):
    def __init__(self, **kwargs):
        kwargs["name"] = "water"
        super(WaterTile, self).__init__(**kwargs)

    def item(self):
        return WaterItem()


class WaterItem(DiggableItem):
    def __init__(self):
        super(WaterItem, self).__init__("water", WaterTile, "water")

    def alter_tiles(self, tier, x, y):
        if super(WaterItem, self).alter_tiles(tier, x, y):
            # we successfully placed or incremented a water tile
            water = tier.layers[self.layer].get_tile(x, y)
            if water.bitmask == 0b1111:
                # kill grass if there is any
                if "grass" in tier.layers.keys():
                    tier.layers["grass"].set_tile(x, y, None)
            return True
        return False


class BlockingTile(Tile):
    "A Tile which can't be walked over (same arguments as Tile)."
    def __init__(self, **kwargs):
        super(BlockingTile, self).__init__(**kwargs)
        self.flags["walkable"] = False


class DirtTile(Tile):
    def __init__(self, **kwargs):
        kwargs["name"] = "dirt"
        super(DirtTile, self).__init__(**kwargs)
        self.health_variants.pop(6)
        # this one is too conspicuous
        self.health_max -= 1
        # because we have one fewer tile for it

    def item(self):
        return DirtItem()

    def pick_up(self):
        # this is temporary, for testing with water filling
        return self.item()


class DirtItem(Item):
    def __init__(self):
        super(DirtItem, self).__init__("dirt", DirtTile, "dirt")

    def alter_tiles(self, tier, x, y):
        tile = self.tile_available(tier, x, y, WaterTile)
        layer = self.layer_available(tier, x, y, "water")
        if tile and layer:
            layer.set_tile(x, y, None)
            return True
        return False
