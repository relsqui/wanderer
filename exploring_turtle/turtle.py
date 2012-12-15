#!/usr/bin/python

import pygame, sys
from modules.constants import *
from modules import game, sprites, particles

def input(events):
    for event in events:
        if event.type is QUIT or (event.type is KEYDOWN and event.key is K_q):
            sys.exit(0)
        elif event.type is KEYDOWN:
            game.keys_down[event.key] = True
            if event.key is K_SPACE:
                import random
                player.say(random.choice(GREETINGS))
        elif event.type is KEYUP:
            game.keys_down[event.key] = False

# Set up sprites.
player = sprites.Turtle()
sprites.all_sprites.add(player)

while True:
    # Here we go!
    game.clock.tick(60)
    input(pygame.event.get())
    sprites.all_sprites.update()
    particles.all_particles.update()

    game.screen.blit(game.background, (0,0))
    sprites.all_sprites.draw(game.screen)
    particles.all_particles.draw(game.screen)
    pygame.display.flip()
