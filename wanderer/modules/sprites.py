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

    def init_images(self):
        for direction in (DOWN, LEFT, RIGHT, UP):
            for position in (0, 1, 2):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.images[direction][position] = self.sheet.subsurface(cursor)

    def reimage(self, direction, position = 1):
        self.image = self.images[direction][position]
        self.image.set_colorkey(self.colorkey)

    def update(self):
        pass

    def move(self, direction):
        oldpos = self.rect
        if direction is LEFT:
            self.reimage(LEFT)
            newpos = oldpos.move(-1 * self.speed, 0)
        elif direction is RIGHT:
            self.reimage(RIGHT)
            newpos = oldpos.move(self.speed, 0)
        elif direction is UP:
            newpos = oldpos.move(0, -1 * self.speed)
        elif direction is DOWN:
            newpos = oldpos.move(0, self.speed)
        if newpos.left < self.area.left or newpos.right > self.area.right or newpos.top < self.area.top or newpos.bottom > self.area.bottom:
            return
        else:
            self.rect = newpos
