import pygame, os
from modules.constants import *
from modules import game, particles

all_sprites = pygame.sprite.RenderClear()

class Turtle(pygame.sprite.Sprite):
    def __init__(self):
        super(Turtle, self).__init__()
        self.images = dict()
        self.images[LEFT] = "Turtle-left.png"
        self.images[RIGHT] = "Turtle-right.png"
        self.reimage(RIGHT)
        self.area = game.screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center
        self.speed = 3

    def reimage(self, direction):
        self.image = pygame.image.load(os.path.join("images", self.images[direction])).convert()
        self.image.set_colorkey(self.image.get_at((0,0)))

    def update(self):
        for key in LEFT_KEYS:
            if game.keys_down.get(key):
                self.reimage(LEFT)
                self.move(LEFT)
        for key in RIGHT_KEYS:
            if game.keys_down.get(key):
                self.reimage(RIGHT)
                self.move(RIGHT)
        for key in UP_KEYS:
            if game.keys_down.get(key):
                self.move(UP)
        for key in DOWN_KEYS:
            if game.keys_down.get(key):
                self.move(DOWN)

    def move(self, direction):
        oldpos = self.rect
        if direction is LEFT:
            newpos = oldpos.move(-1 * self.speed, 0)
        elif direction is RIGHT:
            newpos = oldpos.move(self.speed, 0)
        elif direction is UP:
            newpos = oldpos.move(0, -1 * self.speed)
        elif direction is DOWN:
            newpos = oldpos.move(0, self.speed)
        if newpos.left < self.area.left or newpos.right > self.area.right or newpos.top < self.area.top or newpos.bottom > self.area.bottom:
            return
        else:
            self.rect = newpos

    def say(self, message):
        destination = self.rect.move(0, -20)
        particles.all_particles.add(particles.TextParticle(message, destination))
