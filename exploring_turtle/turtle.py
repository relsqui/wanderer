#!/usr/bin/python

import pygame, sys, os
from modules.constants import *
from modules.sprites import Player

if not pygame.font:
    print "Couldn't load pygame.font!"
    sys.exit(1)

def input(events):
    for event in events:
        if event.type is QUIT or (event.type is KEYDOWN and event.key is K_q):
            sys.exit(0)
        elif event.type is KEYDOWN:
            keys_down[event.key] = True
        elif event.type is KEYUP:
            keys_down[event.key] = False

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
font = pygame.font.Font(None, 20)

while True:
    # OKAY LET'S DO THIS THING
    clock.tick(60)
    input(pygame.event.get())
    allsprites.update()

    screen.blit(background, (0,0))
    allsprites.draw(screen)
    pygame.display.flip()
