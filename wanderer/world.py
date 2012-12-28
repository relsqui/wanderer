import pygame, numpy, random, os
from pytmx import tmxloader
from wanderer.constants import *


class Map(object):
    "Stores data about the map. Initialize with the location of a map to load."

    def __init__(self):
        self.data = tmxloader.load_pygame(os.path.join(DATA_DIR, "maps", "island.tmx"))
        color_key = self.data.tilesets[0].trans
        self.color_key = tuple(ord(c) for c in color_key.decode('hex'))
        pxwidth, pxheight = self.tile2px(self.data.width, self.data.height)
        self.surface = pygame.Surface((pxwidth, pxheight))
        self.walk_mask = pygame.sprite.Sprite()
        self.walk_mask.image = pygame.Surface((pxwidth, pxheight))
        self.walk_mask.image.set_colorkey(self.color_key)
        self.walk_mask.rect = self.walk_mask.image.get_rect()
        self.tile_masks = {}
        for l in xrange(len(self.data.tilelayers)):
            for y in xrange(self.data.height):
                for x in xrange(self.data.width):
                    tile = self.data.getTileImage(x, y, l)
                    if tile:
                        self.surface.blit(tile, self.tile2px(x, y))
        print "   (Initializing walk mask, this might take a sec ...)"
        for x in xrange(self.data.width):
            for y in xrange(self.data.height):
                px_x = x * self.data.tilewidth
                px_y = y * self.data.tileheight
                mask = self.get_tile_mask(px_x, px_y)
                self.walk_mask.image.blit(mask, (px_x, px_y))

    def walkable_rect(self, position):
        "Takes a pygame.Rect, returns True iff all corners are on walkable points."
        for corner in (position.topleft, position.bottomleft, position.topright, position.bottomright):
            if not self.walkable_coords(*corner):
                return False
        return True

    def walkable_coords(self, x, y):
        "Returns True if the pixel at the coordinates given is walkable, False otherwise."
        tile, remainder = self.px2tile_remainder(x, y)
        mask = self.get_tile_mask(x, y)
        pixel = mask.get_at(remainder)[0:3]
        if pixel == self.color_key:
            return True
        return False

    def walkable_mask(self, sprite):
        "Takes a sprite (with .image and .rect attributes), and returns True unless any non-alpha part of that sprite is on top of any visible part of a nowalk tile."
        """
        # This is from when I was generating tile masks on the fly.
        # Saved so I can reuse the code when I'm generating new terrain.
        tw, th = (self.data.tilewidth, self.data.tileheight)
        corners = []
        corners.append(sprite.rect.topleft)
        corners.append((corners[0][0] + tw, corners[0][1]))
        corners.append((corners[0][0], corners[0][1] + th))
        corners.append((corners[0][0] + tw, corners[0][1] + th))
        # this instead of just using coords for each corner because
        # the sprite is taller than the tiles--top left and bottom left
        # tile position aren't necessarily vertically adjacent
        masks = []
        for corner in corners:
            masks.append(self.get_tile_mask(*corner))
        terrain = pygame.Surface((tw * 2, th * 2))
        terrain.set_colorkey(self.color_key)
        terrain.blit(masks[0], (0, 0))
        terrain.blit(masks[1], (tw, 0))
        terrain.blit(masks[2], (0, th))
        terrain.blit(masks[3], (tw, th))
        terrain_sprite = pygame.sprite.Sprite()
        terrain_sprite.image = terrain
        terrain_sprite.rect = terrain.get_rect()
        tile, remainder = self.px2tile_remainder(*sprite.rect.topleft)
        terrain_sprite.rect.topleft = (sprite.rect.left - remainder[0], sprite.rect.top - remainder[1])
        """
        if pygame.sprite.collide_mask(sprite, self.walk_mask):
            return False
        return True

    def get_tile_mask(self, px_x, px_y):
        "Returns a pygame.Surface whose colorkey transparency values match the walkable status of the terrain at the given tile location. Caches these masks."
        x, y = self.px2tile(px_x, px_y)
        if self.tile_masks.has_key((x, y)):
            tile_mask = self.tile_masks[(x, y)]
        else:
            color_key = self.color_key
            if color_key == (0, 0, 0):
                new_color_key = (255, 255, 255)
            else:
                new_color_key = (0, 0, 0)
            tile_mask = pygame.Surface((self.data.tilewidth, self.data.tileheight))
            for tile in self.tiles_under(px_x, px_y):
                if tile:
                    if self.tile_is_nowalk(tile):
                        tile_mask.fill(color_key)
                    else:
                        tile_mask.blit(self.data.images[tile], (0, 0))
            mask_array = pygame.surfarray.pixels3d(tile_mask)
            key_array = numpy.array(color_key)
            new_key_array = numpy.array(new_color_key)
            for x in xrange(32):
                for y in xrange(32):
                    if numpy.equal(mask_array[x][y], key_array).all():
                        mask_array[x][y] = new_key_array
                    else:
                        mask_array[x][y] = key_array
            self.tile_masks[(x, y)] = tile_mask
        return tile_mask

    def tile_is_nowalk(self, gid):
        "Returns True if the given tile GID is set nowalk, False otherwise."
        nowalk = False
        try:
            properties = self.data.tile_properties[gid]
            if properties["nowalk"]:
                nowalk = True
        except KeyError:
            # no properties for that tile
            pass
        return nowalk

    def tiles_under(self, x, y):
        "Returns a list of tiles under the coordinates given, from bottom layer to top."
        x, y = self.px2tile(x, y)
        tiles = []
        for layer in self.data.tilelayers:
            tiles.append(layer.data[y][x])
        return tiles

    def px2tile(self, x, y):
        "Converts an x, y position from real (pixel) position to tile location, losing precision."
        return (x / self.data.tilewidth, y / self.data.tileheight)

    def px2tile_remainder(self, px_x, px_y):
        "Converts an x, y real (pixel) position to tile location and pixel location within the tile."
        x = px_x / self.data.tilewidth
        y = px_y / self.data.tileheight
        rem_x = px_x - (x * self.data.tilewidth)
        rem_y = px_y - (y * self.data.tileheight)
        return ((x, y), (rem_x, rem_y))

    def tile2px(self, x, y):
        "Converts an x, y position from tile location to real (pixel) position of the tile's (0, 0)."
        return (x * self.data.tilewidth, y * self.data.tileheight)


class Layer(object):
    def __init__(self, width, height):
        super(Layer, self).__init__()
        self.width = width
        self.height = height
        self.tiles = {}

    def get_tile(self, x, y):
        if self.tiles.has_key((x, y)):
            return self.tiles[(x, y)]
        return None

    def set_tile(self, tile, x, y):
        self.tiles[(x, y)] = tile

    def fill(self, tile):
        for x in xrange(self.width):
            for y in xrange(self.height):
                self.tiles[(x, y)] = tile


class Tile(object):
    "Information about a specific tile."
    NORTH = 1
    SOUTH = 2
    EAST = 4
    WEST = 8
    TSIZE = 32  # pixels per side per tile

    def __init__(self, name, layer, x, y):
        super(Tile, self).__init__()
        self.name = name
        self.x = x
        self.y = y
        self.neighbors = {}
        self.neighbors[self.NORTH] = layer.get_tile(x, y-1)
        self.neighbors[self.SOUTH] = layer.get_tile(x, y+1)
        self.neighbors[self.EAST] = layer.get_tile(x+1, y)
        self.neighbors[self.WEST] = layer.get_tile(x-1, y)
        tile_sheet = pygame.image.load(os.path.join(DATA_DIR, "images", "tiles", name + ".png"))
        cursor = pygame.Rect(0, 0, self.TSIZE, self.TSIZE)
        self.spot = [tile_sheet.subsurface(cursor)]
        cursor.top += self.TSIZE
        self.spot.append(tile_sheet.subsurface(cursor))
        cursor.left += 2 * self.TSIZE
        self.anticorner = [tile_sheet.subsurface(cursor)]
        cursor.left -= 2 * self.TSIZE
        cursor.top += self.TSIZE
        self.corner = [tile_sheet.subsurface(cursor)]
        cursor.left += self.TSIZE
        self.edge = [tile_sheet.subsurface(cursor)]
        cursor.top += self.TSIZE
        self.center = [tile_sheet.subsurface(cursor)]
        cursor.top += 2 * self.TSIZE
        self.center.append(tile_sheet.subsurface(cursor))
        cursor.left -= self.TSIZE
        self.center.append(tile_sheet.subsurface(cursor))
        cursor.left += 2 * self.TSIZE
        self.center.append(tile_sheet.subsurface(cursor))

    def get_image(self):
        NORTH, SOUTH, EAST, WEST = (self.NORTH, self.SOUTH, self.EAST, self.WEST)
        ALL = NORTH & SOUTH & EAST & WEST
        image = None
        like_neighbors = 0
        for direction, neighbor in self.neighbors:
            if neighbor and neighbor.name == self.name:
                like_neighbors += direction

        spot = [0]
        center = [ALL]
        corner = [NORTH+WEST, SOUTH+WEST, SOUTH+EAST, NORTH+EAST]
        edge = [ALL-WEST, ALL-SOUTH, ALL-EAST, ALL-NORTH]
        if like_neighbors not in center + spot + corner + edge:
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
                    rotation = 90 * index

        if rotation:
            image = pygame.transform.rotate(image, rotation)
        return image
