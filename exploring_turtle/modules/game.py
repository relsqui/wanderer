import pygame
from modules.constants import *

if not pygame.font:
    print "Couldn't load pygame.font!"
    sys.exit(1)

#Set up pygame and the window.
pygame.init()
window = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption(WINDOW_TITLE)
screen = pygame.display.get_surface()
background = pygame.Surface(screen.get_size()).convert()
background.fill(BACKGROUND_COLOR)

# Other setup.
keys_down = dict()
clock = pygame.time.Clock()
font = pygame.font.Font(None, 20)
