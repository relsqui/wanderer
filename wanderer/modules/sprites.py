import pygame, os
from modules.constants import *

class Character(pygame.sprite.Sprite):
    def __init__(self, screen, sheet):
        super(Character, self).__init__()
        self.sheet = sheet
        self.colorkey = self.sheet.get_at((0,0))
        self.images = [[x for x in xrange(3)] for x in xrange(4)]
        self.init_images()
        self.reimage(DOWN, 1)
        self.area = screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center
        self.speed = 3
        self.velocity = (0,0)

    def init_images(self):
        for direction in (DOWN, LEFT, RIGHT, UP):
            for position in (0, 1, 2):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.images[direction][position] = self.sheet.subsurface(cursor)

    def reimage(self, direction, position = 1):
        self.image = self.images[direction][position]
        self.image.set_colorkey(self.colorkey)

    def update(self):
        oldpos = self.rect
        newpos = oldpos.move(self.velocity)
        if newpos.left > self.area.left and newpos.right < self.area.right and newpos.top > self.area.top and newpos.bottom < self.area.bottom:
            self.rect = newpos

    def move(self, direction):
        self.reimage(direction)
        self.accelerate(direction)

    def accelerate(self, direction):
        xvel, yvel = self.velocity
        if direction is LEFT:
            xvel -= self.speed
        elif direction is RIGHT:
            xvel += self.speed
        elif direction is UP:
            yvel -= self.speed
        elif direction is DOWN:
            yvel += self.speed
        xvel = min(xvel, self.speed)
        xvel = max(xvel, -1 * self.speed)
        yvel = min(yvel, self.speed)
        yvel = max(yvel, -1 * self.speed)
        self.velocity = (xvel, yvel)
