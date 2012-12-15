#!/usr/bin/python

import pygame, sys, os
from pygame.locals import *

WIDTH = 0
HEIGHT = 1
WINDOW_SIZE = (600,200)
WINDOW_TITLE = "Hark! A turtle."
BACKGROUND_COLOR = (50, 200, 70)
LEFT_KEYS = (K_h, K_LEFT)
RIGHT_KEYS = (K_l, K_RIGHT)
UP_KEYS = (K_k, K_UP)
DOWN_KEYS = (K_j, K_DOWN)
CONTROLS = (LEFT_KEYS, RIGHT_KEYS, UP_KEYS, DOWN_KEYS)
LEFT, RIGHT, UP, DOWN = (0, 1, 2, 3)

def input(events):
    for event in events:
        if event.type is QUIT or (event.type is KEYDOWN and event.key is K_q):
            sys.exit(0)
        elif event.type is KEYDOWN:
            keys_down[event.key] = True
        elif event.type is KEYUP:
            keys_down[event.key] = False

class Turtle(pygame.sprite.Sprite):
    def __init__(self):
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
        self.image = pygame.image.load(self.images[direction]).convert()
        self.image.set_colorkey(self.image.get_at((0,0)))

    def update(self):
        for key in LEFT_KEYS:
            if keys_down.get(key):
                self.reimage(LEFT)
                self.move(LEFT)
        for key in RIGHT_KEYS:
            if keys_down.get(key):
                self.reimage(RIGHT)
                self.move(RIGHT)
        for key in UP_KEYS:
            if keys_down.get(key):
                self.move(UP)
        for key in DOWN_KEYS:
            if keys_down.get(key):
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

# Set up pygame and the window.
pygame.init()
window = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption(WINDOW_TITLE)
screen = pygame.display.get_surface()
background = pygame.Surface(screen.get_size()).convert()
background.fill(BACKGROUND_COLOR)

# Set up sprites.
player = Turtle()
allsprites = pygame.sprite.RenderPlain((player, ))

# Other setup.
keys_down = dict()
clock = pygame.time.Clock()

while True:
    # OKAY LET'S DO THIS THING
    clock.tick(60)
    input(pygame.event.get())
    allsprites.update()

    screen.blit(background, (0,0))
    allsprites.draw(screen)
    pygame.display.flip()
