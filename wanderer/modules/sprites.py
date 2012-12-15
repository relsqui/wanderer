import pygame, os
from modules.constants import *

class Character(pygame.sprite.Sprite):
    def __init__(self, screen, sheet):
        super(Character, self).__init__()
        self.sheet = sheet
        self.colorkey = self.sheet.get_at((0,0))
        self.images = [[x for x in xrange(3)] for x in xrange(4)]
        self.init_images()
        self.velocity = (0,0)
        self.direction = DOWN
        self.position = 1
        self.walk_timer = 0
        self.image = self.images[self.direction][self.position]
        self.image.set_colorkey(self.colorkey)
        self.area = screen.get_rect()
        self.rect = self.image.get_rect()
        self.rect.center = self.area.center
        self.speed = SPRITE_SPEED

    def init_images(self):
        for direction in (DOWN, LEFT, RIGHT, UP):
            self.images[direction] = [0, 1, 2, 3]
            for position in (0, 1, 2):
                cursor = pygame.Rect(position * SPRITE_WIDTH, direction * SPRITE_HEIGHT, SPRITE_WIDTH, SPRITE_HEIGHT)
                self.images[direction][position] = self.sheet.subsurface(cursor)
            self.images[direction][3] = self.images[direction][1]

    def update(self, loop_time):
        if self.velocity == (0,0):
            self.position = 1
        else:
            newpos = self.rect.move(self.velocity)
            if newpos.left > self.area.left and newpos.right < self.area.right and newpos.top > self.area.top and newpos.bottom < self.area.bottom:
                self.rect = newpos
            if self.walk_timer:
                self.walk_timer -= loop_time
                if self.walk_timer < 0:
                    self.walk_timer = 0
            else:
                self.position = (self.position + 1) % 4
                self.walk_timer = WALK_RATE

        self.image = self.images[self.direction][self.position]
        self.image.set_colorkey(self.colorkey)


    def move(self, direction):
        self.direction = direction
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
