#!/usr/bin/python

import pygame
from wanderer import game

pygame.init()

print "Welcome! Initializing game ..."
game = game.Game()
while not game.finished:
    game.loop()

pygame.quit()
# ^ not usually necessary, but some interpreters hang without it
print "Goodbye!"
