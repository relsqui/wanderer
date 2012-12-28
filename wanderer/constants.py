"""
Various constants for use in other modules.
"""

import os, sys
from pygame.locals import *

# General
DOWN, LEFT, RIGHT, UP = (0, 1, 2, 3)
OPPOSITE = [UP, RIGHT, LEFT, DOWN]

# Sprites
SPRITE_WIDTH = 32   # pixels
SPRITE_HEIGHT = 34  # pixels

if getattr(sys, 'frozen', None):
    BASEDIR = sys._MEIPASS
else:
    BASEDIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASEDIR, "data")
