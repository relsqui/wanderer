#!/usr/bin/python

import pygame, sys
from modules.constants import *
from modules.sprites import Turtle
from modules import game

def input(events):
    for event in events:
        if event.type is QUIT or (event.type is KEYDOWN and event.key is K_q):
            sys.exit(0)
        elif event.type is KEYDOWN:
            game.keys_down[event.key] = True
        elif event.type is KEYUP:
            game.keys_down[event.key] = False

# Set up sprites.
player = Turtle()
allsprites = pygame.sprite.RenderPlain((player, ))

while True:
    # OKAY LET'S DO THIS THING
    game.clock.tick(60)
    input(pygame.event.get())
    allsprites.update()

    game.screen.blit(game.background, (0,0))
    allsprites.draw(game.screen)
    pygame.display.flip()
