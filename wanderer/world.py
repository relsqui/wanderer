import pygame, numpy
from pytmx import tmxloader
from wanderer.constants import *


class Map(object):
    "Stores data about the map. Initialize with the location of a map to load."

    def __init__(self, map_location):
        self.data = tmxloader.load_pygame(map_location)
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
