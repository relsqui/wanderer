import pygame, os
from modules.constants import *

class Turtle(pygame.sprite.Sprite):
    def __init__(self, screen):
        super(Turtle, self).__init__()
        self.images = dict()
        self.images[LEFT] = "Turtle-left.png"
        self.images[RIGHT] = "Turtle-right.png"
        self.reimage(RIGHT)
        self.area = screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center
        self.speed = 3

    def reimage(self, direction):
        self.image = pygame.image.load(os.path.join("images", self.images[direction])).convert()
        self.image.set_colorkey(self.image.get_at((0,0)))

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
