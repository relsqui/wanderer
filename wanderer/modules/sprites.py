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
        if newpos.left < self.area.left or newpos.right > self.area.right or newpos.top < self.area.top or newpos.bottom > self.area.bottom:
            self.velocity = 0
        else:
            self.rect = newpos

    def accelerate(self, direction):
        oldpos = self.rect
        if direction is LEFT:
            self.reimage(LEFT)
            self.velocity = (-1 * self.speed, 0)
        elif direction is RIGHT:
            self.reimage(RIGHT)
            self.velocity = (self.speed, 0)
        elif direction is UP:
            self.reimage(UP)
            self.velocity = (0, -1 * self.speed)
        elif direction is DOWN:
            self.reimage(DOWN)
            self.velocity = (0, self.speed)
