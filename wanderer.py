#!/usr/bin/python

import pygame
from wanderer import game

pygame.init()

print "Welcome! Initializing game ..."
game = game.Game()
try:
    game.load()
except IOError:
    print "No savefile found or not readable, starting new game."
    game.new()
game.init_controls()
game.confirm_start()

while not game.finished:
    game.loop()

pygame.quit()
# ^ not usually necessary, but some interpreters hang without it
print "Goodbye!"
